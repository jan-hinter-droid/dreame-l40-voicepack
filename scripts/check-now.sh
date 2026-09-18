#!/bin/bash
# Aktueller Sprachpaket-Zustand + volles Bridge-Log der letzten Minuten.
set -u

echo "=== Jetzt-Zustand ==="
timeout 12 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/vp_now.json 2>/dev/null &
S=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true

python3 - <<'PYEOF'
import json
raw = open("/tmp/vp_now.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder(); idx = 0; last = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace(): idx += 1
    if idx >= len(raw): break
    obj, end = dec.raw_decode(raw, idx); idx = end; last = obj
if not last:
    print("  keine Daten"); raise SystemExit(1)
for k in ("voice_packet_id", "voice_change_status", "volume", "bridge_mode",
          "bridge_last_command", "bridge_last_command_error",
          "bridge_last_command_result"):
    v = last.get(k)
    print("  %-28s = %s" % (k, str(v)[:200]))
PYEOF

echo
echo "=== Bridge-Log, letzte 40 Zeilen (ungefiltert) ==="
journalctl -u dreame-fhem.service -n 40 --no-pager | tail -40
