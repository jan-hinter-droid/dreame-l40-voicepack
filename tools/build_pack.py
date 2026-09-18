#!/usr/bin/env python3
"""
Baut ein Dreame-Sprachpaket (tar.gz mit Ogg-Vorbis, mono 16 kHz) aus einer
Text-Tabelle und liefert MD5 + Groesse fuer den Install-Befehl.

Pipeline:  CSV -> SAPI-TTS (WAV) -> ffmpeg loudnorm -> OGG Vorbis -> tar.gz
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

# --- Encoding-Profil: entspricht dem GLaDOS-Referenzpack, das auf Dreame laeuft
SAMPLE_RATE = 16000
CHANNELS = 1
OGG_QUALITY = 4          # ~100 kbit/s bei 16 kHz mono
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

PS_TTS = r"""
param([string]$Voice, [string]$ListFile)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice($Voice)
$synth.Rate = 0
$synth.Volume = 100
foreach ($line in [System.IO.File]::ReadAllLines($ListFile, [System.Text.Encoding]::UTF8)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line -split "`t", 2
    if ($parts.Count -lt 2) { continue }
    $synth.SetOutputToWaveFile($parts[0])
    $synth.Speak($parts[1])
}
$synth.SetOutputToNull()
$synth.Dispose()
Write-Output "TTS fertig"
"""


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        sys.exit(f"FEHLER: '{name}' nicht gefunden (bitte installieren und in PATH legen).")
    return path


def read_phrases(csv_path: Path) -> list[tuple[int, str]]:
    """Liest id;text;note und gibt nur Zeilen mit echtem Text zurueck."""
    rows: list[tuple[int, str]] = []
    seen: set[int] = set()
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        header = next(reader, None)
        if not header or header[0].strip().lower() != "id":
            sys.exit("FEHLER: CSV muss mit der Kopfzeile 'id;text;note' beginnen.")
        for lineno, row in enumerate(reader, start=2):
            if not row or not row[0].strip():
                continue
            try:
                sid = int(row[0].strip())
            except ValueError:
                sys.exit(f"FEHLER: Zeile {lineno}: '{row[0]}' ist keine Zahl.")
            text = row[1].strip() if len(row) > 1 else ""
            if not text:
                continue                      # leere Zeile = Werkssound behalten
            if sid in seen:
                sys.exit(f"FEHLER: Zeile {lineno}: ID {sid} kommt doppelt vor.")
            seen.add(sid)
            rows.append((sid, text))
    return rows


def synth_tts(rows: list[tuple[int, str]], wav_dir: Path, voice: str) -> None:
    """Erzeugt alle WAV-Dateien in EINEM PowerShell-Prozess (SAPI-Start ist teuer)."""
    list_file = wav_dir / "_tts_list.txt"
    lines = [f"{wav_dir / f'{sid}.wav'}\t{text}" for sid, text in rows]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    script_file = wav_dir / "_tts.ps1"
    script_file.write_text(PS_TTS, encoding="utf-8")

    subprocess.run(
        [tool("powershell"), "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(script_file), "-Voice", voice, "-ListFile", str(list_file)],
        check=True,
    )


def encode(src_wav: Path, dst_ogg: Path) -> None:
    """Resample + Loudness-Normalisierung + Vorbis-Encoding in einem ffmpeg-Lauf."""
    cmd = [
        tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src_wav),
        "-af", LOUDNORM,
        "-ar", str(SAMPLE_RATE),
        "-ac", str(CHANNELS),
        "-c:a", "libvorbis",
        "-q:a", str(OGG_QUALITY),
        str(dst_ogg),
    ]
    subprocess.run(cmd, check=True)


def build_tar(ogg_dir: Path, tar_path: Path) -> None:
    """tar.gz mit flacher Struktur (keine Unterordner) - so erwartet es der Roboter."""
    names = sorted(ogg_dir.glob("*.ogg"), key=lambda p: int(p.stem))
    with tarfile.open(tar_path, "w:gz") as tar:
        for name in names:
            info = tar.gettarinfo(str(name), arcname=name.name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 1700000000            # deterministisch
            with name.open("rb") as fh:
                tar.addfile(info, fh)


def resolve(base: Path, value: str, *, prefer: str = "cwd") -> Path:
    """Relative Pfade aufloesen: erst bevorzugte Basis, dann die andere."""
    p = Path(value)
    if p.is_absolute():
        return p
    first, second = ((Path.cwd(), base) if prefer == "cwd" else (base, Path.cwd()))
    cand_first = (first / p).resolve()
    cand_second = (second / p).resolve()
    if cand_first.exists():
        return cand_first
    if cand_second.exists():
        return cand_second
    return cand_first


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="../phrases/de_custom.csv")
    ap.add_argument("--out", default="../dist")
    ap.add_argument("--pack", default="de-custom", help="Name des Pakets/der Dateien")
    ap.add_argument("--voice", default="Microsoft Hedda Desktop")
    ap.add_argument("--keep-work", action="store_true", help="Zwischendateien behalten")
    ap.add_argument(
        "--overrides",
        default="../sounds/overrides",
        help="Ordner mit <id>.ogg, die TTS fuer diese IDs ersetzen (z.B. 40.ogg = Schrei)",
    )
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    csv_path = resolve(base, args.csv, prefer="cwd")
    out_dir = resolve(base, args.out, prefer="cwd")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_phrases(csv_path)

    override_dir = resolve(base, args.overrides, prefer="script")
    overrides: dict[int, Path] = {}
    if override_dir.is_dir():
        for ogg in sorted(override_dir.glob("*.ogg")):
            if ogg.stem.isdigit():
                overrides[int(ogg.stem)] = ogg

    # Overrides, die nicht in der CSV stehen, kommen als eigene Zeilen dazu
    known = {sid for sid, _ in rows}
    for sid in sorted(overrides):
        if sid not in known:
            rows.append((sid, "(Sound-Override, kein TTS)"))
            known.add(sid)

    print(f"[i] {len(rows)} Ansagen im Paket ({csv_path.name})")
    if overrides:
        print(f"[i] {len(overrides)} Sound-Override(s): "
              + ", ".join(f"{k}={v.name}" for k, v in sorted(overrides.items())))

    work = Path(tempfile.mkdtemp(prefix="dreame-pack-"))
    wav_dir, ogg_dir = work / "wav", work / "ogg"
    wav_dir.mkdir()
    ogg_dir.mkdir()

    try:
        tts_rows = [(sid, t) for sid, t in rows if sid not in overrides]
        print(f"[i] TTS mit Stimme '{args.voice}' ({len(tts_rows)} Ansagen) ...")
        synth_tts(tts_rows, wav_dir, args.voice)

        missing = [sid for sid, _ in tts_rows if not (wav_dir / f"{sid}.wav").exists()]
        if missing:
            sys.exit(f"FEHLER: TTS hat {len(missing)} Dateien nicht erzeugt: {missing[:10]}")

        print(f"[i] Encoding nach OGG Vorbis ({SAMPLE_RATE} Hz, mono, q{OGG_QUALITY}) ...")
        for sid, _ in tts_rows:
            encode(wav_dir / f"{sid}.wav", ogg_dir / f"{sid}.ogg")

        # Overrides muessen auf dasselbe Profil gebracht werden
        for sid, src in overrides.items():
            encode(src, ogg_dir / f"{sid}.ogg")

        tar_path = out_dir / f"{args.pack}.tar.gz"
        build_tar(ogg_dir, tar_path)

        data = tar_path.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        size = len(data)

        durations = (work / "durations.txt")
        with durations.open("w", encoding="utf-8") as fh:
            for sid, text in rows:
                ogg = ogg_dir / f"{sid}.ogg"
                fh.write(f"{sid}\t{ogg.stat().st_size}\t{text}\n")

        print()
        print("=" * 68)
        print(f"  Paket : {tar_path}")
        print(f"  Dateien: {len(rows)} OGGs")
        print(f"  MD5   : {md5}")
        print(f"  size  : {size}")
        print("=" * 68)
        print()
        print("Install-Daten fuer die Bridge:")
        print(f'  lang_id = {args.pack.upper()}')
        print(f'  md5     = {md5}')
        print(f'  size    = {size}')

        if args.keep_work:
            print(f"\n[i] Zwischendateien liegen in {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)

        (out_dir / f"{args.pack}.md5").write_text(md5, encoding="utf-8")
        (out_dir / f"{args.pack}.size").write_text(str(size), encoding="utf-8")
    except Exception:
        print(f"\n[!] Fehlgeschlagen. Zwischendateien liegen in {work}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

