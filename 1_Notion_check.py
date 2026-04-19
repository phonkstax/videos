import os
import requests
import json
import sys
import re
 
# --- CONFIGURATION (Environment Variables) ---
NOTION_DB_ID = os.environ.get('NOTION_DB_ID')
NOTION_PAGE_ID = os.environ.get('NOTION_PAGE_ID')
YT_PLAYLIST_ID = os.environ.get('YT_PLAYLIST_ID')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')

def clean_name(text):
    """Cleans 'Topic' and 'Release' noise from YouTube titles."""
    text = re.sub(r'\s*[-–—]\s*Topic\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Release\s*[-–—]?\s*', '', text, flags=re.IGNORECASE)
    return text.strip()

def get_yt_token():
    """Refreshes the YouTube OAuth2 access token."""
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
    """Removes the processed/duplicate item from the YouTube playlist."""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"id": playlist_item_id}
    
    print(f"🗑️ Attempting to delete playlist item: {playlist_item_id}...")
    try:
        response = requests.delete(url, headers=headers, params=params)
        if response.status_code == 204:
            print("✅ Successfully deleted from YouTube Playlist.")
        else:
            print(f"⚠️ Delete failed. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error during deletion: {e}")

def check_notion_entry(video_id):
    """Checks Notion to see if this Video ID exists as a Reel."""
    if not NOTION_DB_ID or not NOTION_PAGE_ID or not NOTION_TOKEN:
        print("❌ Error: Notion configuration secrets are missing.")
        return False

    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Video"}},
                {"property": "Channel", "relation": {"contains": NOTION_PAGE_ID}}
            ]
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        return len(res_data.get("results", [])) > 0
    except Exception as e:
        print(f"⚠️ Notion Check failed: {e}")
        return False

def main():
    if not YT_PLAYLIST_ID:
        print("❌ Error: YT_PLAYLIST_ID secret is missing.")
        sys.exit(1)

    token = get_yt_token()
    if not token: 
        sys.exit(1)

    # 1. Fetch Top 2 Items (1 for Active, 1 for Pre-fetch)
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails", 
        "playlistId": YT_PLAYLIST_ID, 
        "maxResults": 2 
    }
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1)

    # 2. Setup Active Item (Item #1)
    active_item = items[0]
    playlist_item_id = active_item.get('id') 
    vid_id = active_item['contentDetails']['videoId']
    
    # 3. Check Notion for Active Item
    if check_notion_entry(vid_id):
        print(f"🚩 MATCH FOUND: {vid_id} is already in Notion.")
        delete_playlist_item(token, playlist_item_id)
        print("⏩ Stopping workflow. Duplicate removed from playlist.")
        sys.exit(1)

    # 4. Collect 1 Pre-fetch URL (Item #2)
    prefetch_urls = []
    if len(items) > 1:
        next_vid_id = items[1]['contentDetails']['videoId']
        prefetch_urls.append(f"https://www.youtube.com/watch?v={next_vid_id}")
        print(f"⚡ Queueing 1 URL for background pre-fetching: {next_vid_id}")

    # 5. Process Metadata
    raw_artist = active_item['snippet'].get('videoOwnerChannelTitle', 'Unknown')
    raw_track = active_item['snippet'].get('title', 'Unknown')
    artist, track = clean_name(raw_artist), clean_name(raw_track)

    metadata = {
        "title": f"{artist} - {track}",
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "playlist_item_id": playlist_item_id, 
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}",
        "prefetch_urls": prefetch_urls 
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print("-" * 40)
    print(f"✅ READY: {artist} - {track}")
    print(f"🚀 Warm-up active for next song: {'Yes' if prefetch_urls else 'No'}")
    print("-" * 40)

if __name__ == "__main__":
    main()
