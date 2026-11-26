#!/bin/sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-/home/devuser/lemo-opuscar}
export LIB
cd "$LIB"
"$LIB/.venv/bin/python" core/tts/tts_zh.py "$HERE/lines.json" "$HERE/voices/"
node core/render/events.mjs "$HERE"
"$LIB/.venv/bin/python" "$HERE/mix.py"
node core/render/video.mjs "$HERE" --fps 24 --workers 3 --out "$HERE/out/video.mp4"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/enron-investigation.mp4" 24 0
node core/render/readcheck.mjs "$HERE"
node core/render/still.mjs "$HERE" 2.0 6.0 10.5 16.0 23.0 29.5 35.0 42.0
cp "$HERE/stills/t_42.0.jpg" "$HERE/poster.jpg"
