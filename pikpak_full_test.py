import subprocess
import time
import json
import sys
import os

# --- CONFIG ---
REMOTE = "mypikpak"
FOLDER = "/R97group/phonkstax/reels/"
VIDEO_URL = "https://www.youtube.com/watch?v=tdocUW4aKnY"
# --------------

def run_rclone_json(args):
    # We add --json to force rclone to output machine-readable data
    cmd = ["rclone", "backend"] + args + ["--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: Non-JSON response received: {result.stdout}")
        return None

def test_round_trip():
    # 1. Trigger the download
    print(f"📡 Step 1: Sending URL to PikPak...")
    # addurl doesn't always support --json on all rclone versions, so we parse carefully
    send_cmd = subprocess.run(["rclone", "backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL], capture_output=True, text=True)
    
    try:
        task_data = json.loads(send_cmd.stdout)
        task_id = task_data.get("id")
        file_name = task_data.get("file_name")
        print(f"✅ Task created! ID: {task_id} | Target: {file_name}")
    except:
        print(f"❌ Failed to parse task response: {send_cmd.stderr}")
        return False

    # 2. Polling Loop
    print("⏳ Step 2: Waiting for PikPak to finish download...")
    for i in range(25): # Increased to 125 seconds
        time.sleep(5)
        
        # We check the status of the specific task
        status_data = run_rclone_json(["status", f"{REMOTE}:", task_id])
        
        if not status_data:
            print("   - Waiting for status data...")
            continue
            
        phase = status_data.get("phase")
        print(f"   - Status: {phase} ({i*5}s elapsed)")
        
        if phase == "PHASE_TYPE_COMPLETE":
            print("🎉 PikPak download finished!")
            break
        elif phase == "PHASE_TYPE_ERROR":
            print("❌ PikPak encountered an error.")
            return False
    else:
        print("⏰ Timeout waiting for PikPak.")
        return False

    # 3. Pull file to GitHub
    print(f"🚀 Step 3: Retrieving '{file_name}' to GitHub runner...")
    subprocess.run(["rclone", "copyto", f"{REMOTE}:{FOLDER}{file_name}", f"./{file_name}"])
    
    if os.path.exists(file_name):
        size = os.path.getsize(file_name)
        print(f"✅ SUCCESS! File '{file_name}' retrieved. Size: {size} bytes.")
        return True
    else:
        print("❌ File sync failed. Is the filename correct?")
        return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
