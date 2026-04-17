import subprocess
import time
import json
import os
import sys
import glob

REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"

def download():
    if not os.path.exists("metadata.json"): 
        print("ℹ️ No metadata.json found.")
        return

    # 1. CLEANUP (Wipe folders before new download)
    print("🧹 Cleaning local asset folders...")
    for folder in [LOCAL_DIR, "./assets/audio/", "./assets/image/"]:
        if os.path.exists(folder):
            for f in glob.glob(os.path.join(folder, "*")):
                try: os.remove(f)
                except: pass
        else:
            os.makedirs(folder, exist_ok=True)
    
    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # 2. TRIGGER PIKPAK
    print(f"📡 Requesting PikPak for: {meta['yt_url']}")
    cmd = ["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", meta['yt_url']]
    send_res = subprocess.run(cmd, capture_output=True, text=True)
    
    # SAFETY CHECK: If rclone output is empty
    if not send_res.stdout.strip():
        print(f"❌ Rclone returned empty response. Error: {send_res.stderr}")
        sys.exit(1)

    try:
        task_data = json.loads(send_res.stdout)
        file_name = task_data.get("file_name")
    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON from rclone. Raw output: {send_res.stdout}")
        sys.exit(1)

    # 3. POLL AND COPY
    print(f"⏳ Waiting for {file_name} in cloud...")
    for i in range(60):
        list_cmd = subprocess.run(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"], capture_output=True, text=True)
        if file_name in list_cmd.stdout:
            print(f"✅ Found! Pulling to {LOCAL_DIR}...")
            subprocess.run(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", f"{LOCAL_DIR}{file_name}"])
            return
        time.sleep(10)
    
    print("⏰ Timeout waiting for PikPak.")
    sys.exit(1)

if __name__ == "__main__":
    download()
