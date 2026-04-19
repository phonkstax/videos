import os
import json
import subprocess

def pattern_cleanup():
    # 1. Load metadata to find the specific Video ID processed in this run
    if not os.path.exists("metadata.json"):
        print("⚠️ metadata.json not found. Cleanup skipped.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # Use the unique Video ID (e.g., SVP1hF7hNxQ) as the search pattern
    video_id = meta.get('video_id')
    remote_name = "mypikpak"
    remote_path = "Download/temp/"

    if not video_id:
        print("⚠️ No video_id found in metadata. Cannot perform cleanup.")
        return

    print(f"🧹 Searching for all files containing ID: {video_id}")
    
    # 2. Use 'rclone delete' with an include pattern
    # Pattern: *ID* matches 'Song_ID.webm', 'Song_ID(1).webm', etc.
    remote_target = f"{remote_name}:{remote_path}"
    pattern = f"*{video_id}*"
    
    # We use 'delete' with '--include' to target multiple matching files at once
    cmd = [
        "rclone", "delete", remote_target, 
        "--include", pattern
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode == 0:
        print(f"🗑️ Successfully purged all versions of {video_id} (including duplicates).")
    else:
        # If no file was found, rclone might exit with an error; we log it but don't stop the job
        print(f"ℹ️ Cleanup Note: {res.stderr.strip() if res.stderr else 'No files found to delete.'}")

if __name__ == "__main__":
    pattern_cleanup()
