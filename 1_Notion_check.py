def main():
    token = get_yt_token()
    if not token: sys.exit(1)

    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID, "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1)

    item = items[0]
    
    # --- CAPTURE ID ---
    playlist_item_id = item.get('id') 
    
    snippet = item['snippet']
    vid_id = snippet['resourceId']['videoId']
    
    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} already exists in Notion. Stopping workflow.")
        sys.exit(1)

    raw_artist = snippet.get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = snippet.get('title', 'Unknown Track')
    
    artist = clean_name(raw_artist)
    track = clean_name(raw_track)

    # --- SAVE EVERYTHING ---
# ... (at the end of your main function)
    metadata = {
        "title": title,
        "video_id": v_id,
        "playlist_item_id": item_id,
        "yt_url": f"https://www.youtube.com/watch?v={v_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"✅ metadata.json saved for {title}")
    
    # --- LOUD LOGGING ---
    print("--------------------------------------------------")
    print(f"✅ METADATA GENERATED SUCCESSFULLY")
    print(f"🎵 Track: {artist} - {track}")
    print(f"🆔 Playlist Item ID: {playlist_item_id}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
