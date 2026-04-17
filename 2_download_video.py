import subprocess
import time
import json
import os
import sys
import glob

# --- CONFIG ---
REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"
# Folders that must be emptied to prevent using old repo files
CLEAN_PATHS = [
    LOCAL_DIR, 
    "./assets/audio/", 
    "./assets/image/", 
    "./assets/trim_audio/", # Added this to be safe
    "./output/"
]

def download():
    if not os.path.exists("metadata.json"): 
        print("ℹ️ No metadata.json found.")
        return

    # 1. AGGRESSIVE CLEANUP
    print("🧹 Wiping local asset folders to ensure fresh render...")
    for folder in CLEAN_PATHS:
        if os.path.exists(folder):
            # Remove every file inside the folder
            files = glob.glob(os.path.join(folder, "*"))
            for f in files:
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                        print(f"  🗑️ Deleted: {f}")
                except Exception as e:
                    print(f"  ⚠️ Could not delete {f}: {e}")
        else:
            # Create the folder if it doesn't exist
            os.makedirs(folder, exist_ok=True)
            print(f"  📁 Created: {folder}")
    
    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # 2. TRIGGER PIKPAK
    print(f"📡 Requesting PikPak for: {meta['yt_url']}")
    # Using 'addurl' to trigger the cloud download
    cmd = ["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", meta['yt_url']]
    send_res = subprocess.run(cmd, capture_output=True, text=True)
    
    if not send_res.stdout.strip():
        print(f"❌ Rclone returned empty response. Error: {send_res.stderr}")
        sys.exit(1)

    try:
        task_data = json.loads(send_res.stdout)
        file_name = task_data.get("file_name")
        if not file_name:
            raise ValueError("No file_name in response")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ Failed to parse task data. Raw: {send_res.stdout}")
        sys.exit(1)

    # 3. POLL AND COPY
    print(f"⏳ Waiting for cloud completion: {file_name}...")
    # 60 attempts * 10 seconds = 10 minute timeout
    for i in range(60):
        list_cmd = subprocess.run(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"], capture_output=True, text=True)
        
        if file_name in list_cmd.stdout:
            print(f"✅ Cloud download finished! Pulling to {LOCAL_DIR}...")
            # Use copyto to ensure the filename is exactly what we expect
            target_local = os.path.join(LOCAL_DIR, file_name)
            subprocess.run(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", target_local])
            
            if os.path.exists(target_local):
                print(f"🎉 Successfully pulled: {target_local}")
                return
            else:
                print("❌ Copy failed.")
                sys.exit(1)
                
        time.sleep(10)
    
    print("⏰ Timeout waiting for PikPak.")
    sys.exit(1)

if __name__ == "__main__":
    download()
