#!/usr/bin/env python3
"""
Kontrollierter Kollisionstest.

Protokolliert 240s lang alles, was auf einen Anstoss hindeuten koennte.
Der Roboter muss dabei FAHREN und absichtlich blockiert werden.

Aufruf: collision_test.py [sekunden]
"""
from __future__ import annotations

import json
import sys
import time

import paho.mqtt.client as mqtt

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 240

state: dict = {}


def on_message(client, userdata, msg):
    try:
        state.update(json.loads(msg.payload.decode("utf-8")))
    except Exception:
        pass


try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except Exception:
    client = mqtt.Client()

client.on_message = on_message
client.connect("127.0.0.1", 1883, keepalive=60)
client.subscribe("dreame/L40/state", qos=0)
client.loop_start()

WATCH = ["error", "faults", "warn_status", "state", "task_status", "task_type",
         "cleaning_progress", "relocation_status", "voice_change_status"]

print(f"=== Kollisionstest {DURATION}s ===")
print("Roboter muss FAHREN. Blockiere ihn absichtlich (Hand vor den Bumper,")
print("oder ein Handtuch unter die Räder legen).")
print("-" * 74, flush=True)

seen: dict = {}
start = time.time()
hits = 0
while time.time() - start < DURATION:
    time.sleep(0.4)
    for key in WATCH:
        if key not in state:
            continue
        val = state[key]
        if seen.get(key) == val:
            continue
        line = f"[{time.time()-start:6.1f}s] {key:<20} {seen.get(key)!r:>12} -> {val!r}"
        if key in ("error", "faults") and str(val) not in ("0", "None"):
            line += "   <<<<<< FEHLER"
            hits += 1
        print(line, flush=True)
        seen[key] = val

client.loop_stop()
client.disconnect()
print("-" * 74)
print(f"=== {hits} Fehlerereignisse ===")
print(f"  error={state.get('error')}  faults={state.get('faults')}")
if hits == 0:
    print("  -> Auch bei absichtlicher Blockade kein Fehlercode.")
