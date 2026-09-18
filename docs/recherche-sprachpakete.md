# Dreame Voice Packs – Rechercheergebnis für `dreame.vacuum.r2492j` (L40 Ultra / L40 Ultra AE, EU)

Recherchestand: durchgeführt mit HEAD-/GET-Manifest-Prüfungen gegen die echten Dreame-/Xiaomi-CDN-Hosts.
Alle unten als **verifiziert** markierten URLs wurden per HTTP-Request geprüft (Status + Content-Length).

---

## 1. Kernbefund: Es gibt ZWEI verschiedene Voice-Pack-Schemata

Deine 404er sind **kein Tippfehler und kein falscher Modellcode** – das Modell benutzt das alte
Schema schlicht nicht mehr.

### Schema A – „Legacy“ (nur alte Modelle, `p…`-Serie)
```
http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.<MODELL>/voices/package/<code>.tar.gz
```
Sprachcodes sind hier chinesische Umschriften, nicht ISO-Codes:

| id | Dateiname | Sprache |
|----|-----------|---------|
| DE | `deyu.tar.gz` | Deutsch |
| EN | `enyu.tar.gz` / teils `yidali.tar.gz` (fehlerhaft im Manifest) | Englisch |
| RU | `eyu.tar.gz` | Russisch |
| FR | `fayu.tar.gz` | Französisch |
| ES | `xibanya.tar.gz` | Spanisch |
| IT | `yidali.tar.gz` | Italienisch |
| ZH | `hanyu.tar.gz` | Chinesisch |
| KO | `hanyu.tar.gz` | Koreanisch |
| PL | `bolan_mijia.tar.gz` | Polnisch |
| TR | `tuerqi_mijia.tar.gz` | Türkisch |
| PT | `putaoya.tar.gz` | Portugiesisch |

Das ist die Quelle des „deyu" – es ist der **Legacy-Code für Deutsch**.

### Schema B – „Resources/OSS“ (neue Modelle ab ca. `r2xxx`, inkl. `r2492j`)
```
https://oss.iot.dreame.tech/dreame-product/resources/<md5>     ← Europa / DreameHome
https://oss.iot.dreame.life/dreame-product/resources/<md5>     ← andere Region
https://awsde0.fds.api.xiaomi.com/dreame-product/resources/<md5>
```
Der Dateiname **ist** der MD5-Hash, es gibt **keinen Sprachcode im Pfad** und **keine `.tar.gz`-Endung**.
Für `dreame.vacuum.r2492j` existiert der komplette `voices/package/…`-Pfad nicht – deshalb 404.

---

## 2. Der offizielle Listen-Endpunkt (das ist der „Schlüssel")

Für **jedes** Modell mit Voice-Support liegt ein Manifest auf der CDN:

```
http://awsde0.fds.api.xiaomi.com/dreame-product/<MODELL>/voices/soundpackage.json
```

Antwort ist JSON mit `code: 0` und `data.voices[]`; jeder Eintrag enthält
`id` (ISO-Sprachcode), `name`, `size` (Bytes), `md5sum` **und `download` (fertige URL)**.

**Verifiziert:** `…/dreame.vacuum.r2492j/voices/soundpackage.json` → **HTTP 200, 7102 Bytes, 17 Sprachen**

> Nur der Host `awsde0.fds.api.xiaomi.com` funktioniert (EU/German-Node).
> `awsus0`/`awssg0`/`awsjp0`/`awsde1`/`awsde2`/`awsus1` sind nicht auflösbar, `cnbj0` liefert 404.

---

## 3. Verifizierte URLs (alle per HEAD geprüft, Content-Length = Manifest-Größe)

### 3.1 Dein Zielmodell: `dreame.vacuum.r2492j` (L40 Ultra, EU)

| Sprache | URL | HTTP | Größe (Bytes) | MD5 | Quelle |
|---|---|---|---|---|---|
| **DE** | `https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642` | **200** | **8 954 023** | `2ee3cc51bef5352957fe4c30b39d5642` | Manifest |
| EN | `https://oss.iot.dreame.tech/dreame-product/resources/f103533b8691278aeb3256908ecd5a57` | (Manifest) | 6 455 927 | `f103533b8691278aeb3256908ecd5a57` | Manifest |
| ZH | `https://oss.iot.dreame.tech/dreame-product/resources/97c83a4de3e7bd9ee48b362e26ca0a39` | (Manifest) | 6 921 719 | `97c83a4de3e7bd9ee48b362e26ca0a39` | Manifest |
| RU | `https://oss.iot.dreame.tech/dreame-product/resources/bd6dae2e6fab18371f8f4be99ad46a37` | (Manifest) | 7 950 902 | `bd6dae2e6fab18371f8f4be99ad46a37` | Manifest |
| FR | `https://oss.iot.dreame.tech/dreame-product/resources/9b35703ef5f0461c1969eec3d50b8cd4` | (Manifest) | 8 221 580 | `9b35703ef5f0461c1969eec3d50b8cd4` | Manifest |
| IT | `https://oss.iot.dreame.tech/dreame-product/resources/ec8873dc8ff50057fdbbde14d76738e1` | (Manifest) | 8 902 427 | `ec8873dc8ff50057fdbbde14d76738e1` | Manifest |
| ES | `https://oss.iot.dreame.tech/dreame-product/resources/584c9dedf33ca76ec3017081b21748a1` | (Manifest) | 6 082 108 | `584c9dedf33ca76ec3017081b21748a1` | Manifest |
| PL | `https://oss.iot.dreame.tech/dreame-product/resources/38fde9a3d98109e42214a4fe9e6b2201` | (Manifest) | 5 549 313 | `38fde9a3d98109e42214a4fe9e6b2201` | Manifest |
| weitere | KO, JA, TR, TH, VI, SV, NO, DK, PT | (Manifest) | – | – | Manifest |

**Format-Nachweis:** Range-GET `bytes=0-3` → **HTTP 206**, Magic Bytes `1f 8b 08 08`
(= gzip/tar.gz, mit Original-Dateinamen-Flag). Es ist also wirklich ein `.tar.gz`, nur ohne Endung.
Der MD5 ist aus dem Manifest übernommen und **nicht** lokal nachgerechnet (kein Download der 8,9 MB).

### 3.2 Weitere Modelle – deutsche Werkspakete, alle **HTTP 200** verifiziert

| Modell (Gerät) | Sprache | URL | HTTP | Größe | MD5 |
|---|---|---|---|---|---|
| `r2492j` (L40 Ultra) | DE | `https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642` | 200 | 8 954 023 | `2ee3cc51bef5352957fe4c30b39d5642` |
| `r2579a` (L40 Ultra AE) | DE | `https://oss.iot.dreame.life/dreame-product/resources/44cfdc0eed190ae7965c1735045d1ae3` | 200 | 6 993 670 | `44cfdc0eed190ae7965c1735045d1ae3` |
| `r2562a` (L40 Ultra CE) | DE | `https://oss.iot.dreame.life/dreame-product/resources/0e7d582689cc9bb516eee0c6e0e07a31` | 200 | 10 198 476 | `0e7d582689cc9bb516eee0c6e0e07a31` |
| `r2416a` / `r2449a` (X40 Ultra) | DE | `https://oss.iot.dreame.tech/dreame-product/resources/0513367e494ed0cc37570f0954246e25` | 200 | 8 795 545 | `0513367e494ed0cc37570f0954246e25` |
| `r2361a` (L30 Ultra) | DE | `https://awsde0.fds.api.xiaomi.com/dreame-product/resources/66ba640e9d744834b9d90e4c5f2fbd2d` | 200 | 4 419 961 | `66ba640e9d744834b9d90e4c5f2fbd2d` |
| `r2228o` (L10s Ultra) | DE | `https://awsde0.fds.api.xiaomi.com/dreame-product/resources/482e8940924b891d37276fe34e963b7c` | 200 | 2 742 446 | `482e8940924b891d37276fe34e963b7c` |
| `p2009` | DE | `https://awsde0.fds.api.xiaomi.com/dreame-product/resources/1cc42f1547d42128d434e2c18c1046c6` | 200 | 5 097 518 | `1cc42f1547d42128d434e2c18c1046c6` |

### 3.3 Klassische `deyu.tar.gz`-URLs (Schema A) – alle **HTTP 200** verifiziert

| Modell | URL | HTTP | Größe | MD5 |
|---|---|---|---|---|
| `p2008` (Mijia 1C) | `http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.p2008/voices/package/deyu.tar.gz` | 200 | 1 391 385 | `96ab843008bb4d19480ac8a07d648aa7` |
| `p2009` | `http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.p2009/voices/package/deyu.tar.gz` | 200 | 4 067 845 | `d25986c1f608c0897475707e77d856f9` |
| `p2029` | `http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.p2029/voices/package/deyu.tar.gz` | 200 | 4 814 391 | – |
| `p2041o` / `p2041` | `http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.p2041o/voices/package/deyu.tar.gz` | 200 | 2 257 393 | `4d00fd023855163fd143d779b4df67a1` |

> Der p2009-Wert `d25986c1f608c0897475707e77d856f9` / 4 067 845 aus deiner Frage ist damit **bestätigt**.

---

## 4. Modellcodes L40 Ultra / L40 Ultra AE / L40 Ultra CE

Aus der offiziellen Support-Liste des Integrations-Repos
(`docs/supported_devices.md`, Branch `dev`):

| Marketingname | Modellcodes |
|---|---|
| **L40 Ultra** | `dreame.vacuum.r2492a`, `dreame.vacuum.r2492b`, **`dreame.vacuum.r2492j`** |
| **L40 Ultra AE** | `dreame.vacuum.r2579a`, `dreame.vacuum.r2579h`, `dreame.vacuum.r500za`, `dreame.vacuum.r500zh` |
| L40 Ultra CE | `dreame.vacuum.r2562a`, `dreame.vacuum.r2562b`, `dreame.vacuum.r5021a`, `dreame.vacuum.r5021b`, `dreame.vacuum.r5021h` |
| L40 Ultra A | `dreame.vacuum.r5057a` |
| L40 Ultra Gen 2 | `dreame.vacuum.r501t` |
| L40s Ultra AE | `dreame.vacuum.r2579c`, `dreame.vacuum.r2579k`, `dreame.vacuum.r500zc`, `dreame.vacuum.r500zk` |

Valetudo bestätigt für den L40 Ultra genau `r2492a`, `r2492b`, `r2492j`
(`DreameL40UltraValetudoRobot.IMPLEMENTATION_AUTO_DETECTION_HANDLER`).
Wichtig: **`r2492j` ist also korrekt** – nicht `r2493` (das ist X40 Pro Plus).

Getestete und **404**-geprüfte Fehlannahmen (nicht verwenden):
`r2492/…/deyu.tar.gz`, `r2492j/…/deyu.tar.gz`, `r2492j/…/de.tar.gz`, `r2492j/…/deyu_mijia.tar.gz`,
`r2492a/b/c/e/h`, `r2493`, `r2493j`, `r2494`, `r2532`, `r2534`, `r2474`, `r2485` (jeweils `deyu` + `de`).
`r2492j` hat **keinen** `voices/package/`-Pfad – siehe Abschnitt 1.

---

## 5. Gibt es einen Cloud-API-Endpunkt für die Sprachpaket-Liste?

**Kurz: In `Tasshack/dreame-vacuum` gibt es keinen.** Der Code kennt nur *Installieren*, nicht *Auflisten*:

* `dreame/device.py`: `install_voice_pack(lang_id, url, md5, size)` →
  setzt MIoT-Property `VOICE_CHANGE` („siid 7 / piid 4") mit Payload
  `{"id":…,"url":…,"md5":…,"size":…}`.
* Service `dreame_vacuum.vacuum_install_voice_pack` (`services.yaml`) – Beispiel benutzt genau die
  p2009-`deyu`-URL.
* **Der offizielle Listen-Endpunkt ist das CDN-Manifest `…/voices/soundpackage.json`** (Abschnitt 2).
  Das ist der Weg, den die App selbst nutzt – kein Cloud-RPC.

**Zusatzbefund – DreameHome-Cloud (neu, Branch `dev`):** Es gibt jetzt
`DreameVacuumDreameHomeCloudProtocol` (Login mit DreameHome- statt Mi-Home-Konto). Die Endpunkte
stecken in einem base64+zlib-verschleierten String-Table (`DREAME_STRINGS`); ich habe ihn
dekodiert. Basis-URL: `https://{country}.iot.dreame.tech:13267` (bzw. `.iot.mova-tech.com`,
`.iot.trouver-tech.com`). Endpunkte u. a.:

| Zweck | Pfad |
|---|---|
| OAuth-Login | `/dreame-auth/oauth/token` |
| Geräteliste | `/dreame-user-iot/iotuserbind/device/listV2` |
| Geräte-Info | `/dreame-user-iot/iotuserbind/device/info` |
| OTC-Info | `/dreame-user-iot/iotstatus/devOTCInfo` |
| RPC an Gerät | `/dreame-iot-com{ -<host> }/device/sendCommand` |
| Datei-Download-URL | `/dreame-user-iot/iotfile/getDownloadUrl`, `/…/getOss1dDownloadUrl` |
| Gerätedatei | `/file-bridge/user/getDeiviceFile` |

**Ein Voice-Pack-Listen-Endpunkt existiert dort nicht** (im dekodierten Table gibt es keinen
`voice`/`sound`-String). Die App holt die Liste ebenfalls über `soundpackage.json`.

---

## 6. Empfehlung: So bekommst du das deutsche Werkspaket für `dreame.vacuum.r2492j`

1. **Manifest abrufen** (klein, ~7 KB – kein „großer Download"):
   ```
   http://awsde0.fds.api.xiaomi.com/dreame-product/dreame.vacuum.r2492j/voices/soundpackage.json
   ```
2. Im JSON `data.voices[]` den Eintrag mit `"id":"DE"` nehmen. Ergebnis:
   ```
   url  = https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642
   size = 8954023
   md5  = 2ee3cc51bef5352957fe4c30b39d5642
   ```
3. Installieren über den HA-Service:
   ```yaml
   service: dreame_vacuum.vacuum_install_voice_pack
   data:
     lang_id: "DE"          # NICHT "deyu" – das ist der alte Code
     url: "https://oss.iot.dreame.tech/dreame-product/resources/2ee3cc51bef5352957fe4c30b39d5642"
     md5: "2ee3cc51bef5352957fe4c30b39d5642"
     size: 8954023
   target:
     entity_id: vacuum.<dein_l40_ultra>
   ```
4. **Für andere Modelle identisch:** Modellcode im Manifest-Pfad austauschen. Das ist die
   generische, offizielle Methode (Lifehack aus der Community, siehe Quelle unten).
   Der Modellcode steht in der App unter Geräte-Info bzw. in `docs/supported_devices.md`.

**Fallstricke:**
* Nur `awsde0.fds.api.xiaomi.com` antwortet (EU-Node); andere Regionalhosts sind toter DNS.
* Die `resources/<md5>`-Objekte haben **keine Dateiendung** und liefern
  `Content-Type: application/octet-stream` – trotzdem gültige gzip-Archive (Magic `1f 8b 08`).
* `lang_id` ist der ISO-Code aus dem Manifest (`DE`), **nicht** `deyu`.
* Der CDN-Link funktioniert ohne Login; `oss.iot.dreame.tech/…/dreame.vacuum.r2492j/voices/…`
  liefert dagegen 403 (Bucket-Listing verboten) – nicht mit „nicht vorhanden“ verwechseln.

---

## 7. Quellen

* [Tasshack/dreame-vacuum – `docs/supported_devices.md` (Branch dev)](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/supported_devices.md) – Modellcode-Liste
* [Tasshack/dreame-vacuum – `custom_components/dreame_vacuum/services.yaml`](https://github.com/Tasshack/dreame-vacuum/blob/9a5d84dc/custom_components/dreame_vacuum/services.yaml) – `vacuum_install_voice_pack` mit p2009-`deyu`-Beispiel
* [Tasshack/dreame-vacuum – `docs/services.md`](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/services.md) – Service-Doku
* [sverdlyuk/glados_ukr](https://github.com/sverdlyuk/glados_ukr) – beschreibt den `soundpackage.json`-Lifehack („replace the model part … you can see all the voice packages available for your vacuum cleaner“)
* [rytilahti/python-miio Issue #1181](https://github.com/rytilahti/python-miio/issues/1181) – p2008-`deyu.tar.gz`-Beispiel, MIoT-Payload `siid/aiid` mit `piid 3..6`
* [Tasshack/dreame-vacuum Issue #893](https://github.com/Tasshack/dreame-vacuum/issues/893) – Nutzer mit `dreame.vacuum.r2492j` (L40 Ultra), Firmware 4.3.9_1659
* [Tasshack/dreame-vacuum Issue #982](https://github.com/Tasshack/dreame-vacuum/issues/982) – weiterer `r2492j`-Nachweis
* [builder.dontvacuum.me – Dreame L40 Ultra](https://builder.dontvacuum.me/_dreame_r2492.html) – `r2492` = L40 Ultra
* [HA-Community: Custom Component Dreame Vacuum, Seite 43](https://community.home-assistant.io/t/custom-component-dreame-vacuum/473026?page=43) – „tested with a L40 Ultra (dreame.vacuum.r2492j)“; Hinweis auf DreameHome-Login
* [Valetudo – `DreameL40UltraValetudoRobot`](https://github.com/Hypfer/Valetudo) – Auto-Detection-Liste `r2492a`, `r2492b`, `r2492j`
* [willemcvu/valetudo-dreame-voicepacks](https://github.com/willemcvu/c3po-valetudo-voicepack) – Pack-Format: tar.gz aus Ogg-Vorbis-Dateien, MD5-Prüfung durch den Roboter
* [Dreame Support – R2492C L40 Ultra User Manual](https://support.dreametech.com/hc/en-us/articles/10820384374159-R2492C-L40-Ultra-User-Manual-US)
