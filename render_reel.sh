#!/bin/bash
set -e

# 1. Configuration & Variables
VIDEO_ID=$(jq -r '.video_id' video_data.json)
TITLE=$(jq -r '.title' video_data.json)
ARTIST="phonkstax"
WORKDIR="/tmp/reels_phonkstax"
OUTPUT_FILE="output.mp4"
FONT="$WORKDIR/BebasNeue.ttf"

echo "🚀 Starting render process for: $TITLE ($VIDEO_ID)"

# 2. Prepare Assets
if [ -f "./assets/spotify.png" ]; then
    cp ./assets/spotify.png "$WORKDIR/spotify.png"
else
    echo "⚠️ Warning: spotify.png not found in ./assets/"
fi

# Download Font if missing
[ -f "$FONT" ] || curl -sL -o "$FONT" "https://github.com/googlefonts/BebasNeue/raw/main/fonts/ttf/BebasNeue-Regular.ttf"

# 3. Trim Audio
echo "✂️ Trimming audio to 20s segment..."
python3 -c "
import subprocess, json, os
probe = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '$WORKDIR/audio.mp3'], capture_output=True, text=True)
dur = float(json.loads(probe.stdout)['format']['duration'])
start_point = max(0, dur - 30)
subprocess.run(['ffmpeg', '-y', '-i', '$WORKDIR/audio.mp3', '-ss', str(start_point), '-t', '20', '-c:a', 'libmp3lame', '-b:a', '192k', '$WORKDIR/trimmed.mp3'])
os.replace('$WORKDIR/trimmed.mp3', '$WORKDIR/audio.mp3')
"

# 4. Calculate Dynamic Timings
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$WORKDIR/audio.mp3")
LOGO_START=$(echo "$DUR * 0.5" | bc)
FADE_OUT=$(echo "$DUR - 2" | bc)

echo "🎬 Rendering FFmpeg Composition..."

# 5. The Main Render
ffmpeg -y \
-loop 1 -i "$WORKDIR/audio.jpg" \
-i "$WORKDIR/audio.mp3" \
-loop 1 -i "$WORKDIR/spotify.png" \
-filter_complex "
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1500:1500,gblur=sigma=30,zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1400x1400:fps=30,rotate='0.04*sin(2*PI*t/5)':fillcolor=black@0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];
[cover]scale=900:900[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2-200[vbase];
[vbase]drawtext=fontfile=$FONT:text='$ARTIST':fontcolor=white:fontsize=78:x=(w-text_w)/2:y=1400+160*exp(-5*t)*abs(cos(18.85*t)):borderw=3:bordercolor=black@0.95:shadowcolor=black@0.7:shadowx=5:shadowy=5,
drawtext=fontfile=$FONT:text='$TITLE':fontcolor=0xE0E0E0:fontsize=54:x=(w-text_w)/2:y=1495+160*exp(-5*(t-0.25))*abs(cos(18.85*(t-0.25))):borderw=2:bordercolor=black@0.95:shadowcolor=black@0.7:shadowx=4:shadowy=4[vtext];
[2:v]scale=200:-1[logo];
[logo]fade=t=in:st=$LOGO_START:d=0.6:alpha=1,fade=t=out:st=$FADE_OUT:d=2:alpha=1[logofaded];
[vtext][logofaded]overlay=(W-w)/2:H-h-60:enable='between(t,$LOGO_START,$DUR)',format=yuv420p[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -t "$DUR" "$OUTPUT_FILE"

echo "✅ Render Complete: $OUTPUT_FILE"
