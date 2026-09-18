#!/usr/bin/env python3
"""
Sammelt ALLE Ausloeser, die der L40 kennt:
  1. Properties (was der Roboter meldet) - inkl. Fehler und Umgebungssensoren
  2. Actions (was man ausloesen kann)
  3. setList-Befehle der FHEM-Bridge (was praktisch nutzbar ist)
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types

BASE_DIR = "/home/pi/dreame-vacuum-v2/custom_components/dreame_vacuum/dreame"
CAP = "/home/pi/dreame_l40_capabilities.json"

dreame_package = types.ModuleType("dreame")
dreame_package.__path__ = [BASE_DIR]
dreame_package.VERSION = "2.0.0b25"
sys.modules["dreame"] = dreame_package


def load_module(name, filename):
    path = os.path.join(BASE_DIR, filename)
    spec = importlib.util.spec_from_file_location("dreame." + name, path)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "dreame"
    sys.modules["dreame." + name] = module
    spec.loader.exec_module(module)
    return module


load_module("exceptions", "exceptions.py")
types_mod = load_module("types", "types.py")

Action = types_mod.DreameVacuumAction
ActionMapping = types_mod.DreameVacuumActionMapping

data = json.load(open(CAP, encoding="utf-8"))
supported = {it["name"] for it in data.get("supported", [])}
prop_by_name = {it["name"]: it for it in data.get("supported", [])}

print("=" * 78)
print("1. ACTIONS - was sich aktiv ausloesen laesst")
print("=" * 78)
rows = []
for member in Action:
    name = member.name
    mapping = ActionMapping.get(member)
    if not mapping:
        continue
    rows.append((name, mapping.get("siid"), mapping.get("aiid")))
for name, siid, aiid in sorted(rows):
    print(f"  {name:<34} siid={siid} aiid={aiid}")

print()
print("=" * 78)
print("2. UMGEBUNGS- UND ZUSTANDSSENSOREN (was der Roboter wahrnimmt)")
print("=" * 78)
groups = {
    "Position/Ort": ("POSITION", "MAP", "SEGMENT", "ROOM", "CURRENT"),
    "Hindernis/Umgebung": ("OBSTACLE", "CARPET", "CLIFF", "BUMP", "SENSOR", "WALL"),
    "Schmutz/Reinigung": ("DIRT", "CLEANED", "AREA", "TIME", "PROGRESS"),
    "Station": ("STATION", "DOCK", "WASH", "DRY", "EMPTY", "TANK", "BAG", "DETERGENT"),
    "Fehler/Warnung": ("ERROR", "FAULT", "WARN", "STATUS"),
    "Personen/Kamera": ("CAMERA", "AI_", "PERSON", "PET", "CRUIS"),
    "Batterie": ("BATTERY", "CHARGING"),
}
for label, keys in groups.items():
    hits = sorted(n for n in supported if any(k in n for k in keys))
    if hits:
        print(f"\n  --- {label} ({len(hits)}) ---")
        for n in hits:
            it = prop_by_name[n]
            print(f"    {n:<34} siid={it['siid']} piid={it['piid']}  wert={str(it.get('value'))[:40]}")

print()
print("=" * 78)
print("3. FEHLER-TAXONOMIE (ERROR / FAULTS / WARN_STATUS sind Codes)")
print("=" * 78)
for n in ("ERROR", "FAULTS", "WARN_STATUS", "STATE", "STATUS", "TASK_STATUS", "TASK_TYPE"):
    if n in prop_by_name:
        it = prop_by_name[n]
        print(f"  {n:<34} istwert={it.get('value')}")
