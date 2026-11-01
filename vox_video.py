#!/usr/bin/env python3
"""Render a Vox-style animated explainer video: "Why your brain needs sleep".

Everything is drawn in code: cream paper texture, bold headlines,
highlighter swipes, animated charts, cut-paper cards and a generated
music bed. No stock footage, API keys or internet access are needed.

Usage:
    python3 vox_video.py                     # -> vox_sleep.mp4 (1920x1080, 30 fps)
    python3 vox_video.py -o out.mp4 --preview 12.5   # save one frame as PNG instead

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
from PIL import Image, ImageDraw, ImageFont

FPS = 30
W, H = 1920, 1080
S = 2  # supersampling factor: draw at 2x, downscale for smooth edges
TRANS = 0.6  # seconds for the slide transition between scenes

# Palette
PAPER = (243, 235, 221)
INK = (30, 30, 30)
MUTED = (128, 118, 102)
GRID = (222, 211, 192)
HL = (255, 222, 60)  # highlighter yellow
RED = (226, 64, 52)
TEAL = (38, 140, 128)
BLUE = (60, 96, 170)
CARD = (255, 251, 243)
SHADOW = (205, 193, 172)

FONT_DIRS = [
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/truetype/dejavu/",
    "/Library/Fonts/",
    "C:/Windows/Fonts/",
]
FONT_FILES = {
    "serif": ["LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", "georgiab.ttf"],
    "sans": ["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"],
    "sansr": ["LiberationSans-Regular.ttf", "DejaVuSans.ttf", "arial.ttf"],
}
_font_cache = {}


def font(kind, size):
    key = (kind, size)
    if key not in _font_cache:
        for name in FONT_FILES[kind]:
            for d in FONT_DIRS:
                p = os.path.join(d, name)
                if os.path.exists(p):
                    _font_cache[key] = ImageFont.truetype(p, int(size * S))
                    break
            if key in _font_cache:
                break
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ---------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_back(p):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def mix(c1, c2, p):
    """Blend colour c1 -> c2 by p (used for fades over the flat paper)."""
    return tuple(int(a + (b - a) * p) for a, b in zip(c1, c2))


def fade(color, p):
    return mix(PAPER, color, clamp(p))


# ---------------------------------------------------------------- canvas

class Canvas:
    """Thin wrapper around ImageDraw that takes 1080p coordinates."""

    def __init__(self, img):
        self.d = ImageDraw.Draw(img)
        self.dx = 0.0

    def p(self, x, y):
        return ((x + self.dx) * S, y * S)

    def rect(self, x0, y0, x1, y1, fill=None, r=0, outline=None, w=0):
        a, b = self.p(x0, y0), self.p(x1, y1)
        box = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            return
        r = min(r * S, (box[2] - box[0]) / 2, (box[3] - box[1]) / 2)
        self.d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=int(w * S))

    def circle(self, x, y, r, fill=None, outline=None, w=0):
        if r <= 0:
            return
        cx, cy = self.p(x, y)
        self.d.ellipse([cx - r * S, cy - r * S, cx + r * S, cy + r * S],
                       fill=fill, outline=outline, width=int(w * S))

    def line(self, pts, fill, w, caps=True):
        if len(pts) < 2:
            return
        sp = [self.p(x, y) for x, y in pts]
        self.d.line(sp, fill=fill, width=int(w * S), joint="curve")
        if caps:
            for x, y in (pts[0], pts[-1]):
                self.circle(x, y, w / 2, fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([self.p(x, y) for x, y in pts], fill=fill)

    def text(self, x, y, txt, fnt, fill, anchor="la"):
        self.d.text(self.p(x, y), txt, font=fnt, fill=fill, anchor=anchor)

    def tracked(self, x, y, txt, fnt, fill, spacing=4):
        """Letter-spaced text (left aligned)."""
        for ch in txt:
            self.text(x, y, ch, fnt, fill)
            x += tw(ch, fnt) + spacing


def tw(txt, fnt):
    return fnt.getlength(txt) / S


def highlight(c, x0, y0, x1, y1, p, color=HL):
    """Marker swipe that grows left -> right with slightly uneven edges."""
    if p <= 0:
        return
    xe = x0 + (x1 - x0) * ease_out(p)
    c.poly([(x0 - 8, y0 + 6), (xe, y0), (xe + 6, y1 - 3), (x0 - 2, y1 + 4)], color)


def rise_text(c, t, start, x, y, txt, fnt, color, anchor="la", dist=24, dur=0.5):
    p = prog(t, start, dur)
    if p <= 0:
        return
    c.text(x, y + (1 - ease_out(p)) * dist, txt, fnt, fade(color, p), anchor)


def header(c, t, txt, kicker):
    """Scene title in the top-left with a red kicker label."""
    c.tracked(120, 82, kicker.upper(), font("sans", 26), RED, spacing=5)
    c.text(120, 122, txt, font("serif", 62), INK)
    c.rect(120, 210, 220, 216, fill=INK)


def source(c, t, txt, start=1.0):
    p = prog(t, start, 0.6)
    if p > 0:
        c.text(120, 1010, "Source: " + txt, font("sansr", 24), fade(MUTED, p))


# ---------------------------------------------------------------- scenes

def scene_title(c, t):
    # moon with a bite taken out (paper-coloured circle over a yellow one)
    pm = ease_back(prog(t, 0.2, 0.7))
    if pm > 0:
        r = 95 * pm
        c.circle(960, 250, r, fill=HL)
        c.circle(960 + 42 * pm, 225, r * 0.86, fill=PAPER)
    for i, (sx, sy) in enumerate([(820, 190), (1110, 170), (1150, 320), (780, 330), (1040, 110)]):
        ps = prog(t, 0.6 + i * 0.12, 0.3)
        if ps > 0:
            tw_ = 0.6 + 0.4 * math.sin(t * 4 + i * 1.7)
            r = 9 * ease_back(ps) * tw_
            c.poly([(sx, sy - r * 2), (sx + r * 0.5, sy), (sx, sy + r * 2), (sx - r * 0.5, sy)], INK)
            c.poly([(sx - r * 2, sy), (sx, sy - r * 0.5), (sx + r * 2, sy), (sx, sy + r * 0.5)], INK)

    pk = prog(t, 0.5, 0.5)
    if pk > 0:
        f = font("sans", 30)
        label = "EXPLAINED"
        width = sum(tw(ch, f) + 6 for ch in label) - 6
        c.tracked(960 - width / 2, 420 + (1 - ease_out(pk)) * 15, label, f, fade(RED, pk), spacing=6)

    big = font("serif", 130)
    rise_text(c, t, 0.7, 960, 600, "Why your brain", big, INK, anchor="ms", dist=40)
    # second line: "needs sleep" with a highlight on "sleep"
    w1, w2 = tw("needs ", big), tw("sleep", big)
    x0 = 960 - (w1 + w2) / 2
    p2 = prog(t, 0.95, 0.5)
    if p2 > 0:
        highlight(c, x0 + w1 - 6, 680, x0 + w1 + w2 + 10, 772, prog(t, 1.6, 0.6))
        y = 755 + (1 - ease_out(p2)) * 40
        c.text(x0, y, "needs ", big, fade(INK, p2), "ls")
        c.text(x0 + w1, y, "sleep", big, fade(INK, p2), "ls")

    rise_text(c, t, 2.2, 960, 870, "and what happens when it doesn't get enough",
              font("sansr", 40), MUTED, anchor="ms")


def person(c, x, y, color, scale=1.0):
    if scale <= 0:
        return
    s = scale
    c.circle(x, y - 34 * s, 17 * s, fill=color)
    c.rect(x - 24 * s, y - 12 * s, x + 24 * s, y + 46 * s, fill=color, r=18 * s)


def scene_people(c, t):
    header(c, t, "A lot of us run on empty", "The problem")
    big = font("serif", 190)
    pn = prog(t, 0.5, 0.5)
    if pn > 0:
        highlight(c, 112, 360, 130 + tw("1 in 3", big), 440, prog(t, 1.1, 0.6))
        c.text(120, 440 + (1 - ease_out(pn)) * 30, "1 in 3", big, fade(INK, pn), "ls")
    f = font("sansr", 46)
    for i, line in enumerate(["adults don't get the", "7+ hours of sleep", "they need each night"]):
        rise_text(c, t, 1.0 + i * 0.15, 124, 540 + i * 64, line, f, INK)

    # 3 x 10 grid of people; every third one (randomised) turns red
    chosen = {1, 4, 8, 10, 13, 17, 20, 22, 26, 29}
    for i in range(30):
        row, col = divmod(i, 10)
        x = 1000 + col * 80
        y = 380 + row * 175
        ps = ease_back(prog(t, 0.8 + i * 0.045, 0.35))
        turn = prog(t, 3.0 + (i % 10) * 0.05, 0.3) if i in chosen else 0
        color = mix(INK, RED, turn)
        bump = 1 + 0.18 * math.sin(math.pi * turn)
        person(c, x, y, color, ps * bump)
    source(c, t, "U.S. Centers for Disease Control and Prevention (CDC)")


AGES = [
    ("Newborns", "0-3 months", 14, 17),
    ("Toddlers", "1-2 years", 11, 14),
    ("Kids", "6-13 years", 9, 11),
    ("Teens", "14-17 years", 8, 10),
    ("Adults", "18-64 years", 7, 9),
    ("Older adults", "65+ years", 7, 8),
]


def scene_chart(c, t):
    header(c, t, "How much sleep do you need?", "By age")
    x0, x1, hmax = 560, 1760, 18
    sx = (x1 - x0) / hmax
    top, step, bh = 300, 108, 54
    bottom = top + step * len(AGES) - 20
    pg = prog(t, 0.4, 0.6)
    for h in range(0, hmax + 1, 3):
        x = x0 + h * sx
        c.line([(x, top - 30), (x, top - 30 + (bottom - top + 30) * ease_out(pg))], GRID, 2, caps=False)
        if pg > 0:
            c.text(x, bottom + 40, f"{h}h", font("sansr", 26), fade(MUTED, pg), "ms")
    for i, (name, ages, lo, hi) in enumerate(AGES):
        y = top + i * step
        pl = prog(t, 0.6 + i * 0.12, 0.5)
        if pl <= 0:
            continue
        is_adult = name == "Adults"
        if is_adult:
            highlight(c, 112, y - 2, 140 + tw(name, font("sans", 36)), y + 40, prog(t, 4.2, 0.5))
        c.text(120, y + 30, name, font("sans", 36), fade(INK, pl), "ls")
        c.text(120, y + 62, ages, font("sansr", 24), fade(MUTED, pl), "ls")
        pb = ease_out(prog(t, 1.2 + i * 0.25, 0.8))
        if pb > 0:
            xa = x0 + lo * sx
            xb = xa + (hi - lo) * sx * pb
            color = RED if is_adult else TEAL
            # faint bar from 0 to the minimum, solid bar for the recommended range
            c.rect(x0, y + 8, x0 + (xa - x0) * pb, y + bh - 8, fill=mix(PAPER, color, 0.18), r=6)
            c.rect(xa, y, xb, y + bh, fill=color, r=10)
            pv = prog(t, 1.8 + i * 0.25, 0.4)
            if pv > 0:
                c.text(xb + 18, y + bh / 2 + 12, f"{lo}-{hi} h", font("sans", 32), fade(color, pv), "ls")
    source(c, t, "National Sleep Foundation recommendations", start=2.0)


STAGES = {"Awake": 300, "REM": 420, "Light": 560, "Deep": 720}
STAGE_COLOR = {"Awake": MUTED, "REM": RED, "Light": BLUE, "Deep": TEAL}
NIGHT = [
    ("Awake", 10), ("Light", 20), ("Deep", 40), ("Light", 10), ("REM", 10),
    ("Light", 25), ("Deep", 35), ("Light", 10), ("REM", 20),
    ("Light", 35), ("Deep", 15), ("Light", 10), ("REM", 30),
    ("Light", 45), ("REM", 45),
    ("Light", 40), ("REM", 40), ("Awake", 10),
]


def scene_cycles(c, t):
    header(c, t, "Sleep comes in 90-minute cycles", "Inside one night")
    x0, x1, total = 330, 1760, 480
    sx = (x1 - x0) / total
    pa = prog(t, 0.3, 0.5)
    for name, y in STAGES.items():
        if pa > 0:
            c.text(x0 - 40, y + 12, name, font("sans", 34), fade(STAGE_COLOR[name], pa), "rs")
            c.line([(x0, y), (x1, y)], fade(GRID, pa), 2, caps=False)
    for hr in range(0, 9):
        if pa > 0:
            c.text(x0 + hr * 60 * sx, 800, f"{hr}h", font("sansr", 26), fade(MUTED, pa), "ms")

    # dashed cycle dividers
    pd = prog(t, 5.2, 0.6)
    if pd > 0:
        for k in range(1, 6):
            x = x0 + (10 + 90 * k) * sx
            for yy in range(260, 760, 28):
                c.line([(x, yy), (x, yy + 14)], fade(INK, pd * 0.5), 3, caps=False)

    reveal = total * ease_in_out(prog(t, 0.8, 4.4))
    m = 0
    prev = None
    head = None
    for stage, dur in NIGHT:
        if m >= reveal:
            break
        y = STAGES[stage]
        a = x0 + m * sx
        b = x0 + min(m + dur, reveal) * sx
        if prev is not None and prev != y:
            c.line([(a, prev), (a, y)], INK, 4, caps=False)
        c.line([(a, y), (b, y)], STAGE_COLOR[stage], 12)
        head = (b, y)
        prev = y
        m += dur
    if head and reveal < total - 1:
        c.circle(head[0], head[1], 13, fill=INK)

    # annotations
    pn = prog(t, 5.8, 0.5)
    if pn > 0:
        xa, xb = x0 + 10 * sx, x0 + 100 * sx
        y = 250
        c.line([(xa, y + 20), (xa, y), (xb, y), (xb, y + 20)], fade(INK, pn), 4, caps=False)
        c.text((xa + xb) / 2, y - 14, "one cycle", font("sans", 28), fade(INK, pn), "ms")
    rise_text(c, t, 6.2, 330, 900, "Deep sleep repairs the body early in the night.",
              font("sansr", 36), TEAL)
    rise_text(c, t, 6.5, 330, 950, "REM sleep, when we dream, gets longer toward morning.",
              font("sansr", 36), RED)


def card(c, x, y, w, h, p):
    if p <= 0:
        return
    c.rect(x + 12, y + 14, x + w + 12, y + h + 14, fill=fade(SHADOW, p), r=24)
    c.rect(x, y, x + w, y + h, fill=fade(CARD, p), r=24)


def scene_drunk(c, t):
    header(c, t, "Staying awake too long is like being drunk", "Why it matters")
    cw, ch, cy = 600, 520, 300
    # left card: clock
    pl = ease_back(prog(t, 0.5, 0.6))
    if pl > 0:
        x = 200
        y = cy + (1 - pl) * 120
        card(c, x, y, cw, ch, min(1, pl))
        cx, cyy = x + cw / 2, y + 190
        c.circle(cx, cyy, 120, fill=INK)
        c.circle(cx, cyy, 106, fill=CARD)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            c.line([(cx + 88 * math.sin(a), cyy - 88 * math.cos(a)),
                    (cx + 98 * math.sin(a), cyy - 98 * math.cos(a))], INK, 5)
        spin = t * 2.2
        c.line([(cx, cyy), (cx + 75 * math.sin(spin), cyy - 75 * math.cos(spin))], RED, 8)
        c.line([(cx, cyy), (cx + 50 * math.sin(spin / 12), cyy - 50 * math.cos(spin / 12))], INK, 10)
        c.circle(cx, cyy, 10, fill=INK)
        c.text(cx, y + 410, "17 hours", font("serif", 70), INK, "ms")
        c.text(cx, y + 465, "without sleep", font("sansr", 34), MUTED, "ms")
    # right card: glass
    pr = ease_back(prog(t, 1.0, 0.6))
    if pr > 0:
        x = 1120
        y = cy + (1 - pr) * 120
        card(c, x, y, cw, ch, min(1, pr))
        gx, gt, gb = x + cw / 2, y + 80, y + 300
        fill = ease_out(prog(t, 1.5, 1.2))
        lt = gb - (gb - gt - 40) * fill
        half_top, half_bot = 85, 60

        def half(yv):
            return half_bot + (half_top - half_bot) * (gb - yv) / (gb - gt)
        if fill > 0:
            c.poly([(gx - half(lt), lt), (gx + half(lt), lt), (gx + half_bot, gb), (gx - half_bot, gb)],
                   (232, 170, 60))
            for k, (bx, by) in enumerate([(-20, 40), (18, 80), (-5, 120)]):
                yb = gb - ((t * 60 + by) % max(1, gb - lt - 10)) - 10
                c.circle(gx + bx, yb, 6, outline=CARD, w=3)
        c.line([(gx - half_top, gt), (gx - half_bot, gb), (gx + half_bot, gb), (gx + half_top, gt)],
               INK, 10)
        c.text(gx, y + 410, "0.05%", font("serif", 70), INK, "ms")
        c.text(gx, y + 465, "blood alcohol level", font("sansr", 34), MUTED, "ms")
    pe = ease_back(prog(t, 1.9, 0.5))
    if pe > 0:
        c.circle(960, cy + ch / 2, 62 * pe, fill=HL)
        c.text(960, cy + ch / 2 + 32 * pe, "≈", font("serif", int(96 * pe) or 1), INK, "ms")
    rise_text(c, t, 3.0, 960, 935, "Reaction time and accuracy fall to similar levels.",
              font("sansr", 40), INK, anchor="ms")
    source(c, t, "Williamson & Feyer, Occupational and Environmental Medicine (2000)", start=3.2)


TIPS = [
    ("Keep the same bedtime", "even on weekends"),
    ("Make your room dark, cool and quiet", "around 18°C / 65°F is ideal for most people"),
    ("Put screens away an hour before bed", "bright light tells your brain it's daytime"),
]


def scene_tips(c, t):
    header(c, t, "Three ways to sleep better", "What you can do")
    for i, (main, sub) in enumerate(TIPS):
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
            pts_draw = [pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1,
                                 pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)]
            if pc > 0.5:
                seg2 = (pc - 0.5) * 2
                pts_draw.append((pts[1][0] + (pts[2][0] - pts[1][0]) * seg2,
                                 pts[1][1] + (pts[2][1] - pts[1][1]) * seg2))
            c.line(pts_draw, RED, 13)
        rise_text(c, t, st + 0.15, 290, y + 2, main, font("serif", 58), INK, anchor="ls")
        rise_text(c, t, st + 0.3, 292, y + 48, sub, font("sansr", 32), MUTED, anchor="ls")
    pf = prog(t, 4.2, 0.6)
    if pf > 0:
        f = font("serif", 64)
        w = tw("Sleep well.", f)
        highlight(c, 1700 - w - 10, 902, 1712, 966, prog(t, 4.6, 0.6))
        c.text(1700, 950, "Sleep well.", f, fade(INK, pf), "rs")


SCENES = [
    (scene_title, 5.0),
    (scene_people, 6.5),
    (scene_chart, 8.0),
    (scene_cycles, 9.0),
    (scene_drunk, 7.5),
    (scene_tips, 7.0),
]


def timeline():
    starts, s = [], 0.0
    for _, dur in SCENES:
        starts.append(s)
        s += dur - TRANS
    return starts, s + TRANS


STARTS, TOTAL = timeline()


# ---------------------------------------------------------------- frame rendering

def make_textures():
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vignette = (1 - 0.10 * np.clip(d - 0.35, 0, None) ** 1.6)[..., None]
    # paper fibres: blurred low-frequency noise + fine grain
    low = rng.normal(0, 1, (H // 8, W // 8)).astype(np.float32)
    low = np.array(Image.fromarray(low).resize((W, H), Image.BICUBIC))
    grains = [(low * 3 + rng.normal(0, 4, (H, W)).astype(np.float32))[..., None] for _ in range(3)]
    return vignette, grains


_tex = None


def render_frame(i):
    global _tex
    if _tex is None:
        _tex = make_textures()
    vignette, grains = _tex
    t = i / FPS
    img = Image.new("RGB", (W * S, H * S), PAPER)
    c = Canvas(img)
    # find the active scene(s)
    idx = max(k for k, s in enumerate(STARTS) if t >= s)
    fn, dur = SCENES[idx]
    local = t - STARTS[idx]
    nxt = idx + 1 < len(SCENES) and local > dur - TRANS
    if nxt:
        e = ease_in_out(prog(local, dur - TRANS, TRANS))
        c.dx = -W * e
        fn(c, local)
        c.dx = W * (1 - e)
        SCENES[idx + 1][0](c, local - (dur - TRANS))
    else:
        fn(c, local)
    img = img.resize((W, H), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) * vignette + grains[0]
    # global fade in/out
    fio = min(prog(t, 0, 0.4), prog(TOTAL - t, 0, 0.6))
    if fio < 1:
        arr = arr * fio  # fade from/to black
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


# ---------------------------------------------------------------- audio

def make_music(path, seconds, sr=44100):
    """Soft pad + plucked arpeggio + whooshes on each scene transition."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = np.zeros(n, np.float32)
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    bar = 2.4
    for k in range(int(seconds / bar) + 1):
        ch = chords[k % 4]
        a, b = int(k * bar * sr), min(n, int((k + 1) * bar * sr + 0.6 * sr))
        if a >= n:
            break
        tt = t[a:b] - k * bar
        env = np.minimum(1, tt / 0.5) * np.exp(-np.maximum(0, tt - bar) / 0.25)
        for m in ch:
            f = note(m)
            out[a:b] += 0.05 * env * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt))
        out[a:b] += 0.06 * env * np.sin(2 * np.pi * note(ch[0] - 12) * tt)
        # arpeggio, 8th notes
        arp = ch + [ch[1] + 12]
        for j in range(8):
            s0 = a + int(j * bar / 8 * sr)
            s1 = min(n, s0 + int(0.6 * sr))
            if s0 >= n:
                break
            ta = t[s0:s1] - t[s0]
            f = note(arp[j % 4] + 12)
            out[s0:s1] += 0.035 * np.exp(-ta * 7) * np.sin(2 * np.pi * f * ta) * (1 + 0.3 * np.sin(2 * np.pi * 2 * f * ta))
    rng = np.random.default_rng(3)
    for s in STARTS[1:]:
        a, b = int((s + 0.0) * sr), min(n, int((s + TRANS + 0.2) * sr))
        L = b - a
        noise = rng.normal(0, 1, L).astype(np.float32)
        # crude band-limited whoosh: running average with sweeping window
        noise = np.convolve(noise, np.ones(24) / 24, mode="same")
        env = np.sin(np.linspace(0, np.pi, L)) ** 2
        out[a:b] += 0.25 * env * noise
    fade_n = int(1.5 * sr)
    out[:int(0.5 * sr)] *= np.linspace(0, 1, int(0.5 * sr))
    out[-fade_n:] *= np.linspace(1, 0, fade_n)
    out /= max(1e-6, np.abs(out).max()) / 0.8
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="vox_sleep.mp4")
    ap.add_argument("--preview", type=float, help="render only the frame at this second to a PNG")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    if not shutil.which("ffmpeg") and args.preview is None:
        sys.exit("ffmpeg not found on PATH")

    if args.preview is not None:
        out = os.path.splitext(args.output)[0] + f"_{args.preview:.1f}s.png"
        frame = render_frame(int(args.preview * FPS))
        Image.frombytes("RGB", (W, H), frame).save(out)
        print("saved", out)
        return

    frames = int(TOTAL * FPS)
    tmp = tempfile.mkdtemp()
    try:
        audio = os.path.join(tmp, "music.wav")
        make_music(audio, TOTAL)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
               "-movflags", "+faststart", args.output]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with mp.Pool(args.workers) as pool:
            for k, data in enumerate(pool.imap(render_frame, range(frames), chunksize=4)):
                ff.stdin.write(data)
                if k % FPS == 0:
                    print(f"\rrendering {k / FPS:5.1f}s / {TOTAL:.1f}s", end="", flush=True)
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
        print(f"\nsaved {args.output} ({TOTAL:.1f}s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
