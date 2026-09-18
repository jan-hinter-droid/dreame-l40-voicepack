#!/bin/bash
# Installiert das vollstaendige deutsche Sprachpaket ueber die Bridge (MQTT).
set -u

LANG_ID="DECUSTOM"
URL="https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/decustom.tar.gz"
MD5="421d6637e5a256ab5992e8a4d4a73398"
SIZE="3213752"

echo "=== Zustand vorher ==="
timeout 10 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/vp_before.json 2>/dev/null &
S=$!
sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true
python3 - <<'PYEOF'
import json
raw = open("/tmp/vp_before.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder(); idx = 0; last = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace(): idx += 1
    if idx >= len(raw): break
    obj, end = dec.raw_decode(raw, idx); idx = end; last = obj
if last:
    print("  voice_packet_id     =", last.get("voice_packet_id"))
    print("  voice_change_status =", last.get("voice_change_status"))
PYEOF

echo
echo "=== Installationsbefehl senden ==="
PAYLOAD=$(python3 -c "
import json
print(json.dumps({'command':'installVoicePack','value':{'lang_id':'$LANG_ID','url':'$URL','md5':'$MD5','size':int('$SIZE')}}))
")
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m "$PAYLOAD"
echo "gesendet (lang_id=$LANG_ID, size=$SIZE)"

echo
echo "=== Status mitschneiden (max. 240s) ==="
timeout 240 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -v 2>/dev/null | python3 -u - <<'PYEOF'
import json, sys, time

start = time.time()
seen = set()
last_packet = None
for line in sys.stdin:
    line = line.strip()
    if not line or " " not in line:
        continue
    _, _, payload = line.partition(" ")
    try:
        obj = json.loads(payload)
    except Exception:
        continue
    packet = obj.get("voice_packet_id")
    status = obj.get("voice_change_status")
    err = obj.get("bridge_last_command_error") or ""
    key = (packet, status, err)
    if key in seen:
        continue
    seen.add(key)
    el = int(time.time() - start)
    print(f"[{el:3d}s] packet_id={packet}  status={status}  error={err[:120]}")
    if packet == "DECUSTOM" and status and '"state":"success"' in status:
        print("\n[+] ERFOLG: deutsches Custom-Paket aktiv.")
        break
PYEOF

echo
echo "=== Bridge-Log ==="
journalctl -u dreame-fhem.service --since "-6min" --no-pager | grep -iE 'sprachpaket|voice|befehl' | tail -15
