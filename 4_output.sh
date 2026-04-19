#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"

# --- CLEAN OUTPUT FOLDER ---
rm -rf "$OUT_DIR"/*
git add -A

# 1. READ METADATA
if [ -f "$METADATA" ]; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="output.mp4"
fi

FINAL_OUT="$OUT_DIR/$FILENAME"

# 2. VERIFY ASSETS
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio"; exit 1; fi

# 3. TIMING CALCULATIONS
# Logo: starts at 5s, stays for 5s (ends at 10s)
LOGO_START=5
LOGO_END=10
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT=$(echo "$DURATION - 2" | bc -l)

echo "🎬 Rendering Landscape with Shake: $FILENAME"

# 4. RENDER ENGINE
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=800:800,eq=saturation=1.2:contrast=1.05[fg];
[0:v]format=yuv420p,scale=1920:1080:force_original_aspect_ratio=increase,
crop=1920:1080,gblur=sigma=15,
zoompan=z='1.05+0.03*sin(on*0.5)':d=1:s=1920x1080:fps=30,
rotate='0.05*sin(2*PI*t/0.5)':fillcolor=black@0[bg_shaky];
[bg_shaky][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[2:v]scale=100:-1[logo_small];
[logo_small]fade=t=in:st=$LOGO_START:d=0.5:alpha=1,
fade=t=out:st=$LOGO_END:d=0.5:alpha=1[logofaded];
[vbase][logofaded]overlay=40:40:enable='between(t,$LOGO_START,$LOGO_END+1)',format=yuv420p[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 22 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

echo "✅ Success: $FINAL_OUT"
