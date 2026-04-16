import os
import requests
import json
import sys

def get_access_token():
    """Refreshes the OAuth token using your credentials."""
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
        print(f"Auth Error: {e}")
        return None

def delete_playlist_item(item_id):
    """Deletes the specific item from the playlist."""
    token = get_access_token()
    if not token:
        return

    # Official Google API endpoint for deleting playlist items
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"id": item_id}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    print(f"Attempting to delete item: {item_id}")
    r = requests.delete(url, params=params, headers=headers)

    if r.status_code == 204:
        print("Successfully removed from playlist!")
    else:
        print(f"Failed to delete. Status: {r.status_code}")
        print(f"Response: {r.text}")

if __name__ == "__main__":
    # Get ID from command line or use your provided ID as default
    target_id = sys.argv[1] if len(sys.argv) > 1 else "UEw4V0dZdDJmaGVuQ0puQkhGQktxdzhTWmwtb3lPMDNVci5ENUI5OTFCQkYxNDUxQjQ3"
    delete_playlist_item(target_id)
