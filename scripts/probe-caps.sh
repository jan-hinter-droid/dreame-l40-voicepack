#!/bin/bash
# Liest die L40-Capability-Datei der FHEM-Bridge aus und zeigt Voice-relevante Properties.
set -u

CAP=/home/pi/dreame_l40_capabilities.json
echo "=== Datei ==="
ls -la "$CAP"

python3 - "$CAP" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("Top-Keys:", list(d.keys()))
sup = d.get("supported", [])
print("Anzahl supported:", len(sup))
print()
print("--- Voice/Audio/Volume/Language ---")
hits = [it for it in sup if any(k in it.get("name", "").upper()
        for k in ("VOICE", "AUDIO", "VOLUME", "LANG", "SPEAK"))]
for it in hits:
    print(it)
if not hits:
    print("(keine Treffer)")
print()
print("--- siid 7 ---")
for it in sup:
    try:
        if int(it.get("siid", -1)) == 7:
            print(it)
    except Exception:
        pass
print()
print("--- Property-Enum: Voice-Eintraege ---")
base = "/home/pi/dreame-vacuum-v2/custom_components/dreame_vacuum/dreame/types.py"
src = open(base, encoding="utf-8").read()
import re
for m in re.finditer(r"^\s*(VOICE\w*)\s*=\s*(\d+)", src, re.M):
    print(m.group(1), "=", m.group(2))
print()
print("--- Mapping fuer VOICE_CHANGE ---")
for m in re.finditer(r"DreameVacuumProperty\.(VOICE\w*):\s*\{[^}]*\}", src):
    print(m.group(0))
PY

echo
echo "=== protocol.py: DreameHome-Cloud-Varianten ==="
grep -nE "^class |def send\(|def set_property" \
  /home/pi/dreame-vacuum-v2/custom_components/dreame_vacuum/dreame/protocol.py | head -40

echo
echo "=== dreame-fhem.service ==="
systemctl cat dreame-fhem.service 2>/dev/null

echo
echo "=== pip / venv ==="
python3 -c "import paho.mqtt.client as c; print('paho', c.__file__)" 2>&1
ls -la /home/pi/.config/dreame-fhem/ 2>&1
