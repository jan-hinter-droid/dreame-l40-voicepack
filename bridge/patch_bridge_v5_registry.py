#!/usr/bin/env python3
"""
Sprachpaket-Umschalter fuer die Bridge.

Statt jedes Mal URL, MD5 und Groesse zu tippen, kennt die Bridge jetzt
Kurznamen. Damit wird das Umschalten ein Einzeiler in FHEM:

  set Dreame_L40 voicepack gordon
  set Dreame_L40 voicepack fullde
  set Dreame_L40 voicepack factoryde    # Werksstimme zurueck
  set Dreame_L40 voicepack list

Die Registry liegt in /home/pi/voicepacks.json und wird beim Start geladen.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

BRIDGE = Path("/home/pi/dreame_fhem_bridge.py")
REGISTRY = Path("/home/pi/voicepacks.json")

REGISTRY_JSON = """{
  "_hinweis": "Kurznamen fuer den voicepack-Befehl. url/md5/size aus dem Build uebernehmen.",
  "packs": {
    "gordon": {
      "name": "Gordon Ramsay (englisch, 417 IDs)",
      "lang_id": "GORDON",
      "url": "https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/gordon.tar.gz",
      "md5": "757b03b51107b8bffc477515542e816a",
      "size": 5532769
    },
    "fullde": {
      "name": "Deutsch, eigene Ansagen (466 IDs)",
      "lang_id": "FULLDE",
      "url": "https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/fullde.tar.gz",
      "md5": "d92f468e340fd3d0056d06e7f8ad0e6d",
      "size": 8182192
    },
    "decustom": {
      "name": "Deutsch, kurze Fassung (185 IDs)",
      "lang_id": "DECUSTOM",
      "url": "https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/decustom.tar.gz",
      "md5": "421d6637e5a256ab5992e8a4d4a73398",
      "size": 3213752
    },
    "screamtest": {
      "name": "Testpaket: locate spielt den Schrei",
      "lang_id": "SCREAMTEST",
      "url": "https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist/screamtest.tar.gz",
      "md5": "c3b2e03440fe1cf47b8421c662ff8b72",
      "size": 8196176
    },
    "factoryde": {
      "name": "Werksstimme Deutsch (Rollback)",
      "lang_id": "DE",
      "url": "https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642",
      "md5": "2ee3cc51bef5352957fe4c30b39d5642",
      "size": 8954023
    }
  }
}
"""

ANCHOR = '''    if command in ("volume", "lautstaerke"):'''

NEW = '''    if command in ("voicepack", "sprachpaket"):
        return voicepack_command(value)

    if command in ("volume", "lautstaerke"):'''

HELPER = '''
# ---------------------------------------------------------------------------
# Sprachpaket-Umschalter: Kurznamen aus /home/pi/voicepacks.json
# ---------------------------------------------------------------------------
VOICEPACK_FILE = "/home/pi/voicepacks.json"
_voicepack_cache = {"mtime": 0, "packs": {}}


def load_voicepacks():
    """Registry laden, bei Aenderung automatisch neu einlesen."""
    try:
        mtime = os.path.getmtime(VOICEPACK_FILE)
    except OSError:
        return {}
    if mtime != _voicepack_cache["mtime"]:
        with open(VOICEPACK_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        _voicepack_cache["packs"] = data.get("packs", {})
        _voicepack_cache["mtime"] = mtime
        log.info("Sprachpaket-Registry geladen: %d Eintraege",
                 len(_voicepack_cache["packs"]))
    return _voicepack_cache["packs"]


def voicepack_command(value):
    """value = Kurzname, oder 'list' fuer eine Uebersicht."""
    packs = load_voicepacks()
    if not packs:
        raise RuntimeError("Keine Registry unter %s gefunden" % VOICEPACK_FILE)

    key = str(value or "").strip().lower()

    if key in ("", "list", "liste"):
        return {
            "verfuegbar": {k: v.get("name", "") for k, v in sorted(packs.items())},
            "aktiv": raw_state.get("VOICE_PACKET_ID"),
        }

    if key not in packs:
        raise ValueError(
            "Unbekanntes Sprachpaket '%s'. Verfuegbar: %s"
            % (key, ", ".join(sorted(packs)))
        )

    entry = packs[key]
    return install_voice_pack(
        entry["lang_id"], entry["url"], entry["md5"], entry["size"]
    )

'''


def main() -> None:
    src = BRIDGE.read_text(encoding="utf-8")

    if REGISTRY.exists():
        print(f"[=] {REGISTRY} existiert bereits - wird nicht ueberschrieben.")
    else:
        REGISTRY.write_text(REGISTRY_JSON, encoding="utf-8")
        print(f"[+] {REGISTRY} angelegt")

    if "def voicepack_command(" in src:
        print("[=] voicepack-Befehl ist bereits eingebaut.")
        return
    if ANCHOR not in src:
        sys.exit("FEHLER: volume-Anker nicht gefunden - erst patch_bridge_v4.py anwenden")

    # Helper vor set_property einfuegen
    sp_anchor = "\ndef set_property(name, value):"
    if sp_anchor not in src:
        sys.exit("FEHLER: set_property-Anker nicht gefunden")
    src = src.replace(sp_anchor, HELPER + "\ndef set_property(name, value):", 1)

    # Kommandozweig ergaenzen
    src = src.replace(ANCHOR, NEW, 1)

    src = re.sub(r'BRIDGE_VERSION = "[^"]*"',
                 'BRIDGE_VERSION = "3.7-voicepack-switch"', src, count=1)

    backup = BRIDGE.with_name(
        BRIDGE.name + ".bak.voicepack-registry-" + time.strftime("%Y%m%d-%H%M%S"))
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

    print("[+] Bridge v5: Befehl 'voicepack <name>' mit Registry")
    print("[i] Neu starten: sudo systemctl restart dreame-fhem.service")


if __name__ == "__main__":
    main()
