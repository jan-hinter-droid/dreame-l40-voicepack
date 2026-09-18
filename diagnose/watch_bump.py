#!/usr/bin/env python3
"""
Live-Monitor: protokolliert alles, was auf einen Anstoss hindeutet.

Beobachtet ERROR, FAULTS, WARN_STATUS, STATE und den Sprachwechsel-Status
und schreibt jede Aenderung mit Zeitstempel weg.

Aufruf: watch_bump.py [sekunden]
"""
from __future__ import annotations

import json
import sys
import time

import paho.mqtt.client as mqtt

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 180

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
client.connect("127.0.0.1", 1883, keepalive=30)
client.subscribe("dreame/L40/state", qos=0)
client.loop_start()

WATCH = ["error", "faults", "warn_status", "state", "state_raw", "status",
         "task_status", "task_type", "battery_level", "cleaning_progress",
         "voice_change_status", "voice_packet_id", "relocation_status"]

print(f"=== Live-Monitor fuer {DURATION}s ===")
print("Beobachte:", ", ".join(WATCH))
print("Stoss den Roboter jetzt an! (vorne gegen den Bumper tippen)")
print("-" * 70, flush=True)

seen = {}
start = time.time()
last_voice = None
while time.time() - start < DURATION:
    time.sleep(0.5)
    for key in WATCH:
        if key not in state:
            continue
        val = state[key]
        if seen.get(key) != val:
            el = time.time() - start
            marker = ""
            if key in ("error", "faults") and val not in (0, "0"):
                marker = "   <<<<<< FEHLER!"
            print(f"[{el:6.1f}s] {key:<22} {seen.get(key)!r:>12} -> {val!r}{marker}",
                  flush=True)
            seen[key] = val

client.loop_stop()
client.disconnect()

print("-" * 70)
print("=== Zusammenfassung der Fehlerwerte ===")
print(f"  error        = {state.get('error')}")
print(f"  faults       = {state.get('faults')}")
print(f"  warn_status  = {state.get('warn_status')}")
print(f"  state        = {state.get('state')}")
