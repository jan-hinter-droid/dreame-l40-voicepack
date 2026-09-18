#!/bin/bash
# Abschlusszustand nach dem Schrei-Test.
set -u

echo "=== Roboter ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/fin2.json 2>/dev/null &
S=$!; sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true

python3 - <<'PYEOF'
import json
raw = open("/tmp/fin2.json", encoding="utf-8", errors="replace").read().strip()
d = json.JSONDecoder(); i = 0; last = None
while i < len(raw):
    while i < len(raw) and raw[i].isspace(): i += 1
    if i >= len(raw): break
    o, e = d.raw_decode(raw, i); i = e; last = o
if last:
    for k in ("voice_packet_id", "voice_change_status", "volume", "state",
              "battery_level", "bridge_mode", "online"):
        print("  %-22s = %s" % (k, last.get(k)))
PYEOF

echo
echo "=== Aufgeraeumte Timer? ==="
systemctl list-units 'dreame-*' --all --no-pager 2>/dev/null | head -6
echo -n "  dreame-scream aktiv: "
systemctl is-active dreame-scream.service 2>&1
echo -n "  dreame-voicecheck aktiv: "
systemctl is-active dreame-voicecheck.timer 2>&1

echo
echo "=== Bridge ==="
systemctl is-active dreame-fhem.service
grep -m1 BRIDGE_VERSION /home/pi/dreame_fhem_bridge.py
