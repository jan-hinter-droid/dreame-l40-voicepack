#!/usr/bin/env python3
"""Prueft, ob die Voice-Befehle in der FHEM-setList angekommen sind."""
from __future__ import annotations

from pathlib import Path

CFG = Path("/opt/fhem/fhem.cfg")
src = CFG.read_text(encoding="utf-8", errors="replace")

print("Dateigroesse:", len(src), "Zeichen")
print("installVoicePack enthalten:", "installVoicePack" in src)
print("voiceStatus enthalten     :", "voiceStatus" in src)

idx = src.find("define Dreame_L40 MQTT2_DEVICE")
if idx == -1:
    raise SystemExit("Dreame_L40 nicht gefunden")
end = src.find("\ndefine ", idx)
block = src[idx:end]
print("\n=== Dreame_L40-Definition, letzte 700 Zeichen ===")
print(block[-700:])
print("\n=== Zeilen mit Voice ===")
for line in block.splitlines():
    if "voice" in line.lower():
        print(" ", line)
