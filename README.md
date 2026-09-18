# Dreame L40 Ultra – Custom Voice Packs

Eigene Ansagen für einen **Dreame L40 Ultra** (`dreame.vacuum.r2492j`), installiert über die
Dreame-Cloud-API. Der Roboter lädt das Paket selbst herunter, prüft die MD5 und entpackt es.

## Wie es funktioniert

Die Ansagen des Roboters liegen als Ogg-Vorbis-Dateien vor, benannt nach einer Sound-ID
(`7.ogg` = „Start cleaning", `11.ogg` = „Paused", `40.ogg` = „Robot stuck", `45.ogg` = „I am here" …).
Über die write-only Property **`siid 7 / piid 4` (VOICE_CHANGE)** nimmt der Roboter ein
Sprachpaket entgegen:

```
set_properties → siid 7, piid 4
value = {"id":"<LANG>","url":"<tar.gz-URL>","md5":"<md5>","size":<bytes>}
```

Archivformat: **gzip-tar mit Ogg-Vorbis-Dateien, mono 16 kHz, flache Struktur** (keine Unterordner).

Mit einer eigenen `id` (z. B. `DE-CUSTOM`) bleiben die Werkssprachpakete unangetastet –
zurück geht es jederzeit durch Setzen der ID auf `DE`.

## Paket bauen

```powershell
python tools/build_pack.py --csv phrases/de_custom.csv --pack de-custom
```

Pipeline: `CSV → SAPI-TTS (WAV) → ffmpeg loudnorm → Ogg Vorbis 16 kHz mono → tar.gz`
Ausgabe inklusive MD5 und Byte-Größe für den Install-Befehl landet in `dist/`.

Sound-Overrides (kein TTS, eigene Audiodatei) liegen in `sounds/overrides/<id>.ogg`.
Aktuell: `40.ogg` – der Schrei.

## Installieren

1. Paket in dieses Repo committen und pushen.
2. In FHEM bzw. per MQTT den Befehl absetzen:

```
set Dreame_L40 installVoicePack {"lang_id":"DE-CUSTOM","url":"https://github.com/.../dist/de-custom.tar.gz","md5":"<md5>","size":<bytes>}
```

3. Fortschritt beobachten: `set Dreame_L40 voiceStatus`
   → Readings `voice_packet_id` und `voice_change_status`.

## Rollback

```
set Dreame_L40 installVoicePack {"lang_id":"DE","url":"<offizielle-DE-Paket-URL>","md5":"...","size":...}
```

## Herkunft und Lizenzen

* Die Sound-IDs stammen aus der Community-Inventur
  ([ccoors/dreame_voice_packs](https://github.com/ccoors/dreame_voice_packs),
  [willemcvu/valetudo-dreame-voicepacks](https://github.com/willemcvu/c3po-valetudo-voicepack)).
* `sounds/sources/wilhelm.ogg` – Wilhelm Scream, **CC0** (Wikimedia Commons, 2023 vom USC
  freigegeben). Der Schrei in `sounds/overrides/40.ogg` ist eine pitch-verschobene Ableitung davon.
* Deutsche Ansagen: Windows-SAPI-Stimme, lokal synthetisiert.
* Dieses Repo enthält **keine** Dreame-Werksaudiodateien.
