# Dreame L40 Ultra – Custom Voice Packs

Eigene Ansagen für einen **Dreame L40 Ultra** (`dreame.vacuum.r2492j`), installiert über die
Dreame-Cloud-API. Der Roboter lädt das Paket selbst herunter, prüft die MD5 und entpackt es.

**Status: am Gerät verifiziert.** Das deutsche Custom-Paket ist installiert und aktiv.

## Ergebnis auf einen Blick

| Was | Wert |
|---|---|
| Aktives Sprachpaket | `FULLDE` (466 deutsche Ansagen) |
| Installationsdauer | ~16 Sekunden nach dem Befehl (8,2 MB) |
| Fortschrittsmeldung | `VOICE_CHANGE_STATUS`: `state=downloading` → `state=success`, `progress=100` |
| Schrei bei „steckt fest" | Sound-ID 40 (CC0-Wilhelm-Scream, pitch-verschoben) |
| Lautstärke | 10 von 10 |
| Rollback-Ziel | offizielles DE-Paket, URL siehe unten (verifiziert) |

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
Referenz-Encoding: `ogg/vorbis, 16000 Hz, 1 Kanal, ~100 kbit/s`.

Mit einer eigenen `id` (z. B. `DECUSTOM`) bleiben die Werkssprachpakete unangetastet.

## Fallstricke (alle am Gerät erlebt)

1. **`lang_id` darf keine Bindestriche enthalten.** `SMOKE-TEST` → `code -1`, abgelehnt.
   `DECUSTOM` → funktioniert. Erlaubt: `[A-Za-z0-9_]`, max. 32 Zeichen.
2. **Der Endpoint braucht das Host-Präfix.** Die Bridge holt es in `get_device_info()`
   (Host `10000.mt.eu.iot.dreame.tech:19973`) und baut daraus
   `dreame-iot-com-10000/device/sendCommand`. Ohne diesen Schritt: HTTP 404.
3. **Der Roboter lädt das Paket immer aus dem Netz.** Ein Rollback mit leerer URL scheitert
   mit `state=fail, progress=25`. Auch Werkssprachen brauchen eine gültige tar.gz-URL.
4. **Nicht zu viele Schreibzugriffe in kurzer Folge.** Mehrere `set_properties` hintereinander
   quittiert das Gerät mit `code -1` (Rate-Limit). Die Bridge wartet deshalb 5 s pro Statusabfrage.
5. **Das Paket ist eine Ergänzung, keine Vollabdeckung.** Fehlt eine Sound-ID im Archiv,
   spielt der Roboter für diese Ansage nichts ab. Die Werksdateien liegen nicht auf dem Gerät,
   sie werden bei Bedarf nachgeladen. Das ausgelieferte `fullde` deckt 466 der 470 bekannten
   IDs ab – die vier reinen Geräusche (0, 200, 274, 488) sind absichtlich nicht enthalten,
   weil sie keinen Text haben und die Werkssignaltöne erhalten bleiben sollen.

## Sound-IDs des L40

Die vollständige Inventur liegt in `reference/sound_inventory.csv` (470 IDs, Union aus
[ccoors/dreame_voice_packs](https://github.com/ccoors/dreame_voice_packs) und
[willemcvu/valetudo-dreame-voicepacks](https://github.com/willemcvu/c3po-valetudo-voicepack)).
Das offizielle deutsche Werkspaket für `dreame.vacuum.r2492j` enthält 515 OGG-Dateien –
es ist damit die vollständigste verfügbare Referenz für die tatsächlich belegten IDs.

Besonders relevant für eigene Anpassungen:

| ID | Original | Bedeutung |
|---|---|---|
| 7 | Start cleaning | Start der Reinigung |
| 11 | Paused | Pause |
| 12 / 143 | Cleaning task completed | Fertig |
| 40 | Robot stuck | **steckt fest – hier sitzt der Schrei** |
| 45 | I am here | Antwort auf `locate` |
| 57 | Start zoned cleaning | Bereichsreinigung |
| 110 | Start auto empty | Absaugen |

## Paket bauen

```powershell
python tools/build_pack.py --csv phrases/de_custom.csv --pack decustom
```

Pipeline: `CSV → SAPI-TTS (WAV) → ffmpeg loudnorm → Ogg Vorbis 16 kHz mono → tar.gz`
Ausgabe inklusive MD5 und Byte-Größe landet in `dist/`.

Sound-Overrides (kein TTS, eigene Audiodatei) liegen in `sounds/overrides/<id>.ogg`.
Aktuell: `40.ogg` – der Schrei.

Kandidaten für den Schrei erzeugen:

```powershell
python tools/make_scream.py
```

## Installieren

```powershell
# 1. Paket bauen und pushen
python tools/build_pack.py --csv phrases/de_custom.csv --pack decustom
git add -A; git commit -m "Paket aktualisiert"; git push
```

2. In FHEM absetzen (die Befehle sind in der `setList` von `Dreame_L40` eingetragen):

```
set Dreame_L40 installVoicePack FULLDE|https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/fullde.tar.gz|d92f468e340fd3d0056d06e7f8ad0e6d|8182192
```

3. Status und Lautstärke prüfen:

```
set Dreame_L40 voiceStatus
set Dreame_L40 volume 10
```

Readings: `voice_packet_id`, `voice_change_status`, `volume`.

Alternativ über MQTT mit JSON:

```bash
mosquitto_pub -h 127.0.0.1 -t dreame/L40/set -m \
 '{"command":"installVoicePack","value":{"lang_id":"DECUSTOM","url":"...","md5":"...","size":123}}'
```

## Rollback auf die Werksstimme

Der Roboter lädt Sprachpakete **immer** aus dem Netz (siehe Fallstrick 3), also braucht
auch der Rollback eine gültige URL. Die offizielle deutsche Paket-URL für `dreame.vacuum.r2492j`
ist verifiziert (HTTP 200, 8.954.023 Bytes, MD5 lokal nachgerechnet, 515 OGG-Dateien, gleiches
16-kHz-mono-Format):

| Feld | Wert |
|---|---|
| URL | `https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642` |
| MD5 | `2ee3cc51bef5352957fe4c30b39d5642` |
| Größe | `8954023` |
| `lang_id` | `DE` |

Zurück zur Werksstimme – eine Zeile in FHEM:

```
set Dreame_L40 installVoicePack DE|https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642|2ee3cc51bef5352957fe4c30b39d5642|8954023
```

Das Paket liegt zusätzlich als lokale Sicherung unter
`reference/official-de-r2492j.tar.gz` (nicht im Repo, da Fremdmaterial).

### Das Sprachpaket-Verzeichnis eines Modells

Dreame veröffentlicht pro Modell ein Manifest mit allen verfügbaren Sprachen:

```
http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.r2492j/voices/soundpackage.json
```

Es enthält je Sprache `id`, `name`, `size`, `md5sum` und `download`. Für andere Modelle
einfach den Modellcode im Pfad austauschen. Wichtig: bei neuen Modellen (ab `r2xxx`) liegt das
Paket unter `.../resources/<md5>` – **ohne Sprachcode im Pfad**; das alte Schema
`.../<modell>/voices/package/deyu.tar.gz` gibt es dort nicht mehr (daher HTTP 404).

## Bridge-Anpassung

`dreame-fhem.service` läuft mit `/home/pi/dreame_fhem_bridge.py`. Die Patches liegen in
`bridge/` und sind in dieser Reihenfolge anzuwenden:

| Patch | Wirkung |
|---|---|
| `patch_bridge.py` | fügt `installVoicePack` (JSON) und `voiceStatus` hinzu |
| `patch_bridge_v2.py` | prüft `lang_id`, sichert das Host-Präfix, verfolgt den Fortschritt |
| `patch_bridge_v3.py` | erlaubt zusätzlich das FHEM-taugliche Pipe-Format |
| `patch_bridge_v4.py` | ergänzt den Befehl `volume 0..10` |
| `patch_fhem_setlist.py` | trägt die Befehle `installVoicePack` und `voiceStatus` in die `setList` ein |
| `patch_fhem_volume.py` | trägt `volume:0..10` in die `setList` ein |

Bridge-Version nach allen Patches: `3.6-voicepack-fhem`.
Nach jedem Patch `sudo systemctl restart dreame-fhem.service`, nach den FHEM-Patches
zusätzlich `rereadcfg` in FHEM.

Jeder Patch legt vorher ein Backup an und prüft die Syntax; bei einem Fehler wird
automatisch zurückgerollt.

Diagnose-Werkzeuge in `diagnose/`:

* `trace_http.py` – protokolliert jeden Cloud-HTTP-Call samt Status und Antwort
* `capture_api.py` – fängt die Rohantwort auf `VOICE_CHANGE` ab
* `voice_id_probe.py` – testet, welche `lang_id` das Gerät akzeptiert
* `install_direct.py` – Installation ohne Bridge, direkt über die Cloud
* `set_voicepack.py` – beliebiges Sprachpaket setzen, mit Fortschrittsanzeige

## Herkunft und Lizenzen

* Die Sound-IDs stammen aus der Community-Inventur
  ([ccoors/dreame_voice_packs](https://github.com/ccoors/dreame_voice_packs),
  [willemcvu/valetudo-dreame-voicepacks](https://github.com/willemcvu/c3po-valetudo-voicepack)).
* `sounds/sources/wilhelm.ogg` – Wilhelm Scream, **CC0** (Wikimedia Commons, 2023 vom USC
  freigegeben). Der Schrei in `sounds/overrides/40.ogg` ist eine pitch-verschobene Ableitung davon.
* Deutsche Ansagen: Windows-SAPI-Stimme, lokal synthetisiert.
* Dieses Repo enthält **keine** Dreame-Werksaudiodateien und keine Tonspur aus fremden Videos.
