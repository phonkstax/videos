import os
import requests
import json
import sys
import re

# Constants
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
NOTION_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

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
        print(f"❌ OAuth Refresh Failed: {e}")
        return None

def clean_title(artist, track):
    # 1. Strip "Release - " from the start of the track name
    track = re.sub(r'^Release\s*-\s*', '', track, flags=re.IGNORECASE).strip()
    
    # 2. Clean " - Topic" out of the artist name
    artist = re.sub(r'\s*-\s*Topic\s*$', '', artist, flags=re.IGNORECASE).strip()
    
    # 3. Logic check: If artist is "Various Artists" or generic, just use the track name
    if artist.lower() in ["various artists", "unknown artist", "youtube","Release - Topic"]:
        return track
    
    # 4. If the track title already contains the artist name, don't double it
    if artist.lower() in track.lower():
        return track
        
    return f"{artist} - {track}"

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
    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", 
        "Notion-Version": "2022-06-28", 
        "Content-Type": "application/json"
    }
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
        print("📭 Playlist is empty.")
        sys.exit(0)

    item = items[0]
    snippet = item['snippet']
    vid_id = snippet['resourceId']['videoId']
    
    # Extract Artist and Track
    raw_artist = snippet.get('videoOwnerChannelTitle', 'Various Artists')
    raw_track = snippet.get('title', 'Unknown Track')
    
    # Apply the new cleaning logic
    final_title = clean_title(raw_artist, raw_track)

    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} ({final_title}) exists in Notion. Skipping.")
        sys.exit(0)

    metadata = {
        "video_id": vid_id,
        "playlist_item_id": item['id'],
        "title": final_title,
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"📝 Metadata saved: {final_title}")

if __name__ == "__main__":
    main()
