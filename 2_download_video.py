import subprocess
import time
import json
import os
import sys

# CONFIG
REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"

def download():
    if not os.path.exists("metadata.json"):
        print("ℹ️ No metadata.json found, skipping download.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    os.makedirs(LOCAL_DIR, exist_ok=True)

    print(f"📡 Sending to PikPak: {meta['yt_url']}")
    cmd = ["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", meta['yt_url']]
    send_res = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        file_name = json.loads(send_res.stdout).get("file_name")
    except:
        print(f"❌ PikPak error: {send_res.stderr}")
        sys.exit(1)

    # Wait for cloud download
    print(f"⏳ Waiting for {file_name}...")
    for _ in range(60):
        list_cmd = subprocess.run(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"], capture_output=True, text=True)
        if file_name in list_cmd.stdout:
            print("🎉 Found in cloud, siphoning...")
            subprocess.run(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", f"{LOCAL_DIR}{file_name}"])
            print(f"✅ Download complete: {LOCAL_DIR}{file_name}")
            return
        time.sleep(10)
    
    print("⏰ Download timed out")
    sys.exit(1)

if __name__ == "__main__":
    download()
