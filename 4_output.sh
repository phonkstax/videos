#!/bin/bash

# --- 1. CONFIG ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
OUT_DIR="./output"
mkdir -p "$OUT_DIR"

# --- 2. CALCULATE DURATION ---
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)

# --- 3. STEP ONE: CREATE A 10s MOTION LOOP ---
# This creates the movement once so FFmpeg doesn't have to calculate it for 3 minutes straight.
echo "🌀 Generating Motion Loop..."
ffmpeg -y -loop 1 -t 10 -i "$IMAGE" \
-filter_complex "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='1.03+0.01*sin(on*0.3)':d=300:s=1920x1080:fps=30" \
-c:v libx264 -pix_fmt yuv420p -preset superfast ./temp_motion.mp4

# --- 4. STEP TWO: FINAL ASSEMBLY ---
# We use -stream_loop -1 to repeat the 10s clip for the full duration of the audio.
echo "🎬 Assembling Final Video..."
ffmpeg -y \
-stream_loop -1 -t "$DURATION" -i ./temp_motion.mp4 \
-i "$AUDIO" \
-loop 1 -t "$DURATION" -i "$IMAGE" \
-loop 1 -t "$DURATION" -i "$LOGO" \
-filter_complex "
[0:v]gblur=sigma=20,rotate='0.04*sin(2*PI*n/150)':fillcolor=black@0[bg];
[2:v]scale=600:600:force_original_aspect_ratio=increase,crop=600:600,eq=saturation=1.2:contrast=1.05[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[3:v]scale=150:-1,format=yuva420p,fade=t=in:st=5:d=1:alpha=1,fade=t=out:st=9:d=1:alpha=1[logo_f];
[vbase][logo_f]overlay=60:60:enable='between(t,5,10)'[v_fading];
[v_fading]fade=t=in:st=0:d=1,fade=t=out:st=$FADE_OUT_START:d=2[v];
[1:a]afade=t=in:st=0:d=1,afade=t=out:st=$FADE_OUT_START:d=2[a]
" \
-map "[v]" -map "[a]" \
-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p \
-c:a aac -b:a 192k -shortest \
"$OUT_DIR/final_reel.mp4"

# Clean up
rm ./temp_motion.mp4
echo "✅ Done!"
