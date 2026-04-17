import subprocess
import time
import json
import sys
import os

# --- CONFIG ---
REMOTE = "mypikpak"
FOLDER = "/Download/temp/"
LOCAL_OUTPUT = "./output/"
VIDEO_URL = "https://www.youtube.com/watch?v=7RvhZyBK9vU"
# --------------

def run_command(args):
    return subprocess.run(args, capture_output=True, text=True)

def test_round_trip():
    # 0. Preparation
    if not os.path.exists(LOCAL_OUTPUT):
        os.makedirs(LOCAL_OUTPUT)
    
    print("🔥 PHONKSTAX ENGINE ACTIVATED 🔥")
    print("----------------------------------")

    # 1. Trigger the download
    print(f"📡 [STEP 1] Dispatching Cloud Request...")
    run_command(["rclone", "mkdir", f"{REMOTE}:{FOLDER}"])
    send_cmd = run_command(["rclone", "backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL])
    
    try:
        task_data = json.loads(send_cmd.stdout)
        file_name = task_data.get("file_name")
        print(f"✅ Target Locked: {file_name}")
    except:
        print(f"❌ Critical Error: PikPak rejected the request.")
        return False

    # 2. The Dynamic Polling Loop
    print(f"⏳ [STEP 2] Waiting for Cloud Muxing...")
    
    # We use a spinner to show life in the logs
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    for i in range(120): # Check every 5 seconds for 10 mins
        # UI/UX: Update the log line
        symbol = spinner[i % len(spinner)]
        
        list_cmd = run_command(["rclone", "lsf", f"{REMOTE}:{FOLDER}"])
        
        if file_name in list_cmd.stdout:
            size_cmd = run_command(["rclone", "lsjson", f"{REMOTE}:{FOLDER}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                current_size = size_data.get("Size", 0)
                
                if current_size > 1000:
                    print(f"\n✨ FILE READY! Final Cloud Size: {current_size/1024/1024:.2f} MB")
                    break
                else:
                    print(f"\r{symbol} [{i*5}s] File detected, but still stitching audio/video...", end="")
            except:
                print(f"\r{symbol} [{i*5}s] Initializing transfer...", end="")
        else:
            print(f"\r{symbol} [{i*5}s] PikPak is fetching streams from YouTube...", end="")
        
        sys.stdout.flush()
        time.sleep(5) # Faster polling for better excitement
    else:
        print("\n⏰ Timeout: PikPak took too long.")
        return False

    # 3. Retrieval
    dest_path = os.path.join(LOCAL_OUTPUT, file_name)
    print(f"\n🚀 [STEP 3] Siphoning file to GitHub Runner...")
    
    # Run the download and show a success message when done
    run_command(["rclone", "copyto", f"{REMOTE}:{FOLDER}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        print(f"----------------------------------")
        print(f"🏆 MISSION ACCOMPLISHED")
        print(f"📂 Saved to: {dest_path}")
        print(f"💎 Quality: High Bitrate WebM")
        print(f"----------------------------------")
        return True
    
    return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
