#!/bin/bash
# Laesst den Roboter mehrfach den Locate-Spruch sagen - reine Hoerprobe.
# Aendert KEINEN Zustand, der Roboter bewegt sich nicht.
set -u

COUNT="${COUNT:-5}"
GAP="${GAP:-5}"

echo "=== Zustand ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id=%s  volume=%s  state=%s' % (
    o.get('voice_packet_id'), o.get('volume'), o.get('state')))
print('  status=%s' % o.get('voice_change_status'))
"

echo
echo "=== $COUNT x locate im ${GAP}s-Takt (macht nichts ausser sprechen) ==="
START=$(date +%s)
for i in $(seq 1 "$COUNT"); do
  mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m 1
  T=$(( $(date +%s) - START ))
  echo "  [t+${T}s] locate $i/$COUNT gesendet"
  sleep "$GAP"
done

echo
echo "=== Fertig. Letzte Befehle im Log: ==="
journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep "Befehl: locate" | tail -"$COUNT"
