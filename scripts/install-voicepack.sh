#!/bin/bash
# Loest die Sprachpaket-Installation aus und verfolgt VOICE_CHANGE_STATUS.
set -u

LANG_ID="SMOKE-TEST"
URL="https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/smoke-test.tar.gz"
MD5="3351ea8dd7493a1480b0df612d1352c2"
SIZE="29247"
VOLUME_BEFORE=""
TIMEOUT_S=150

snapshot() {
  timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 > /tmp/vp_state.json 2>/dev/null &
  local sub=$!
  sleep 1
  mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}' >/dev/null 2>&1
  wait $sub 2>/dev/null || true
  python3 - <<'PYEOF'
import json
raw = open("/tmp/vp_state.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder()
try:
    obj, _ = dec.raw_decode(raw)
except Exception:
    print("")
    raise SystemExit
print("%s|%s|%s" % (obj.get("voice_packet_id"), obj.get("voice_change_status"),
                    obj.get("bridge_last_command_error", "")))
PYEOF
}

echo "=== Vorher ==="
BEFORE=$(snapshot)
echo "voice_packet_id|voice_change_status|error = $BEFORE"
VOLUME_BEFORE=$(python3 -c "
import json
raw=open('/tmp/vp_state.json',encoding='utf-8',errors='replace').read().strip()
dec=json.JSONDecoder(); obj,_=dec.raw_decode(raw)
print(obj.get('volume','?'))
")
echo "volume vorher = $VOLUME_BEFORE"

echo
echo "=== Installation ausloesen ==="
PAYLOAD=$(python3 -c "
import json,sys
print(json.dumps({'command':'installVoicePack','value':{'lang_id':'$LANG_ID','url':'$URL','md5':'$MD5','size':int('$SIZE')}}))
")
echo "$PAYLOAD" | head -c 200; echo
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m "$PAYLOAD"
echo "gesendet."

echo
echo "=== Verlauf VOICE_CHANGE_STATUS ==="
START=$(date +%s)
LAST=""
while [ $(( $(date +%s) - START )) -lt $TIMEOUT_S ]; do
  NOW=$(snapshot)
  ELAPSED=$(( $(date +%s) - START ))
  if [ "$NOW" != "$LAST" ]; then
    echo "[${ELAPSED}s] $NOW"
    LAST="$NOW"
  fi
  STATE=$(echo "$NOW" | cut -d'|' -f2)
  if [ "$ELAPSED" -gt 8 ] && echo "$STATE" | grep -q '"state":"idle"'; then
    echo "[${ELAPSED}s] -> zurueck auf idle, Vorgang beendet"
    break
  fi
  sleep 5
done

echo
echo "=== Nachher ==="
snapshot

echo
echo "=== Bridge-Log (letzte 20 Zeilen) ==="
journalctl -u dreame-fhem.service -n 20 --no-pager | tail -20
