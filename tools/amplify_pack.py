#!/usr/bin/env python3
"""
Macht ein Sprachpaket lauter.

Hintergrund: Die Gordon-Dateien sind sehr zahm ausgesteuert (Spitzen um
-7 dB). Bei Lautstaerke 10 ist damit Schluss - mehr geht nur ueber die
Dateien selbst.

Vorgehen: Peak-Anhebung auf einen Zielwert + Limiter. Bewusst KEIN harter
Limiter auf 0 dB, weil der kleine Roboter-Lautsprecher sonst verzerrt.

Aufruf: amplify_pack.py <quelle.tar.gz> <ziel.tar.gz> [ziel-pegel-dBFS]
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

src_pack = Path(sys.argv[1])
name = sys.argv[2]
target_peak = sys.argv[3] if len(sys.argv) > 3 else "-1.0"

ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    sys.exit("ffmpeg nicht gefunden")

work = Path(tempfile.mkdtemp(prefix="amplify-"))
in_dir, out_dir = work / "in", work / "out"
in_dir.mkdir()
out_dir.mkdir()

with tarfile.open(src_pack, "r:gz") as tar:
    members = [m for m in tar.getmembers()
               if m.isfile() and m.name.endswith(".ogg") and m.name[:-4].isdigit()]
    tar.extractall(in_dir, members=members)

files = sorted(in_dir.glob("*.ogg"), key=lambda p: int(p.stem))
print(f"[i] {len(files)} Dateien, Ziel-Spitzenpegel {target_peak} dBFS", flush=True)


def peak_of(path: Path) -> float | None:
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    for line in out.splitlines():
        if "max_volume:" in line:
            try:
                return float(line.split("max_volume:")[1].replace("dB", "").strip())
            except ValueError:
                return None
    return None


before = [peak_of(p) for p in files[:15]]
before = [b for b in before if b is not None]
avg_before = sum(before) / len(before) if before else None
print(f"[i] mittlerer Spitzenpegel vorher (Stichprobe 15): "
      f"{avg_before:.1f} dB" if avg_before is not None else "[i] kein Pegel lesbar", flush=True)

gain = None
if avg_before is not None:
    gain = float(target_peak) - avg_before
    gain = max(0.0, min(gain, 12.0))
print(f"[i] Anhebung: {gain:.1f} dB" if gain else "[i] keine Anhebung ermittelt", flush=True)

for i, p in enumerate(files, 1):
    dst = out_dir / p.name
    if gain and gain > 0.2:
        af = f"volume={gain:.2f}dB,alimiter=limit=0.94"
    else:
        af = "alimiter=limit=0.94"
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(p),
         "-af", af, "-ar", "16000", "-ac", "1",
         "-c:a", "libvorbis", "-q:a", "5", str(dst)],
        check=True,
    )
    if i % 100 == 0:
        print(f"  {i}/{len(files)}", flush=True)

# Vergleichsmessung
after = [peak_of(p) for p in sorted(out_dir.glob("*.ogg"), key=lambda x: int(x.stem))[:15]]
after = [a for a in after if a is not None]
avg_after = sum(after) / len(after) if after else None

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
print("=" * 68)
print(f"  vorher  Spitze: {avg_before:.1f} dB" if avg_before is not None else "  vorher: ?")
print(f"  nachher Spitze: {avg_after:.1f} dB" if avg_after is not None else "  nachher: ?")
print(f"  Paket : {out_path}")
print(f"  MD5   : {md5}")
print(f"  size  : {len(blob)}")
print("=" * 68)
shutil.rmtree(work, ignore_errors=True)
