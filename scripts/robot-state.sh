#!/bin/bash
# Zeigt den aktuellen Zustand des Roboters - Voraussetzung fuer die Sprachpaket-Installation.
set -u

echo "=== Mitschnitt (4 Nachrichten) ==="
timeout 12 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 4 > /tmp/state_now.json 2>/dev/null &
SUBPID=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"refresh"}'
wait $SUBPID 2>/dev/null || true

python3 - <<'PYEOF'
import json

raw = open("/tmp/state_now.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder()
idx = 0
last = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace():
        idx += 1
    if idx >= len(raw):
        break
    obj, end = dec.raw_decode(raw, idx)
    idx = end
    last = obj

if last is None:
    print("KEINE Daten empfangen")
    raise SystemExit(1)

watch = [
    "state", "status", "task_status", "task_type", "battery_level",
    "charging_status", "cleaning_paused", "scheduled_clean", "error",
    "faults", "self_wash_base_status", "auto_empty_status",
    "voice_packet_id", "voice_change_status", "volume",
    "station_drainage_status", "dock_cleaning_status",
    "bridge_mode", "online",
]
print("%-24s %s" % ("Feld", "Wert"))
print("-" * 60)
for k in watch:
    if k in last:
        print("%-24s %s" % (k, last[k]))

print()
snap = {k: last.get(k) for k in ("task_status", "task_type", "state", "battery_level", "bridge_mode")}
busy = str(snap.get("task_status", "")).lower() not in ("", "completed", "idle", "none")
print("task_status =", snap.get("task_status"), "| state =", snap.get("state"),
      "| bridge_mode =", snap.get("bridge_mode"))
print("EINSCHAETZUNG:", "GERAET BESCHAEFTIGT - Installation besser spaeter" if busy
      else "IDLE/DOCKED - Installation kann laufen")
PYEOF
