#!/bin/bash

# Define paths
DOWNLOAD_DIR="./assets/download"
AUDIO_DIR="./assets/audio"
IMAGE_DIR="./assets/image"

# 1. CLEANUP OLD FILES (But keep the folders)
echo "🧹 Cleaning up old assets..."
rm -f "$DOWNLOAD_DIR"/*
rm -f "$AUDIO_DIR"/*
rm -f "$IMAGE_DIR"/*

# Ensure directories exist (in case rm -rf was used instead of rm -f)
mkdir -p "$AUDIO_DIR" "$IMAGE_DIR" "$DOWNLOAD_DIR"

# 2. FIND NEW INPUT
INPUT_FILE=$(ls "$DOWNLOAD_DIR"/* 2>/dev/null | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "❌ No new file found in $DOWNLOAD_DIR"
    exit 1
fi

echo "🎬 Processing: $INPUT_FILE"

# 3. SPLIT MEDIA
# Extract Audio (MP3 192k)
ffmpeg -y -i "$INPUT_FILE" -vn -ar 44100 -ac 2 -b:a 192k "$AUDIO_DIR/audio.mp3"

# Extract First Frame (High Quality JPG)
ffmpeg -y -i "$INPUT_FILE" -frames:v 1 -q:v 2 "$IMAGE_DIR/image.jpg"

echo "✅ Assets Split Successfully!"
