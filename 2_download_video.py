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
# Folders to wipe for a fresh start
# Updated CLEAN_PATHS to be safer
CLEAN_PATHS = [
    "./assets/download/", 
    "./assets/audio/", 
    "./assets/image/", 
    "./assets/trim_audio/"
    # Removed "./output/" and "./" to protect metadata.json
]
def run_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)

def download():
    # 1. Load Metadata from Step 1
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found. Did Step 1 fail?")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)
    
    VIDEO_URL = meta['yt_url']

    # 2. Cleanup (Wipe folders, but KEEP metadata.json in root)
    print("🧹 Cleaning local asset folders...")
    for folder in CLEAN_PATHS:
        os.makedirs(folder, exist_ok=True)
        for f in glob.glob(os.path.join(folder, "*")):
            try: os.remove(f)
            except: pass

    # 3. CHECK IF FILE ALREADY EXISTS IN PIKPAK (The "Rerun Speedup")
    print(f"📡 Checking if file exists in Cloud...")
    
    # We check the directory once before dispatching a new task
    list_check = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
    
    # PikPak usually names YouTube files starting with 'www.youtube.com_watch'
    # Or you can look for the specific Video ID if you want to be 100% precise
    existing_file = None
    for line in list_check.stdout.splitlines():
        if meta['video_id'] in line or "www.youtube.com_watch" in line:
            existing_file = line
            break

    if existing_file:
        print(f"⏩ Instant Hit! Found existing file: {existing_file}")
        file_name = existing_file
    else:
        print(f"🆕 No existing file found. Dispatching fresh Cloud Request...")
        run_cmd(["rclone", "mkdir", f"{REMOTE}:{REMOTE_PATH}"])
        send_res = run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", VIDEO_URL])
        
        try:
            task_data = json.loads(send_res.stdout)
            file_name = task_data.get("file_name")
            print(f"✅ Target Locked: {file_name}")
        except:
            print(f"❌ PikPak Error: {send_res.stderr or send_res.stdout}")
            sys.exit(1)

    # 4. Polling Loop
    print(f"⏳ Waiting for Cloud Muxing...")
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    for i in range(120):
        symbol = spinner[i % len(spinner)]
        list_cmd = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
        
        if file_name in list_cmd.stdout:
            # Check size to ensure PikPak finished stitching
            size_cmd = run_cmd(["rclone", "lsjson", f"{REMOTE}:{REMOTE_PATH}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                # If size is > 1KB, it's ready
                if size_data.get("Size", 0) > 1000:
                    print(f"\n✨ FILE READY! Size: {size_data['Size']/1024/1024:.2f} MB")
                    break
            except: pass
            print(f"\r{symbol} [{i*5}s] File detected, stitching audio/video...", end="")
        else:
            print(f"\r{symbol} [{i*5}s] PikPak is fetching from YouTube...", end="")
        
        sys.stdout.flush()
        time.sleep(5)
    else:
        print("\n⏰ Timeout waiting for PikPak.")
        sys.exit(1)

    # 5. Pull to Runner
    dest_path = os.path.join(LOCAL_DIR, file_name)
    print(f"🚀 Pulling file to GitHub Runner...")
    run_cmd(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        print(f"🏆 MISSION ACCOMPLISHED: {dest_path}")
    else:
        print("❌ Download failed.")
        sys.exit(1)

if __name__ == "__main__":
    download()
