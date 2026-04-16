import os
import requests
import json
import sys

# Constants from your Notion setup
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 

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
    
    # Combined filter: Video ID match AND Type is Reel AND Channel is phonkstax
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Video ID",
                    "rich_text": {"equals": video_id}
                },
                {
                    "property": "Type",
                    "select": {"equals": "Reel"}
                },
                {
                    "property": "Channel",
                    "select": {"equals": "phonkstax"}
                }
            ]
        }
    }
    res = requests.post(url, json=payload, headers=headers).json()
    return len(res.get("results", [])) > 0

def main():
    yt_token = get_yt_token()
    item = get_first_item(yt_token)

    if not item:
        print("Playlist is empty.")
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    item_id = item['id']
    title = item['snippet']['title']

    if check_notion_entry(v_id):
        print(f"SKIPPING: {title} already exists as a 'Reel' for 'phonkstax' in Notion.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
    else:
        print(f"PROCEEDING: {title} is a new entry for your channel.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=false\n")
            f.write(f"video_id={v_id}\n")
            f.write(f"item_id={item_id}\n")
            f.write(f"title={title}\n")

if __name__ == "__main__":
    main()
