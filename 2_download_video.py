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
CLEAN_PATHS = [
    "./assets/download/", 
    "./assets/audio/", 
    "./assets/image/", 
    "./assets/trim_audio/"
]

def run_cmd(args):
    """Helper to run shell commands."""
    return subprocess.run(args, capture_output=True, text=True)

def download():
    # 1. Load Metadata
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found.")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)
    
    VIDEO_URL = meta['yt_url']
    VIDEO_ID = meta['video_id']
    PREFETCH_LIST = meta.get('prefetch_urls', [])

    # 2. Cleanup local folders
    print("🧹 Cleaning local asset folders...")
    for folder in CLEAN_PATHS:
        os.makedirs(folder, exist_ok=True)
        for f in glob.glob(os.path.join(folder, "*")):
            try: os.remove(f)
            except: pass

    # 3. SCAN CLOUD & SMART DISPATCH
    print("📡 Scanning Cloud storage...")
    cloud_ls = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"]).stdout

    # A. Handle Pre-fetch (Limit 1)
    if PREFETCH_LIST:
        for url in PREFETCH_LIST:
            p_vid_id = url.split("v=")[-1].split("&")[0]
            if p_vid_id in cloud_ls:
                print(f"  > Skip Warm-up: {p_vid_id} already in Cloud.")
            else:
                run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", url])
                print(f"  > Dispatched Warm-up: {p_vid_id}")

    # B. Identify Active Video
    file_name = None
    for line in cloud_ls.splitlines():
        if VIDEO_ID in line:
            file_name = line
            print(f"⏩ Instant Hit! Found file: {file_name}")
            break

    if not file_name:
        print(f"🆕 Dispatching active request: {VIDEO_ID}")
        send_res = run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", VIDEO_URL])
        try:
            task_data = json.loads(send_res.stdout)
            file_name = task_data.get("file_name")
        except:
            time.sleep(5)
            retry_ls = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"]).stdout
            for line in retry_ls.splitlines():
                if VIDEO_ID in line:
                    file_name = line
                    break

    if not file_name:
        print("❌ Error: Filename not found.")
        sys.exit(1)

    # 4. Polling Loop
    print(f"⏳ Waiting for Cloud Muxing...")
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(120):
        symbol = spinner[i % len(spinner)]
        if file_name in run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"]).stdout:
            size_cmd = run_cmd(["rclone", "lsjson", f"{REMOTE}:{REMOTE_PATH}{file_name}"])
            try:
                size = json.loads(size_cmd.stdout)[0].get("Size", 0)
                if size > 1000:
                    print(f"\n✨ READY: {size/1024/1024:.2f} MB")
                    break
            except: pass
        print(f"\r{symbol} [{i*5}s] Processing...", end="")
        sys.stdout.flush()
        time.sleep(5)

    # 5. Pull to Runner & SAVE DATA FOR STEP 8
    dest_path = os.path.join(LOCAL_DIR, file_name)
    print(f"🚀 Pulling to Runner...")
    run_cmd(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        print(f"🏆 Downloaded: {dest_path}")
        
        # --- THE FIX FOR STEP 8 ---
        # Update metadata with the exact cloud filename
        meta['cloud_file_name'] = file_name
        with open("metadata.json", "w") as f:
            json.dump(meta, f, indent=4)
        print(f"📝 Cloud filename saved for cleanup.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    download()
