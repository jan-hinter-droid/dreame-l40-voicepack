#!/bin/bash
# Zeigt die relevanten Stellen der Bridge fuer den Voice-Install-Patch.
set -u
B=/home/pi/dreame_fhem_bridge.py

echo "=== PUBLISH / STATE-LISTEN (380-412) ==="
sed -n '380,412p' "$B"

echo
echo "=== build_published_state (297-330) ==="
sed -n '297,330p' "$B"

echo
echo "=== should_publish + HIDDEN (108-130) ==="
sed -n '108,130p' "$B"

echo
echo "=== set_property (422-445) ==="
sed -n '422,445p' "$B"

echo
echo "=== command_worker (1398-1435) ==="
sed -n '1398,1435p' "$B"
