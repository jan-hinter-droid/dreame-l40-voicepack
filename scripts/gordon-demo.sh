#!/bin/bash
# Gordon-Demo: spielt verschiedene Ansagen ueber Befehle, die den Roboter
# NICHT fahren lassen.
#
# Welcher Befehl welche Sound-ID ausloest (aus dem Inventar):
#   locate        -> ID 45   "I am here."
#   volume 1/10   -> ID 7    "Start cleaning." (Lautstaerke-Bestaetigung)
#   childLock     -> ID 116/117  "Child lock on/off"
#   suction       -> Bestaetigung der Saugstufe
#
# Jeder Befehl wird angesagt. Reihenfolge bewusst so, dass die Lautstaerke
# am Ende wieder auf 10 steht.
set -u

say() { printf '\n>>> %s\n' "$1"; }

banner() {
  echo
  echo "================================================================"
  echo "  $1"
  echo "================================================================"
}

banner "GORDON-DEMO  (Roboter bleibt stehen)"
echo "  Aktives Paket und Lautstaerke werden gleich geprueft."

echo
echo "--- 1) locate  (Sound-ID 45: \"I am here\") ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m 1
sleep 6

echo
echo "--- 2) Lautstaerke auf 1   (Sound-ID 7: Bestaetigung) ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/volume' -m 1
sleep 8

echo
echo "--- 3) Lautstaerke zurueck auf 10   (Sound-ID 7 nochmal, lauter) ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/volume' -m 10
sleep 8

echo
echo "--- 4) Kindersicherung ein   (Sound-ID 116) ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/childLock' -m on
sleep 8

echo
echo "--- 5) Kindersicherung aus   (Sound-ID 117) ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/childLock' -m off
sleep 8

echo
echo "--- 6) locate nochmal   (Sound-ID 45) ---"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m 1
sleep 6

banner "Endzustand wiederherstellen"
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/volume' -m 10
sleep 4
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id   = %s' % o.get('voice_packet_id'))
print('  volume      = %s' % o.get('volume'))
print('  child_lock  = %s' % o.get('child_lock'))
print('  state       = %s' % o.get('state'))
"

echo
echo "=== Ausgefuehrte Befehle ==="
journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep "Befehl:" | tail -10
