#!/usr/bin/env bash
set -euo pipefail

DIR="/home/devuser/projects/rea-video/binance-cinema/act1"
PHOTOS="/home/devuser/projects/rea-video/binance-cinema/assets/photos"
OUT="$DIR/binance-act1-studio.mp4"
TMP="$DIR/clips"
mkdir -p "$TMP"

# Helper: render one 1920x804 -> 1920x1080 (2.39:1) 24fps clip with smooth motion + 35mm grain
make_clip() {
  local idx="$1"
  local src="$2"
  local dur="$3"
  local zexpr="$4"
  local xexpr="$5"
  local yexpr="$6"
  local frames
  frames=$(python3 -c "print(int(round($dur * 24)))")
  ffmpeg -y -loop 1 -i "$src" -vf "scale=2560:1072:force_original_aspect_ratio=increase,crop=2560:1072,zoompan=z='${zexpr}':x='${xexpr}':y='${yexpr}':d=${frames}:s=1920x804:fps=24,pad=1920:1080:0:138:black,noise=alls=6:allf=t+u,vignette=PI/5" -t "$dur" -c:v libx264 -pix_fmt yuv420p -r 24 "$TMP/b${idx}.mp4" 2>/dev/null
}

# Beat 1 (0.00-4.20 = 4.20s): Slow push-in toward monolith
make_clip "01" "$DIR/blender/beat01_monolith.png" "4.20" "1.0+0.08*on/101" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 2 (4.20-8.52 = 4.32s): Crane pull-back over 10 nodes
make_clip "02" "$DIR/blender/beat02_overhead_nodes.png" "4.32" "1.10-0.10*on/104" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 3 (8.52-12.00 = 3.48s): Low-angle subtle push onto $6.3 BILLION
make_clip "03" "$DIR/blender/beat03_void_ledger.png" "3.48" "1.0+0.06*on/84" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 4 (12.00-15.80 = 3.80s): Dark bedroom phone glow
make_clip "04" "$PHOTOS/bed_phone.jpg" "3.80" "1.0+0.05*on/91" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 5 (15.80-19.04 = 3.24s): Macro thumb on grey Withdraw
make_clip "05" "$PHOTOS/phone_thumb.jpg" "3.24" "1.08+0.04*on/78" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 6 (19.04-22.08 = 3.04s): CRT telemetry logs
make_clip "06" "$DIR/lemo/beat06_crt.png" "3.04" "1.0+0.04*on/73" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 7 (22.08-26.32 = 4.24s): Intact padlock pedestal subtle drift
make_clip "07" "$DIR/blender/beat07_padlock.png" "4.24" "1.0+0.06*on/102" "iw/2-(iw/zoom/2)-20+40*on/102" "ih/2-(ih/zoom/2)"

# Beat 8 (26.32-29.60 = 3.28s): Mechanical APPROVED stamp
make_clip "08" "$DIR/blender/beat08_stamp.png" "3.28" "1.06-0.06*on/79" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 9 (29.60-33.00 = 3.40s): Blueprint signing pipeline
make_clip "09" "$DIR/lemo/beat09_blueprint.png" "3.40" "1.0+0.05*on/82" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 10 (33.00-37.28 = 4.28s): Dark server corridor dolly forward
make_clip "10" "$DIR/blender/beat10_corridor.png" "4.28" "1.0+0.10*on/103" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)"

# Beat 11 (37.28-41.08 = 3.80s): Woodcut fortress gate & forged keycard
make_clip "11" "$DIR/lemo/beat11_woodcut.png" "3.80" "1.0+0.05*on/91" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)+18*on/91"

# Concatenate all 11 clips
printf "" > "$TMP/concat.txt"
for i in 01 02 03 04 05 06 07 08 09 10 11; do
  echo "file '$TMP/b${i}.mp4'" >> "$TMP/concat.txt"
done

ffmpeg -y -f concat -safe 0 -i "$TMP/concat.txt" -i "$DIR/act1_mix.wav" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "$OUT" 2>/dev/null

ls -lh "$OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT"
