#!/usr/bin/env python3
"""
Findet heraus, welche Befehle beim L40 tatsaechlich Ton ausloesen.

Wichtig: Dieser Test erzeugt bewusst nur kurze, unkritische Zustandswechsel
und setzt alles wieder zurueck.

Kandidaten:
  1. VOICE_TEST   (siid 7 / piid 9)  - ungetestete Property
  2. VOLUME       (siid 7 / piid 1)  - Loeschen/Schreiben
  3. LOCATE-Action(siid 7 / aiid 1)  - bekanntermassen laut
  4. SUCTION      (siid 4 / piid 4)  - Saugstufe aendern
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
print(f"[i] verbunden, packet={bridge.MODEL}")


def setprop(siid, piid, value, label):
    print(f"\n--- {label}  (siid {siid} / piid {piid} = {value!r}) ---", flush=True)
    res = cloud.send("set_properties",
                     [{"did": did, "siid": siid, "piid": piid, "value": value}],
                     retry_count=1, timeout=25)
    print("    Antwort:", json.dumps(res, ensure_ascii=False))
    print("    >>> HINGEHÖRT? <<<", flush=True)
    time.sleep(7)


def action(siid, aiid, label, params=None):
    print(f"\n--- {label}  (action {siid}/{aiid}) ---", flush=True)
    res = cloud.send("action", {"did": did, "siid": siid, "aiid": aiid,
                                "in": params or []}, retry_count=1, timeout=25)
    print("    Antwort:", json.dumps(res, ensure_ascii=False))
    print("    >>> HINGEHÖRT? <<<", flush=True)
    time.sleep(7)


print("=" * 70)
print("TEST: Welche Befehle loesen Ton aus?")
print("=" * 70)

# 1) VOICE_TEST - bisher nur auf 0/1 gesetzt, ohne bekannte Wirkung
setprop(7, 9, 1, "VOICE_TEST = 1")
setprop(7, 9, 0, "VOICE_TEST = 0")

# 2) Saugstufe aendern (harmlos, wird gleich zurueckgesetzt)
for level, name in ((0, "quiet"), (2, "strong"), (1, "standard")):
    setprop(4, 4, level, f"SUCTION_LEVEL = {level} ({name})")

# 3) Lautstaerke
setprop(7, 1, 5, "VOLUME = 5")
setprop(7, 1, 10, "VOLUME = 10")

# 4) Locate als Kontrolle - das ist bekannt laut
action(7, 1, "LOCATE (Kontrolle)")

print()
print("=" * 70)
print("Fertig. Bitte mitteilen, bei welchen Schritten Ton kam.")
print("=" * 70)
