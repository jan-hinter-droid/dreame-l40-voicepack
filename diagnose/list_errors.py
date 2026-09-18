#!/usr/bin/env python3
"""
Zeigt die Fehler-/Warncode-Taxonomie des L40 und die TASK-Typen.
Grundlage fuer 'reagiert auf Umgebung'-Ausloeser.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import types

BASE_DIR = "/home/pi/dreame-vacuum-v2/custom_components/dreame_vacuum/dreame"

dreame_package = types.ModuleType("dreame")
dreame_package.__path__ = [BASE_DIR]
dreame_package.VERSION = "2.0.0b25"
sys.modules["dreame"] = dreame_package


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(
        "dreame." + name, os.path.join(BASE_DIR, filename))
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "dreame"
    sys.modules["dreame." + name] = module
    spec.loader.exec_module(module)
    return module


load_module("exceptions", "exceptions.py")
t = load_module("types", "types.py")
c = load_module("const", "const.py")

print("=" * 78)
print("TASK-TYPEN (TASK_TYPE)")
print("=" * 78)
for member in t.DreameVacuumTaskType:
    text = (t.DreameVacuumTaskTypeMapping or {}).get(member)
    print(f"  {member.value:<4} {member.name:<28} {text or ''}")

print()
print("=" * 78)
print("STATUS-WERTE (STATUS)")
print("=" * 78)
for member in t.DreameVacuumStatus:
    print(f"  {member.value:<4} {member.name}")

print()
print("=" * 78)
print("FEHLERCODES (ERROR) - Auszug der sprech-relevanten")
print("=" * 78)
mapping = getattr(t, "DreameVacuumErrorCodeMapping", None) or \
          getattr(c, "ERROR_CODE_TO_STRING", None) or {}
if isinstance(mapping, dict):
    for key in sorted(mapping):
        try:
            print(f"  {int(key):<4} {mapping[key]}")
        except Exception:
            print(f"  {key}  {mapping[key]}")
else:
    print("  (keine Mapping-Tabelle gefunden)")
    print("  Verfuegbare Namen in types.py mit ERROR:")
    for n in dir(t):
        if "ERROR" in n.upper() or "FAULT" in n.upper():
            print("   ", n)

print()
print("=" * 78)
print("WARN_STATUS-Codes")
print("=" * 78)
warn = getattr(t, "DreameVacuumWarningMapping", None) or {}
if isinstance(warn, dict) and warn:
    for key in sorted(warn, key=lambda x: int(x) if str(x).isdigit() else 0):
        print(f"  {key}  {warn[key]}")
else:
    for n in dir(t):
        if "WARN" in n.upper():
            print("   ", n)
