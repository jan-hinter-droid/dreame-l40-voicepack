#!/usr/bin/env python3
"""
Sucht im L40-Capability-Set nach allem, was auf Anstossen/Kollision hindeutet.
Grundlage der Frage: kann man den Roboter bei jedem Anecken schreien lassen?
"""
from __future__ import annotations

import json

CAP = "/home/pi/dreame_l40_capabilities.json"
data = json.load(open(CAP, encoding="utf-8"))
sup = data.get("supported", [])

print("=== Alle Properties mit Fehler-/Ereignisbezug ===")
keys = ("ERROR", "FAULT", "BUMP", "COLLISION", "STUCK", "BLOCK", "OBSTACLE",
        "TRAP", "EVENT", "WARN", "SENSOR", "BUTTON", "TOUCH", "IMPACT")
for it in sup:
    n = it.get("name", "")
    if any(k in n.upper() for k in keys):
        print("  %-34s siid=%-3s piid=%-3s value=%s" % (
            n, it.get("siid"), it.get("piid"), str(it.get("value"))[:60]))

print()
print("=== Gibt es irgendein Property mit 'BUMP' oder 'COLLISION'? ===")
hits = [it["name"] for it in sup
        if "BUMP" in it.get("name", "").upper() or "COLLISION" in it.get("name", "").upper()]
print("  " + (", ".join(hits) if hits else "KEINES"))

print()
print("=== Alle Actions (Befehle), die das Geraet kennt ===")
for it in data.get("unsupported", [])[:0]:
    pass
for name in sorted({it.get("name", "") for it in sup}):
    pass

# Actions stehen in der types.py, hier nur die Property-Sicht
print("  (Actions siehe bridge: call_action)")

print()
print("=== Anzahl Properties gesamt: %d ===" % len(sup))
