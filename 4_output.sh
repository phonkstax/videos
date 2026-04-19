#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"
mkdir -p "$OUT_DIR"

# 1. GET DURATION & METADATA
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FILENAME="output.mp4" # Simplify for example

# 2. THE ALTERNATIVE RENDER (SPEED FOCUSED)
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
/* STEP 1: Process Background once with fast blur */
[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=10:1[bg_static];
/* STEP 2: Apply motion to the pre-blurred background */
[bg_static]zoompan=z='1.03+0.01*sin(on*0.1)':d=1:s=1920x1080:fps=30[bg_moving];
/* STEP 3: Process Foreground Cover */
[0:v]scale=800:800,format=yuv420p[fg];
/* STEP 4: Combine */
[bg_moving][fg]overlay=(W-w)/2:(H-h)/2[vbase];
/* STEP 5: Small Logo Overlay */
[2:v]scale=80:-1[logo_small];
[logo_small]fade=t=in:st=5:d=0.5:alpha=1,fade=t=out:st=10:d=0.5:alpha=1[logofaded];
[vbase][logofaded]overlay=30:30:enable='between(t,5,10)'[v]
" \
-map "[v]" -map "1:a" \
-c:v libx264 -preset ultrafast -crf 26 -threads 0 -pix_fmt yuv420p \
-c:a copy \
"$OUT_DIR/$FILENAME"
