#!/bin/bash
# Abschlusspruefung: Zustand von Roboter, Bridge und FHEM-Anbindung.
set -u

echo "=========== 1. BRIDGE ==========="
systemctl is-active dreame-fhem.service
grep -m1 'BRIDGE_VERSION' /home/pi/dreame_fhem_bridge.py
echo -n "Patches eingebaut: "
for m in install_voice_pack voice_status ensure_cloud_host; do
  grep -q "def $m" /home/pi/dreame_fhem_bridge.py && echo -n "$m "
done
echo
echo "Backups:"
ls -1 /home/pi/dreame_fhem_bridge.py.bak* 2>/dev/null | tail -5

echo
echo "=========== 2. ROBOTER ==========="
timeout 12 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 2 > /tmp/final.json 2>/dev/null &
S=$!; sleep 2
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"voiceStatus"}'
wait $S 2>/dev/null || true
python3 - <<'PYEOF'
import json
raw = open("/tmp/final.json", encoding="utf-8", errors="replace").read().strip()
d = json.JSONDecoder(); i = 0; last = None
while i < len(raw):
    while i < len(raw) and raw[i].isspace(): i += 1
    if i >= len(raw): break
    o, e = d.raw_decode(raw, i); i = e; last = o
if last:
    for k in ("voice_packet_id", "voice_change_status", "volume", "state",
              "battery_level", "bridge_mode", "online"):
        print("  %-22s = %s" % (k, last.get(k)))
PYEOF

echo
echo "=========== 3. FHEM-SETLIST ==========="
python3 - <<'PYEOF'
from pathlib import Path
src = Path("/opt/fhem/fhem.cfg").read_text(encoding="utf-8", errors="replace")
i = src.find("define Dreame_L40 MQTT2_DEVICE")
end = src.find("\ndefine ", i)
block = src[i:end]
for line in block.splitlines():
    if any(k in line for k in ("installVoicePack", "voiceStatus", "volume")):
        print("  " + line)
PYEOF

echo
echo "=========== 4. LETZTE VOICE-AKTION IM LOG ==========="
journalctl -u dreame-fhem.service --since "-30min" --no-pager | grep -iE 'Sprachpaket' | tail -6
