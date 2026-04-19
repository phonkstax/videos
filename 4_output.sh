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
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)

# CRITICAL FIX for 1:50 freeze: Calculate total frames needed
# zoompan defaults to 3300 frames (~1:50 @ 30fps). We must override 'd'
TOTAL_FRAMES=$(echo "$DURATION * 30" | bc | cut -d. -f1)

echo "🎬 Rendering Horizontal (16:9): $FILENAME"
echo "⏱️ Total Frames for Movement: $TOTAL_FRAMES"

# 5. RENDER ENGINE
# Added 'd=$TOTAL_FRAMES' to zoompan to prevent the 1:50 freeze
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
