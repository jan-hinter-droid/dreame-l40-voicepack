#!/bin/bash
# Sucht alle locate-Befehle und zeigt, was die Bridge in der Testphase tat.
set -u

echo "=== Alle locate-Vorkommen (letzte 20 Minuten) ==="
journalctl -u dreame-fhem.service --since "-20min" --no-pager | grep -i "locate" || echo "  (keine)"

echo
echo "=== Alle Befehle der letzten 20 Minuten ==="
journalctl -u dreame-fhem.service --since "-20min" --no-pager | grep "Befehl:" || echo "  (keine)"

echo
echo "=== Fehler der letzten 20 Minuten ==="
journalctl -u dreame-fhem.service --since "-20min" --no-pager | grep -iE "error|fehlgeschlagen|warning" || echo "  (keine)"

echo
echo "=== Zeitleiste 20:04 bis jetzt ==="
journalctl -u dreame-fhem.service --since "20:04" --no-pager | tail -30
