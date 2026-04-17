import os
import requests
import json
import sys
import re

# --- CONFIGURATION ---
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
NOTION_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

def clean_name(text):
    """Cleans 'Topic' and 'Release' noise from YouTube titles."""
    text = re.sub(r'\s*[-–—]\s*Topic\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Release\s*[-–—]?\s*', '', text, flags=re.IGNORECASE)
    return text.strip()

def get_yt_token():
    """Refreshes the YouTube OAuth2 token."""
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
        res.raise_for_status()
        return res.json().get('access_token')
    except Exception as e:
        print(f"❌ YouTube Auth Error: {e}")
        return None

def check_notion_entry(video_id):
    """Checks if the video already exists in the Notion Database."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Reel"}},
                {"property": "Channel", "relation": {"contains": NOTION_PAGE_ID}}
            ]
        }
    }
    
    print(f"📡 Querying Notion for Video ID: {video_id}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        results = res_data.get("results", [])
        
        if len(results) > 0:
            print(f"🚩 MATCH FOUND: This video is already in your Notion database.")
            return True
        else:
            print(f"✨ NEW TRACK: No entry found in Notion.")
            return False
    except Exception as e:
        print(f"⚠️ Notion API Error: {e}")
        return False

def main():
    # 1. Auth
    token = get_yt_token()
    if not token:
        sys.exit(1)

    # 2. Fetch Playlist
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID, "maxResults": 1}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get(url, params=params, headers=headers).json()
        items = r.get('items', [])
    except Exception as e:
        print(f"❌ YouTube API Request Failed: {e}")
        sys.exit(1)
    
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1)

    # 3. Extract Data
    item = items[0]
    playlist_item_id = item.get('id') 
    snippet = item['snippet']
    vid_id = snippet['resourceId']['videoId']
    
    # 4. Check Notion
    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} already exists. Stopping workflow to save minutes.")
        sys.exit(1)

    # 5. Process Names
    raw_artist = snippet.get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = snippet.get('title', 'Unknown Track')
    
    artist = clean_name(raw_artist)
    track = clean_name(raw_track)
    full_title = f"{artist} - {track}"

    # 6. Save Metadata for Next Steps
    metadata = {
        "title": full_title,
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "playlist_item_id": playlist_item_id, 
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    # 7. Final Report
    print("-" * 50)
    print(f"✅ METADATA GENERATED")
    print(f"🎵 Track: {full_title}")
    print(f"🆔 Playlist Item ID: {playlist_item_id}")
    print("-" * 50)

if __name__ == "__main__":
    main()
