#!/bin/bash

# --- 1. SETUP FILENAMES ---
OUT_FILE=$(ls ./output/*.mp4 2>/dev/null | head -n 1)

if [ ! -f "$OUT_FILE" ]; then
    echo "❌ Error: Final video file was not created."
    exit 1
fi

URL_FILENAME=$(basename "$OUT_FILE")
SAFE_NAME="${URL_FILENAME%.*}"

# --- 2. GITHUB UPLOAD (FORCE PUSH) ---
echo "-----------------------------------------------"
echo "📤 UPLOADING TO GITHUB REPO..."

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🌿 Detected branch: $CURRENT_BRANCH"

# Clean output except the current reel
find ./output -type f ! -name "$URL_FILENAME" -delete

# Force add in case they are in gitignore
git add -f "$OUT_FILE"
git add -f metadata.json

RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${URL_FILENAME}"

echo "⚙️ Force pushing to $CURRENT_BRANCH..."
# FIX: Added quotes and ensured the [skip ci] is inside the commit message string
git commit -m "Refresh Reel: $SAFE_NAME [skip ci]" || git commit --amend --no-edit
git push origin "$CURRENT_BRANCH" --force

# --- 3. WEBHOOK CALL ---
if [ -n "$WEBHOOK_URL" ]; then
    echo "⏳ Waiting 5 seconds for GitHub sync..."
    sleep 5

    echo "📡 Sending Webhook: $URL_FILENAME"
    
    # Generate JSON payload
    PAYLOAD=$(jq -n --arg url "$RAW_URL" --arg name "$URL_FILENAME" \
        '{fileUrl: $url, fileName: $name}')

    RESPONSE=$(curl -L -s -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$WEBHOOK_URL")
    
    echo "📩 Server Response: $RESPONSE"
    echo -e "\n✨ Process Complete."
fi
echo "-----------------------------------------------"
