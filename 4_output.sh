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
if [ ! -f "$AUDIO" ] || [ ! -f "$IMAGE" ]; then echo "❌ Missing assets"; exit 1; fi

# 3. TIMING CALCULATIONS
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT=$(echo "$DURATION - 2" | bc -l)
LOGO_START=5
LOGO_END=10

echo "🎬 Rendering Stable Square-over-Blur: $FILENAME"

# 4. RENDER ENGINE
ffmpeg -y \
-loop 1 -t "$DURATION" -i "$IMAGE" \
-i "$AUDIO" \
-loop 1 -t "$DURATION" -i "$LOGO" \
-filter_complex "
[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=20:10[bg];
[0:v]scale=800:800:force_original_aspect_ratio=increase,crop=800:800,format=yuv420p[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[2:v]scale=120:-1[logo_small];
[logo_small]fade=t=in:st=$LOGO_START:d=0.5:alpha=1,
            fade=t=out:st=$LOGO_END:d=0.5:alpha=1[logofaded];
[vbase][logofaded]overlay=60:60:enable='between(t,$LOGO_START,$LOGO_END+1)'[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
-c:a aac -b:a 192k \
-shortest \
"$FINAL_OUT"

echo "✅ Success: $FINAL_OUT"
