#!/bin/bash
# Startet die Transkription abgekoppelt, damit sie einen SSH-Abbruch ueberlebt.
set -u

echo "=== Laufende Transkription beenden (falls vorhanden) ==="
sudo -n pkill -f transcribe_worker 2>/dev/null || true
sleep 1

echo "=== Worker-Skript schreiben ==="
cat > /home/pi/transcribe_worker.py <<'PYEOF'
import csv
import os
import sys
import time

from faster_whisper import WhisperModel

pack_dir = "/home/pi/gordon-pack"
out_path = "/home/pi/gordon_transcript.csv"
model_size = sys.argv[1] if len(sys.argv) > 1 else "tiny"

files = sorted(
    (f for f in os.listdir(pack_dir) if f.endswith(".ogg") and f[:-4].isdigit()),
    key=lambda f: int(f[:-4]),
)
print(f"START {len(files)} Dateien, Modell={model_size}", flush=True)

model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("MODELL GELADEN", flush=True)

rows = []
start = time.time()
for i, name in enumerate(files, 1):
    path = os.path.join(pack_dir, name)
    try:
        segments, info = model.transcribe(
            path, language="en", beam_size=1, vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        dur = round(info.duration, 2)
    except Exception as ex:
        text, dur = f"<FEHLER: {ex}>", 0
    rows.append((int(name[:-4]), dur, text))
    if i % 25 == 0 or i == len(files):
        print(f"FORTSCHRITT {i}/{len(files)} ({time.time()-start:.0f}s)", flush=True)

with open(out_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["id", "duration", "text"])
    w.writerows(rows)

print(f"FERTIG {out_path} ({len(rows)} Zeilen)", flush=True)
PYEOF

echo "=== venv + faster-whisper (kann dauern) ==="
[ -d /home/pi/whisper-venv ] || python3 -m venv /home/pi/whisper-venv
/home/pi/whisper-venv/bin/pip install --quiet --upgrade pip 2>&1 | tail -1
/home/pi/whisper-venv/bin/pip install --quiet faster-whisper 2>&1 | tail -3
/home/pi/whisper-venv/bin/python -c "import faster_whisper; print('faster-whisper', faster_whisper.__version__)" 2>&1

echo
echo "=== Transkription abgekoppelt starten ==="
: > /home/pi/transcribe.log
setsid nohup /home/pi/whisper-venv/bin/python -u /home/pi/transcribe_worker.py tiny \
  >> /home/pi/transcribe.log 2>&1 < /dev/null &
sleep 12
echo "--- Log nach 12s ---"
cat /home/pi/transcribe.log
echo
echo "--- Prozess laeuft? ---"
pgrep -f transcribe_worker | head -3
