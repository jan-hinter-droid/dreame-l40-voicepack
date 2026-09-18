#!/usr/bin/env python3
"""
Schrei-Kandidaten fuer Sound-ID 40, korrekt gefiltert.

Wichtig: nur EIN -af pro ffmpeg-Lauf, sonst ueberschreibt der letzte den ersten.
Filterkette:  Resample -> Pitch (asetrate) -> Laengenausgleich (atempo) -> Loudnorm
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC_DIR = BASE / "sounds" / "sources"
OUT_DIR = BASE / "sounds" / "candidates"


def run_ffmpeg(args: list[str]) -> None:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg nicht gefunden")
    subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def build(src: Path, name: str, pitch: float, extra: str = "") -> Path:
    """pitch > 1 = hoeher und quietschiger, Laenge bleibt gleich."""
    sr = int(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", str(src)],
        capture_output=True, text=True, check=True,
    ).stdout.strip() or "44100")

    chain = [f"asetrate={sr}*{pitch}", "aresample=16000", f"atempo={1/pitch:.4f}"]
    if extra:
        chain.append(extra)
    chain.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    out = OUT_DIR / f"{name}.ogg"
    run_ffmpeg(["-i", str(src), "-af", ",".join(chain),
                "-ar", "16000", "-ac", "1", "-c:a", "libvorbis", "-q:a", "4", str(out)])
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    wilhelm = SRC_DIR / "wilhelm.ogg"
    enscream = SRC_DIR / "en-us-scream.ogg"

    jobs: list[tuple[Path, str, float, str]] = []
    if wilhelm.exists():
        jobs += [
            (wilhelm, "wilhelm-original", 1.00, ""),
            (wilhelm, "wilhelm-high", 1.35, ""),
            (wilhelm, "wilhelm-veryhigh", 1.60, ""),
        ]
    if enscream.exists():
        jobs += [
            (enscream, "en-original", 1.00, ""),
            (enscream, "en-high", 1.35, ""),
        ]
    if not jobs:
        sys.exit("Keine Quellen in sounds/sources/")

    print(f"{'Variante':<22} {'Pitch':>6} {'Dauer':>7} {'Groesse':>9}  MD5(10)")
    print("-" * 70)
    import hashlib
    for src, name, pitch, extra in jobs:
        out = build(src, name, pitch, extra)
        md5 = hashlib.md5(out.read_bytes()).hexdigest()[:10]
        print(f"{name:<22} {pitch:>6.2f} {duration(out):>6.2f}s {out.stat().st_size:>8} B  {md5}")

    print(f"\n[i] Dateien liegen in {OUT_DIR}")
    print("[i] Anhoeren, dann die Wunschdatei als 40.ogg ins Paket uebernehmen.")


if __name__ == "__main__":
    main()
