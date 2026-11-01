#!/usr/bin/env python3
"""Render a Vox-style animated explainer: "What if AI stopped working?"

Uses the drawing helpers from vox_video.py (paper texture, highlighter,
cards, easing) and adds a digital glitch effect plus a music drop-out at
the moment the AI "switches off".

Usage:
    python3 vox_ai_video.py                    # -> vox_ai.mp4 (1920x1080, 30 fps)
    python3 vox_ai_video.py --preview 12       # save the frame at 12s as a PNG

Requirements: Python 3.8+, Pillow, numpy and ffmpeg on PATH.
"""
import argparse
import math
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image

import vox_video as v
from vox_video import (CARD, GRID, HL, INK, MUTED, PAPER, RED, SHADOW, TEAL, Canvas, card, ease_back,
                       ease_out, fade, font, header, highlight, mix, person, prog, rise_text, source, tw)

FPS, W, H, S, TRANS = v.FPS, v.W, v.H, v.S, v.TRANS
GREEN = (52, 150, 84)
v.FONT_FILES["sym"] = ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]

TITLE_GLITCH = 3.6  # local time in the title scene when the chip flickers off
SWITCH_OFF = 5.0    # local time in the "everywhere" scene when everything goes dark


# ---------------------------------------------------------------- scenes

def chip(c, x, y, size, on):
    body = mix(MUTED, INK, on)
    half = size / 2
    for k in range(4):
        off = -half * 0.6 + k * size * 0.4
        for (ax, ay, bx, by) in [(x + off, y - half, x + off, y - half - 26),
                                 (x + off, y + half, x + off, y + half + 26),
                                 (x - half, y + off, x - half - 26, y + off),
                                 (x + half, y + off, x + half + 26, y + off)]:
            c.line([(ax, ay), (bx, by)], body, 10)
    c.rect(x - half, y - half, x + half, y + half, fill=body, r=22)
    c.rect(x - half + 18, y - half + 18, x + half - 18, y + half - 18, outline=mix(GRID, HL, on), w=4, r=12)
    c.text(x, y + 26, "AI", font("sans", 74), mix((150, 140, 125), HL, on), "ms")


def scene_title(c, t):
    pc = ease_back(prog(t, 0.2, 0.7))
    if pc > 0:
        if t < TITLE_GLITCH:
            on = 1.0
        elif t < TITLE_GLITCH + 0.5:
            on = float(int(t * 22) % 2)
        else:
            on = 0.0
        chip(c, 960, 250, 150 * pc, on)
        # glow rings while it's on
        if t < TITLE_GLITCH:
            r = 120 + 30 * ((t * 0.9) % 1)
            c.circle(960, 250, r, outline=fade(HL, 1 - ((t * 0.9) % 1)), w=4)

    pk = prog(t, 0.5, 0.5)
    if pk > 0:
        f = font("sans", 30)
        label = "A THOUGHT EXPERIMENT"
        width = sum(tw(ch, f) + 6 for ch in label) - 6
        c.tracked(960 - width / 2, 420 + (1 - ease_out(pk)) * 15, label, f, fade(RED, pk), spacing=6)

    big = font("serif", 130)
    rise_text(c, t, 0.7, 960, 600, "What if AI", big, INK, anchor="ms", dist=40)
    w1, w2 = tw("stopped ", big), tw("working?", big)
    x0 = 960 - (w1 + w2) / 2
    p2 = prog(t, 0.95, 0.5)
    if p2 > 0:
        highlight(c, x0 + w1 - 6, 680, x0 + w1 + w2 + 10, 772, prog(t, 1.6, 0.6))
        y = 755 + (1 - ease_out(p2)) * 40
        c.text(x0, y, "stopped ", big, fade(INK, p2), "ls")
        c.text(x0 + w1, y, "working?", big, fade(INK, p2), "ls")
    rise_text(c, t, 2.2, 960, 870, "Not a disaster movie. Just a normal Tuesday, without the algorithms.",
              font("sansr", 38), MUTED, anchor="ms")


TILES = [
    ("⚑", "Maps & traffic"),
    ("✉", "Spam filters"),
    ("$", "Card fraud checks"),
    ("A⇄Ж", "Translation"),
    ("★", "Recommendations"),
    ("❝", "Voice assistants"),
    ("☂", "Weather forecasts"),
    ("⚕", "Medical scans"),
]


def scene_everywhere(c, t):
    header(c, t, "AI is already everywhere", "Right now")
    tw_, th, gap = 380, 250, 40
    x_start = (W - (4 * tw_ + 3 * gap)) / 2
    for k, (glyph, label) in enumerate(TILES):
        row, col = divmod(k, 4)
        x = x_start + col * (tw_ + gap)
        y = 290 + row * (th + 50)
        pa = ease_back(prog(t, 0.6 + k * 0.12, 0.5))
        if pa <= 0:
            continue
        y += (1 - pa) * 80
        card(c, x, y, tw_, th, min(1, pa))
        off = prog(t, SWITCH_OFF + 0.15 + k * 0.05, 0.12)
        icon = mix(TEAL, (190, 180, 162), off)
        c.text(x + tw_ / 2, y + 140, glyph, font("sym", 84 if len(glyph) == 1 else 60), icon, "ms")
        c.text(x + tw_ / 2, y + 210, label, font("sans", 30), mix(INK, MUTED, off), "ms")
        pill = mix(GREEN, RED, off)
        c.rect(x + tw_ - 96, y + 20, x + tw_ - 20, y + 54, fill=pill, r=17)
        c.text(x + tw_ - 58, y + 46, "OFF" if off > 0.5 else "ON", font("sans", 22), CARD, "ms")
    f = font("sansr", 40)
    p_before = prog(t, 2.0, 0.5) * (1 - prog(t, SWITCH_OFF, 0.2))
    if p_before > 0:
        c.text(960, 950, "Most of it works quietly in the background.", f, fade(INK, p_before), "ms")
    rise_text(c, t, SWITCH_OFF + 0.9, 960, 950, "Now imagine it all switched off. At once.", f, RED,
              anchor="ms")


TIMELINE = [
    ("Minute 1", "Chatbots and voice assistants go quiet", "Customer-service lines suddenly get very long"),
    ("Hour 1", "Maps lose live traffic", "Deliveries and ride-hailing slow to a crawl"),
    ("Hour 6", "Inboxes flood with spam", "Scams and phishing slip straight through"),
    ("Day 1", "Banks check payments by hand", "Card purchases get delayed or declined"),
]


def scene_timeline(c, t):
    header(c, t, "The first day without AI", "A thought experiment")
    lx, top, step = 320, 320, 160
    bottom = top + step * (len(TIMELINE) - 1)
    pl = ease_out(prog(t, 0.4, 1.2 + len(TIMELINE) * 1.4))
    c.line([(lx, top - 30), (lx, top - 30 + (bottom - top + 60) * pl)], GRID, 6)
    for i, (when, main, sub) in enumerate(TIMELINE):
        y = top + i * step
        st = 0.8 + i * 1.6
        pd = ease_back(prog(t, st, 0.4))
        if pd > 0:
            c.circle(lx, y, 22 * pd, fill=RED)
            c.circle(lx, y, 9 * pd, fill=CARD)
        rise_text(c, t, st, lx - 50, y + 12, when, font("sans", 34), RED, anchor="rs")
        rise_text(c, t, st + 0.15, lx + 60, y + 14, main, font("serif", 54), INK, anchor="ls")
        rise_text(c, t, st + 0.3, lx + 62, y + 58, sub, font("sansr", 32), MUTED, anchor="ls")
    rise_text(c, t, 8.0, 120, 1010, "An illustration of likely effects, not a prediction.",
              font("sansr", 24), MUTED)


SPAM = set(np.random.default_rng(11).permutation(100)[:45].tolist())


def envelope(c, x, y, fill, p):
    if p <= 0:
        return
    w, h = 54 * p, 38 * p
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=fill, outline=INK, w=3, r=4)
    c.line([(x - w / 2 + 3, y - h / 2 + 3), (x, y + 2 * p), (x + w / 2 - 3, y - h / 2 + 3)], INK, 3, caps=False)


def scene_spam(c, t):
    header(c, t, "Your inbox would be the first to notice", "Example")
    big = font("serif", 190)
    pn = prog(t, 0.5, 0.5)
    if pn > 0:
        highlight(c, 112, 360, 130 + tw("~45%", big), 440, prog(t, 1.1, 0.6))
        c.text(120, 440 + (1 - ease_out(pn)) * 30, "~45%", big, fade(INK, pn), "ls")
    f = font("sansr", 46)
    for i, line in enumerate(["of all email sent", "worldwide is spam"]):
        rise_text(c, t, 1.0 + i * 0.15, 124, 540 + i * 64, line, f, INK)
    rise_text(c, t, 3.2, 124, 720, "AI filters catch almost all of it.", font("sans", 38), TEAL)
    rise_text(c, t, 5.2, 124, 780, "Without them, it all lands in your inbox.", font("sans", 38), RED)
    for i in range(100):
        row, col = divmod(i, 10)
        x = 1040 + col * 76
        y = 300 + row * 66
        pa = ease_back(prog(t, 0.7 + i * 0.012, 0.3))
        turn = prog(t, 2.2 + (i % 17) * 0.04, 0.25) if i in SPAM else 0
        # spam envelopes fade back to paper while filters work, return red when they stop
        hidden = prog(t, 3.4, 0.4) * (1 - prog(t, 5.4, 0.3)) if i in SPAM else 0
        fill = mix(CARD, RED, turn)
        if hidden > 0:
            fill = mix(fill, PAPER, hidden)
        envelope(c, x, y, fill, pa * (1 - 0.6 * hidden))
    source(c, t, "Kaspersky, Spam and phishing report 2023 (45.6% of email traffic)", start=1.5)


def map_icon(c, x, y, p):
    pts = [(-110, -60), (-40, -80), (40, -60), (110, -80), (110, 60), (40, 80), (-40, 60), (-110, 80)]
    pts = [(x + a * p, y + b * p) for a, b in pts]
    shades = [(225, 214, 190), (240, 232, 214), (225, 214, 190)]
    for k in range(3):
        a, b = pts[k], pts[k + 1]
        d, e = pts[6 - k], pts[7 - k]
        c.poly([a, b, d, e], shades[k])
    c.line([(x - 80 * p, y + 30 * p), (x - 20 * p, y - 10 * p), (x + 30 * p, y + 20 * p), (x + 70 * p, y - 30 * p)],
           RED, 6)
    c.circle(x + 70 * p, y - 30 * p, 14 * p, fill=RED)


def clipboard_icon(c, x, y, p):
    c.rect(x - 75 * p, y - 90 * p, x + 75 * p, y + 90 * p, fill=CARD, outline=INK, w=6, r=12)
    c.rect(x - 35 * p, y - 104 * p, x + 35 * p, y - 76 * p, fill=INK, r=8)
    for k in range(3):
        yy = y - 40 * p + k * 45 * p
        c.line([(x - 50 * p, yy), (x - 38 * p, yy + 12 * p), (x - 18 * p, yy - 12 * p)], TEAL, 6)
        c.line([(x - 2 * p, yy), (x + 52 * p, yy)], INK, 6)


BACKUPS = [
    (map_icon, "Paper maps", ["Slower, but they", "never lose signal"]),
    (None, "Human experts", ["Translators, doctors and", "analysts still do this work"]),
    (clipboard_icon, "Manual backups", ["Banks, airports and hospitals", "keep paper procedures"]),
]


def scene_backup(c, t):
    header(c, t, "We would slow down, not stop", "The good news")
    cw, ch, gap = 500, 480, 70
    x_start = (W - (3 * cw + 2 * gap)) / 2
    for i, (icon, title, lines) in enumerate(BACKUPS):
        pa = ease_back(prog(t, 0.6 + i * 0.45, 0.6))
        if pa <= 0:
            continue
        x = x_start + i * (cw + gap)
        y = 290 + (1 - pa) * 120
        card(c, x, y, cw, ch, min(1, pa))
        pi = ease_back(prog(t, 0.9 + i * 0.45, 0.5))
        if pi > 0:
            if icon is None:
                person(c, x + cw / 2 - 45, y + 175, TEAL, 1.6 * pi)
                person(c, x + cw / 2 + 45, y + 175, INK, 1.6 * pi)
            else:
                icon(c, x + cw / 2, y + 160, pi)
        c.text(x + cw / 2, y + 340, title, font("serif", 54), INK, "ms")
        for k, line in enumerate(lines):
            c.text(x + cw / 2, y + 392 + k * 38, line, font("sansr", 28), MUTED, "ms")
    rise_text(c, t, 3.2, 960, 945, "Most AI speeds up jobs that people already know how to do.",
              font("sansr", 40), INK, anchor="ms")


LESSONS = [
    ("Keep human skills sharp", "know how to do it without the app"),
    ("Have an offline plan", "paper copies of key numbers, maps and documents"),
    ("Don't let one system run everything", "backups beat single points of failure"),
]


def scene_lesson(c, t):
    header(c, t, "The real lesson", "What it means for you")
    for i, (main, sub) in enumerate(LESSONS):
        y = 320 + i * 190
        st = 0.6 + i * 0.9
        pb = ease_back(prog(t, st, 0.4))
        if pb > 0:
            s = 44 * pb
            c.rect(190 - s, y - s, 190 + s, y + s, outline=INK, w=7, r=10)
        pc = prog(t, st + 0.35, 0.35)
        if pc > 0:
            pts = [(166, y + 2), (186, y + 24), (230, y - 34)]
            seg1 = min(1, pc * 2)
            draw = [pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1, pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)]
            if pc > 0.5:
                seg2 = (pc - 0.5) * 2
                draw.append((pts[1][0] + (pts[2][0] - pts[1][0]) * seg2, pts[1][1] + (pts[2][1] - pts[1][1]) * seg2))
            c.line(draw, RED, 13)
        rise_text(c, t, st + 0.15, 290, y + 2, main, font("serif", 58), INK, anchor="ls")
        rise_text(c, t, st + 0.3, 292, y + 48, sub, font("sansr", 32), MUTED, anchor="ls")
    pf = prog(t, 4.2, 0.6)
    if pf > 0:
        f = font("serif", 64)
        txt = "Use AI. Don't depend on it."
        w = tw(txt, f)
        highlight(c, 1700 - w - 10, 902, 1712, 966, prog(t, 4.6, 0.6))
        c.text(1700, 950, txt, f, fade(INK, pf), "rs")


SCENES = [
    (scene_title, 6.0),
    (scene_everywhere, 8.5),
    (scene_timeline, 10.0),
    (scene_spam, 8.5),
    (scene_backup, 8.0),
    (scene_lesson, 7.5),
]

STARTS = []
_s = 0.0
for _, _d in SCENES:
    STARTS.append(_s)
    _s += _d - TRANS
TOTAL = _s + TRANS
GLITCHES = [(TITLE_GLITCH, 0.5), (STARTS[1] + SWITCH_OFF, 0.5)]
MUTES = [(TITLE_GLITCH + 0.05, TITLE_GLITCH + 0.45), (STARTS[1] + SWITCH_OFF + 0.1, STARTS[1] + SWITCH_OFF + 1.8)]


# ---------------------------------------------------------------- rendering

def glitch(arr, g, seed):
    """RGB split + displaced horizontal slices + scanlines, strength g in 0..1."""
    rng = np.random.default_rng(seed)
    out = arr.copy()
    dx = int(6 + 18 * g)
    out[:, :, 0] = np.roll(arr[:, :, 0], dx, axis=1)
    out[:, :, 2] = np.roll(arr[:, :, 2], -dx, axis=1)
    for _ in range(int(4 + 10 * g)):
        y = int(rng.integers(0, H - 80))
        h = int(rng.integers(6, 80))
        out[y:y + h] = np.roll(out[y:y + h], int(rng.integers(-120, 120) * g), axis=1)
    out[::3] *= 1 - 0.25 * g
    return out


_tex = None


def render_frame(i):
    global _tex
    if _tex is None:
        _tex = v.make_textures()
    vignette, grains = _tex
    t = i / FPS
    img = Image.new("RGB", (W * S, H * S), PAPER)
    c = Canvas(img)
    idx = max(k for k, s in enumerate(STARTS) if t >= s)
    fn, dur = SCENES[idx]
    local = t - STARTS[idx]
    if idx + 1 < len(SCENES) and local > dur - TRANS:
        e = v.ease_in_out(prog(local, dur - TRANS, TRANS))
        c.dx = -W * e
        fn(c, local)
        c.dx = W * (1 - e)
        SCENES[idx + 1][0](c, local - (dur - TRANS))
    else:
        fn(c, local)
    img = img.resize((W, H), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) * vignette + grains[0]
    for g0, gd in GLITCHES:
        if g0 <= t < g0 + gd:
            p = (t - g0) / gd
            strength = math.sin(math.pi * p) * (0.6 + 0.4 * ((i * 7919) % 5) / 4)
            arr = glitch(arr, strength, i)
    fio = min(prog(t, 0, 0.4), prog(TOTAL - t, 0, 0.6))
    if fio < 1:
        arr = arr * fio
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def make_audio(path):
    chords = [[57, 60, 64], [52, 55, 59], [53, 57, 60], [50, 53, 57]]  # Am Em F Dm
    v.make_music(path, TOTAL, chords=chords, starts=STARTS[1:], mute=MUTES)
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
    pcm = pcm.copy()
    # electric "power-down" buzz at each glitch
    for g0, _ in GLITCHES:
        n = int(0.7 * sr)
        tt = np.arange(n) / sr
        freq = 180 * np.exp(-tt * 3) + 40
        phase = 2 * np.pi * np.cumsum(freq) / sr
        saw = 2 * ((phase / (2 * np.pi)) % 1) - 1
        buzz = 0.35 * saw * np.exp(-tt * 4) * (1 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * tt)))
        a = int(g0 * sr)
        pcm[a:a + n] += buzz[:len(pcm) - a]
    pcm /= max(1e-6, np.abs(pcm).max()) / 0.85
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="vox_ai.mp4")
    ap.add_argument("--preview", type=float, help="render only the frame at this second to a PNG")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    if args.preview is not None:
        out = os.path.splitext(args.output)[0] + f"_{args.preview:.1f}s.png"
        Image.frombytes("RGB", (W, H), render_frame(int(args.preview * FPS))).save(out)
        print("saved", out)
        return
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    frames = int(TOTAL * FPS)
    tmp = tempfile.mkdtemp()
    try:
        audio = os.path.join(tmp, "music.wav")
        make_audio(audio)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
               "-movflags", "+faststart", args.output]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with mp.Pool(args.workers) as pool:
            for k, data in enumerate(pool.imap(render_frame, range(frames), chunksize=4)):
                ff.stdin.write(data)
                if k % (FPS * 5) == 0:
                    print(f"rendering {k / FPS:5.1f}s / {TOTAL:.1f}s", flush=True)
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
        print(f"saved {args.output} ({TOTAL:.1f}s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
