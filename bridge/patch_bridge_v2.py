#!/usr/bin/env python3
"""
Praeziser Patch der Bridge: ersetzt install_voice_pack/voice_status durch
robuste Fassungen und ergaenzt eine Status-Polling-Schleife.

Gelernt aus dem Live-Test am Geraet:
  * siid 7 / piid 4 antwortet mit code -1, wenn Aufrufe zu schnell kommen
    (auch harmlose Schreibzugriffe). -> nicht in einer Schleife feuern.
  * Der Endpoint braucht das Host-Praefix, das erst get_device_info() setzt.
    -> vor dem Schreiben sicherstellen.
  * Nach Erfolg meldet VOICE_CHANGE_STATUS state=success, progress=100.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")
NEW_HELPER_START = "# ---------------------------------------------------------------------------\n# Sprachpaket-Installation"
OLD_HELPER_MARKER = "def install_voice_pack("
END_MARKER = "\ndef set_property(name, value):"

NEW_HELPER = '''# ---------------------------------------------------------------------------
# Sprachpaket-Installation (VOICE_CHANGE = siid 7 / piid 4, write-only)
#
# Am Geraet verifiziert: der Roboter laedt das tar.gz selbst, prueft die MD5
# und meldet den Fortschritt ueber VOICE_CHANGE_STATUS
# (state=downloading/installing/success, progress=0..100).
# Wichtig: lang_id alphanumerisch halten - Werte mit Bindestrich lehnt der
# L40 Ultra mit code -1 ab.
# ---------------------------------------------------------------------------
VOICE_POLL_STATUS = ["VOICE_PACKET_ID", "VOICE_CHANGE_STATUS"]


def ensure_cloud_host():
    """Der sendCommand-Endpoint braucht das Host-Praefix aus get_device_info()."""
    if not getattr(cloud, "_host", None):
        log.info("Cloud-Host fehlt - hole Geraeteinfo nach")
        cloud.get_device_info()


def install_voice_pack(lang_id, url, md5, size):
    """Sprachpaket installieren und den Fortschritt bis zum Ende verfolgen."""
    lang_id = str(lang_id).strip()
    url = str(url).strip()
    md5 = str(md5).strip()

    if not lang_id or not url or not md5:
        raise ValueError("lang_id, url und md5 sind Pflicht")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,32}", lang_id):
        raise ValueError(
            "lang_id darf nur A-Z, a-z, 0-9 und _ enthalten (max. 32 Zeichen). "
            "Der L40 Ultra lehnt z. B. Bindestriche mit code -1 ab."
        )
    try:
        size = int(size)
    except (TypeError, ValueError):
        raise ValueError("size muss eine Zahl in Bytes sein")
    if size <= 0:
        raise ValueError("size muss groesser als 0 sein")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("url muss mit http:// oder https:// beginnen")

    ensure_cloud_host()

    payload = '{"id":"%s","url":"%s","md5":"%s","size":%d}' % (
        lang_id, url, md5, size,
    )
    params = [{"did": str(DEVICE_ID), "siid": 7, "piid": 4, "value": payload}]

    log.info("Sprachpaket: starte Installation id=%s size=%d", lang_id, size)

    with operation_lock:
        with cloud_lock:
            result = cloud.send("set_properties", params, retry_count=1)

    # code -1 = vom Geraet abgelehnt (meist ungueltige id oder Rate-Limit)
    if not result_ok(result):
        raise RuntimeError(
            "Geraet hat die Installation abgelehnt (Antwort: %s). "
            "Haeufigste Ursache: ungueltige lang_id oder zu viele Befehle "
            "in kurzer Zeit - kurz warten und erneut versuchen."
            % json_safe(result)
        )
    save_token()

    # Fortschritt verfolgen - bewusst langsam, das Geraet mag keine Hektik.
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

    publish_state()
    return {
        "lang_id": lang_id,
        "size": size,
        "final": final,
        "accepted": bool(final and final.get("status")),
    }


def voice_status():
    """Aktuellen Zustand des Sprachpakets abfragen."""
    property_request(VOICE_POLL_STATUS, publish=True)
    return {
        "voice_packet_id": raw_state.get("VOICE_PACKET_ID"),
        "voice_change_status": json_safe(raw_state.get("VOICE_CHANGE_STATUS")),
    }

'''

COMMAND_BRANCH = '''    if command == "installVoicePack":
        if not isinstance(value, dict):
            raise ValueError(
                "installVoicePack braucht ein Objekt mit lang_id, url, md5, size"
            )
        return install_voice_pack(
            value.get("lang_id"),
            value.get("url"),
            value.get("md5"),
            value.get("size"),
        )
    if command == "voiceStatus":
        return voice_status()

'''


def main() -> None:
    if not BRIDGE.exists():
        sys.exit(f"FEHLER: {BRIDGE} nicht gefunden")

    src = BRIDGE.read_text(encoding="utf-8")

    if '"import re"' not in src and "\nimport re\n" not in src:
        src = src.replace("import os\n", "import os\nimport re\n", 1)
        print("[i] import re ergaenzt")

    # --- alten Helper-Block entfernen
    start = src.find(NEW_HELPER_START)
    end = src.find(END_MARKER, start) if start != -1 else -1
    if start == -1 or end == -1:
        sys.exit("FEHLER: alter Helper-Block nicht gefunden")
    src = src[:start] + NEW_HELPER + src[end:]

    # --- alten Kommandozweig entfernen
    branch_start = src.find('    if command == "installVoicePack":')
    branch_end = src.find('    raise ValueError("Unbekannter Befehl: " + command)')
    if branch_start == -1 or branch_end == -1 or branch_start > branch_end:
        sys.exit("FEHLER: alter Kommandozweig nicht gefunden")
    src = src[:branch_start] + COMMAND_BRANCH + src[branch_end:]

    src = re.sub(r'BRIDGE_VERSION = "[^"]*"',
                 'BRIDGE_VERSION = "3.4-voicepack-fhem"', src, count=1)

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.voicepack-v2-" + time.strftime("%Y%m%d-%H%M%S"))
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

    print("[+] Bridge auf Voice-Pack v2 aktualisiert.")
    print("[i] Neu starten: sudo systemctl restart dreame-fhem.service")


if __name__ == "__main__":
    main()
