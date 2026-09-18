#!/usr/bin/env python3
"""
Diagnose: Warum bleibt VOICE_CHANGE ohne Wirkung?

Importiert die laufende Bridge als Modul und benutzt EXAKT deren Cloud-Objekt,
damit es keinen Konfigurationsunterschied gibt. Setzt nur unkritische Werte.
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
print("[i] Bridge-Modul geladen (ohne main())")

# Cloud-Objekt exakt so aufbauen wie main() es tut (Refresh-Token als auth_key)
token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME,
    password="",
    account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY,
    auth_key=token,
    did=bridge.DEVICE_ID,
)
device_id = bridge.DEVICE_ID
print(f"[i] Modell={bridge.MODEL}  Device-ID={device_id}  Bridge={bridge.BRIDGE_VERSION}")

if not cloud.login():
    sys.exit("Login fehlgeschlagen")
print("[i] Login OK")


def show(title, result):
    print(f"\n--- {title} ---")
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text[:1500])


# 1) Lesen: was liefert siid 7 piid 2/3/4?
show("LESEN siid7 piid2=VOICE_PACKET_ID, piid3=STATUS, piid4=VOICE_CHANGE", cloud.send(
    "get_properties",
    [
        {"did": str(device_id), "siid": 7, "piid": 2},
        {"did": str(device_id), "siid": 7, "piid": 3},
        {"did": str(device_id), "siid": 7, "piid": 4},
    ],
    retry_count=1,
))

# 2) Kontrolle: ist Schreiben auf siid 7 ueberhaupt moeglich? (VOLUME auf Ist-Wert)
show("SCHREIBEN siid7 piid1 VOLUME=1 (Kontrolle, harmlos)", cloud.send(
    "set_properties",
    [{"did": str(device_id), "siid": 7, "piid": 1, "value": 1}],
    retry_count=1,
))

# 3) Der eigentliche Test: ungueltiger Payload - zeigt, ob die Property ueberhaupt
#    beschrieben wird (erwartet einen Fehlercode, KEINE stille Annahme).
show("SCHREIBEN siid7 piid4 mit Absicht ungueltigem Payload", cloud.send(
    "set_properties",
    [{"did": str(device_id), "siid": 7, "piid": 4,
      "value": '{"id":"","url":"","md5":"","size":0}'}],
    retry_count=1,
))

print("\n[i] Fertig.")
