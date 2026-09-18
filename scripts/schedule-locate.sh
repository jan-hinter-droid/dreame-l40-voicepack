#!/bin/bash
# Legt eine einmalige Hoerprobe an: spielt in 60s Sound-ID 45 ("Hier bin ich!").
# Entfernt sich danach selbst wieder.
set -u

echo "=== Bestehende Testdefinition entfernen (falls vorhanden) ==="
mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set' -m '{"command":"locate"}' >/dev/null 2>&1 || true

echo "=== at-Job anlegen: locate in 60 Sekunden ==="
which at >/dev/null 2>&1 || { echo "at ist nicht installiert - nutze systemd-run"; }

if which at >/dev/null 2>&1; then
  echo "mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m '1'" | at now + 1 minute 2>&1
  echo "-> Job geplant. Roboter sagt in ~60s 'Hier bin ich!' (Sound-ID 45)"
  atq 2>&1
else
  sudo -n systemd-run --on-active=60 --unit=dreame-voicecheck \
    /usr/bin/mosquitto_pub -h 127.0.0.1 -t 'dreame/L40/set/locate' -m '1' 2>&1
  echo "-> systemd-Timer gesetzt (60s)"
fi
