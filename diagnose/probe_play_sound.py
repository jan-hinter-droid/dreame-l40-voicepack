#!/usr/bin/env python3
"""
Testet die PLAY_SOUND-Action (siid 7 / aiid 2).

Hypothese: Damit laesst sich eine bestimmte Sound-ID gezielt abspielen.
Die Bridge nutzt diese Action bisher nicht.

Getestet werden mehrere Parameterformen.
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
    country=bridge.COUNTRY, auth_key=token, did=bridge.DEVICE_ID)
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


def show(label, result):
    print(f"\n--- {label} ---")
    print("  Antwort:", json.dumps(result, ensure_ascii=False))


# Variante A: Parameter als Liste von piid/value-Objekten (wie START_WASHING es nutzt)
print("\n=== A: action PLAY_SOUND mit [{'piid':..,'value':..}] ===")
raw.clear()
r = cloud.send("action", {
    "did": did, "siid": 7, "aiid": 2,
    "in": [{"piid": 1, "value": 45}],
}, retry_count=1, timeout=25)
show("A", r)
if raw:
    print("  Huelle:", json.dumps(raw[-1], ensure_ascii=False)[:500])
time.sleep(6)

# Variante B: einfache Liste
print("\n=== B: action PLAY_SOUND mit [45] ===")
raw.clear()
r = cloud.send("action", {"did": did, "siid": 7, "aiid": 2, "in": [45]},
               retry_count=1, timeout=25)
show("B", r)
if raw:
    print("  Huelle:", json.dumps(raw[-1], ensure_ascii=False)[:500])
time.sleep(6)

# Variante C: ohne Parameter
print("\n=== C: action PLAY_SOUND ohne Parameter ===")
raw.clear()
r = cloud.send("action", {"did": did, "siid": 7, "aiid": 2, "in": []},
               retry_count=1, timeout=25)
show("C", r)
if raw:
    print("  Huelle:", json.dumps(raw[-1], ensure_ascii=False)[:500])

print("\n[i] Fertig. Was der Roboter gesagt hat, ist von hier nicht hoerbar.")
