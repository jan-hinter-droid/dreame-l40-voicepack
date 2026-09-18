#!/bin/bash
# Belastungstest: Pack wechseln und sofort einen zweiten Befehl senden.
# Vor dem v6-Fix blockierte der zweite Befehl minutenlang.
set -u

STAMP() { date '+%H:%M:%S'; }

echo "=== Test 1: Wechsel auf ein anderes Pack ==="
echo "$(STAMP)  sende voicepack dalek"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voicepack' -m 'dalek'

echo "$(STAMP)  sende sofort voiceStatus hinterher"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voiceStatus' -m 'x'

echo "$(STAMP)  warte 30s und schaue ins Log"
sleep 30
journalctl -u dreame-fhem.service --since "-60s" --no-pager | tail -12

echo
echo "=== Test 2: Wechsel zurueck auf gordon + sofortige Registry-Abfrage ==="
echo "$(STAMP)  sende voicepack gordon"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voicepack' -m 'gordon'
sleep 2
echo "$(STAMP)  sende voicepack list"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voicepack' -m 'list'
sleep 30
journalctl -u dreame-fhem.service --since "-45s" --no-pager | tail -14

echo
echo "=== Endzustand ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id          = %s' % o.get('voice_packet_id'))
print('  voice_change_status= %s' % o.get('voice_change_status'))
print('  volume             = %s' % o.get('volume'))
print('  bridge_mode        = %s' % o.get('bridge_mode'))
"
