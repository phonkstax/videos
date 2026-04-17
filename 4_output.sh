#!/bin/bash

# --- CONFIG ---
# We now use the trimmed audio from Step 3.5
AUDIO="./assets/trim_audio/trim_audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
OUTPUT_DIR="./output"
FINAL_OUT="$OUTPUT_DIR/output.mp4"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# 1. Verify Assets
if [ ! -f "$AUDIO" ]; then echo "❌ Missing trimmed audio"; exit 1; fi
if [ ! -f "$IMAGE" ]; then echo "❌ Missing image"; exit 1; fi
if [ ! -f "$LOGO" ]; then echo "❌ Missing spotify.png"; exit 1; fi

# 2. Timing Calculations (Always based on 20s now)
CLIP_LEN=20
LOGO_START=10
FADE_OUT=18

echo "🎬 Rendering 20s Phonk Reel using pre-trimmed audio..."

# 3. FFmpeg Engine
# Optimization: Background is scaled down to 300px before blur for 5x speed boost
ffmpeg -y \
-loop 1 -i "$IMAGE" \
-i "$AUDIO" \
-loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=300:300,gblur=sigma=15,
scale=1080:1920:force_original_aspect_ratio=increase,
zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1080x1920:fps=30,
rotate='0.04*sin(2*PI*t/5)':fillcolor=black@0,
crop=1080:1920[bg];
[cover]scale=900:900[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2-200[vbase];
[2:v]scale=200:-1[logo];
[logo]fade=t=in:st=$LOGO_START:d=0.6:alpha=1,
fade=t=out:st=$FADE_OUT:d=2:alpha=1[logofaded];
[vbase][logofaded]overlay=(W-w)/2:H-h-60:enable='between(t,$LOGO_START,$CLIP_LEN)',format=yuv420p[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset ultrafast -crf 22 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
-shortest \
"$FINAL_OUT"

echo "✅ Rendering Complete: $FINAL_OUT"
