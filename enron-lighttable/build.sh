#!/bin/sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-/home/devuser/lemo-opuscar}
export LIB
cd "$LIB"
"$LIB/.venv/bin/python" core/tts/tts_zh.py "$HERE/lines.json" "$HERE/voices/"
node core/render/events.mjs "$HERE"
"$LIB/.venv/bin/python" "$HERE/mix.py"
node core/render/video.mjs "$HERE" --fps 24 --workers 2 --out "$HERE/out/video.mp4"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/enron-lighttable.mp4" 24 0
node core/render/readcheck.mjs "$HERE"
node core/render/still.mjs "$HERE" 4.0 16.0 28.5 38.0
cp "$HERE/stills/t_16.0.jpg" "$HERE/poster.jpg"
