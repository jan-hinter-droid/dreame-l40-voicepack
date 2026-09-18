#!/usr/bin/env python3
"""
Langzeit-Monitor fuer Kollisions-Ereignisse waehrend einer echten Reinigung.

Protokolliert jede Aenderung von error/faults/warn_status und zusaetzlich
jeden Wechsel von state und task_type, damit man Anstoesse zuordnen kann.
Schreibt fortlaufend in eine Datei, damit nichts verloren geht.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 360
LOG = Path("/home/pi/bump_watch.log")

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
         "battery_level", "cleaning_progress"]

fh = LOG.open("w", encoding="utf-8")
fh.write(f"=== Monitor gestartet {time.strftime('%Y-%m-%d %H:%M:%S')} "
         f"fuer {DURATION}s ===\n")
fh.flush()

print(f"=== Kollisions-Monitor {DURATION}s ===", flush=True)
print("Der Roboter reinigt. Ich protokolliere jede Fehlerregung.", flush=True)
print("-" * 74, flush=True)

seen: dict = {}
start = time.time()
error_events = 0
while time.time() - start < DURATION:
    time.sleep(0.4)
    for key in WATCH:
        if key not in state:
            continue
        val = state[key]
        if seen.get(key) == val:
            continue
        el = time.time() - start
        mark = ""
        if key in ("error", "faults") and str(val) not in ("0", "None"):
            mark = "   <<<<<< FEHLER"
            error_events += 1
        line = f"[{el:6.1f}s] {key:<20} {seen.get(key)!r:>10} -> {val!r}{mark}"
        print(line, flush=True)
        fh.write(line + "\n")
        fh.flush()
        seen[key] = val

fh.write(f"\n=== Ende. Fehlerereignisse: {error_events} ===\n")
fh.write(f"error={state.get('error')} faults={state.get('faults')} "
         f"warn={state.get('warn_status')}\n")
fh.close()
client.loop_stop()
client.disconnect()

print("-" * 74)
print(f"=== Ergebnis: {error_events} Fehlerereignisse ===")
print(f"  error={state.get('error')}  faults={state.get('faults')}  "
      f"warn_status={state.get('warn_status')}")
print(f"  Protokoll: {LOG}")

if error_events == 0:
    print()
    print("  Kein einziger Fehlercode trotz Reinigung.")
    print("  -> Normales Anecken erzeugt beim L40 KEIN Cloud-Ereignis.")
