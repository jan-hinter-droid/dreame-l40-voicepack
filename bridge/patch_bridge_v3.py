#!/usr/bin/env python3
"""
v3-Patch: installVoicePack auch mit pipe-Format aufrufbar.

FHEM zerlegt set-Befehle an Leerzeichen, deshalb ist JSON dort unbrauchbar.
Zusaetzlich unterstuetzt der Befehl jetzt:

  installVoicePack DECUSTOM|https://.../decustom.tar.gz|<md5>|<size>

JSON bleibt weiterhin gueltig (fuer MQTT und Skripte).
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")

OLD = '''    if command == "installVoicePack":
        if not isinstance(value, dict):
            raise ValueError(
                "installVoicePack braucht ein Objekt mit lang_id, url, md5, size"
            )
        return install_voice_pack(
            value.get("lang_id"),
            value.get("url"),
            value.get("md5"),
            value.get("size"),
        )'''

NEW = '''    if command == "installVoicePack":
        # Zwei Schreibweisen:
        #   JSON (MQTT/Skripte): {"command":"installVoicePack","value":{...}}
        #   Pipe (FHEM, weil dort an Leerzeichen getrennt wird):
        #   installVoicePack LANGID|URL|MD5|SIZE
        if isinstance(value, dict):
            return install_voice_pack(
                value.get("lang_id"),
                value.get("url"),
                value.get("md5"),
                value.get("size"),
            )
        if isinstance(value, str) and "|" in value:
            parts = [p.strip() for p in value.split("|")]
            if len(parts) != 4:
                raise ValueError(
                    "Format: installVoicePack LANGID|URL|MD5|SIZE "
                    "(4 durch | getrennte Felder, keine Leerzeichen)"
                )
            return install_voice_pack(parts[0], parts[1], parts[2], parts[3])
        raise ValueError(
            "installVoicePack erwartet JSON oder LANGID|URL|MD5|SIZE"
        )'''

BRIDGE_VERSION = 'BRIDGE_VERSION = "3.5-voicepack-fhem"'


def main() -> None:
    src = BRIDGE.read_text(encoding="utf-8")

    if "Pipe (FHEM" in src:
        print("[=] v3 ist bereits eingebaut.")
        return
    if OLD not in src:
        sys.exit("FEHLER: v2-Kommandozweig nicht gefunden - erst patch_bridge_v2.py laufen lassen")

    src = src.replace(OLD, NEW, 1)

    import re
    src = re.sub(r'BRIDGE_VERSION = "[^"]*"', BRIDGE_VERSION, src, count=1)

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.voicepack-v3-" + time.strftime("%Y%m%d-%H%M%S"))
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

    print("[+] Bridge v3: installVoicePack akzeptiert JSON und LANGID|URL|MD5|SIZE")
    print("[i] Neu starten: sudo systemctl restart dreame-fhem.service")


if __name__ == "__main__":
    main()
