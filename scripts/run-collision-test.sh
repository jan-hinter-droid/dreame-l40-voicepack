#!/bin/bash
# Kontrollierter Kollisionstest - startet den Monitor und sagt, was zu tun ist.
set -u

DURATION="${DURATION:-150}"

echo "=== Zustand ==="
python3 - <<'PYEOF'
import json, subprocess
out = subprocess.run(["mosquitto_sub", "-h", "127.0.0.1", "-t", "dreame/L40/state",
                      "-C", "1", "-W", "8"], capture_output=True, text=True)
try:
    o = json.loads(out.stdout.strip().splitlines()[-1])
    print("  state    = %s" % o.get("state"))
    print("  task     = %s" % o.get("task_status"))
    print("  akku     = %s %%" % o.get("battery_level"))
    print("  fortschr = %s %%" % o.get("cleaning_progress"))
    print("  packet   = %s" % o.get("voice_packet_id"))
    driving = str(o.get("state")) in ("sweeping", "sweeping_and_mopping", "mopping",
                                      "segment_cleaning", "zone_cleaning", "spot_cleaning")
    print()
    if driving:
        print("  -> Roboter FAEHRT. Jetzt absichtlich blockieren!")
    else:
        print("  -> Roboter steht. Bitte in FHEM starten: set Dreame_L40 start")
except Exception as ex:
    print("  Zustand nicht lesbar:", ex)
PYEOF

echo
echo "=== Monitor laeuft jetzt ${DURATION}s - bitte den Roboter blockieren ==="
echo "     Idee: Handtuch unter die Rae der, oder Hand vor den Bumper halten."
echo
timeout $((DURATION + 40)) python3 /tmp/collision_test.py "$DURATION" 2>&1
