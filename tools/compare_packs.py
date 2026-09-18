#!/usr/bin/env python3
"""
Vergleicht die Sound-IDs des Werkspakets mit einem Community-Pack.

Ziel: herausfinden, welche IDs im Gordon-Pack fehlen - dort liegen
vermutlich die Fehler-/Anstoss-Ansagen.
"""
from __future__ import annotations

import csv
import tarfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FACTORY = BASE / "reference" / "official-de-r2492j.tar.gz"
COMMUNITY = BASE / "dist" / "gordon.tar.gz"
INVENTORY = BASE / "reference" / "sound_inventory.csv"
TRANSCRIPT = BASE / "reference" / "gordon_transcript.csv"


def ids_from_tar(path: Path) -> set[int]:
    with tarfile.open(path, "r:gz") as tar:
        return {
            int(m.name[:-4]) for m in tar.getmembers()
            if m.isfile() and m.name.endswith(".ogg") and m.name[:-4].isdigit()
        }


factory = ids_from_tar(FACTORY)
gordon = ids_from_tar(COMMUNITY)

print(f"Werkspaket DE : {len(factory)} IDs   ({min(factory)}..{max(factory)})")
print(f"Gordon-Pack   : {len(gordon)} IDs   ({min(gordon)}..{max(gordon)})")
print(f"Schnittmenge  : {len(factory & gordon)}")
print(f"nur Werkspaket: {len(factory - gordon)}")
print(f"nur Gordon    : {len(gordon - factory)}")

# Inventar-Bedeutungen laden
meaning: dict[int, str] = {}
if INVENTORY.exists():
    with INVENTORY.open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh, delimiter=";")
        next(rd, None)
        for row in rd:
            if row and row[0].strip().isdigit():
                meaning[int(row[0])] = row[1].strip() if len(row) > 1 else ""

missing = sorted(factory - gordon)
print()
print("=" * 90)
print(f"IDs NUR im Werkspaket ({len(missing)}) - Kandidaten fuer Anstoss/Fehler")
print("=" * 90)
for sid in missing:
    print(f"  {sid:>4}  {meaning.get(sid, '(unbekannt)')[:70]}")
