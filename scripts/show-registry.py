#!/usr/bin/env python3
"""
Fragt die Sprachpaket-Registry ueber MQTT ab und zeigt sie uebersichtlich.
Reines Lesen - installiert nichts.
"""
from __future__ import annotations

import json
import time

import paho.mqtt.client as mqtt

state = {}


def on_message(client, userdata, msg):
    try:
        state.update(json.loads(msg.payload.decode("utf-8")))
    except Exception:
        pass


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) if hasattr(mqtt, "CallbackAPIVersion") \
    else mqtt.Client()
client.on_message = on_message
client.connect("127.0.0.1", 1883, keepalive=30)
client.subscribe("dreame/L40/state", qos=0)
client.loop_start()

time.sleep(2)
# Die Bridge abonniert dreame/L40/set UND dreame/L40/set/# - der Topic-Pfad ist
# der zuverlaessige Weg, weil keine JSON-Struktur noetig ist.
client.publish("dreame/L40/set/voicepack", "list", qos=0)

deadline = time.time() + 30
result = None
while time.time() < deadline:
    time.sleep(1)
    if state.get("bridge_last_command") == "voicepack":
        try:
            result = json.loads(state.get("bridge_last_command_result") or "{}")
        except Exception:
            result = None
        if result and "verfuegbar" in result:
            break

client.loop_stop()
client.disconnect()

if not result or "verfuegbar" not in result:
    print("Keine Registry-Antwort erhalten.")
    raise SystemExit(1)

print("=== Verfuegbare Sprachpakete ===")
for key, name in sorted(result["verfuegbar"].items()):
    marker = "  <-- aktiv" if key == result.get("aktiv", "").lower() else ""
    print(f"  {key:<12} {name}{marker}")
print()
print(f"  Aktiv laut Registry: {result.get('aktiv')}")
print(f"  Volume             : {state.get('volume')}")
