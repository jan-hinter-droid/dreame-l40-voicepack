#!/bin/bash
# Laesst den Roboter mehrere Gordon-Kommentare sagen.
# Nutzt nur Befehle, die eine Reinigung NICHT unterbrechen.
# Protokolliert je Befehl, welche Sound-ID gesprochen wurde.
set -u

step() {
  local label="$1"; local topic="$2"; local value="$3"
  echo
  echo "--------------------------------------------------------------"
  echo "  $label"
  echo "--------------------------------------------------------------"
  mosquitto_pub -h 127.0.0.1 -t "$topic" -m "$value"
  sleep 7
}

echo "=== Zustand ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  state=%s  task=%s  prozent=%s  akku=%s%%' % (
  o.get('state'), o.get('task_status'), o.get('cleaning_progress'), o.get('battery_level')))
print('  packet=%s  volume=%s' % (o.get('voice_packet_id'), o.get('volume')))
"

step "1) locate        -> ID 45"  'dreame/L40/set/locate' '1'
step "2) autoEmpty an  -> Bestaetigung" 'dreame/L40/set/autoEmpty' 'on'
step "3) autoEmpty aus -> Bestaetigung" 'dreame/L40/set/autoEmpty' 'off'
step "4) carpetBoost an -> Bestaetigung" 'dreame/L40/set/carpetBoost' 'on'
step "5) carpetBoost aus" 'dreame/L40/set/carpetBoost' 'off'
step "6) autoDetergent an" 'dreame/L40/set/autoDetergent' 'on'
step "7) autoDetergent aus" 'dreame/L40/set/autoDetergent' 'off'
step "8) Lautstaerke 3  -> ID 7" 'dreame/L40/set/volume' '3'
step "9) Lautstaerke 10 -> ID 7" 'dreame/L40/set/volume' '10'
step "10) locate nochmal -> ID 45" 'dreame/L40/set/locate' '1'

echo
echo "=== Zustand danach ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  state=%s  task=%s  prozent=%s' % (
  o.get('state'), o.get('task_status'), o.get('cleaning_progress')))
print('  volume=%s  packet=%s' % (o.get('volume'), o.get('voice_packet_id')))
print('  auto_empty=%s  carpet_boost=%s  auto_detergent=%s' % (
  o.get('auto_dust_collecting'), o.get('carpet_boost'), o.get('auto_add_detergent')))
"

echo
echo "=== Ausgefuehrte Befehle ==="
journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep "Befehl:" | tail -12
