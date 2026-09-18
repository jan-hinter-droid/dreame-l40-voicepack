#!/usr/bin/env python3
"""
Fuehrt die handkuratierte Ansagenliste mit dem vollstaendigen Sound-Inventar
zu einer Gesamtliste zusammen.

Vorrang: phrases/de_custom.csv (kuratiert, inkl. Schrei-Slot 40) gewinnt bei
Doppelungen. Aus reference/sound_inventory.csv kommen alle uebrigen IDs dazu.
"""
from __future__ import annotations

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CURATED = BASE / "phrases" / "de_custom.csv"
INVENTORY = BASE / "reference" / "sound_inventory.csv"
OUT = BASE / "phrases" / "de_full.csv"

# Reine Geraeusche - als leerer Slot gehalten, damit die Zuordnung dokumentiert bleibt
SOUND_ONLY_NOTE = "Geraeusch - Werkssound (kein TTS)"


def load_curated() -> dict[int, tuple[str, str]]:
    out: dict[int, tuple[str, str]] = {}
    with CURATED.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        next(reader, None)
        for row in reader:
            if not row or not row[0].strip():
                continue
            sid = int(row[0].strip())
            text = row[1].strip() if len(row) > 1 else ""
            note = row[2].strip() if len(row) > 2 else ""
            out[sid] = (text, note)
    return out


def main() -> None:
    curated = load_curated()
    print(f"[i] kuratiert: {len(curated)} IDs")

    merged: dict[int, tuple[str, str]] = {}
    from_inventory = 0
    skipped_sound = 0

    with INVENTORY.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        header = next(reader, None)
        if not header or header[0].strip().lower() != "id":
            raise SystemExit("FEHLER: Inventar-Kopfzeile unerwartet: %r" % (header,))
        for row in reader:
            if not row or not row[0].strip():
                continue
            sid = int(row[0].strip())
            de = row[2].strip() if len(row) > 2 else ""
            if sid in curated:
                merged[sid] = curated[sid]
                continue
            if not de or de == "-":
                merged[sid] = ("", SOUND_ONLY_NOTE)
                skipped_sound += 1
            else:
                merged[sid] = (de, "aus Inventar")
                from_inventory += 1

    # Kuratierte IDs, die im Inventar fehlen, trotzdem aufnehmen
    extra = [sid for sid in curated if sid not in merged]
    for sid in extra:
        merged[sid] = curated[sid]

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=";", lineterminator="\n")
        writer.writerow(["id", "text", "note"])
        for sid in sorted(merged):
            text, note = merged[sid]
            writer.writerow([sid, text, note])

    with_text = sum(1 for t, _ in merged.values() if t)
    print(f"[i] Inventar-Uebersetzungen uebernommen : {from_inventory}")
    print(f"[i] Geraeusch-IDs (kein TTS)           : {skipped_sound}")
    print(f"[i] nur kuratiert (nicht im Inventar)  : {len(extra)} {extra if extra else ''}")
    print(f"[i] Gesamt-IDs                          : {len(merged)}")
    print(f"[i] davon mit deutschem Text            : {with_text}")
    print(f"[+] geschrieben: {OUT}")


if __name__ == "__main__":
    main()
