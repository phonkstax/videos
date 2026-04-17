#!/bin/bash
mkdir -p ./assets/audio ./assets/image

# Find the file (supports webm or mp4)
INPUT_FILE=$(ls ./assets/download/* | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "❌ No file found in assets/download"
    exit 1
fi

echo "🎬 Processing: $INPUT_FILE"

# 1. Extract Audio (MP3 192k)
ffmpeg -y -i "$INPUT_FILE" -vn -ar 44100 -ac 2 -b:a 192k ./assets/audio/audio.mp3

# 2. Extract First Frame (High Quality JPG)
ffmpeg -y -i "$INPUT_FILE" -frames:v 1 -q:v 2 ./assets/image/image.jpg

echo "✅ Assets Split Successfully!"
