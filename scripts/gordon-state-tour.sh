#!/bin/bash
# Gordon-Durchlauf ueber Zustandswechsel, die nachweislich Sprache ausloesen.
#
# Bekannt laut: pause (ID 11), resume (ID 10), dock (ID 13),
#               start (ID 7), stop/finish (ID 12/143), locate (ID 45)
#
# Der Roboter wird dabei mehrfach pausiert und fortgesetzt - am Ende laeuft
# die Reinigung wieder.
set -u

cmd() {
  local label="$1"; local topic="$2"; local value="$3"; local wait="${4:-9}"
  echo
  echo "---------------------------------------------------------------"
  echo "  $label"
  echo "---------------------------------------------------------------"
  mosquitto_pub -h 127.0.0.1 -t "$topic" -m "$value"
  sleep "$wait"
}

zeige() {
  timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  state=%s  task=%s  prozent=%s' % (
  o.get('state'), o.get('task_status'), o.get('cleaning_progress')))
"
}

echo "=== Ausgangszustand ==="
zeige

cmd "1) PAUSE            -> Gordon: 'Finally, a bloody second to breathe.'" \
    'dreame/L40/set/pause' '1' 9

cmd "2) RESUME           -> Gordon beim Weiterputzen" \
    'dreame/L40/set/resume' '1' 12

cmd "3) PAUSE (nochmal)" 'dreame/L40/set/pause' '1' 9

cmd "4) RESUME (nochmal) - Gordon wird langsam genervt" \
    'dreame/L40/set/resume' '1' 12

cmd "5) LOCATE           -> ID 45" 'dreame/L40/set/locate' '1' 8

cmd "6) KINDERSICHERUNG an  - falls er das kommentiert" \
    'dreame/L40/set/childLock' 'on' 8

cmd "7) KINDERSICHERUNG aus" 'dreame/L40/set/childLock' 'off' 8

echo
echo "=== Endzustand (Reinigung soll weiterlaufen) ==="
zeige
echo
echo "=== Letzte Befehle ==="
journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep "Befehl:" | tail -10
