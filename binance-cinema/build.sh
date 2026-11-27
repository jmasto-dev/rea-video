#!/usr/bin/env bash
set -euo pipefail

PROJ="/home/devuser/projects/rea-video/binance-cinema"
LIB="/home/devuser/lemo-opuscar"

cd "$LIB"
"$LIB/.venv/bin/python" "$PROJ/mix.py"
mkdir -p "$PROJ/out"
LEMO_ANGLE=swiftshader node core/render/video.mjs "$PROJ" --fps 24 --workers 2 --out "$PROJ/out/video.mp4"
sh core/render/mux.sh "$PROJ/out/video.mp4" "$PROJ/mix.wav" "$PROJ/binance-cinema-arc1.mp4" 24 0
echo "=== DONE: $PROJ/binance-cinema-arc1.mp4 ==="
