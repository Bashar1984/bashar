# Pexels Video Maker

Turns keywords into a finished MP4 made from free Pexels stock footage.

## Setup
1. Get a free API key: https://www.pexels.com/api/
2. Install [ffmpeg](https://ffmpeg.org/download.html) (Python 3.8+ is the only other requirement).
3. `export PEXELS_API_KEY=your_key` (Windows: `set PEXELS_API_KEY=your_key`)

## Examples
```bash
# Vertical video for Reels / TikTok / Shorts: one 4-second clip per keyword
python3 pexels_video.py "healthy food" "morning yoga" "drinking water" --title "Daily Health Tips"

# Horizontal YouTube video with music and hard cuts
python3 pexels_video.py ocean forest mountains --orientation landscape \
    --music song.mp3 --fade 0 --clip-seconds 5 -o nature.mp4

# Use your own clips instead of Pexels
python3 pexels_video.py --local clip1.mp4 clip2.mp4 --title "My Video"
```

| Option | Default | Meaning |
|---|---|---|
| `--orientation` | `portrait` | `portrait` 1080x1920, `landscape` 1920x1080, `square` 1080x1080 |
| `--clip-seconds` | `4` | Length of each clip |
| `--fade` | `0.5` | Crossfade between clips (`0` = hard cut) |
| `--title` | none | Text shown over the first 3 seconds |
| `--music` | none | Soundtrack (looped if short, faded out at end) |
| `-o` | `pexels_video.mp4` | Output file |

A `*_credits.txt` file listing each Pexels creator is saved next to the video.
