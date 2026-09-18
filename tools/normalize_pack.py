#!/usr/bin/env python3
"""
Normalisiert ein Sprachpaket auf einheitliche Loudness.

Befund am Gordon-Pack:
  * Loudness schwankt zwischen -9 und -17 LUFS (7 dB Unterschied)
  * mehrere Dateien clippen ueber 0 dBFS
  * die leiseste Datei ist ausgerechnet die "Fertig"-Ansage

Das erklaert den Eindruck "zu leise": nicht der Pegel ist das Problem,
sondern die Inkonsistenz - leise Stellen fallen gegen laute ab und der
kleine Lautsprecher verzerrt an den geclippten Stellen.

Vorgehen: zweistufige Loudnorm auf einen Zielwert pro Datei.
  Stufe 1: messen
  Stufe 2: mit gemessenen Werten anwenden (genauer als ein Durchlauf)

Aufruf: normalize_pack.py <quelle.tar.gz> <zielname> [ziel-LUFS]
"""
from __future__ import annotations

import hashlib
import io
import json
import re
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

src_pack = Path(sys.argv[1])
name = sys.argv[2]
target_lufs = sys.argv[3] if len(sys.argv) > 3 else "-11"

ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    sys.exit("ffmpeg nicht gefunden")

work = Path(tempfile.mkdtemp(prefix="normalize-"))
in_dir, out_dir = work / "in", work / "out"
in_dir.mkdir()
out_dir.mkdir()

with tarfile.open(src_pack, "r:gz") as tar:
    members = [m for m in tar.getmembers()
               if m.isfile() and m.name.endswith(".ogg") and m.name[:-4].isdigit()]
    for m in members:
        fh = tar.extractfile(m)
        if fh:
            (in_dir / m.name).write_bytes(fh.read())

files = sorted(in_dir.glob("*.ogg"), key=lambda p: int(p.stem))
print(f"[i] {len(files)} Dateien -> Ziel {target_lufs} LUFS", flush=True)


def measure(path: Path) -> dict | None:
    """Erste Stufe der Loudnorm: messen."""
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path),
         "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=9:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", out, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


measured = 0
for i, p in enumerate(files, 1):
    stats = measure(p)
    dst = out_dir / p.name
    if stats:
        af = (
            f"loudnorm=I={target_lufs}:TP=-1.5:LRA=9:"
            f"measured_I={stats['input_i']}:"
            f"measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:"
            f"measured_thresh={stats['input_thresh']}:"
            f"offset={stats.get('target_offset', 0)}:linear=true"
        )
        measured += 1
    else:
        af = f"loudnorm=I={target_lufs}:TP=-1.5:LRA=9"
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(p),
         "-af", af, "-ar", "16000", "-ac", "1",
         "-c:a", "libvorbis", "-q:a", "5", str(dst)],
        check=True,
    )
    if i % 50 == 0 or i == len(files):
        print(f"  {i}/{len(files)}  (zweistufig: {measured})", flush=True)


def loudness(path: Path) -> tuple[float, float] | None:
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true",
         "-f", "null", "-"], capture_output=True, text=True).stderr
    im = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", out, re.M)
    pm = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if im and pm:
        return float(im[-1]), float(pm[-1])
    return None


def stats_of(directory: Path) -> tuple[float, float, float]:
    vals = [loudness(p) for p in sorted(directory.glob("*.ogg"),
                                        key=lambda x: int(x.stem))[:20]]
    vals = [v for v in vals if v]
    if not vals:
        return (0.0, 0.0, 0.0)
    ls = [v[0] for v in vals]
    ps = [v[1] for v in vals]
    return (sum(ls) / len(ls), min(ls), max(ps))


b_avg, b_min, b_peak = stats_of(in_dir)
a_avg, a_min, a_peak = stats_of(out_dir)

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    for p in sorted(out_dir.glob("*.ogg"), key=lambda x: int(x.stem)):
        data = p.read_bytes()
        info = tarfile.TarInfo(name=p.name)
        info.size = len(data)
        info.mtime = 1700000000
        info.mode = 0o644
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        tar.addfile(info, io.BytesIO(data))

blob = buf.getvalue()
md5 = hashlib.md5(blob).hexdigest()
out_path = DIST / f"{name}.tar.gz"
out_path.write_bytes(blob)
(DIST / f"{name}.md5").write_text(md5, encoding="utf-8")
(DIST / f"{name}.size").write_text(str(len(blob)), encoding="utf-8")

print()
print("=" * 70)
print(f"  vorher : Schnitt {b_avg:6.1f} LUFS   leisester {b_min:6.1f}   Spitze {b_peak:+5.1f} dBFS")
print(f"  nachher: Schnitt {a_avg:6.1f} LUFS   leisester {a_min:6.1f}   Spitze {a_peak:+5.1f} dBFS")
print("=" * 70)
print(f"  Paket : {out_path}")
print(f"  MD5   : {md5}")
print(f"  size  : {len(blob)}")
shutil.rmtree(work, ignore_errors=True)
