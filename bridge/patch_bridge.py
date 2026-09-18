#!/usr/bin/env python3
"""
Patcht /home/pi/dreame_fhem_bridge.py um einen installVoicePack-Befehl.

Fuegt hinzu:
  1. install_voice_pack()  -> set_properties siid 7 / piid 4 (write-only)
  2. execute_command(): Zweig "installVoicePack" und "voiceStatus"
  3. FAST_PROPERTIES: VOICE_PACKET_ID, VOICE_CHANGE_STATUS (Status sichtbar in FHEM)
  4. Versionskennung

Idempotent: laeuft der Patch zweimal, passiert beim zweiten Mal nichts.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")
MARKER = "def install_voice_pack("

HELPER = '''

# ---------------------------------------------------------------------------
# Sprachpaket-Installation (VOICE_CHANGE = siid 7 / piid 4, write-only)
# ---------------------------------------------------------------------------
def install_voice_pack(lang_id, url, md5, size):
    """Laesst den Roboter ein Sprachpaket von einer URL laden und installieren.

    Der Roboter holt die Datei selbst, prueft die MD5 und entpackt sie.
    Fortschritt danach ueber VOICE_CHANGE_STATUS / VOICE_PACKET_ID.
    """
    lang_id = str(lang_id).strip()
    url = str(url).strip()
    md5 = str(md5).strip()
    if not lang_id or not url or not md5:
        raise ValueError("lang_id, url und md5 sind Pflicht")
    try:
        size = int(size)
    except (TypeError, ValueError):
        raise ValueError("size muss eine Zahl in Bytes sein")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("url muss mit http:// oder https:// beginnen")

    # Genau so erwartet es das Geraet - kompakt, ohne Leerzeichen.
    payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (
        lang_id, url, md5, size,
    )
    params = [{
        "did": str(DEVICE_ID),
        "siid": 7,
        "piid": 4,
        "value": payload,
    }]
    log.info("Sprachpaket-Installation: id=%s size=%d url=%s", lang_id, size, url)
    with operation_lock:
        with cloud_lock:
            result = cloud.send("set_properties", params, retry_count=1)
    save_token()

    # Sofort nachsehen, was das Geraet daraus macht.
    try:
        property_request(["VOICE_PACKET_ID", "VOICE_CHANGE_STATUS"], publish=True)
    except Exception:
        log.warning("Statusabfrage nach Voice-Install fehlgeschlagen", exc_info=True)
    return {"lang_id": lang_id, "size": size, "result": json_safe(result)}


def voice_status():
    """Aktueller Zustand des Sprachpakets."""
    property_request(["VOICE_PACKET_ID", "VOICE_CHANGE_STATUS"], publish=True)
    return {
        "voice_packet_id": raw_state.get("VOICE_PACKET_ID"),
        "voice_change_status": json_safe(raw_state.get("VOICE_CHANGE_STATUS")),
    }

'''

COMMAND_BRANCH = '''    if command == "installVoicePack":
        return install_voice_pack(
            value.get("lang_id") if isinstance(value, dict) else None,
            value.get("url") if isinstance(value, dict) else None,
            value.get("md5") if isinstance(value, dict) else None,
            value.get("size") if isinstance(value, dict) else None,
        )
    if command == "voiceStatus":
        return voice_status()

'''


def main() -> None:
    if not BRIDGE.exists():
        sys.exit(f"FEHLER: {BRIDGE} nicht gefunden")

    src = BRIDGE.read_text(encoding="utf-8")

    if MARKER in src:
        print("[=] Patch ist bereits eingebaut - nichts zu tun.")
        return

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.voicepack-" + time.strftime("%Y%m%d-%H%M%S")
    )
    shutil.copy2(BRIDGE, backup)
    print(f"[i] Backup: {backup}")

    changed = src

    # --- 1) Helper einfuegen, direkt vor set_property()
    anchor = "\ndef set_property(name, value):"
    if anchor not in changed:
        sys.exit("FEHLER: Anker 'def set_property(name, value):' nicht gefunden")
    changed = changed.replace(anchor, HELPER + "\ndef set_property(name, value):", 1)

    # --- 2) Kommandozweige in execute_command() ergaenzen
    cmd_anchor = '    raise ValueError("Unbekannter Befehl: " + command)'
    if cmd_anchor not in changed:
        sys.exit("FEHLER: Anker 'Unbekannter Befehl' nicht gefunden")
    changed = changed.replace(cmd_anchor, COMMAND_BRANCH + cmd_anchor, 1)

    # --- 3) Voice-Properties in FAST_PROPERTIES aufnehmen
    fast_anchor = '"WATER_TEMPERATURE", "MOP_IN_STATION", "MOP_PAD_INSTALLED",\n]'
    if fast_anchor in changed:
        changed = changed.replace(
            fast_anchor,
            '"WATER_TEMPERATURE", "MOP_IN_STATION", "MOP_PAD_INSTALLED",\n'
            '    "VOICE_PACKET_ID", "VOICE_CHANGE_STATUS",\n]',
            1,
        )
    else:
        print("[!] FAST_PROPERTIES-Anker nicht gefunden - Status wird seltener aktualisiert")

    # --- 4) Versionskennung
    changed = re.sub(
        r'BRIDGE_VERSION = "[^"]*"',
        'BRIDGE_VERSION = "3.3-voicepack-fhem"',
        changed,
        count=1,
    )

    BRIDGE.write_text(changed, encoding="utf-8")
    print("[+] Bridge gepatcht.")

    # Syntaxpruefung
    import py_compile
    try:
        py_compile.compile(str(BRIDGE), doraise=True)
        print("[+] Syntaxpruefung OK")
    except py_compile.PyCompileError as ex:
        shutil.copy2(backup, BRIDGE)
        sys.exit(f"FEHLER: Syntax kaputt, Backup zurueckgespielt.\n{ex}")

    print("[i] Neu starten mit: sudo systemctl restart dreame-fhem.service")


if __name__ == "__main__":
    main()
