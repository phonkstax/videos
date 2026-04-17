import os
import requests
import json
import sys

# --- CONFIGURATION ---
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_DB_ID = os.environ.get('NOTION_DB_ID')
PHONKSTAX_PAGE_ID = os.environ.get('NOTION_PAGE_ID')

def update_notion():
    # 1. Load Metadata from previous steps
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found.")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # 2. Prepare the Page Data
    # Note: Ensure these property names match your Notion Database exactly!
    # ... inside 6_notion_update.py ...
    
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            # Fixed from 'Name' to 'Title'
            "Title": {
                "title": [{"text": {"content": meta['title']}}]
            },
            # Matches your screenshot exactly
            "Video ID": {
                "rich_text": [{"text": {"content": meta['video_id']}}]
            },
            # Matches your screenshot exactly
            "Type": {
                "select": {"name": "Reel"}
            },
            # Matches your screenshot exactly
            "Channel": {
                "relation": [{"id": PHONKSTAX_PAGE_ID}]
            }
            # NOTE: Removed "URL" because it's not in your Notion database!
        }
    }

    print(f"📡 Updating Notion for: {meta['title']}...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ Notion updated successfully!")
    else:
        print(f"❌ Notion Update Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    update_notion()
