#!/bin/bash

# --- 1. CONFIG & ASSETS ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# --- 2. CLEAN & SYNC ---
# Clean local output files
rm -f "$OUT_DIR"/*

# Note: 'git add -A' here tracks the deletions. 
# If you run this before generating the new file, 
# the repo will show the folder as empty in the next commit.
git add "$OUT_DIR"

# --- 3. READ METADATA ---
if [ -f "$METADATA" ] && command -v jq >/dev/null 2>&1; then
    # Sanitize names: remove special characters, replace spaces with underscores
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="reel_$(date +%s).mp4"
fi

FINAL_OUT="$OUT_DIR/$FILENAME"

# --- 4. VERIFY ASSETS ---
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio: $AUDIO"; exit 1; fi
if [ ! -f "$IMAGE" ]; then echo "❌ Missing image: $IMAGE"; exit 1; fi

# --- 5. CALCULATE TIMINGS ---
# Use 'bc' to handle decimals for the fade start
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)
TOTAL_FRAMES=$(echo "$DURATION * 30" | bc | cut -d. -f1)

echo "🎬 Rendering: $FILENAME"
echo "⏱️ Duration: ${DURATION}s | Frames: $TOTAL_FRAMES"

# --- 6. RENDER ENGINE ---
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=20,
zoompan=z='1.03+0.01*sin(on*0.3)':d=$TOTAL_FRAMES:s=1920x1080:fps=30,
rotate='0.04*sin(2*PI*n/150)':fillcolor=black@0[bg];
[cover]scale=600:600[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[2:v]scale=150:-1[logo_scaled];
[logo_scaled]fade=t=in:st=5:d=1:alpha=1,fade=t=out:st=9:d=1:alpha=1[logofaded];
[vbase][logofaded]overlay=60:60:enable='between(t,5,10)'[v_temp];
[v_temp]fade=t=in:st=0:d=1,fade=t=out:st=$FADE_OUT_START:d=2[v];
[1:a]afade=t=in:st=0:d=1,afade=t=out:st=$FADE_OUT_START:d=2[a]
" \
-map "[v]" -map "[a]" \
-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

echo "✅ Done: $FINAL_OUT"
