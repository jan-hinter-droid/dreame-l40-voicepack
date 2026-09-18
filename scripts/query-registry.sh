#!/bin/bash
# Registry ueber MQTT abfragen - mit mosquitto-Clients, dem erprobten Weg.
set -u

echo "=== Mitschnitt starten, dann 'voicepack list' senden ==="
timeout 25 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 4 > /tmp/reg.json 2>/dev/null &
S=$!
sleep 3
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/voicepack' -m 'list'
echo "gesendet: voicepack list"
wait $S 2>/dev/null || true

python3 - <<'PYEOF'
import json

raw = open("/tmp/reg.json", encoding="utf-8", errors="replace").read().strip()
dec = json.JSONDecoder()
idx = 0
found = None
while idx < len(raw):
    while idx < len(raw) and raw[idx].isspace():
        idx += 1
    if idx >= len(raw):
        break
    obj, end = dec.raw_decode(raw, idx)
    idx = end
    if obj.get("bridge_last_command") == "voicepack":
        found = obj

if not found:
    print("Keine voicepack-Antwort im Mitschnitt.")
    raise SystemExit(1)

print()
print("=== Antwort der Bridge ===")
try:
    res = json.loads(found.get("bridge_last_command_result") or "{}")
except Exception:
    res = {}

verf = res.get("verfuegbar") or {}
if verf:
    for key, name in sorted(verf.items()):
        print("  %-12s %s" % (key, name))
else:
    print("  rohe Antwort:", str(found.get("bridge_last_command_result"))[:400])

print()
print("  aktiv  = %s" % res.get("aktiv") or found.get("voice_packet_id"))
print("  volume = %s" % found.get("volume"))
print("  status = %s" % found.get("voice_change_status"))
PYEOF
