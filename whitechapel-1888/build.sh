#!/usr/bin/env bash
set -euo pipefail

PROJ="/home/devuser/projects/rea-video/whitechapel-1888"
LIB="/home/devuser/lemo-opuscar"

cd "$LIB"

echo "=== 1. Generating US English TTS (en-US-AndrewNeural) ==="
"$LIB/.venv/bin/python" core/tts/tts_zh.py "$PROJ/lines.json" "$PROJ/voices/"

echo "=== 2. Exporting animation events ==="
node core/render/events.mjs "$PROJ"

echo "=== 3. Mixing audio (score + foley + voice + 2s silence) ==="
"$LIB/.venv/bin/python" "$PROJ/mix.py"

echo "=== 4. Rendering 24fps WebGL2 woodcut video (SwiftShader) ==="
mkdir -p "$PROJ/out"
LEMO_ANGLE=swiftshader node core/render/video.mjs "$PROJ" --fps 24 --workers 2 --out "$PROJ/out/video.mp4"

echo "=== 5. Muxing final MP4 (24fps, grain=0) ==="
sh core/render/mux.sh "$PROJ/out/video.mp4" "$PROJ/mix.wav" "$PROJ/whitechapel-1888.mp4" 24 0

echo "=== 6. Running readcheck ==="
node core/render/readcheck.mjs "$PROJ"

echo "=== 7. Saving poster ==="
if [ -f "$PROJ/stills/t_4.5.jpg" ]; then
  cp "$PROJ/stills/t_4.5.jpg" "$PROJ/poster.jpg"
fi

echo "=== DONE: $PROJ/whitechapel-1888.mp4 ==="
