import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    # 1. Retrieve everything from GitHub Secrets
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    client_id = os.environ.get("YTM_CLIENT_ID")
    client_secret = os.environ.get("YTM_CLIENT_SECRET")
    
    # 2. Re-create the file on the runner
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    # 3. Create the credentials object
    auth_keys = OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret
    )

    try:
        # 4. Pass BOTH the filename and the credentials object
        return YTMusic(auth="oauth.json", oauth_credentials=auth_keys)
    except Exception as e:
        print(f"Init Error: {e}")
        return None

def main():
    yt = get_ytm_client()
    if not yt: return

    # Your private playlist ID
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    print(f"Accessing Private Playlist: {playlist_id}")
    try:
        playlist = yt.get_playlist(playlist_id)
        print(f"--- SUCCESS! Found: {playlist['title']} ---")
        
        for track in playlist['tracks']:
            print(f"ID: {track['videoId']} | {track['title']}")
            
    except Exception as e:
        print(f"Fetch Error: {e}")

if __name__ == "__main__":
    main()
