#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"

rm -rf ./output/*
git add -A


# 1. READ METADATA
# We use jq to extract the artist and track, then replace spaces with underscores for a clean filename
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

# 3. AUTO-CALCULATE TIMINGS
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
LOGO_START=$(echo "$DURATION / 2" | bc -l)
FADE_OUT=$(echo "$DURATION - 2" | bc -l)

echo "🎬 Rendering: $FILENAME"
echo "⏱️ Duration: $DURATION | Logo at: $LOGO_START"

# 4. RENDER ENGINE
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,
crop=min(iw\,ih):min(iw\,ih),
scale=1920:1080:force_original_aspect_ratio=increase,
crop=1920:1080,
eq=saturation=1.2:contrast=1.05,
fade=t=in:st=0:d=1,
fade=t=out:st=($DURATION-1):d=1[base];

[2:v]scale=200:-1,
fade=t=in:st=5:d=1:alpha=1,
fade=t=out:st=10:d=1:alpha=1[logo];

[base][logo]overlay=20:20:enable='between(t,5,10)'[v];

[1:a]afade=t=in:st=0:d=1.5,
afade=t=out:st=($DURATION-1.5):d=1.5[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 22 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"
echo "✅ Success: $FINAL_OUT"

# ... (FFmpeg command finishes above) ...



# Check if the secret variable is actually set
