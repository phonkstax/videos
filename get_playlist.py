import os
import requests
import json
import sys

# --- CONFIGURATION ---
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
# You can also pass this as an argument: python remove_item.py VIDEO_ID
TARGET_VIDEO_ID = sys.argv[1] if len(sys.argv) > 1 else "-oIMyMEvMLI"
API_KEY = "AIzaSy..." # <--- PASTE YOUR API KEY HERE

def get_fresh_access_token():
    print("Refreshing access token...")
    try:
        # Load the full JSON secret
        oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
        
        # Google's OAuth2 endpoint
        url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": os.environ['YTM_CLIENT_ID'],
            "client_secret": os.environ['YTM_CLIENT_SECRET'],
            "refresh_token": oauth_data['refresh_token'],
            "grant_type": "refresh_token"
        }
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"Failed to refresh token: {e}")
        return None

def remove_track():
    token = get_fresh_access_token()
    if not token: return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Internal YouTube Music Context
    context = {
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20240410.01.00"
            }
        }
    }

    # STEP 1: Find the setVideoId
    print(f"Searching for track {TARGET_VIDEO_ID} in playlist...")
    browse_url = f"https://music.youtube.com/youtubei/v1/browse?key={API_KEY}"
    browse_payload = {**context, "browseId": f"VL{PLAYLIST_ID}"}
    
    r = requests.post(browse_url, json=browse_payload, headers=headers)
    
    set_video_id = None
    try:
        # Deep dive into the YouTube response to find the hidden ID
        results = r.json()['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']['contents']
        for item in results:
            data = item.get('musicResponsiveListItemRenderer', {}).get('playlistItemData', {})
            if data.get('videoId') == TARGET_VIDEO_ID:
                set_video_id = data.get('setVideoId')
                break
    except Exception as e:
        print(f"Error parsing playlist contents: {e}")
        return

    if not set_video_id:
        print("Track not found. (It might have been removed already)")
        return

    # STEP 2: Execute the Removal
    print(f"Found setVideoId: {set_video_id}. Removing...")
    edit_url = f"https://music.youtube.com/youtubei/v1/browse/edit_playlist?key={API_KEY}"
    edit_payload = {
        **context,
        "playlistId": PLAYLIST_ID,
        "actions": [
            {
                "action": "ACTION_REMOVE_VIDEO",
                "setVideoId": set_video_id
            }
        ]
    }
    
    final_res = requests.post(edit_url, json=edit_payload, headers=headers)
    if final_res.status_code == 200:
        print("Successfully removed track from playlist!")
    else:
        print(f"Failed to remove. Status: {final_res.status_code}, Body: {final_res.text}")

if __name__ == "__main__":
    remove_track()
