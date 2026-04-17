import subprocess
import json
import os
import sys
import re

# --- CONFIG ---
AUDIO = "./assets/audio/audio.mp3"
IMAGE = "./assets/image/image.jpg"
LOGO = "./assets/spotify.png"
OUTPUT = "./output/output.mp4"
CLIP_LEN = 20
STEP = 2

def get_duration(file):
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file
    ], capture_output=True, text=True)
    return float(json.loads(probe.stdout)["format"]["duration"])

def find_best_drop(file, duration):
    print(f"🔍 Analyzing audio for the best {CLIP_LEN}s drop...")
    best_start = 0
    best_score = -999

    for t in range(0, int(duration - CLIP_LEN), STEP):
        cmd = [
            "ffmpeg", "-ss", str(t), "-t", str(CLIP_LEN),
            "-i", file,
            "-af", "highpass=f=40,lowpass=f=200,volumedetect",
            "-f", "null", "-"
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        
        # We look for mean_volume. Closer to 0 is louder/more energy.
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

def render_video(start_t):
    # Calculations for your n8n logic
    logo_start = CLIP_LEN * 0.5
    fade_out = CLIP_LEN - 2
    
    print(f"🎬 Rendering drop starting at {start_t}s...")
    
    # Construct the complex filter string
    filter_complex = (
        f"[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1080:1080,eq=saturation=1.2:contrast=1.05[cover];"
        f"[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1500:1500,gblur=sigma=30,"
        f"zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1400x1400:fps=30,"
        f"rotate='0.04*sin(2*PI*t/5)':fillcolor=black@0,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[cover]scale=900:900[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2-200[vbase];"
        f"[2:v]scale=200:-1[logo];"
        f"[logo]fade=t=in:st={logo_start}:d=0.6:alpha=1,fade=t=out:st={fade_out}:d=2:alpha=1[logofaded];"
        f"[vbase][logofaded]overlay=(W-w)/2:H-h-60:enable='between(t,{logo_start},{CLIP_LEN})',format=yuv420p[v];"
        f"[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out}:d=2[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_t), "-t", str(CLIP_LEN), "-loop", "1", "-i", IMAGE,
        "-ss", str(start_t), "-t", str(CLIP_LEN), "-i", AUDIO,
        "-loop", "1", "-i", LOGO,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-shortest", OUTPUT
    ]
    
    subprocess.run(cmd)

def main():
    if not os.path.exists("./output"): os.makedirs("./output")
    
    total_duration = get_duration(AUDIO)
    best_start = find_best_drop(AUDIO, total_duration)
    
    print(f"🔥 Found best part at {best_start}s. Starting Render...")
    render_video(best_start)
    print(f"✅ Video saved to {OUTPUT}")

if __name__ == "__main__":
    main()
