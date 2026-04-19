#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"
rm -rf "$OUT_DIR"/*
git add -A

# --- METADATA ---
if [ -f "$METADATA" ]; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="output.mp4"
fi

FINAL_OUT="$OUT_DIR/$FILENAME"

# --- CHECK FILES ---
[ ! -f "$AUDIO" ] && echo "❌ Missing audio" && exit 1
[ ! -f "$IMAGE" ] && echo "❌ Missing image" && exit 1
[ ! -f "$LOGO" ] && echo "❌ Missing logo" && exit 1

# --- DURATION ---
DURATION=$(ffprobe -v error -show_entries format=duration \
-of default=noprint_wrappers=1:nokey=1 "$AUDIO")

VIDEO_FADE_OUT=$(echo "$DURATION - 1" | bc -l)
AUDIO_FADE_OUT=$(echo "$DURATION - 1.5" | bc -l)

echo "🎬 Rendering: $FILENAME"
echo "⏱️ Duration: $DURATION"

# --- RENDER ---
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,
crop=min(iw\,ih):min(iw\,ih),
scale=800:800,
fade=t=in:st=0:d=1,
fade=t=out:st=$VIDEO_FADE_OUT:d=1[cover];

[0:v]format=yuv420p,
crop=min(iw\,ih):min(iw\,ih),
scale=1920:1080:force_original_aspect_ratio=increase,
gblur=sigma=25,
scale=2000:1125,
crop=1920:1080,
rotate='0.03*sin(2*PI*t/6)':fillcolor=black@0,
fade=t=in:st=0:d=1,
fade=t=out:st=$VIDEO_FADE_OUT:d=1[bg];

[bg][cover]overlay=(W-w)/2:(H-h)/2[vbase];

[2:v]scale=100:-1,
fade=t=in:st=5:d=0.6:alpha=1,
fade=t=out:st=10:d=0.6:alpha=1[logo];

[vbase][logo]overlay=20:20:enable='between(t,5,10)'[v];

[1:a]afade=t=in:st=0:d=1,
afade=t=out:st=$AUDIO_FADE_OUT:d=1[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 20 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

# --- RESULT ---
if [ $? -eq 0 ]; then
  echo "✅ Success: $FINAL_OUT"
else
  echo "❌ FFmpeg failed"
  exit 1
fi
