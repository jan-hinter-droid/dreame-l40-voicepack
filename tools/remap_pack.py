#!/usr/bin/env python3
"""
Baut ein Spass-Paket: legt ausgewaehlte Ansagen eines Packs auf andere Slots um.

Damit lassen sich die Sprueche, die per FHEM ausloesbar sind (locate, pause,
resume, start, fertig), mit den lustigsten Zeilen des Packs belegen.

Aufruf: remap_pack.py <quelle.tar.gz> <zielname> <map.json>
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIST = BASE / "dist"

if len(sys.argv) < 4:
    sys.exit(__doc__)

src_pack = Path(sys.argv[1])
name = sys.argv[2]
map_path = Path(sys.argv[3])

mapping = json.loads(map_path.read_text(encoding="utf-8"))

work = Path(tempfile.mkdtemp(prefix="remap-"))
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
print(f"[i] {len(files)} Dateien im Quellpaket", flush=True)

# Ziel-Slots mit Quelldateien belegen
changes = []
for target, source in mapping.items():
    if target.startswith("_"):
        continue
    tpath = in_dir / f"{target}.ogg"
    spath = in_dir / str(source)
    if not spath.exists():
        print(f"[!] Quelle {source} fehlt - {target} wird nicht ersetzt")
        continue
    if int(str(source).split('.')[0]) == int(target):
        continue
    changes.append((int(target), source))

print(f"[i] {len(changes)} Slots werden ersetzt:")
for target, source in changes:
    print(f"      {target:>4}.ogg  <-  {source}")

shutil.copytree(in_dir, out_dir, dirs_exist_ok=True)
for target, source in changes:
    shutil.copy2(in_dir / str(source), out_dir / f"{target}.ogg")

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
print("=" * 66)
print(f"  Paket : {out_path}")
print(f"  Dateien: {len(files)} OGGs")
print(f"  MD5   : {md5}")
print(f"  size  : {len(blob)}")
print("=" * 66)
shutil.rmtree(work, ignore_errors=True)
