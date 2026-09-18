#!/bin/bash
# Zeigt, wie die FHEM-Bridge Befehle von MQTT auf die Cloud-API abbildet.
set -u
B=/home/pi/dreame_fhem_bridge.py

echo "=== execute_command (1213-1360) ==="
sed -n '1213,1360p' "$B"

echo
echo "=== mqtt_on_message (1442-1475) ==="
sed -n '1442,1475p' "$B"

echo
echo "=== VOICE_CHANGE_STATUS im Bridge-Code? ==="
grep -n "VOICE_CHANGE_STATUS\|VOICE_PACKET_ID\|VOLUME" "$B" || echo "(nicht referenziert)"

echo
echo "=== wird bridge_state/publish fuer Voice benutzt? ==="
grep -n "bridge_mode\|def publish_state" "$B" | head -20
