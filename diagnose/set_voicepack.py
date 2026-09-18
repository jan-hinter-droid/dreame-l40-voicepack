#!/usr/bin/env python3
"""
Sprachpaket setzen - mit vollem Payload.

Wichtig (am Geraet verifiziert): Der L40 Ultra laedt das Paket IMMER aus dem
Netz. Ein Rollback mit leerer URL scheitert mit state=fail, progress=25.
Werkssprachen brauchen also ebenfalls eine gueltige tar.gz-URL.

Aufruf:
  set_voicepack.py <lang_id> <url> <md5> <size> [--wait]
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time

BRIDGE = "/home/pi/dreame_fhem_bridge.py"

if len(sys.argv) < 5:
    sys.exit(__doc__)

LANG_ID, URL, MD5, SIZE = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
WAIT = "--wait" in sys.argv

spec = importlib.util.spec_from_file_location("dreame_bridge_probe", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
sys.modules["dreame_bridge_probe"] = bridge
spec.loader.exec_module(bridge)

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME, password="", account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY, auth_key=token, did=bridge.DEVICE_ID,
)
if not cloud.login():
    sys.exit("Login fehlgeschlagen")
if not cloud.get_device_info():          # setzt das Host-Praefix
    sys.exit("get_device_info fehlgeschlagen")
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


print("vorher :", json.dumps(read_voice(), ensure_ascii=False))

payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (LANG_ID, URL, MD5, SIZE)
print("payload:", payload)
result = cloud.send("set_properties", [
    {"did": did, "siid": 7, "piid": 4, "value": payload},
], retry_count=1, timeout=25)
print("Antwort:", json.dumps(result, ensure_ascii=False))

ok = isinstance(result, list) and result and result[0].get("code") == 0
if not ok:
    print("[!] Vom Geraet abgelehnt (code -1 = ungueltige id / Rate-Limit).")
    sys.exit(2)

if not WAIT:
    sys.exit(0)

start = time.time()
last = None
while time.time() - start < 180:
    time.sleep(5)
    now = read_voice()
    key = json.dumps(now, ensure_ascii=False, sort_keys=True)
    if key != last:
        print(f"[{int(time.time()-start):3d}s] {key}")
        last = key
    st = str(now.get("status", ""))
    if '"state":"success"' in st and now.get("packet_id") == LANG_ID:
        print(f"\n[+] ERFOLG: '{LANG_ID}' aktiv nach {int(time.time()-start)}s")
        break
    if '"state":"fail"' in st:
        print("\n[!] Installation fehlgeschlagen - URL/MD5/Groesse pruefen.")
        break
