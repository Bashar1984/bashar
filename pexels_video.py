#!/usr/bin/env python3
"""Create a video from Pexels stock footage.

Searches the Pexels Video API for each keyword, downloads one clip per
keyword, trims and resizes every clip to the same format, and joins them
into a single MP4 with an optional title and background music.

Usage:
    export PEXELS_API_KEY=your_key        # free key: https://www.pexels.com/api/
    python3 pexels_video.py "ocean" "forest" "city night" \
        --title "Beautiful World" --orientation portrait --clip-seconds 4

Requirements: Python 3.8+ and ffmpeg on PATH. No third-party packages.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

API_URL = "https://api.pexels.com/videos/search"
SIZES = {"portrait": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def search_video(api_key, query, orientation, min_seconds):
    """Return (download_url, credit) for the best Pexels match for `query`."""
    params = urllib.parse.urlencode(
        {"query": query, "orientation": orientation, "per_page": 15, "size": "medium"}
    )
    req = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"Authorization": api_key, "User-Agent": "pexels-video-maker/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    target_w, target_h = SIZES[orientation]
    for video in data.get("videos", []):
        if video.get("duration", 0) < min_seconds:
            continue
        mp4s = [f for f in video.get("video_files", [])
                if f.get("file_type") == "video/mp4" and f.get("width")]
        if not mp4s:
            continue
        # Smallest file that still covers the target resolution, else the largest.
        big_enough = [f for f in mp4s if f["width"] * f["height"] >= target_w * target_h]
        best = (min(big_enough, key=lambda f: f["width"] * f["height"]) if big_enough
                else max(mp4s, key=lambda f: f["width"] * f["height"]))
        credit = f"{video['user']['name']} ({video['url']})"
        return best["link"], credit
    raise RuntimeError(f"No suitable Pexels video found for '{query}'")


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "pexels-video-maker/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def find_font():
    return next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)


def escape_text(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")


def normalize(src, dest, width, height, seconds, fps):
    """Trim, scale-and-crop to fill the frame, fix fps, drop audio."""
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
          f"crop={width}:{height},fps={fps},setsar=1,format=yuv420p")
    ffmpeg("-i", src, "-t", str(seconds), "-vf", vf, "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dest)


def assemble(clips, output, seconds, fade, title, music, width, height):
    """Join normalized clips with crossfades, then add title and music."""
    inputs, filters = [], []
    for c in clips:
        inputs += ["-i", c]

    last = "[0:v]"
    if len(clips) > 1 and fade > 0:
        for i in range(1, len(clips)):
            offset = i * (seconds - fade)
            out = f"[x{i}]"
            filters.append(f"{last}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset}{out}")
            last = out
    elif len(clips) > 1:
        filters.append("".join(f"[{i}:v]" for i in range(len(clips)))
                       + f"concat=n={len(clips)}:v=1:a=0[x]")
        last = "[x]"

    total = len(clips) * seconds - (len(clips) - 1) * (fade if fade > 0 else 0)

    if title:
        font = find_font()
        font_opt = f"fontfile='{font}':" if font else ""
        size = int(width / 12)
        filters.append(
            f"{last}drawtext={font_opt}text='{escape_text(title)}':fontsize={size}:"
            f"expansion=none:fontcolor=white:borderw=4:bordercolor=black@0.6:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:enable='lt(t,{min(3, total)})'[t]"
        )
        last = "[t]"

    fade_out = max(total - 1, 0)
    filters.append(f"{last}fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out}:d=1[v]")

    args = inputs[:]
    if music:
        args += ["-stream_loop", "-1", "-i", music]
    args += ["-filter_complex", ";".join(filters), "-map", "[v]"]
    if music:
        args += ["-map", f"{len(clips)}:a", "-af", f"afade=t=out:st={fade_out}:d=1",
                 "-c:a", "aac", "-b:a", "192k"]
    args += ["-t", str(total), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", output]
    ffmpeg(*args)
    return total


def main():
    p = argparse.ArgumentParser(description="Create a video from Pexels clips.")
    p.add_argument("keywords", nargs="*", help="One clip is used per keyword, in order.")
    p.add_argument("--local", nargs="+", metavar="FILE",
                   help="Use local video files instead of searching Pexels.")
    p.add_argument("-o", "--output", default="pexels_video.mp4")
    p.add_argument("--title", help="Text shown over the first 3 seconds.")
    p.add_argument("--music", help="Audio file to use as the soundtrack (loops if short).")
    p.add_argument("--orientation", choices=SIZES, default="portrait",
                   help="portrait = Reels/TikTok/Shorts, landscape = YouTube.")
    p.add_argument("--clip-seconds", type=float, default=4.0)
    p.add_argument("--fade", type=float, default=0.5, help="Crossfade seconds (0 = hard cut).")
    p.add_argument("--fps", type=int, default=30)
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is required: https://ffmpeg.org/download.html")
    if not a.keywords and not a.local:
        p.error("give at least one keyword or --local file")
    if a.fade >= a.clip_seconds:
        p.error("--fade must be shorter than --clip-seconds")

    width, height = SIZES[a.orientation]
    work = tempfile.mkdtemp(prefix="pexels_")
    try:
        sources, credits = list(a.local or []), []
        if a.keywords:
            key = os.environ.get("PEXELS_API_KEY")
            if not key:
                sys.exit("Set PEXELS_API_KEY (get a free key at https://www.pexels.com/api/)")
            for i, kw in enumerate(a.keywords):
                print(f"Searching Pexels for '{kw}'...")
                url, credit = search_video(key, kw, a.orientation, a.clip_seconds)
                path = os.path.join(work, f"raw_{i}.mp4")
                download(url, path)
                sources.append(path)
                credits.append(f"{kw}: video by {credit}")

        clips = []
        for i, src in enumerate(sources):
            print(f"Preparing clip {i + 1}/{len(sources)}...")
            out = os.path.join(work, f"clip_{i}.mp4")
            normalize(src, out, width, height, a.clip_seconds, a.fps)
            clips.append(out)

        print("Assembling final video...")
        total = assemble(clips, a.output, a.clip_seconds, a.fade, a.title, a.music, width, height)
        print(f"Done: {a.output} ({total:.1f}s, {width}x{height})")

        if credits:
            credit_file = os.path.splitext(a.output)[0] + "_credits.txt"
            with open(credit_file, "w", encoding="utf-8") as f:
                f.write("Videos provided by Pexels (https://www.pexels.com)\n")
                f.write("\n".join(credits) + "\n")
            print(f"Credits: {credit_file}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
