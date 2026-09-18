#!/bin/bash
# Hoerprobe: laesst den Roboter dreimal den Locate-Sound sagen.
set -u

SLEEP_BEFORE="${1:-0}"
COUNT="${2:-3}"

sleep "$SLEEP_BEFORE"
for i in $(seq 1 "$COUNT"); do
  mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m 1
  echo "  [$i/$COUNT] locate gesendet"
  sleep 6
done

echo
echo "=== Aktives Paket ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id = %s' % o.get('voice_packet_id'))
print('  volume    = %s' % o.get('volume'))
"
