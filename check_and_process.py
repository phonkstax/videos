import os
import requests
import json
import sys
import subprocess

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

def download_thumbnail(video_id):
    """Download thumbnail with multiple quality fallbacks"""
    print("📸 Downloading Thumbnail...")
    thumbnail_urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]
    
    for thumb_url in thumbnail_urls:
        try:
            res = requests.get(thumb_url, timeout=10)
            if res.status_code == 200:
                with open(f"{WORKDIR}/audio.jpg", "wb") as f:
                    f.write(res.content)
                print(f"✅ Thumbnail saved")
                return True
        except Exception as e:
            print(f"⚠️ Thumbnail URL {thumb_url} failed: {e}")
    
    print("⚠️ Could not download thumbnail")
    return False

def download_media(video_id):
    """Download media using yt-dlp (most reliable method)"""
    print(f"📡 Downloading media for {video_id}...")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Try yt-dlp first (most reliable)
    try:
        print("🔗 Attempting yt-dlp download...")
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "-x", "--audio-format", "mp3",
            "-o", f"{WORKDIR}/audio.mp3",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(f"{WORKDIR}/audio.mp3"):
            print("🎉 Audio downloaded successfully with yt-dlp!")
            download_thumbnail(video_id)
            return True
        else:
            print(f"⚠️ yt-dlp failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️ yt-dlp not available or failed: {e}")
    
    # Fallback: Invidious proxy
    print("📡 Falling back to Invidious proxy...")
    instances = [
        "https://invidious.snopyta.org",
        "https://y.com.sb",
        "https://invidious.sethforprivacy.com",
        "https://iv.nboeck.de"
    ]
    
    for base_url in instances:
        try:
            print(f"🔗 Trying Invidious instance: {base_url}")
            api_url = f"{base_url}/api/v1/videos/{video_id}"
            data = requests.get(api_url, timeout=15).json()
            
            # Log available formats for debugging
            formats = data.get("adaptiveFormats", [])
            print(f"   Found {len(formats)} formats")
            
            # Find best audio stream
            best_audio = None
            for fmt in formats:
                fmt_type = fmt.get("type", "")
                if "audio/mp4" in fmt_type or "audio/webm" in fmt_type:
                    # Prefer higher bitrate
                    if best_audio is None or fmt.get("bitrate", 0) > best_audio.get("bitrate", 0):
                        best_audio = fmt
            
            if best_audio and best_audio.get("url"):
                audio_url = best_audio["url"]
                bitrate = best_audio.get("bitrate", "unknown")
                print(f"   ⏳ Downloading audio (bitrate: {bitrate})...")
                
                res = requests.get(audio_url, stream=True, timeout=60, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                res.raise_for_status()
                
                with open(f"{WORKDIR}/audio.mp3", "wb") as f:
                    downloaded = 0
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                    print(f"   Downloaded {downloaded / (1024*1024):.2f} MB")
                
                download_thumbnail(video_id)
                print("🎉 Success via Invidious!")
                return True
            else:
                print(f"   ❌ No audio format found")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout on {base_url}")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection error on {base_url}")
        except json.JSONDecodeError:
            print(f"   📄 Invalid JSON response from {base_url}")
        except Exception as e:
            print(f"   ⚠️ Error with {base_url}: {str(e)}")
            continue
    
    print("❌ All methods failed. Unable to download media.")
    return False


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
        success = download_media(v_id)
        
        if success:
            with open('video_data.json', 'w') as f:
                json.dump({"video_id": v_id, "title": title, "item_id": item_id}, f)
                
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")
        else:
            print("❌ Failed to download media")
            sys.exit(1)

if __name__ == "__main__":
    main()
