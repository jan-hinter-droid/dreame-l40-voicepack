#!/usr/bin/env python3
"""
Laedt ein Community-Sprachpaket, prueft es und legt eine bereinigte Fassung
in dist/ ab (ohne macOS-Metadaten, deterministisch gepackt).

Aufruf:  fetch_pack.py <name> <url>
"""
from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIST = BASE / "dist"

if len(sys.argv) < 3:
    sys.exit(__doc__)

name, url = sys.argv[1], sys.argv[2]

req = urllib.request.Request(url, headers={"User-Agent": "dreame-voicepack/1.0"})
with urllib.request.urlopen(req, timeout=180) as resp:
    data = resp.read()
print(f"[i] geladen: {len(data):,} Bytes")

with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
    members = [m for m in tar.getmembers() if m.isfile()]
    good = sorted((m for m in members if m.name.endswith(".ogg") and m.name[:-4].isdigit()),
                  key=lambda m: int(m.name[:-4]))
    bad = [m for m in members if m not in good]

print(f"[i] {len(good)} gueltige Sound-IDs, {len(bad)} Fremddateien")
if good:
    ids = [int(m.name[:-4]) for m in good]
    print(f"[i] ID-Bereich {ids[0]}..{ids[-1]}")

# Profil einer Stichprobe (plattformunabhaengig)
import tempfile
probe_path = Path(tempfile.gettempdir()) / "_probe.ogg"
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
    for m in tar.getmembers():
        if m.name == "7.ogg":
            fh = tar.extractfile(m)
            if fh is not None:
                probe_path.write_bytes(fh.read())
            break
if probe_path.exists():
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,sample_rate,channels", "-of", "csv=p=0", str(probe_path)],
        capture_output=True, text=True)
    print(f"[i] Profil 7.ogg: {probe.stdout.strip()}")

# Bereinigt und deterministisch neu packen
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as out:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as src:
        for m in good:
            fh = src.extractfile(m)
            if fh is None:
                continue
            payload = fh.read()
            info = tarfile.TarInfo(name=m.name)
            info.size = len(payload)
            info.mtime = 1700000000
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            out.addfile(info, io.BytesIO(payload))

clean = buf.getvalue()
md5 = hashlib.md5(clean).hexdigest()
DIST.mkdir(parents=True, exist_ok=True)
tar_path = DIST / f"{name}.tar.gz"
tar_path.write_bytes(clean)
(DIST / f"{name}.md5").write_text(md5, encoding="utf-8")
(DIST / f"{name}.size").write_text(str(len(clean)), encoding="utf-8")

print()
print("=" * 66)
print(f"  Paket : {tar_path}")
print(f"  Dateien: {len(good)} OGGs")
print(f"  MD5   : {md5}")
print(f"  size  : {len(clean)}")
print("=" * 66)
print()
print("Installer-URL (jsDelivr, weil GitHub Raw zu aggressiv cached):")
print(f"  https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/{name}.tar.gz")
