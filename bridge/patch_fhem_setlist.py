#!/usr/bin/env python3
"""
Traegt installVoicePack und voiceStatus in die FHEM-setList von Dreame_L40 ein.

FHEM zerlegt set-Befehle an Leerzeichen, daher hat installVoicePack bewusst
kein Leerzeichen in der Befehlsdefinition (textField, ein Argument).
Idempotent.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

CFG = Path("/opt/fhem/fhem.cfg")

NEW_LINES = (
    "\\\n"
    "installVoicePack:textField dreame/L40/set/installVoicePack $EVTPART1\\\n"
    "voiceStatus:noArg dreame/L40/set/voiceStatus"
)


def main() -> None:
    if not CFG.exists():
        sys.exit(f"FEHLER: {CFG} nicht gefunden")

    src = CFG.read_text(encoding="utf-8", errors="replace")

    if "installVoicePack" in src:
        print("[=] setList enthaelt installVoicePack bereits.")
        return

    # Anker: die letzte Zeile der Dreame_L40-setList
    anchor = "cleanGenius:off,routine,deep dreame/L40/set/cleanGenius $EVTPART1"
    if anchor not in src:
        sys.exit("FEHLER: Anker am Ende der Dreame_L40-setList nicht gefunden")

    # Sicherstellen, dass wir in der richtigen Definition sind
    def_start = src.find("define Dreame_L40 MQTT2_DEVICE")
    def_anchor = src.find(anchor)
    if def_start == -1 or def_anchor == -1 or def_anchor < def_start:
        sys.exit("FEHLER: Anker gehoert nicht zu Dreame_L40")

    nxt = src.find("\ndefine ", def_anchor)
    if nxt == -1:
        nxt = len(src)
    if "setList" not in src[def_start:nxt]:
        sys.exit("FEHLER: Anker liegt nicht innerhalb der setList")

    # fhem.cfg gehoert dem Benutzer 'fhem' -> alles ueber sudo und /tmp abwickeln
    import subprocess

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = Path(f"/opt/fhem/fhem.cfg.bak.voicepack-{stamp}")
    result = subprocess.run(
        ["sudo", "-n", "cp", str(CFG), str(backup)], capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f"FEHLER beim Backup: {result.stderr.strip()}")
    print(f"[i] Backup: {backup}")

    src = src[:def_anchor + len(anchor)] + NEW_LINES + src[def_anchor + len(anchor):]

    tmp = Path("/tmp/fhem_cfg_new")
    tmp.write_text(src, encoding="utf-8")
    result = subprocess.run(
        ["sudo", "-n", "cp", str(tmp), str(CFG)], capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f"FEHLER beim Schreiben: {result.stderr.strip()}")
    print("[+] fhem.cfg aktualisiert.")
    print()
    print("Neue Befehle:")
    print("  set Dreame_L40 voiceStatus")
    print("  set Dreame_L40 installVoicePack DECUSTOM|<url>|<md5>|<size>")
    print()
    print("[i] In FHEM laden mit: rereadcfg   (oder: shutdown restart)")


if __name__ == "__main__":
    main()
