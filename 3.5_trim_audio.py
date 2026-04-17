import subprocess
import json
import os
import sys

# --- CONFIG ---
INPUT_AUDIO = "./assets/audio/audio.mp3"
TRIM_DIR = "./assets/trim_audio"
OUTPUT_TRIM = os.path.join(TRIM_DIR, "trim_audio.mp3")
CLIP_LEN = 20
STEP = 4  # Jump 4s for faster analysis

def find_best_drop(file):
    # 1. Get total duration
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file
    ], capture_output=True, text=True)
    duration = float(json.loads(probe.stdout)["format"]["duration"])

    print(f"🔍 Analyzing {int(duration)}s audio for the best {CLIP_LEN}s drop...")
    best_start = 0
    best_score = -999

    # 2. Loop to find highest energy snippet
    for t in range(0, int(duration - CLIP_LEN), STEP):
        cmd = [
            "ffmpeg", "-ss", str(t), "-t", "1", 
            "-i", file,
            "-af", "highpass=f=40,lowpass=f=200,volumedetect",
            "-f", "null", "-"
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        
        for line in p.stderr.split("\n"):
            if "mean_volume" in line:
                try:
                    score = float(line.split(":")[1].replace(" dB","").strip())
                    if score > best_score:
                        best_score = score
                        best_start = t
                except:
                    pass
    return best_start

def main():
    if not os.path.exists(INPUT_AUDIO):
        print(f"❌ Input missing: {INPUT_AUDIO}")
        sys.exit(1)

    if not os.path.exists(TRIM_DIR):
        os.makedirs(TRIM_DIR)

    # Find the best part
    start_time = find_best_drop(INPUT_AUDIO)
    print(f"🔥 Best drop starts at {start_time}s. Extracting...")

    # Extract the 20s clip
    # -c copy is used here for instant extraction without quality loss
    extract_cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(CLIP_LEN),
        "-i", INPUT_AUDIO,
        "-acodec", "libmp3lame",
        "-ab", "192k",
        OUTPUT_TRIM
    ]
    
    subprocess.run(extract_cmd)
    print(f"✅ Trimmed audio saved to: {OUTPUT_TRIM}")

    # Update metadata so Step 4 knows we are using a 20s base
    if os.path.exists("metadata.json"):
        with open("metadata.json", "r") as f:
            meta = json.load(f)
        meta["best_start_original"] = start_time
        meta["is_trimmed"] = True
        with open("metadata.json", "w") as f:
            json.dump(meta, f, indent=4)

if __name__ == "__main__":
    main()
