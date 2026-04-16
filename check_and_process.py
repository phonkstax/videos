import os
import requests
import json
import sys

# Constants
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
PHONKSTAX_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
WORKDIR = "/tmp/reels_phonkstax"

def get_yt_token():
    url = "https://oauth2.googleapis.com/token"
    oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
    payload = {
        "client_id": os.environ['YTM_CLIENT_ID'],
        "client_secret": os.environ['YTM_CLIENT_SECRET'],
        "refresh_token": oauth_data['refresh_token'],
        "grant_type": "refresh_token"
    }
    return requests.post(url, data=payload).json().get('access_token')

def get_first_item(token):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur", "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    return r.get('items', [])[0] if r.get('items') else None

def check_notion_entry(video_id):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Reel"}},
                {"property": "Channel", "relation": {"contains": PHONKSTAX_PAGE_ID}}
            ]
        }
    }
    headers = {"Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers).json()
    return len(res.get("results", [])) > 0

def download_media(video_id):
    print(f"📡 Fetching stream data for {video_id} via Piped...")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # We use a reliable public Piped instance API
    PIPED_API = f"https://pipedapi.kavin.rocks/streams/{video_id}"
    
    try:
        response = requests.get(PIPED_API, timeout=30)
        if response.status_code != 200:
            print(f"❌ Piped API error: {response.status_code}")
            sys.exit(1)
            
        data = response.json()
        
        # 1. Get Audio Stream
        # Piped provides audioStreams sorted by quality. We take the first one.
        audio_url = data.get("audioStreams", [{}])[0].get("url")
        
        # 2. Get Thumbnail
        # Piped gives us the high-res thumbnail directly
        thumb_url = data.get("thumbnailUrl")

        if not audio_url:
            print("❌ Could not find a valid audio stream.")
            sys.exit(1)

        print("⏳ Downloading Audio...")
        audio_res = requests.get(audio_url, stream=True, timeout=60)
        with open(f"{WORKDIR}/audio.mp3", "wb") as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("🖼️ Downloading Thumbnail...")
        thumb_res = requests.get(thumb_url, timeout=20)
        with open(f"{WORKDIR}/audio.jpg", "wb") as f:
            f.write(thumb_res.content)

        print("🎉 Download successful via Piped!")
        return True

    except Exception as e:
        print(f"💥 Failed via Piped: {e}")
        sys.exit(1)         audio_data = requests.get(download_url, stream=True, timeout=60)
            with open(f"{WORKDIR}/audio.mp3", "wb") as f:
                for chunk in audio_data.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Fetch Thumbnail
            print("🖼️ Fetching Thumbnail...")
            thumb_url = f"https://i3.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            thumb_data = requests.get(thumb_url, timeout=20)
            with open(f"{WORKDIR}/audio.jpg", "wb") as f:
                f.write(thumb_data.content)
                
            print("🎉 Media download complete.")
            return True
        else:
            print(f"❌ Bridge Error: {result.get('text', 'Unknown response state')}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Critical Error: {e}")
        sys.exit(1)


def main():
    token = get_yt_token()
    item = get_first_item(token)
    if not item:
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    title = item['snippet']['title']
    item_id = item['id']

    if check_notion_entry(v_id):
        print("MATCH FOUND: Skipping.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
    else:
        print("NEW ENTRY: Downloading...")
        download_media(v_id)
        
        with open('video_data.json', 'w') as f:
            json.dump({"video_id": v_id, "title": title, "item_id": item_id}, f)
            
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")

if __name__ == "__main__":
    main()
