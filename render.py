import subprocess
import os

def render_phonk_reel(input_path, output_path):
    print(f"🎬 [FFMPEG] Starting Render: {input_path}")
    
    # FFmpeg Command for Vertical Reel:
    # 1. Scale height to 1920
    # 2. Crop the center to 1080 width
    # 3. Set output to high-quality H.264 (mp4)
    
    cmd = [
        "ffmpeg", "-y",             # Overwrite if exists
        "-i", input_path,           # Input file
        "-vf", (
            "scale=-1:1920,"        # Scale height to 1920, keep aspect
            "crop=1080:1920,"       # Crop the center 1080x1920
            "setsar=1"              # Fix pixel aspect ratio
        ),
        "-c:v", "libx264",          # Video codec (Instagram/TikTok standard)
        "-preset", "veryfast",      # Speed up the encode
        "-crf", "18",               # High quality (lower is better, 18-23 is sweet spot)
        "-c:a", "aac",              # Audio codec
        "-b:a", "192k",             # Audio bitrate
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Render Complete: {output_path}")
        return True
    else:
        print(f"❌ Render Failed: {result.stderr}")
        return False

# Usage
render_phonk_reel("./output/X-BREAK.webm", "./output/final_reel.mp4")
