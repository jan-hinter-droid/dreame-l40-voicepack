#!/bin/bash
# Installiert faster-whisper und transkribiert ein Sprachpaket.
# Laeuft auf dem Pi, damit die Audiodateien nicht durchs Netz muessen.
set -u

PACK_DIR="${1:-/home/pi/gordon-pack}"
OUT="${2:-/home/pi/gordon_transcript.csv}"
MODEL="${3:-tiny}"

echo "=== 1. freier Speicher ==="
df -h / | tail -1
free -m | head -2

echo
echo "=== 2. venv anlegen ==="
if [ ! -d /home/pi/whisper-venv ]; then
  python3 -m venv /home/pi/whisper-venv 2>&1 | tail -3
fi
/home/pi/whisper-venv/bin/pip install --quiet --upgrade pip 2>&1 | tail -2

echo "=== 3. faster-whisper installieren (das dauert) ==="
/home/pi/whisper-venv/bin/pip install --quiet faster-whisper 2>&1 | tail -5
echo "installiert:"
/home/pi/whisper-venv/bin/python -c "import faster_whisper; print('  faster-whisper', faster_whisper.__version__)" 2>&1

echo
echo "=== 4. Pack entpacken ==="
if [ ! -d "$PACK_DIR" ]; then
  mkdir -p "$PACK_DIR"
  # Paket liegt im Repo-Checkout des Nutzers - hier wird nur entpackt, was da ist
  echo "  $PACK_DIR fehlt - bitte vorher entpacken"
  exit 1
fi
ls "$PACK_DIR"/*.ogg 2>/dev/null | wc -l | sed 's/^/  OGG-Dateien: /'

echo
echo "=== 5. Transkription ($MODEL) ==="
/home/pi/whisper-venv/bin/python - "$PACK_DIR" "$OUT" "$MODEL" <<'PYEOF'
import csv, os, sys, time
from faster_whisper import WhisperModel

pack_dir, out_path, model_size = sys.argv[1], sys.argv[2], sys.argv[3]
files = sorted(
    (f for f in os.listdir(pack_dir) if f.endswith(".ogg") and f[:-4].isdigit()),
    key=lambda f: int(f[:-4]),
)
print(f"  {len(files)} Dateien zu transkribieren", flush=True)

model = WhisperModel(model_size, device="cpu", compute_type="int8")

rows = []
start = time.time()
for i, name in enumerate(files, 1):
    path = os.path.join(pack_dir, name)
    try:
        segments, info = model.transcribe(path, language="en", beam_size=1,
                                          vad_filter=True, condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception as ex:
        text = f"<FEHLER: {ex}>"
    rows.append((name[:-4], round(info.duration, 2) if 'info' in dir() else "", text))
    if i % 25 == 0 or i == len(files):
        el = time.time() - start
        print(f"  {i}/{len(files)}  ({el:.0f}s)", flush=True)

with open(out_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["id", "duration", "text"])
    w.writerows(rows)

print(f"[+] {out_path} geschrieben ({len(rows)} Zeilen)")
PYEOF

echo
echo "=== 6. Fertig. Erste Zeilen: ==="
head -20 "$OUT" 2>/dev/null
