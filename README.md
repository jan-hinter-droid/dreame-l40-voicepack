# Dreame L40 Ultra – Custom Voice Packs

Eigene Ansagen für einen **Dreame L40 Ultra** (`dreame.vacuum.r2492j`), installiert über die
Dreame-Cloud-API. Der Roboter lädt das Paket selbst herunter, prüft die MD5 und entpackt es.

**Status: am Gerät verifiziert.** Das deutsche Custom-Paket ist installiert und aktiv.

## Ergebnis auf einen Blick

| Was | Wert |
|---|---|
| Aktives Sprachpaket | `DECUSTOM` (185 deutsche Ansagen) |
| Installationsdauer | ~5 Sekunden nach dem Befehl |
| Fortschrittsmeldung | `VOICE_CHANGE_STATUS`: `state=success`, `progress=100` |
| Schrei bei „steckt fest" | Sound-ID 40 (CC0-Wilhelm-Scream, pitch-verschoben) |

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
   sie werden bei Bedarf nachgeladen.

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
set Dreame_L40 installVoicePack DECUSTOM|https://raw.githubusercontent.com/jan-hinter-droid/dreame-l40-voicepack/main/dist/decustom.tar.gz|421d6637e5a256ab5992e8a4d4a73398|3213752
```

3. Status prüfen:

```
set Dreame_L40 voiceStatus
```

Readings: `voice_packet_id`, `voice_change_status`.

Alternativ über MQTT mit JSON:

```bash
mosquitto_pub -h 127.0.0.1 -t dreame/L40/set -m \
 '{"command":"installVoicePack","value":{"lang_id":"DECUSTOM","url":"...","md5":"...","size":123}}'
```

## Rollback auf Werksstimme

Siehe Fallstrick 3: es braucht eine gültige URL des offiziellen Sprachpakets.

```powershell
python diagnose/set_voicepack.py DE "<offizielle-de-Paket-URL>" "<md5>" <size> --wait
```

Das offizielle DE-Paket folgt dem Muster
`http://awsde0.fds.api.xiaomi.com/dreame-product/<modell>/voices/package/deyu.tar.gz`
(für `dreame.vacuum.p2009` belegt, für `r2492j` noch nicht gefunden).

## Bridge-Anpassung

`dreame-fhem.service` läuft mit `/home/pi/dreame_fhem_bridge.py`. Die Patches liegen in
`bridge/` und sind in dieser Reihenfolge anzuwenden:

| Patch | Wirkung |
|---|---|
| `patch_bridge.py` | fügt `installVoicePack` (JSON) und `voiceStatus` hinzu |
| `patch_bridge_v2.py` | prüft `lang_id`, sichert das Host-Präfix, verfolgt den Fortschritt |
| `patch_bridge_v3.py` | erlaubt zusätzlich das FHEM-taugliche Pipe-Format |
| `patch_fhem_setlist.py` | trägt beide Befehle in die `setList` von `Dreame_L40` ein |

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
