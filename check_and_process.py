import os
import requests
import json
import sys

# Your Notion Database ID from the URL
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 

def get_yt_token():
    """Refreshes the YouTube OAuth token using Client ID, Secret, and Refresh Token."""
    url = "https://oauth2.googleapis.com/token"
    try:
        # Parsing the JSON string stored in GitHub Secrets
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
    """Fetches the first item from your specific YouTube Music playlist."""
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
    """
    Queries Notion with a filter for:
    1. Video ID (Rich Text)
    2. Type (Select) == 'Reel'
    3. Channel (Relation) contains a page named 'phonkstax'
    """
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
                        # Since Channel is a Relation, we check if it contains the page name
                        "contains": "phonkstax" 
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
        
    # If results list has items, it means a duplicate exists
    return len(res_data.get("results", [])) > 0

def main():
    # 1. Get Authentication for YouTube
    yt_token = get_yt_token()
    
    # 2. Get the current track from the top of the Playlist
    item = get_first_item(yt_token)
    if not item:
        print("Playlist is empty.")
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    item_id = item['id']
    title = item['snippet']['title']

    # 3. Check Notion for existing entry with specific filters
    if check_notion_entry(v_id):
        print(f"MATCH FOUND: '{title}' ({v_id}) is already logged as a Reel for phonkstax. Skipping.")
        # Set GitHub Output to 'true' to signal a skip to the YAML
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("exists=true\n")
    else:
        print(f"PROCEEDING: '{title}' ({v_id}) is a new Reel entry for phonkstax.")
        # Set GitHub Outputs for the next steps in the YAML workflow
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("exists=false\n")
                f.write(f"video_id={v_id}\n")
                f.write(f"item_id={item_id}\n")
                f.write(f"title={title}\n")

if __name__ == "__main__":
    main()
