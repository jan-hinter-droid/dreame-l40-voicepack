#!/usr/bin/env python3
"""
Transkribiert NUR die Sound-IDs, die im Werkspaket, aber nicht im
Community-Pack vorkommen. Dort liegen die unerforschten Anstoss-/Fehler-Ansagen.

Aufruf: transcribe_missing.py <paket.tar.gz> <ausgabe.csv> [modell]
"""
from __future__ import annotations

import csv
import sys
import tarfile
import tempfile
import time
from pathlib import Path

from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent.parent

if len(sys.argv) < 3:
    sys.exit(__doc__)

pack = Path(sys.argv[1])
out_path = Path(sys.argv[2])
model_size = sys.argv[3] if len(sys.argv) > 3 else "small"

known: set[int] = set()
inv = BASE / "reference" / "sound_inventory.csv"
if inv.exists():
    with inv.open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh, delimiter=";")
        next(rd, None)
        for row in rd:
            if row and row[0].strip().isdigit():
                known.add(int(row[0]))

work = Path(tempfile.mkdtemp(prefix="missing-"))
targets: list[tuple[int, Path]] = []
with tarfile.open(pack, "r:gz") as tar:
    for m in tar.getmembers():
        if not (m.isfile() and m.name.endswith(".ogg") and m.name[:-4].isdigit()):
            continue
        sid = int(m.name[:-4])
        if sid in known:
            continue
        fh = tar.extractfile(m)
        if fh is None:
            continue
        dest = work / f"{sid}.ogg"
        dest.write_bytes(fh.read())
        targets.append((sid, dest))

targets.sort()
print(f"[i] {len(targets)} unbekannte IDs zu transkribieren", flush=True)
print(f"[i] Modell={model_size}", flush=True)

model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("[i] Modell geladen", flush=True)

rows = []
start = time.time()
for i, (sid, path) in enumerate(targets, 1):
    try:
        segments, info = model.transcribe(
            str(path), language="en", beam_size=1, vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        dur = round(info.duration, 2)
    except Exception as ex:
        text, dur = f"<FEHLER: {ex}>", 0.0
    rows.append((sid, dur, text))
    print(f"  {sid:>4}  {dur:>6.2f}s  {text}", flush=True)
    if i % 20 == 0:
        print(f"  --- {i}/{len(targets)} ({time.time()-start:.0f}s) ---", flush=True)

with out_path.open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["id", "duration", "text"])
    w.writerows(rows)

print(f"\n[+] {out_path} ({len(rows)} Zeilen)")
