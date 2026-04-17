import os
import requests
import json
import sys

def delete_from_youtube():
    # 1. Load Metadata
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found. Nothing to delete.")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)
    
    item_id = meta.get('playlist_item_id')
    title = meta.get('title', 'Unknown Track')

    if not item_id:
        print("❌ Error: No playlist_item_id found in metadata.")
        sys.exit(1)

    # 2. Refresh Token
    url_token = "https://oauth2.googleapis.com/token"
    oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
    payload = {
        "client_id": os.environ['YTM_CLIENT_ID'],
        "client_secret": os.environ['YTM_CLIENT_SECRET'],
        "refresh_token": oauth_data['refresh_token'],
        "grant_type": "refresh_token"
    }
    
    token_res = requests.post(url_token, data=payload).json()
    access_token = token_res.get('access_token')

    # 3. Delete Request
    url_delete = "https://www.googleapis.com/youtube/v3/playlistItems"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"id": item_id}

    print(f"🗑️ Deleting '{title}' from YouTube Playlist...")
    response = requests.delete(url_delete, headers=headers, params=params)

    if response.status_code == 204:
        print(f"✅ Successfully removed from playlist.")
    else:
        print(f"⚠️ Delete failed. Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    delete_from_youtube()
