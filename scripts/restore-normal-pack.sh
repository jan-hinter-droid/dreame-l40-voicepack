#!/bin/bash
# Stellt das normale deutsche Paket wieder her (locate sagt wieder "Hier bin ich!").
set -u

LANG_ID="FULLDE"
# jsDelivr statt raw.githubusercontent.com: der Raw-CDN cached zu aggressiv.
URL="https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/fullde.tar.gz"
MD5="d92f468e340fd3d0056d06e7f8ad0e6d"
SIZE="8182192"

echo "=== Vorher ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id=%s  volume=%s' % (o.get('voice_packet_id'), o.get('volume')))
"

echo
echo "=== Normales Paket installieren ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m "{\"command\":\"installVoicePack\",\"value\":{\"lang_id\":\"$LANG_ID\",\"url\":\"$URL\",\"md5\":\"$MD5\",\"size\":$SIZE}}"
echo "gesendet."

for i in $(seq 1 20); do
  sleep 5
  LATEST=$(journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep Sprachpaket-Status | tail -1)
  if echo "$LATEST" | grep -q "$LANG_ID"; then
    echo "  $LATEST" | sed 's/.*Sprachpaket-Status:/  Status:/'
  fi
  echo "$LATEST" | grep -q success && break
  echo "$LATEST" | grep -q fail && { echo "FEHLGESCHLAGEN"; exit 2; }
done

echo
echo "=== Endzustand ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id          = %s' % o.get('voice_packet_id'))
print('  voice_change_status= %s' % o.get('voice_change_status'))
print('  volume             = %s' % o.get('volume'))
"
