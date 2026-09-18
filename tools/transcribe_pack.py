#!/usr/bin/env python3
"""
Transkribiert ein Sprachpaket lokal mit faster-whisper.

Aufruf:  transcribe_pack.py <ordner-mit-oggs> <ausgabe.csv> [modell]
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

if len(sys.argv) < 3:
    sys.exit(__doc__)

pack_dir = Path(sys.argv[1])
out_path = Path(sys.argv[2])
model_size = sys.argv[3] if len(sys.argv) > 3 else "base"

files = sorted(
    (p for p in pack_dir.iterdir() if p.suffix == ".ogg" and p.stem.isdigit()),
    key=lambda p: int(p.stem),
)
print(f"[i] {len(files)} Dateien, Modell={model_size}", flush=True)

model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("[i] Modell geladen", flush=True)

rows = []
start = time.time()
for i, path in enumerate(files, 1):
    try:
        segments, info = model.transcribe(
            str(path), language="en", beam_size=1, vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        dur = round(info.duration, 2)
    except Exception as ex:
        text, dur = f"<FEHLER: {ex}>", 0.0
    rows.append((int(path.stem), dur, text))
    if i % 25 == 0 or i == len(files):
        print(f"  {i}/{len(files)}  ({time.time()-start:.0f}s)", flush=True)

with out_path.open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["id", "duration", "text"])
    w.writerows(rows)

print(f"[+] {out_path} ({len(rows)} Zeilen)")
