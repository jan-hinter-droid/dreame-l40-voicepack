#!/bin/bash
# Installiert das vollstaendige deutsche Sprachpaket (466 Ansagen).
set -u

LANG_ID="FULLDE"
URL="https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/fullde.tar.gz"
MD5="d92f468e340fd3d0056d06e7f8ad0e6d"
SIZE="8182192"

echo "=== Vorher ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/f_before.json 2>/dev/null &
S=$!; sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true
python3 -c "
import json
raw=open('/tmp/f_before.json',encoding='utf-8',errors='replace').read().strip()
d=json.JSONDecoder(); i=0; last=None
while i < len(raw):
    while i < len(raw) and raw[i].isspace(): i+=1
    if i >= len(raw): break
    o,e=d.raw_decode(raw,i); i=e; last=o
if last: print('  packet_id =', last.get('voice_packet_id'), '| volume =', last.get('volume'))
"

echo
echo "=== Installation starten ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m "{\"command\":\"installVoicePack\",\"value\":{\"lang_id\":\"$LANG_ID\",\"url\":\"$URL\",\"md5\":\"$MD5\",\"size\":$SIZE}}"
echo "gesendet: lang_id=$LANG_ID size=$SIZE"

echo
echo "=== Fortschritt aus dem Bridge-Log (max. 200s) ==="
START=$(date +%s)
while [ $(( $(date +%s) - START )) -lt 200 ]; do
  LINE=$(journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep "Sprachpaket-Status" | tail -1)
  if [ -n "$LINE" ] && [ "$LINE" != "${LAST:-}" ]; then
    echo "[$(( $(date +%s) - START ))s] ${LINE#*Sprachpaket-Status: }"
    LAST="$LINE"
  fi
  if echo "$LINE" | grep -q '"state":"success"'; then
    echo
    echo "[+] Installation erfolgreich."
    break
  fi
  if echo "$LINE" | grep -q '"state":"fail"'; then
    echo
    echo "[!] Installation fehlgeschlagen."
    break
  fi
  sleep 5
done

echo
echo "=== Endzustand ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/f_after.json 2>/dev/null &
S=$!; sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true
python3 -c "
import json
raw=open('/tmp/f_after.json',encoding='utf-8',errors='replace').read().strip()
d=json.JSONDecoder(); i=0; last=None
while i < len(raw):
    while i < len(raw) and raw[i].isspace(): i+=1
    if i >= len(raw): break
    o,e=d.raw_decode(raw,i); i=e; last=o
if last:
    for k in ('voice_packet_id','voice_change_status','volume'):
        print('  %-20s = %s' % (k, last.get(k)))
"
