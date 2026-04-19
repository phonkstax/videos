#!/bin/bash

# --- CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"

# 1. READ METADATA
if [ -f "$METADATA" ]; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}_horizontal.mp4"
else
    FILENAME="output_horizontal.mp4"
fi

FINAL_OUT="$OUT_DIR/$FILENAME"

# 2. VERIFY ASSETS
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio"; exit 1; fi

# 3. TIMINGS
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT=$(echo "$DURATION - 2" | bc -l)

# Logo logic: Start at 5s, Fade in 1s, Stay 3s, Fade out 1s (Total 5s visibility window)
LOGO_START=5
LOGO_END=10

echo "🎬 Rendering Horizontal: $FILENAME"

# 4. RENDER ENGINE (1920x1080)
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=20,
zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1920x1080:fps=30[bg];
[cover]scale=600:600[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[2:v]scale=150:-1[logo_scaled];
[logo_scaled]fade=t=in:st=$LOGO_START:d=1:alpha=1,
            fade=t=out:st=$(($LOGO_START+4)):d=1:alpha=1[logofaded];
[vbase][logofaded]overlay=40:40:enable='between(t,$LOGO_START,$LOGO_END)'[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 18 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

# 5. SECRET CHECK
if [ -n "$SECRET_VAR" ]; then
    echo "✅ Secret found, processing final steps..."
else
    echo "ℹ️ No secret variable found."
fi

echo "✅ Success: $FINAL_OUT"
