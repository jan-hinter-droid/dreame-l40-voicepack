#!/usr/bin/env python3
"""
v6-Patch: behebt das Blockieren des Command-Workers nach einer Installation.

Problem (am 18.09. am Geraet aufgetreten): install_voice_pack pollte den
Fortschritt bis zu 240 s weiter, wenn der interne Zustand nicht als "success"
erkannt wurde. Der command_worker verarbeitete in der Zeit keine Befehle mehr -
die Bridge wirkte tot, sendete aber weiter Status.

Loesung:
  * Abbruch zusaetzlich, sobald VOICE_PACKET_ID die Ziel-ID zeigt
  * Poll-Intervall mit Backoff, harte Obergrenze 75 s statt 240 s
  * Fehler beim Zustandsabruf brechen die Schleife nicht mehr ab
  * Zeitablauf wird geloggt statt still zu enden
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")

OLD = '''    # Fortschritt verfolgen - bewusst langsam, das Geraet mag keine Hektik.
    last_status = None
    deadline = time.time() + 240
    final = None
    while time.time() < deadline:
        time.sleep(5)
        try:
            property_request(VOICE_POLL_STATUS, publish=False)
        except Exception:
            log.warning("Statusabfrage waehrend Voice-Install fehlgeschlagen", exc_info=True)
        packet_id = raw_state.get("VOICE_PACKET_ID")
        status = raw_state.get("VOICE_CHANGE_STATUS")
        if status != last_status:
            log.info("Sprachpaket-Status: %s", json_safe(status))
            last_status = status
        final = {
            "packet_id": packet_id,
            "status": json_safe(status),
        }
        state = ""
        if isinstance(status, str):
            try:
                state = json.loads(status).get("state", "")
            except Exception:
                state = ""
        if state == "success":
            break
        if state in ("failed", "error"):
            raise RuntimeError("Installation fehlgeschlagen: %s" % json_safe(status))
'''

NEW = '''    # Fortschritt verfolgen. Wichtig: den command_worker NICHT lange blockieren -
    # solange diese Funktion laeuft, verarbeitet die Bridge keine weiteren Befehle.
    last_status = None
    start = time.time()
    deadline = start + 75          # harte Obergrenze, das Geraet braucht ~5-16 s
    interval = 2
    final = None
    outcome = "timeout"
    while time.time() < deadline:
        time.sleep(interval)
        interval = min(interval + 1, 6)      # sanftes Backoff
        try:
            property_request(VOICE_POLL_STATUS, publish=False)
        except Exception:
            log.warning("Statusabfrage waehrend Voice-Install fehlgeschlagen", exc_info=True)

        packet_id = raw_state.get("VOICE_PACKET_ID")
        status = raw_state.get("VOICE_CHANGE_STATUS")
        if status != last_status:
            log.info("Sprachpaket-Status: %s", json_safe(status))
            last_status = status

        state = ""
        if isinstance(status, str):
            try:
                state = json.loads(status).get("state", "")
            except Exception:
                state = ""

        final = {"packet_id": packet_id, "status": json_safe(status), "state": state}

        # Erfolg: entweder das Geraet meldet success ODER die Ziel-ID ist aktiv.
        # Die zweite Bedingung ist der zuverlaessigere Weg.
        if state == "success" or packet_id == lang_id:
            outcome = "success"
            break
        if state in ("failed", "fail", "error"):
            outcome = "failed"
            break

    elapsed = round(time.time() - start, 1)
    if outcome == "success":
        log.info("Sprachpaket aktiv: id=%s nach %ss", lang_id, elapsed)
    elif outcome == "failed":
        raise RuntimeError("Installation fehlgeschlagen: %s" % json_safe(last_status))
    else:
        log.warning(
            "Sprachpaket-Status nach %ss nicht bestaetigt (letzter Stand: %s). "
            "Bitte mit voiceStatus pruefen.", elapsed, json_safe(last_status),
        )
'''


def main() -> None:
    src = BRIDGE.read_text(encoding="utf-8")

    if "outcome = \"timeout\"" in src:
        print("[=] v6 ist bereits eingebaut.")
        return
    if OLD not in src:
        sys.exit("FEHLER: alter Poll-Block nicht gefunden - ist v2 eingebaut?")

    src = src.replace(OLD, NEW, 1)
    src = re.sub(r'BRIDGE_VERSION = "[^"]*"',
                 'BRIDGE_VERSION = "3.8-voicepack-nonblocking"', src, count=1)

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.nonblocking-" + time.strftime("%Y%m%d-%H%M%S"))
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

    print("[+] Bridge v6: Installations-Polling blockiert den Worker nicht mehr")
    print("[i] Neu starten: sudo systemctl restart dreame-fhem.service")


if __name__ == "__main__":
    main()
