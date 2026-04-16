import os
import requests
import json
import sys

def download_via_cobalt(youtube_url):
    # Public Cobalt instance
    API_URL = "https://cobalt.tools/api/json" 
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": youtube_url,
        "downloadMode": "audio",
        "audioFormat": "mp3",
        "audioBitrate": "192"
    }

    print(f"📡 Requesting Cobalt bridge for: {youtube_url}")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        result = response.json()

        # Cobalt returns 'stream' for direct files or 'redirect' for some instances
        if response.status_code == 200 and result.get("status") in ["stream", "redirect", "tunnel"]:
            download_url = result.get("url")
            print(f"✅ Success! Bridge opened: {download_url}")
            
            print("⏳ Downloading MP3 to workspace...")
            file_data = requests.get(download_url, stream=True)
            with open("output_audio.mp3", "wb") as f:
                for chunk in file_data.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("🎉 File saved: output_audio.mp3")
            return True
        else:
            print(f"❌ Cobalt Error: {result.get('text', 'Unknown response format')}")
            print(f"Full Response: {json.dumps(result, indent=2)}")
            return False

    except Exception as e:
        print(f"💥 Connection failed: {e}")
        return False

if __name__ == "__main__":
    # Testing with the X-BREAK track that was failing
    test_url = "https://www.youtube.com/watch?v=tdocUW4aKnY"
    success = download_via_cobalt(test_url)
    if not success:
        sys.exit(1)
