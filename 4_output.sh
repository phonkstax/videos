#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
SCRATCHES="./assets/scratches/1.mp4"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"

# 1. READ METADATA
FILENAME="output.mp4"
if [ -f "$METADATA" ]; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
fi
FINAL_OUT="$OUT_DIR/$FILENAME"

# 2. TIMING
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
# Calculate fade out timing
VIDEO_FADE_ST=$(echo "$DURATION - 2" | bc -l)
AUDIO_FADE_ST=$(echo "$DURATION - 2" | bc -l)

echo "⚡ Rendering with Global Fades & Scratches: $FILENAME"

# 3. RENDER ENGINE
ffmpeg -y -hide_banner \
-loop 1 -t "$DURATION" -i "$IMAGE" \
-i "$AUDIO" \
-loop 1 -t "$DURATION" -i "$LOGO" \
-stream_loop -1 -i "$SCRATCHES" \
-filter_complex "
[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=15[bg];
[0:v]scale=800:800:force_original_aspect_ratio=increase,crop=800:800[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[3:v]scale=1920:1080,format=yuv420p,colorchannelmixer=aa=0.3[scr];
[vbase][scr]overlay=0:0:shortest=1[v_scratched];
[2:v]scale=120:-1[logo_s];
[logo_s]fade=t=in:st=5:d=0.5:alpha=1,fade=t=out:st=10:d=0.5:alpha=1[logo_f];
[v_scratched][logo_f]overlay=60:60:enable='between(t,5,11)'[v_with_logo];
[v_with_logo]fade=t=in:st=0:d=1.5,fade=t=out:st=$VIDEO_FADE_ST:d=1.5[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$AUDIO_FADE_ST:d=2[a]
" \
-map "[v]" -map "[a]" \
-c:v libx264 -preset ultrafast -crf 26 -threads 0 \
-c:a aac -b:a 128k \
-t "$DURATION" \
"$FINAL_OUT"

echo "✅ Video Complete: $FINAL_OUT"
