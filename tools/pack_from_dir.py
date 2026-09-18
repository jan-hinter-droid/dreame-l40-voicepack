#!/usr/bin/env python3
"""
Baut aus einem Ordner mit Sounddateien ein installierbares Dreame-Sprachpaket.

Akzeptiert .ogg und .mp3 (wird nach OGG Vorbis 16 kHz mono konvertiert),
Dateiname muss die Sound-ID sein.

Aufruf:  pack_from_dir.py <quellordner> <zielname> [--deploy]
"""
from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIST = BASE / "dist"

if len(sys.argv) < 3:
    sys.exit(__doc__)

src_dir = Path(sys.argv[1])
name = sys.argv[2]

files = sorted(
    (p for p in src_dir.iterdir() if p.suffix.lower() in (".ogg", ".mp3") and p.stem.isdigit()),
    key=lambda p: int(p.stem),
)
if not files:
    sys.exit(f"FEHLER: keine passenden Dateien in {src_dir}")

ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    sys.exit("ffmpeg nicht gefunden")

print(f"[i] {len(files)} Quelldateien, ID-Bereich {files[0].stem}..{files[-1].stem}")

work = Path(tempfile.mkdtemp(prefix="packfromdir-"))
ogg_dir = work / "ogg"
ogg_dir.mkdir()

converted = 0
for f in files:
    out = ogg_dir / f"{f.stem}.ogg"
    if f.suffix.lower() == ".ogg":
        shutil.copy2(f, out)
    else:
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(f),
             "-af", "alimiter=limit=0.97", "-ar", "16000", "-ac", "1",
             "-c:a", "libvorbis", "-q:a", "4", str(out)],
            check=True,
        )
        converted += 1

print(f"[i] {converted} Dateien konvertiert, {len(files) - converted} unveraendert uebernommen")

# tar.gz flach und deterministisch
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    for ogg in sorted(ogg_dir.glob("*.ogg"), key=lambda p: int(p.stem)):
        info = tarfile.TarInfo(name=ogg.name)
        data = ogg.read_bytes()
        info.size = len(data)
        info.mtime = 1700000000
        info.mode = 0o644
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        tar.addfile(info, io.BytesIO(data))

blob = buf.getvalue()
md5 = hashlib.md5(blob).hexdigest()
DIST.mkdir(parents=True, exist_ok=True)
out_path = DIST / f"{name}.tar.gz"
out_path.write_bytes(blob)
(DIST / f"{name}.md5").write_text(md5, encoding="utf-8")
(DIST / f"{name}.size").write_text(str(len(blob)), encoding="utf-8")

# Abdeckung gegen das bekannte Inventar
inv = BASE / "reference" / "sound_inventory.csv"
if inv.exists():
    known = set()
    import csv as _csv
    with inv.open(encoding="utf-8-sig", newline="") as fh:
        rd = _csv.reader(fh, delimiter=";")
        next(rd, None)
        for row in rd:
            if row and row[0].strip().isdigit():
                known.add(int(row[0]))
    have = {int(p.stem) for p in ogg_dir.glob("*.ogg")}
    print(f"[i] Abdeckung: {len(have & known)} von {len(known)} bekannten IDs "
          f"({100 * len(have & known) // max(len(known), 1)}%)")

shutil.rmtree(work, ignore_errors=True)

print()
print("=" * 66)
print(f"  Paket : {out_path}")
print(f"  Dateien: {len(files)} OGGs")
print(f"  MD5   : {md5}")
print(f"  size  : {len(blob)}")
print("=" * 66)
