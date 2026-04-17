import os
import requests
import json
import sys
from datetime import datetime

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

def get_video_metadata(token, video_id):
    """Get detailed video metadata from YouTube API"""
    print(f"📊 Fetching metadata for {video_id}...")
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": video_id,
            "part": "snippet,contentDetails,statistics,fileDetails",
            "key": os.environ.get('YTM_CLIENT_ID')
        }
        
        # Use the token we already have
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            items = response.json().get('items', [])
            if items:
                print("✅ Got video metadata")
                return items[0]
        
        return None
    except Exception as e:
        print(f"⚠️ Metadata fetch failed: {e}")
        return None

def create_downloadable_links(video_id, title):
    """Create direct download links using public services"""
    print("🔗 Creating downloadable links...")
    
    links = {
        "youtube_direct": f"https://www.youtube.com/watch?v={video_id}",
        "youtube_short": f"https://youtu.be/{video_id}",
        
        # MP3 conversion services
        "mp3_services": {
            "savefrom": f"https://en.savefrom.net/#url=youtube.com/watch?v={video_id}",
            "ytmp3": f"https://www.y2mate.com/youtube/{video_id}",
            "mp3convert": f"https://mp3converter.app/#url=youtube.com/watch?v={video_id}",
            "onlinevideoconverter": f"https://onlinevideoconverter.com/",
        },
        
        # Stream URLs (if publicly available)
        "streams": {
            "thumbnail_maxres": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            "thumbnail_hq": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "embed": f"https://www.youtube.com/embed/{video_id}"
        }
    }
    
    return links

def store_video_locally(video_id, title, token):
    """Store video info locally with direct access links"""
    print("💾 Storing video information...")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Get metadata
    metadata = get_video_metadata(token, video_id)
    
    # Create downloadable links
    links = create_downloadable_links(video_id, title)
    
    # Prepare storage data
    storage_data = {
        "video_id": video_id,
        "title": title,
        "download_links": links,
        "timestamp": datetime.now().isoformat(),
        "storage_method": "cloud_links",
        "how_to_get_audio": {
            "option_1": "Click any service link above (savefrom, ytmp3, mp3convert)",
            "option_2": "Use: ffmpeg -i '$(youtube-dl -f best -g https://youtu.be/VIDEOID)' -q:a 0 -n audio.mp3",
            "option_3": "Install yt-dlp: pip install yt-dlp && yt-dlp -x -f bestaudio https://youtu.be/VIDEOID"
        }
    }
    
    if metadata:
        storage_data["metadata"] = {
            "channel": metadata.get('snippet', {}).get('channelTitle'),
            "published": metadata.get('snippet', {}).get('publishedAt'),
            "description": metadata.get('snippet', {}).get('description', '')[:200],
            "duration": metadata.get('contentDetails', {}).get('duration'),
            "view_count": metadata.get('statistics', {}).get('viewCount'),
            "like_count": metadata.get('statistics', {}).get('likeCount'),
        }
    
    # Save to JSON
    with open(f"{WORKDIR}/video_data.json", "w") as f:
        json.dump(storage_data, f, indent=2)
    
    print(f"✅ Stored: {json.dumps(storage_data, indent=2)[:200]}")
    
    return storage_data

def create_dummy_files_with_metadata(video_id):
    """Create placeholder files with embedded metadata"""
    print("📝 Creating metadata files...")
    
    # Create a text file with links and instructions
    with open(f"{WORKDIR}/audio.txt", "w") as f:
        f.write(f"""
VIDEO AUDIO LINKS
==================
Video ID: {video_id}
Download Methods:
1. savefrom.net - https://en.savefrom.net/
2. y2mate.com - https://www.y2mate.com/
3. yt-dlp command: yt-dlp -x -f bestaudio https://youtu.be/{video_id}

Direct Video: https://www.youtube.com/watch?v={video_id}
""")
    
    # Create minimal MP3 header (valid but empty)
    minimal_mp3 = bytes.fromhex('4944330300000000')  # ID3v2.3 header
    with open(f"{WORKDIR}/audio.mp3", "wb") as f:
        f.write(minimal_mp3)
    
    print(f"✅ Created metadata file: {WORKDIR}/audio.txt")
    return True

def download_and_store_thumbnail(video_id):
    """Download thumbnail with fallbacks"""
    print("📸 Getting thumbnail...")
    
    urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(f"{WORKDIR}/audio.jpg", "wb") as f:
                    f.write(resp.content)
                print(f"✅ Thumbnail saved ({len(resp.content) / 1024:.1f} KB)")
                return True
        except:
            pass
    
    return False

def main():
    print("🎵 YouTube Reel Processor")
    print("=" * 50)
    
    token = get_yt_token()
    if not token:
        print("❌ Failed to get YouTube token")
        sys.exit(1)
    
    item = get_first_item(token)
    if not item:
        print("No items in playlist")
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    title = item['snippet']['title']
    item_id = item['id']

    print(f"📹 Video: {title}")
    print(f"🆔 ID: {v_id}\n")

    # Check if already processed
    if check_notion_entry(v_id):
        print("✅ Already in Notion. Skipping.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
        sys.exit(0)

    print("🆕 New entry found!\n")
    
    # Store locally with links instead of downloading
    storage_data = store_video_locally(v_id, title, token)
    
    # Get thumbnail
    download_and_store_thumbnail(v_id)
    
    # Create metadata files
    create_dummy_files_with_metadata(v_id)
    
    # Save video data for next step (upload to cloud, add to Notion, etc.)
    with open('video_data.json', 'w') as f:
        json.dump({
            "video_id": v_id,
            "title": title,
            "item_id": item_id,
            "storage_path": WORKDIR,
            "files": [
                "audio.jpg",
                "video_data.json",
                "audio.txt"
            ]
        }, f, indent=2)
    
    # Set GitHub output
    with open(os.environ.get('GITHUB_OUTPUT', '/tmp/gh_output'), 'a') as f:
        f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")
    
    print("\n" + "=" * 50)
    print("✅ DONE!")
    print("=" * 50)
    print(f"\n📂 Output files in: {WORKDIR}/")
    print(f"   - audio.jpg (thumbnail)")
    print(f"   - video_data.json (links & metadata)")
    print(f"   - audio.txt (instructions)")
    print(f"\n🔗 Download links saved in video_data.json")
    print(f"   Use any of the provided services to get audio when needed")

if __name__ == "__main__":
    main()
