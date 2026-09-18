#!/bin/bash
# Sendet einen Befehl an die Bridge und zeigt die Voice-Felder aus der Antwort.
set -u

CMD="${1:-voiceStatus}"
PAYLOAD="${2:-}"

echo "=== Bridge-Zustand ==="
systemctl is-active dreame-fhem.service
journalctl -u dreame-fhem.service -n 4 --no-pager | tail -4

echo
echo "=== Mitschnitt + Befehl ==="
timeout 15 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 4 > /tmp/state_capture.json 2>/tmp/sub_err.txt &
SUBPID=$!
sleep 3

if [ -n "$PAYLOAD" ]; then
  mosquitto_pub -h 127.0.0.1 -t "dreame/L40/set/$CMD" -m "$PAYLOAD"
  echo "gesendet: set/$CMD = $PAYLOAD"
else
  mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m "{\"command\":\"$CMD\"}"
  echo "gesendet: $CMD"
fi

wait $SUBPID 2>/dev/null || true

echo
echo "=== Voice-Felder ==="
python3 - "$CMD" <<'PYEOF'
import json, sys

cmd = sys.argv[1] if len(sys.argv) > 1 else "?"
raw = open("/tmp/state_capture.json", encoding="utf-8", errors="replace").read().strip()
if not raw:
    print("KEINE Antwort empfangen")
    raise SystemExit(1)

dec = json.JSONDecoder()
idx = n = 0
last = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace():
        idx += 1
    if idx >= len(raw):
        break
    obj, end = dec.raw_decode(raw, idx)
    idx = end
    n += 1
    last = obj
    print("--- Nachricht %d ---" % n)
    for k in ("voice_packet_id", "voice_change_status"):
        if k in obj:
            print("  %-22s = %s" % (k, obj[k]))
    if "bridge_last_command" in obj:
        print("  bridge_last_command    = %s" % obj.get("bridge_last_command"))
        print("  bridge_last_cmd_result = %s" % str(obj.get("bridge_last_command_result"))[:300])
        err = obj.get("bridge_last_command_error") or ""
        if err:
            print("  FEHLER                 = %s" % err)

print()
print("=== Fazit ===")
if last is None:
    print("keine Daten")
elif cmd == "voiceStatus":
    missing = [k for k in ("voice_packet_id", "voice_change_status") if k not in last]
    print("Voice-Felder fehlen noch: %s" % missing if missing else "Voice-Felder werden publiziert")
PYEOF
