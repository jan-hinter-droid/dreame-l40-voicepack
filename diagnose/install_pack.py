#!/usr/bin/env python3
"""
Installiert ein Community-Sprachpaket am L40.

Prueft vorher Archiv, ID-Abdeckung und Audio-Profil und laedt das Paket auf
Wunsch in ein eigenes GitHub-Repo (damit der Roboter es zuverlaessig ziehen kann).

Aufruf:
  install_pack.py <name> <url> [--deploy]
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

BRIDGE = "/home/pi/dreame_fhem_bridge.py"
DEPLOY_DIR = "/home/pi/pack-deploy"

if len(sys.argv) < 3:
    sys.exit(__doc__)

NAME = sys.argv[1]
URL = sys.argv[2]
DEPLOY = "--deploy" in sys.argv

LANG_ID = "".join(c for c in NAME.upper() if c.isalnum())[:32]

print(f"=== {NAME}  ->  lang_id={LANG_ID} ===")

# --- 1. Paket laden und pruefen
req = urllib.request.Request(URL, headers={"User-Agent": "dreame-voicepack/1.0"})
with urllib.request.urlopen(req, timeout=120) as resp:
    data = resp.read()
md5 = hashlib.md5(data).hexdigest()
print(f"[i] geladen: {len(data)} Bytes  md5={md5}")

with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
    members = [m for m in tar.getmembers() if m.isfile()]
    good = [m for m in members if m.name.endswith(".ogg") and m.name[:-4].isdigit()]
    bad = [m for m in members if m not in good]
    ids = sorted(int(m.name[:-4]) for m in good)

print(f"[i] {len(good)} gueltige Sound-IDs, Bereich {ids[0]}..{ids[-1]}")
if bad:
    print(f"[!] {len(bad)} Fremddateien im Archiv (werden entfernt): "
          f"{[m.name for m in bad[:5]]}")
    # Sauberes Archiv ohne Beifang neu packen
    clean = io.BytesIO()
    with tarfile.open(fileobj=clean, mode="w:gz") as out:
        for m in sorted(good, key=lambda x: int(x.name[:-4])):
            info = tarfile.TarInfo(name=m.name)
            info.size = m.size
            info.mtime = 1700000000
            info.mode = 0o644
            out.addfile(info, tar.extractfile(m))
    data = clean.getvalue()
    md5 = hashlib.md5(data).hexdigest()
    print(f"[+] bereinigt: {len(data)} Bytes  md5={md5}")

size = len(data)

# --- 2. Audio-Profil einer Stichprobe
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
    sample = None
    for m in tar.getmembers():
        if m.name == "7.ogg":
            sample = tar.extractfile(m).read()
            break
if sample:
    tmp = Path("/tmp/probe_sample.ogg")
    tmp.write_bytes(sample)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,sample_rate,channels", "-of", "csv=p=0", str(tmp)],
        capture_output=True, text=True)
    print(f"[i] Profil Stichprobe 7.ogg: {probe.stdout.strip()}")

# --- 3. Deployment
if DEPLOY:
    Path(DEPLOY_DIR).mkdir(parents=True, exist_ok=True)
    out = Path(DEPLOY_DIR) / f"{LANG_ID.lower()}.tar.gz"
    out.write_bytes(data)
    print(f"[i] abgelegt: {out}")

# --- 4. Installation
spec = importlib.util.spec_from_file_location("dreame_bridge_probe", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
sys.modules["dreame_bridge_probe"] = bridge
spec.loader.exec_module(bridge)

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME, password="", account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY, auth_key=token, did=bridge.DEVICE_ID)
if not cloud.login():
    sys.exit("Login fehlgeschlagen")
if not cloud.get_device_info():
    sys.exit("get_device_info fehlgeschlagen")
did = str(bridge.DEVICE_ID)


def read_voice():
    r = cloud.send("get_properties",
                   [{"did": did, "siid": 7, "piid": 2},
                    {"did": did, "siid": 7, "piid": 3}],
                   retry_count=1, timeout=20)
    out = {}
    if isinstance(r, list):
        for it in r:
            if it.get("piid") == 2:
                out["packet_id"] = it.get("value")
            elif it.get("piid") == 3:
                out["status"] = it.get("value")
    return out


print(f"[i] vorher: {json.dumps(read_voice(), ensure_ascii=False)}")

payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (
    LANG_ID, URL if not DEPLOY else f"file://{DEPLOY_DIR}/{LANG_ID.lower()}.tar.gz",
    md5, size)

if DEPLOY:
    print("[i] --deploy gesetzt, aber der Roboter braucht eine oeffentliche URL.")
    print("[i] Installation wird uebersprungen. Bitte URL nach dem Push angeben.")
    sys.exit(0)

print(f"[i] installiere ...")
res = cloud.send("set_properties",
                 [{"did": did, "siid": 7, "piid": 4, "value": payload}],
                 retry_count=1, timeout=25)
print("Antwort:", json.dumps(res, ensure_ascii=False))

start = time.time()
last = None
while time.time() - start < 240:
    time.sleep(5)
    now = read_voice()
    key = json.dumps(now, ensure_ascii=False, sort_keys=True)
    if key != last:
        print(f"[{int(time.time()-start):3d}s] {key}")
        last = key
    st = str(now.get("status", ""))
    if '"state":"success"' in st and now.get("packet_id") == LANG_ID:
        print(f"\n[+] {NAME} ist aktiv.")
        break
    if '"state":"fail"' in st:
        print("\n[!] fehlgeschlagen.")
        break
