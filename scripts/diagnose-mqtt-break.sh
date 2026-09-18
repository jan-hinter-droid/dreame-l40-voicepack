#!/bin/bash
# Lokalisiert, wo die Befehlsverarbeitung abgerissen ist.
set -u

echo "=== 1. Mosquitto laeuft? ==="
systemctl is-active mosquitto.service
ss -tlnp 2>/dev/null | grep 1883 || netstat -tlnp 2>/dev/null | grep 1883 || echo "  Port 1883 nicht sichtbar"

echo
echo "=== 2. Kommt mein Publish ueberhaupt beim Broker an? ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/set/#' -C 1 -v > /tmp/probe_sub.txt 2>&1 &
S=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voiceStatus' -m 'x'
wait $S 2>/dev/null || true
if [ -s /tmp/probe_sub.txt ]; then
  echo "  JA - Broker verteilt: $(cat /tmp/probe_sub.txt)"
else
  echo "  NEIN - Broker hat nichts verteilt"
fi

echo
echo "=== 3. Publiziert die Bridge noch (State-Topic)? ==="
timeout 12 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 > /tmp/probe_state.json 2>&1 &
S=$!
sleep 11
wait $S 2>/dev/null || true
if [ -s /tmp/probe_state.json ]; then
  echo "  JA - Bridge sendet noch:"
  head -c 200 /tmp/probe_state.json; echo
else
  echo "  NEIN - Bridge sendet nichts mehr (MQTT-Loop tot?)"
fi

echo
echo "=== 4. Subscription der Bridge am Broker sichtbar? ==="
timeout 6 mosquitto_sub -h 127.0.0.1 -t '$SYS/broker/clients/connected' -C 1 2>/dev/null | sed 's/^/  verbundene Clients: /'

echo
echo "=== 5. Bridge-Log seit 20:32 (vollstaendig) ==="
journalctl -u dreame-fhem.service --since "20:32" --no-pager | tail -20

echo
echo "=== 6. Fehler im gesamten Dienst-Log ==="
journalctl -u dreame-fhem.service --since "-30min" --no-pager | grep -iE "error|exception|traceback|fehlgeschlagen" | tail -15 || echo "  keine"
