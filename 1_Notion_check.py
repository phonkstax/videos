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
        res.raise_for_status()
        return res.json().get('access_token')
    except Exception as e:
        print(f"❌ YouTube Auth Error: {e}")
        return None

def delete_playlist_item(token, playlist_item_id):
    """Deletes the item from the YouTube playlist."""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"id": playlist_item_id}
    
    print(f"🗑️ Attempting to delete playlist item: {playlist_item_id}...")
    try:
        response = requests.delete(url, headers=headers, params=params)
        if response.status_code == 204:
            print("✅ Successfully deleted from YouTube Playlist.")
        else:
            print(f"⚠️ Delete failed. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during deletion: {e}")

def check_notion_entry(video_id):
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
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        return len(res_data.get("results", [])) > 0
    except:
        return False

def main():
    token = get_yt_token()
    if not token: sys.exit(1)

    # 1. Fetch Playlist
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID, "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1)

    item = items[0]
    playlist_item_id = item.get('id') 
    vid_id = item['snippet']['resourceId']['videoId']
    
    # 2. Check Notion
    if check_notion_entry(vid_id):
        print(f"🚩 MATCH FOUND: {vid_id} is already in Notion.")
        
        # --- ACTION: DELETE FROM PLAYLIST ---
        delete_playlist_item(token, playlist_item_id)
        
        print("⏩ Stopping workflow. Duplicate removed from playlist.")
        sys.exit(1)

    # 3. If NEW, continue and save metadata
    raw_artist = item['snippet'].get('videoOwnerChannelTitle', 'Unknown')
    raw_track = item['snippet'].get('title', 'Unknown')
    artist, track = clean_name(raw_artist), clean_name(raw_track)

    metadata = {
        "title": f"{artist} - {track}",
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "playlist_item_id": playlist_item_id, 
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"✅ New Track Prepared: {artist} - {track}")

if __name__ == "__main__":
    main()
