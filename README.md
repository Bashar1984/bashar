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

---

# Vox-Style Animated Explainer

`vox_video.py` draws a 40-second, Vox-style animated explainer, **"Why your brain needs sleep"**, entirely in code. It uses cream paper texture, bold serif headlines, highlighter swipes, an animated people grid, a range bar chart, a sleep-cycle hypnogram, cut-paper cards and slide transitions. It also generates its own music bed. No stock footage or API key is needed.

```bash
pip install pillow numpy          # plus ffmpeg on PATH
python3 vox_video.py              # -> vox_sleep.mp4 (1920x1080, 30 fps)
python3 vox_video.py --preview 12 # save the frame at 12s as a PNG
```

To change the story, edit the scene functions and the `SCENES` list (each scene is `(function, seconds)`).
A rendered copy is included as `vox_sleep.mp4`.
