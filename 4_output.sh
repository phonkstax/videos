#!/bin/bash

# --- 1. CONFIG & ASSETS ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"

mkdir -p "$OUT_DIR"

# 2. READ METADATA FOR FILENAME
if [ -f "$METADATA" ]; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="reel_$(date +%s).mp4"
fi

FINAL_OUT="$OUT_DIR/$FILENAME"

# 3. VERIFY ASSETS
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio"; exit 1; fi

# 4. CALCULATE TIMINGS
# Get duration in seconds
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
# Global fade out starts 2 seconds before the end
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)

# Logo logic: Start at 5s, visible for 5s total
LOGO_START=5
LOGO_END=10

echo "🎬 Rendering Horizontal (16:9): $FILENAME"
echo "⏱️ Duration: $DURATION seconds"

# 5. RENDER ENGINE (FFMPEG)
# Note: -loop 1 on the image ensures filters don't 'freeze' early
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=20,
zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1920x1080:fps=30,
rotate='0.04*sin(2*PI*n/150)':fillcolor=black@0[bg];
[cover]scale=600:600[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[2:v]scale=150:-1[logo_scaled];
[logo_scaled]fade=t=in:st=$LOGO_START:d=1:alpha=1,
            fade=t=out:st=9:d=1:alpha=1[logofaded];
[vbase][logofaded]overlay=60:60:enable='between(t,$LOGO_START,$LOGO_END)'[v_temp];
[v_temp]fade=t=in:st=0:d=1,fade=t=out:st=$FADE_OUT_START:d=2[v];
[1:a]afade=t=in:st=0:d=1,afade=t=out:st=$FADE_OUT_START:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

# 6. GITHUB UPLOAD & CLEANUP
echo "-----------------------------------------------"
echo "📤 UPLOADING TO GITHUB REPO..."

# Setup bot identity
git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Clean output folder so only the NEWEST video exists (prevents repo bloat)
find ./output -type f ! -name "$FILENAME" -delete

# Force add files
git add -f "$FINAL_OUT"
git add -f "$METADATA"

# Construct the Raw URL for the Webhook
# Format: https://raw.githubusercontent.com/USER/REPO/BRANCH/PATH
RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${FILENAME}"

SAFE_NAME="${FILENAME%.*}"
git commit -m "Refresh Reel: $SAFE_NAME [skip ci]" || echo "No changes to commit"
git push origin "$CURRENT_BRANCH" --force

# 7. WEBHOOK NOTIFICATION
if [ -n "$WEBHOOK_URL" ]; then
    echo "⏳ Syncing with GitHub..."
    sleep 5
    
    echo "📡 Sending Webhook: $FILENAME"
    PAYLOAD=$(jq -n --arg url "$RAW_URL" --arg name "$FILENAME" \
        '{fileUrl: $url, fileName: $name}')

    RESPONSE=$(curl -L -s -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$WEBHOOK_URL")
    echo "📩 Server Response: $RESPONSE"
fi

echo "✨ Process Complete: $FILENAME"
echo "-----------------------------------------------"
