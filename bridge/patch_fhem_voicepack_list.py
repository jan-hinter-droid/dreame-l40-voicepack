#!/usr/bin/env python3
"""
Aktualisiert die voicepack-Auswahl in der FHEM-setList von Dreame_L40.

Ersetzt die bisherige Liste durch alle registrierten Kurznamen.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

CFG = Path("/opt/fhem/fhem.cfg")

PACKS = ["gordon", "dalek", "bobross", "jarvis", "c3po", "djcatnip", "bertram",
         "fullde", "decustom", "memes", "screamtest", "factoryde", "list"]


def main() -> None:
    src = CFG.read_text(encoding="utf-8", errors="replace")

    pattern = re.compile(r"voicepack:[^\s]+ dreame/L40/set/voicepack \$EVTPART1")
    if not pattern.search(src):
        sys.exit("FEHLER: voicepack-Zeile nicht gefunden - erst patch_fhem_voicepack.py anwenden")

    new_line = ("voicepack:" + ",".join(PACKS)
                + " dreame/L40/set/voicepack $EVTPART1")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = f"/opt/fhem/fhem.cfg.bak.voicepack-list-{stamp}"
    r = subprocess.run(["sudo", "-n", "cp", str(CFG), backup],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FEHLER beim Backup: {r.stderr.strip()}")
    print(f"[i] Backup: {backup}")

    src, n = pattern.subn(new_line, src, count=1)
    print(f"[i] {n} Zeile ersetzt")

    tmp = Path("/tmp/fhem_cfg_vplist")
    tmp.write_text(src, encoding="utf-8")
    r = subprocess.run(["sudo", "-n", "cp", str(tmp), str(CFG)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FEHLER beim Schreiben: {r.stderr.strip()}")

    print("[+] fhem.cfg aktualisiert")
    print("    " + new_line)
    print("[i] In FHEM laden mit: rereadcfg")


if __name__ == "__main__":
    main()
