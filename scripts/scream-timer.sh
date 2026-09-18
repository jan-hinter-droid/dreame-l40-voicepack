#!/bin/bash
# 5 klar getaktete Schreie, ausgefuehrt als systemd-Timer.
# Unabhaengig von der SSH-Sitzung, damit nichts abbricht.
set -u

echo "=== Zustand vorher ==="
timeout 8 mosquitto_sub -h 127.0.0.1 -t 'dreame/L40/state' -C 1 2>/dev/null | python3 -c "
import json,sys
o=json.load(sys.stdin)
print('  packet_id=%s  volume=%s  state=%s  bridge=%s' % (
    o.get('voice_packet_id'), o.get('volume'), o.get('state'), o.get('bridge_mode')))
print('  voice_change_status=%s' % o.get('voice_change_status'))
"
echo '  (SCREAMTEST aktiv? -> dann spielt locate den Schrei)'

echo
echo "=== Alten Timer entfernen ==="
sudo -n systemctl stop dreame-scream.service 2>/dev/null || true
sudo -n systemctl reset-failed dreame-scream.service 2>/dev/null || true

echo "=== 5 Schreie planen: t+5s, +10s, +15s, +20s, +25s ==="
sudo -n systemd-run --on-active=5 --unit=dreame-scream \
  /bin/bash -c 'for i in 1 2 3 4 5; do mosquitto_pub -h 127.0.0.1 -t dreame/L40/set/locate -m 1; sleep 5; done' 2>&1

echo "-> Timer laeuft. Der Roboter sollte jetzt 5x schreien."
