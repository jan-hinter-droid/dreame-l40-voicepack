#!/usr/bin/env python3
"""
Echter Test: Sprachpaket-Installation ueber die Dreame-Cloud.

Wichtig: Die Bridge setzt cloud._host erst in get_device_info(). Ohne diesen
Schritt fehlt das Host-Praefix in der URL und die API antwortet mit 404.
Diese Reihenfolge wird hier exakt nachgebaut.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time

BRIDGE = "/home/pi/dreame_fhem_bridge.py"

spec = importlib.util.spec_from_file_location("dreame_bridge_probe", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
sys.modules["dreame_bridge_probe"] = bridge
spec.loader.exec_module(bridge)

LANG_ID = sys.argv[1] if len(sys.argv) > 1 else "SMOKE-TEST"
URL = sys.argv[2] if len(sys.argv) > 2 else (
    "https://raw.githubusercontent.com/jan-hinter-droid/"
    "dreame-l40-voicepack/main/dist/smoke-test.tar.gz"
)
MD5 = sys.argv[3] if len(sys.argv) > 3 else "3351ea8dd7493a1480b0df612d1352c2"
SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 29247
DRY_RUN = (len(sys.argv) > 5 and sys.argv[5] == "--dry-run")

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME,
    password="",
    account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY,
    auth_key=token,
    did=bridge.DEVICE_ID,
)

if not cloud.login():
    sys.exit("Login fehlgeschlagen")

# --- DER ENTSCHEIDENDE SCHRITT: Host-Praefix setzen
info = cloud.get_device_info()
if not info:
    sys.exit("get_device_info fehlgeschlagen")
print(f"[i] Verbunden: {info.get('customName')} ({info.get('model')})  Host={cloud._host}")

did = str(bridge.DEVICE_ID)


def read_voice():
    result = cloud.send("get_properties", [
        {"did": did, "siid": 7, "piid": 2},
        {"did": did, "siid": 7, "piid": 3},
    ], retry_count=1, timeout=20)
    out = {}
    if isinstance(result, list):
        for item in result:
            if item.get("piid") == 2:
                out["packet_id"] = item.get("value")
            elif item.get("piid") == 3:
                out["status"] = item.get("value")
    return out


print("\n=== Vorher ===")
print(json.dumps(read_voice(), ensure_ascii=False, indent=2))

payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (LANG_ID, URL, MD5, SIZE)
print(f"\n=== Payload ===\n{payload}")

if DRY_RUN:
    print("\n[i] --dry-run: nichts gesendet.")
    sys.exit(0)

print("\n=== Installation ausloesen ===")
result = cloud.send("set_properties", [
    {"did": did, "siid": 7, "piid": 4, "value": payload},
], retry_count=2)
print("Antwort:", json.dumps(result, ensure_ascii=False))

print("\n=== Verlauf (max. 180s) ===")
last = None
start = time.time()
while time.time() - start < 180:
    state = read_voice()
    key = json.dumps(state, ensure_ascii=False, sort_keys=True)
    if key != last:
        print(f"[{int(time.time() - start):3d}s] {key}")
        last = key
    if state.get("packet_id") == LANG_ID:
        print(f"\n[+] ERFOLG: packet_id ist jetzt '{LANG_ID}'")
        break
    time.sleep(6)
else:
    print("\n[!] Timeout - packet_id unveraendert.")
