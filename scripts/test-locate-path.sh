#!/bin/bash
# Direkter Test: kommt ein locate-Befehl ueber MQTT in der Bridge an?
set -u

echo "=== 1. Bridge-Zustand ==="
systemctl is-active dreame-fhem.service
echo -n "Bridge-Modus: "
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
try:
    o=json.load(sys.stdin); print(o.get('bridge_mode'), '| packet:', o.get('voice_packet_id'), '| vol:', o.get('volume'))
except Exception as e: print('Fehler:', e)
"

echo
echo "=== 2. locate senden und Log beobachten ==="
BEFORE=$(journalctl -u dreame-fhem.service --no-pager | grep -c "Befehl: locate" || echo 0)
echo "  locate-Eintraege vorher: $BEFORE"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m '1'
echo "  gesendet, warte 8s ..."
sleep 8
AFTER=$(journalctl -u dreame-fhem.service --no-pager | grep -c "Befehl: locate" || echo 0)
echo "  locate-Eintraege nachher: $AFTER"
if [ "$AFTER" -gt "$BEFORE" ]; then
  echo "  -> Befehl ist angekommen"
else
  echo "  -> NICHT angekommen"
fi

echo
echo "=== 3. Letzte 10 Zeilen des Logs ==="
journalctl -u dreame-fhem.service -n 10 --no-pager | tail -10

echo
echo "=== 4. MQTT-Broker erreichbar / ACL? ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}' -d 2>&1 | tail -8
