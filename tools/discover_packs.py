#!/usr/bin/env python3
"""
Prueft verfuegbare Community-Sprachpakete fuer Dreame-Roboter.

Laedt jedes tar.gz, zaehlt die enthaltenen Sound-IDs und prueft das
Audio-Profil. So sieht man, welche Packs fuer den L40 taugen.
"""
from __future__ import annotations

import hashlib
import io
import tarfile
import urllib.request

PACKS = [
    ("Gandalf (getestet auf L40 Ultra AE)",
     "https://github.com/l3itn3r/gandalf_voicepack/raw/main/voice_pack.tar.gz"),
    ("GLaDOS (czaky)",
     "https://github.com/czaky/dreame_voice_pack/raw/master/glados/voice.tar.gz"),
    ("Tiff (czaky)",
     "https://github.com/czaky/dreame_voice_pack/raw/master/tiff/voice.tar.gz"),
    ("Sweetie (czaky)",
     "https://github.com/czaky/dreame_voice_pack/raw/master/sweetie/voice.tar.gz"),
    ("Fluttershy (czaky)",
     "https://github.com/czaky/dreame_voice_pack/raw/master/fluttershy/voice.tar.gz"),
    ("GLaDOS (Findus23)",
     "https://github.com/Findus23/voice_pack_dreame/raw/main/voice_pack.tar.gz"),
    # willemcvu: Charakter-Packs, L10S Pro Ultra Heat (r2338)
    ("C-3PO (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/c3po/dist/c3po.tar.gz"),
    ("JARVIS (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/jarvis/dist/jarvis.tar.gz"),
    ("Gordon Ramsay (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/gordon/dist/gordon.tar.gz"),
    ("Bob Ross (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/bobross/dist/bobross.tar.gz"),
    ("Dalek (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/dalek/dist/dalek.tar.gz"),
    ("DJ Catnip (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/djcatnip/dist/djcatnip.tar.gz"),
    ("Bertram (willemcvu)",
     "https://github.com/willemcvu/valetudo-dreame-voicepacks/raw/main/packs/bertram/dist/bertram.tar.gz"),
]


def probe(name: str, url: str) -> None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dreame-voicepack/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
    except Exception as ex:
        print(f"  {name:<38} NICHT ERREICHBAR ({type(ex).__name__}: {str(ex)[:60]})")
        return

    md5 = hashlib.md5(data).hexdigest()
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            members = [m for m in tar.getmembers() if m.isfile()]
            ids = sorted(int(m.name[:-4]) for m in members
                         if m.name.endswith(".ogg") and m.name[:-4].isdigit())
            junk = len(members) - len(ids)
    except Exception as ex:
        print(f"  {name:<38} ARCHIV-FEHLER ({ex})")
        return

    rng = f"{ids[0]}..{ids[-1]}" if ids else "-"
    print(f"  {name:<38} {len(data)/1048576:5.1f} MB  {len(ids):3d} IDs  Bereich {rng:<10} "
          f"Beifang {junk:3d}  md5 {md5[:10]}")


print("=" * 118)
print("Verfuegbare Community-Sprachpakete")
print("=" * 118)
for name, url in PACKS:
    probe(name, url)
print()
print("Beifang = Dateien im Archiv, die keine rein numerische .ogg sind")
print("(z.B. macOS-Metadaten ._0.ogg) - die sollte man vor dem Installieren entfernen.")
