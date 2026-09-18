#!/bin/bash
# Startet eine Reinigung und protokolliert dabei jedes Fehlerereignis.
# Der Roboter faehrt selbst los - dabei wird er zwangslaeufig irgendwo anecken.
set -u

DURATION="${DURATION:-300}"

echo "=== 1. Ausgangszustand ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  state=%s  task=%s  akku=%s%%  fortschritt=%s%%' % (
  o.get('state'), o.get('task_status'), o.get('battery_level'), o.get('cleaning_progress')))
print('  voice_packet=%s  volume=%s' % (o.get('voice_packet_id'), o.get('volume')))
"

echo
echo "=== 2. Reinigung starten ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/start' -m 1
echo "  'start' gesendet"
sleep 20

echo
echo "=== 3. Faehrt er? ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  state=%s  task=%s  prozent=%s' % (
  o.get('state'), o.get('task_status'), o.get('cleaning_progress')))
"

echo
echo "=== 4. Monitor ${DURATION}s: jedes Fehlerereignis wird protokolliert ==="
echo "     (Der Roboter faehrt jetzt durch die Wohnung.)"
timeout $((DURATION + 60)) python3 /tmp/collision_test.py "$DURATION" 2>&1
