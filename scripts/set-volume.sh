#!/bin/bash
# Setzt die Lautstaerke des Roboters und loest eine Hoerprobe aus.
set -u

LEVEL="${1:-10}"

echo "=== Lautstaerke auf $LEVEL setzen ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/volume' -m "$LEVEL"
sleep 5

echo "=== Kontrolle ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/vol.json 2>/dev/null &
S=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true
python3 - <<'PYEOF'
import json
raw = open("/tmp/vol.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder(); idx = 0; last = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace(): idx += 1
    if idx >= len(raw): break
    obj, end = dec.raw_decode(raw, idx); idx = end; last = obj
if last:
    print("  volume              =", last.get("volume"))
    print("  voice_packet_id     =", last.get("voice_packet_id"))
    print("  voice_change_status =", last.get("voice_change_status"))
PYEOF
