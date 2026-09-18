#!/usr/bin/env python3
"""
Fangt die ROHANTWORT der Dreame-Cloud auf VOICE_CHANGE ab.

send() verschluckt Fehler zu None - hier wird _api_call ummantelt, damit die
komplette JSON-Antwort sichtbar wird.
"""
from __future__ import annotations

import importlib.util
import json
import sys

BRIDGE = "/home/pi/dreame_fhem_bridge.py"

spec = importlib.util.spec_from_file_location("dreame_bridge_probe", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
sys.modules["dreame_bridge_probe"] = bridge
spec.loader.exec_module(bridge)

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
print("[i] Login OK  Land=%s  Device=%s" % (bridge.COUNTRY, bridge.DEVICE_ID))

captured: list = []
original = cloud._api_call


def spy(url, params=None, retry_count=2, timeout=None):
    result = original(url, params, retry_count, timeout)
    captured.append({"url": url, "params": params, "response": result})
    return result


cloud._api_call = spy
did = str(bridge.DEVICE_ID)


def dump(label: str, entry: dict) -> None:
    print("\n" + "=" * 72)
    print(label)
    print("=" * 72)
    print("URL      :", entry["url"])
    print("PARAMS   :", json.dumps(entry["params"], ensure_ascii=False)[:600])
    print("ANTWORT  :", json.dumps(entry["response"], ensure_ascii=False)[:1800])


# --- 1) Lesen
before = len(captured)
cloud.send("get_properties", [
    {"did": did, "siid": 7, "piid": 2},
    {"did": did, "siid": 7, "piid": 3},
    {"did": did, "siid": 7, "piid": 4},
], retry_count=1)
dump("LESEN siid7 piid2/3/4", captured[before])

# --- 2) Schreiben mit ungueltigem Payload -> zeigt, ob die Property beschreibbar ist
before = len(captured)
cloud.send("set_properties", [
    {"did": did, "siid": 7, "piid": 4, "value": '{"id":"","url":"","md5":"","size":0}'},
], retry_count=1)
dump("SCHREIBEN siid7 piid4 (ungueltiger Payload)", captured[before])

# --- 3) Kontrolle: bekannter, funktionierender Schreibzugriff auf siid 7
before = len(captured)
cloud.send("set_properties", [
    {"did": did, "siid": 7, "piid": 1, "value": 1},
], retry_count=1)
dump("SCHREIBEN siid7 piid1 VOLUME=1 (Kontrolle)", captured[before])

print("\n[i] Fertig.")
