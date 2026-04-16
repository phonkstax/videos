import os
import requests
import json
import sys

# Constants from your Notion setup
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
# The UUID for the 'phonkstax' page in your Channel relation
PHONKSTAX_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"

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
        r = requests.post(url, data=payload)
        r.raise_for_status()
        return r.json().get('access_token')
    except Exception as e:
        print(f"YouTube Auth Error: {e}")
        sys.exit(1)

def get_first_item(token):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur",
        "maxResults": 1
    }
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, params=params, headers=headers).json()
    return r.get('items', [])[0] if r.get('items') else None

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
                {
                    "property": "Video ID",
                    "rich_text": {"equals": video_id.strip()}
                },
                {
                    "property": "Type",
                    "select": {"equals": "Reel"}
                },
                {
                    "property": "Channel",
                    "relation": {
                        "contains": PHONKSTAX_PAGE_ID
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    res_data = response.json()
    
    if response.status_code != 200:
        print(f"Notion API Error: {res_data}")
        return False
        
    return len(res_data.get("results", [])) > 0

def main():
    yt_token = get_yt_token()
    item = get_first_item(yt_token)

    if not item:
        print("Playlist is empty.")
        sys.exit(0)

    # IDs for output and debugging
    v_id = item['contentDetails']['videoId']
    item_id = item['id']  # This is the Playlist Item ID starting with UEw...
    title = item['snippet']['title']

    # Show the IDs in the GitHub log as requested
    print(f"--- Playlist Item Found ---")
    print(f"Title: {title}")
    print(f"Video ID: {v_id}")
    print(f"Playlist Item ID: {item_id}")
    print(f"---------------------------")

    if check_notion_entry(v_id):
        print(f"MATCH FOUND: '{title}' already exists for phonkstax. Skipping.")
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("exists=true\n")
    else:
        print(f"PROCEEDING: '{title}' is a new Reel for phonkstax.")
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("exists=false\n")
                f.write(f"video_id={v_id}\n")
                f.write(f"item_id={item_id}\n")
                f.write(f"title={title}\n")

if __name__ == "__main__":
    main()
