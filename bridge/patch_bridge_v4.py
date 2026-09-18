#!/usr/bin/env python3
"""
v4-Patch: ergaenzt einen volume-Befehl in der Bridge.

Der Roboter hat VOLUME (siid 7 / piid 1) als Property, die Bridge hatte aber
keinen Befehl dafuer. Damit laesst sich die Ansagenlautstaerke aus FHEM setzen:

  set Dreame_L40 volume 10
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")

ANCHOR = '''    if command == "voiceStatus":
        return voice_status()
'''

NEW = '''    if command == "voiceStatus":
        return voice_status()

    if command in ("volume", "lautstaerke"):
        try:
            level = int(value)
        except (TypeError, ValueError):
            raise ValueError("volume erwartet eine Zahl von 0 bis 10")
        if level < 0 or level > 10:
            raise ValueError("volume muss zwischen 0 und 10 liegen")
        result = set_property("VOLUME", level)
        update_property("VOLUME", level, publish=True)
        return {"volume": level, "result": json_safe(result)}
'''


def main() -> None:
    src = BRIDGE.read_text(encoding="utf-8")

    if 'command in ("volume", "lautstaerke")' in src:
        print("[=] v4 ist bereits eingebaut.")
        return
    if ANCHOR not in src:
        sys.exit("FEHLER: voiceStatus-Zweig nicht gefunden - erst v1-v3 anwenden")

    src = src.replace(ANCHOR, NEW, 1)
    src = re.sub(r'BRIDGE_VERSION = "[^"]*"',
                 'BRIDGE_VERSION = "3.6-voicepack-fhem"', src, count=1)

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.volume-" + time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(BRIDGE, backup)
    print(f"[i] Backup: {backup}")

    BRIDGE.write_text(src, encoding="utf-8")

    import py_compile
    try:
        py_compile.compile(str(BRIDGE), doraise=True)
        print("[+] Syntaxpruefung OK")
    except py_compile.PyCompileError as ex:
        shutil.copy2(backup, BRIDGE)
        sys.exit(f"FEHLER: Syntax kaputt, Backup zurueckgespielt.\n{ex}")

    print("[+] Bridge v4: volume-Befehl ergaenzt (0..10)")


if __name__ == "__main__":
    main()
