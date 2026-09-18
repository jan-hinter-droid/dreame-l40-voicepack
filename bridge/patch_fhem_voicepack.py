#!/usr/bin/env python3
"""
Traegt den voicepack-Befehl in die FHEM-setList von Dreame_L40 ein.

  set Dreame_L40 voicepack gordon
  set Dreame_L40 voicepack list
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

CFG = Path("/opt/fhem/fhem.cfg")
ANCHOR = "volume:0..10 dreame/L40/set/volume $EVTPART1"
NEW = ("\\\nvoicepack:gordon,fullde,decustom,screamtest,factoryde,list "
       "dreame/L40/set/voicepack $EVTPART1")


def main() -> None:
    src = CFG.read_text(encoding="utf-8", errors="replace")

    if "voicepack:" in src:
        print("[=] voicepack steht bereits in der setList.")
        return
    if ANCHOR not in src:
        sys.exit("FEHLER: volume-Anker nicht gefunden - erst patch_fhem_volume.py anwenden")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = f"/opt/fhem/fhem.cfg.bak.voicepack-switch-{stamp}"
    r = subprocess.run(["sudo", "-n", "cp", str(CFG), backup],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FEHLER beim Backup: {r.stderr.strip()}")
    print(f"[i] Backup: {backup}")

    src = src.replace(ANCHOR, ANCHOR + NEW, 1)

    tmp = Path("/tmp/fhem_cfg_vp")
    tmp.write_text(src, encoding="utf-8")
    r = subprocess.run(["sudo", "-n", "cp", str(tmp), str(CFG)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FEHLER beim Schreiben: {r.stderr.strip()}")

    print("[+] fhem.cfg aktualisiert: set Dreame_L40 voicepack <name>")
    print("[i] In FHEM laden mit: rereadcfg")


if __name__ == "__main__":
    main()
