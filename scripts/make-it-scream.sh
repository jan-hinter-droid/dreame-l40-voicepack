#!/bin/bash
# Laesst den Roboter mehrfach schreien.
#
# Trick: Im Testpaket SCREAMTEST spielt Sound-ID 45 den Schrei. ID 45 wird vom
# Befehl "locate" ausgeloest, und locate bewegt den Roboter nicht.
set -u

LANG_ID="SCREAMTEST"
URL="https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/screamtest.tar.gz"
MD5="${1:-}"
SIZE="${2:-}"
COUNT="${3:-6}"
GAP="${4:-6}"

if [ -z "$MD5" ] || [ -z "$SIZE" ]; then
  echo "Aufruf: $0 <md5> <size> [anzahl] [abstand_sekunden]"
  exit 1
fi

send() {
  mosquitto_pub -h 127.0.0.1 -t "$1" -m "$2"
}

state() {
  timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 > /tmp/sc.json 2>/dev/null &
  local s=$!; sleep 1
  mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}' >/dev/null 2>&1
  wait $s 2>/dev/null || true
  python3 -c "
import json
raw=open('/tmp/sc.json',encoding='utf-8',errors='replace').read().strip()
d=json.JSONDecoder(); i=0; last=None
while i < len(raw):
    while i < len(raw) and raw[i].isspace(): i+=1
    if i >= len(raw): break
    o,e=d.raw_decode(raw,i); i=e; last=o
if last: print('%s | %s | vol=%s' % (last.get('voice_packet_id'), last.get('voice_change_status'), last.get('volume')))
"
}

echo "=== 1.) Testpaket installieren ==="
send 'dreame/L40/set' "{\"command\":\"installVoicePack\",\"value\":{\"lang_id\":\"$LANG_ID\",\"url\":\"$URL\",\"md5\":\"$MD5\",\"size\":$SIZE}}"
echo "gesendet. Warte auf state=success ..."
for i in $(seq 1 40); do
  sleep 5
  ST=$(journalctl -u dreame-fhem.service --since "-4min" --no-pager | grep "Sprachpaket-Status" | tail -1)
  echo "  $ST" | sed 's/.*Sprachpaket-Status: /  /'
  echo "$ST" | grep -q '"state":"success"' && break
  echo "$ST" | grep -q '"state":"fail"' && { echo "FEHLGESCHLAGEN"; exit 2; }
done
echo
echo "Zustand: $(state)"

echo
echo "=== 2.) Roboter $COUNT mal schreien lassen (locate -> Sound-ID 45) ==="
for n in $(seq 1 "$COUNT"); do
  echo "  [$n/$COUNT] locate ..."
  send 'dreame/L40/set/locate' '1'
  sleep "$GAP"
done

echo
echo "=== 3.) Zustand danach ==="
state
echo
echo "=== 4.) Bridge-Log (letzte Befehle) ==="
journalctl -u dreame-fhem.service --since "-3min" --no-pager | grep -E "Befehl:|Sprachpaket" | tail -12
