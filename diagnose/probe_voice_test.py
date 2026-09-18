#!/usr/bin/env python3
"""
Untersucht, wie man einen bestimmten Sound gezielt abspielen kann.

Kandidaten:
  * VOICE_TEST (siid 7 / piid 9)  - Wert 0 in den Capabilities, Zweck unklar
  * RESONSE_WORD (siid 7 / piid 12) - {"wakeup_ogg":[246]} laut Capabilities

Schreibt nur auf VOICE_TEST und liest danach die Antwort aus.
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

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME, password="", account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY, auth_key=token, did=bridge.DEVICE_ID,
)
if not cloud.login():
    sys.exit("Login fehlgeschlagen")
if not cloud.get_device_info():
    sys.exit("get_device_info fehlgeschlagen")
did = str(bridge.DEVICE_ID)
print(f"[i] verbunden, Host={cloud._host}")

raw: list = []
original = cloud._api_call


def spy(url, params=None, retry_count=2, timeout=None):
    r = original(url, params, retry_count, timeout)
    raw.append(r)
    return r


cloud._api_call = spy


def read(props):
    result = cloud.send("get_properties",
                        [{"did": did, "siid": s, "piid": p} for s, p in props],
                        retry_count=1, timeout=20)
    out = {}
    if isinstance(result, list):
        for item in result:
            out[f"{item.get('siid')}.{item.get('piid')}"] = item.get("value")
    return out


print("\n=== Lesen: VOICE_TEST, RESPONSE_WORD, VOLUME, VOICE_ASSISTANT ===")
print(json.dumps(read([(7, 9), (7, 12), (7, 1), (7, 5), (7, 17)]),
                 ensure_ascii=False, indent=2))

print("\n=== Schreiben VOICE_TEST = 1 ===")
raw.clear()
res = cloud.send("set_properties",
                 [{"did": did, "siid": 7, "piid": 9, "value": 1}],
                 retry_count=1, timeout=20)
print("Antwort:", json.dumps(res, ensure_ascii=False))
time.sleep(3)
print("Zustand danach:", json.dumps(read([(7, 9)]), ensure_ascii=False))

print("\n=== Schreiben VOICE_TEST = 0 (zuruecksetzen) ===")
res = cloud.send("set_properties",
                 [{"did": did, "siid": 7, "piid": 9, "value": 0}],
                 retry_count=1, timeout=20)
print("Antwort:", json.dumps(res, ensure_ascii=False))

print("\n[i] Fertig. Falls der Roboter jetzt gesprochen hat, war VOICE_TEST der Ausloeser.")
