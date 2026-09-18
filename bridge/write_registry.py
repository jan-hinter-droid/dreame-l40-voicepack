#!/usr/bin/env python3
"""
Schreibt die Sprachpaket-Registry mit allen bereitgestellten Packs.

Erzeugt /home/pi/voicepacks.json. Die Bridge liest die Datei bei jeder
Aenderung neu ein - kein Neustart noetig.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TARGET = Path("/home/pi/voicepacks.json")
CDN = "https://cdn.jsdelivr.net/gh/jan-hinter-droid/dreame-l40-voicepack@main/dist"

PACKS = {
    # --- Englische Charakter-Packs, je 417 IDs (89 % Abdeckung) ---
    "gordon": {
        "name": "Gordon Ramsay - wuender Chef",
        "lang_id": "GORDON", "file": "gordon.tar.gz",
        "md5": "757b03b51107b8bffc477515542e816a", "size": 5532769,
    },
    "dalek": {
        "name": "Dalek - EXTERMINATE",
        "lang_id": "DALEK", "file": "dalek.tar.gz",
        "md5": "a0cd97ebc1de7c20f7f67b0a54b31e9c", "size": 6961417,
    },
    "bobross": {
        "name": "Bob Ross - ganz entspannt",
        "lang_id": "BOBROSS", "file": "bobross.tar.gz",
        "md5": "2749578756967bdff60e6e3af464ce37", "size": 6353871,
    },
    "jarvis": {
        "name": "JARVIS - vornehmer Butler",
        "lang_id": "JARVIS", "file": "jarvis.tar.gz",
        "md5": "ab8593ad730a7a33a5118f0e67c9a559", "size": 5782001,
    },
    "c3po": {
        "name": "C-3PO - nervoeser Droide",
        "lang_id": "C3PO", "file": "c3po.tar.gz",
        "md5": "9a628352e629a58a45721b0a9f15ac6b", "size": 5838609,
    },
    "djcatnip": {
        "name": "DJ Catnip - Katzen-DJ",
        "lang_id": "DJCATNIP", "file": "djcatnip.tar.gz",
        "md5": "9295fa113332fd9074252fe2fa1e1330", "size": 6815343,
    },
    "bertram": {
        "name": "Bertram - sarkastischer Butler",
        "lang_id": "BERTRAM", "file": "bertram.tar.gz",
        "md5": "3eea205a0de18178abc2162c89c433e2", "size": 6254759,
    },
    # --- Deutsche Eigenproduktion ---
    "fullde": {
        "name": "Deutsch - eigene Ansagen (466 IDs)",
        "lang_id": "FULLDE", "file": "fullde.tar.gz",
        "md5": "d92f468e340fd3d0056d06e7f8ad0e6d", "size": 8182192,
    },
    "decustom": {
        "name": "Deutsch - kurze Fassung (185 IDs)",
        "lang_id": "DECUSTOM", "file": "decustom.tar.gz",
        "md5": "421d6637e5a256ab5992e8a4d4a73398", "size": 3213752,
    },
    # --- Sonderfaelle ---
    "screamtest": {
        "name": "Testpaket: locate spielt den Schrei",
        "lang_id": "SCREAMTEST", "file": "screamtest.tar.gz",
        "md5": "c3b2e03440fe1cf47b8421c662ff8b72", "size": 8196176,
    },
    "memes": {
        "name": "Meme-Sounds (nur 48 IDs, 10 % Abdeckung)",
        "lang_id": "MEMES", "file": "memes.tar.gz",
        "md5": "2b11d4e90596ed3b653d05115b90e27a", "size": 1907718,
    },
    # --- Werksstimmen (Rollback) ---
    "factoryde": {
        "name": "Werksstimme Deutsch (Rollback)",
        "lang_id": "DE",
        "url": "https://oss.iot.dreame.tech/dreame-product/resources/"
               "2ee3cc51bef5352957fe4c30b39d5642",
        "md5": "2ee3cc51bef5352957fe4c30b39d5642", "size": 8954023,
    },
}


def main() -> None:
    existing = {}
    if TARGET.exists():
        try:
            existing = json.loads(TARGET.read_text(encoding="utf-8")).get("packs", {})
        except Exception:
            existing = {}

    packs = {}
    for key, entry in PACKS.items():
        item = {
            "name": entry["name"],
            "lang_id": entry["lang_id"],
            "url": entry.get("url") or f"{CDN}/{entry['file']}",
            "md5": entry["md5"],
            "size": entry["size"],
        }
        packs[key] = item

    # Eigene Ergaenzungen des Nutzers nicht wegwerfen
    for key, entry in existing.items():
        if key not in packs:
            packs[key] = entry
            print(f"[i] eigene Ergänzung behalten: {key}")

    data = {
        "_hinweis": ("Kurznamen fuer 'set Dreame_L40 voicepack <name>'. "
                     "url/md5/size aus dem Build uebernehmen."),
        "packs": packs,
    }

    TARGET.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] {TARGET} geschrieben: {len(packs)} Pakete")
    for key in sorted(packs):
        print(f"      {key:<12} {packs[key]['name']}")


if __name__ == "__main__":
    main()
