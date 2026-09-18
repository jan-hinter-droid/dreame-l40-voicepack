#!/bin/bash
# Prueft den aktuellen Sprachpaket-Zustand und die letzten Installations-Logs.
set -u

echo "=== Aktueller Zustand ==="
timeout 12 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 3 > /tmp/vp_check.json 2>/dev/null &
SUBPID=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $SUBPID 2>/dev/null || true

python3 - <<'PYEOF'
import json
raw = open("/tmp/vp_check.json", encoding="utf-8", errors="replace").read().strip()
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
    print("keine Daten")
    raise SystemExit(1)
for k in ("voice_packet_id", "voice_change_status", "volume", "bridge_mode",
          "bridge_last_command", "bridge_last_command_error"):
    print("%-24s = %s" % (k, last.get(k)))
PYEOF

echo
echo "=== Bridge-Log: alles zu Sprachpaket/Install ==="
journalctl -u dreame-fhem.service --since "-25min" --no-pager | grep -iE 'sprachpaket|voice|install|befehl' | tail -25
