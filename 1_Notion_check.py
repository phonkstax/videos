import os
import requests
import json
import sys
import re

# Constants
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
NOTION_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

def clean_name(text):
    """Helper to clean strings for filenames."""
    text = re.sub(r'\s*[-–—]\s*Topic\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Release\s*[-–—]?\s*', '', text, flags=re.IGNORECASE)
    return text.strip()

def get_yt_token():
    url = "https://oauth2.googleapis.com/token"
    try:
        oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
        payload = {
            "client_id": os.environ['YTM_CLIENT_ID'],
            "client_secret": os.environ['YTM_CLIENT_SECRET'],
            "refresh_token": oauth_data['refresh_token'],
            "grant_type": "refresh_token"
        }
        res = requests.post(url, data=payload)
        return res.json().get('access_token')
    except Exception as e:
        print(f"❌ Token Error: {e}")
        return None

def check_notion_entry(video_id):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Reel"}},
                {"property": "Channel", "relation": {"contains": NOTION_PAGE_ID}}
            ]
        }
    }
    headers = {"Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", "Notion-Version": "2022-06-28"}
    res = requests.post(url, json=payload, headers=headers).json()
    return len(res.get("results", [])) > 0

def main():
    token = get_yt_token()
    if not token: sys.exit(1)

    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID, "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1) # FAIL if nothing to process

    item = items[0]
    snippet = item['snippet']
    vid_id = snippet['resourceId']['videoId']
    
    # 1. Check Notion FIRST
    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} already exists in Notion. Stopping workflow.")
        sys.exit(1) # FAIL here so Step 2-5 don't run for no reason

    # 2. Extract and Clean
    raw_artist = snippet.get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = snippet.get('title', 'Unknown Track')
    
    artist = clean_name(raw_artist)
    track = clean_name(raw_track)

    # 3. Save Metadata (Important: artist and track separate for Step 4)
    metadata = {
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"✅ metadata.json created for: {artist} - {track}")

if __name__ == "__main__":
    main()
