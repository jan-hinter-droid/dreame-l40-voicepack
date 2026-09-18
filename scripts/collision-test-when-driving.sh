#!/bin/bash
# Startet den Kollisionsmonitor und wartet, bis der Roboter FAEHRT.
# Erst wenn er faehrt, ist ein Anstoss ueberhaupt messbar.
set -u

DURATION="${DURATION:-210}"

echo "=== Warte, bis der Roboter faehrt (max. 120s) ==="
DRIVING=0
for i in $(seq 1 24); do
  STATE=$(timeout 6 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null \
    | python3 -c "
import json,sys
try:
    o=json.load(sys.stdin); print(o.get('state'), o.get('task_status'))
except Exception: print('unbekannt')
" 2>/dev/null)
  echo "  [$((i*5))s] $STATE"
  case "$STATE" in
    *sweep*|*mop*|*cleaning*|*going*|*return*)
      if ! echo "$STATE" | grep -q paused; then DRIVING=1; break; fi ;;
  esac
  sleep 5
done

if [ "$DRIVING" -eq 0 ]; then
  echo
  echo "  Roboter faehrt nicht. Bitte in FHEM starten:"
  echo "      set Dreame_L40 start"
  echo "  und dieses Skript danach erneut ausfuehren."
  exit 1
fi

echo
echo "=== Roboter FAEHRT. Monitor laeuft ${DURATION}s. ==="
echo "=== JETZT BLOCKIEREN: Handtuch unter die Rae der oder Hand vor den Bumper ==="
timeout $((DURATION + 40)) python3 /tmp/collision_test.py "$DURATION" 2>&1
