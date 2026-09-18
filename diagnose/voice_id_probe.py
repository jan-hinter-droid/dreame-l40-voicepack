#!/usr/bin/env python3
"""
Isoliert, warum siid7/piid4 mit code -1 abgelehnt wird.

Theorie: Das Geraet akzeptiert nur offizielle Sprach-IDs in VOICE_CHANGE.
Testet verschiedene Payloads und zeigt jeweils die volle Antwort.

Aufruf:  install_probe.py [--only N]
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

OUR_MD5 = "3351ea8dd7493a1480b0df612d1352c2"
OUR_SIZE = 29247
OUR_URL = ("https://raw.githubusercontent.com/jan-hinter-droid/"
           "dreame-l40-voicepack/main/dist/smoke-test.tar.gz")

TESTS = [
    ("A: offizielle ID 'DE' + unser Paket", "DE", OUR_URL, OUR_MD5, OUR_SIZE),
    ("B: 'CUSTOM' + unser Paket", "CUSTOM", OUR_URL, OUR_MD5, OUR_SIZE),
    ("C: offizielle ID 'EN' + unser Paket", "EN", OUR_URL, OUR_MD5, OUR_SIZE),
]

only = None
if "--only" in sys.argv:
    only = int(sys.argv[sys.argv.index("--only") + 1])

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME, password="", account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY, auth_key=token, did=bridge.DEVICE_ID,
)
if not cloud.login():
    sys.exit("Login fehlgeschlagen")
info = cloud.get_device_info()          # setzt cloud._host - entscheidend!
if not info:
    sys.exit("get_device_info fehlgeschlagen")
print(f"[i] {info.get('customName')}  Host={cloud._host}\n")

did = str(bridge.DEVICE_ID)

# Volle Antwort sichtbar machen (send() verschluckt die Huelle)
raw_responses: list = []
original = cloud._api_call


def spy(url, params=None, retry_count=2, timeout=None):
    result = original(url, params, retry_count, timeout)
    raw_responses.append(result)
    return result


cloud._api_call = spy


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


def do_test(label, lang_id, url, md5, size):
    print("=" * 74)
    print(label)
    print("=" * 74)
    before = read_voice()
    print("  vorher :", json.dumps(before, ensure_ascii=False))

    payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (lang_id, url, md5, size)
    raw_responses.clear()
    result = cloud.send("set_properties", [
        {"did": did, "siid": 7, "piid": 4, "value": payload},
    ], retry_count=1, timeout=25)

    print("  Ergebnis:", json.dumps(result, ensure_ascii=False))
    if raw_responses:
        env = raw_responses[-1]
        print("  Huelle  :", json.dumps(env, ensure_ascii=False)[:700])

    ok = isinstance(result, list) and result and result[0].get("code") == 0
    if not ok:
        print("  -> abgelehnt\n")
        return False

    print("  angenommen - warte auf Wirkung ...")
    for i in range(20):
        time.sleep(6)
        now = read_voice()
        print(f"    [{i*6+6:3d}s] {json.dumps(now, ensure_ascii=False)}")
        if now.get("packet_id") == lang_id:
            print(f"  -> ERFOLG: packet_id = {lang_id}\n")
            return True
        st = str(now.get("status", ""))
        if "error" in st or "fail" in st:
            print("  -> Status meldet Fehler\n")
            return False
    print("  -> keine Wirkung\n")
    return False


for idx, (label, lang_id, url, md5, size) in enumerate(TESTS, start=1):
    if only is not None and idx != only:
        continue
    do_test(label, lang_id, url, md5, size)
    time.sleep(3)

print("[i] Fertig.")
