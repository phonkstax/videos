#!/bin/bash

# --- 1. CONFIG & ASSETS ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"
TEMP_LOOP="./temp_motion.mp4"

mkdir -p "$OUT_DIR"

# --- 2. READ METADATA & SANITIZE ---
if [ -f "$METADATA" ] && command -v jq >/dev/null 2>&1; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="reel_$(date +%s).mp4"
fi
FINAL_OUT="$OUT_DIR/$FILENAME"

# --- 3. CALCULATE TIMINGS ---
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio: $AUDIO"; exit 1; fi
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)

# --- 4. STEP ONE: FAST MOTION LOOP (10 Seconds) ---
echo "🚀 Phase 1: Generating High-Speed Motion Loop..."
ffmpeg -y -loop 1 -t 10 -i "$IMAGE" \
-filter_complex \
"scale=960:540:force_original_aspect_ratio=increase,crop=960:540,zoompan=z='1.03+0.01*sin(on*0.3)':d=300:s=960x540:fps=30,boxblur=10:5" \
-c:v libx264 -preset ultrafast -pix_fmt yuv420p "$TEMP_LOOP"

# --- 5. STEP TWO: FINAL ASSEMBLY ---
echo "🎬 Phase 2: Assembling Final Reel ($FILENAME)..."
ffmpeg -y \
-stream_loop -1 -t "$DURATION" -i "$TEMP_LOOP" \
-i "$AUDIO" \
-loop 1 -t "$DURATION" -i "$IMAGE" \
-loop 1 -t "$DURATION" -i "$LOGO" \
-filter_complex "
[0:v]scale=1920:1080,rotate='0.04*sin(2*PI*n/150)':fillcolor=black@0[bg];
[2:v]scale=600:600:force_original_aspect_ratio=increase,crop=600:600,eq=saturation=1.2:contrast=1.05[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[3:v]scale=150:-1,format=yuva420p,fade=t=in:st=5:d=1:alpha=1,fade=t=out:st=9:d=1:alpha=1[logo_f];
[vbase][logo_f]overlay=60:60:enable='between(t,5,10)'[v_fading];
[v_fading]fade=t=in:st=0:d=1,fade=t=out:st=$FADE_OUT_START:d=2[v];
[1:a]afade=t=in:st=0:d=1,afade=t=out:st=$FADE_OUT_START:d=2[a]
" \
-map "[v]" -map "[a]" \
-c:v libx264 -preset superfast -crf 23 -pix_fmt yuv420p \
-c:a aac -b:a 160k -shortest \
"$FINAL_OUT"

# --- 6. CLEANUP & GIT ---
rm "$TEMP_LOOP"
echo "✅ Process Complete: $FINAL_OUT"
git add "$FINAL_OUT"
