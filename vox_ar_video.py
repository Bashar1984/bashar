#!/usr/bin/env python3
"""Render a 2-minute Arabic (Egyptian) Vox-style explainer:
"هل نخاف من الذكاء الاصطناعي؟" (the harms of AI and why people fear it).

The narration is shown as right-to-left captions, timed for a voiceover.
Record the script yourself (or with any TTS) and pass it with --voice to
mix it over the music.

Usage:
    python3 vox_ar_video.py                          # -> vox_ar_fear.mp4
    python3 vox_ar_video.py --voice narration.mp3    # mix in a voiceover
    python3 vox_ar_video.py --preview 30             # one frame as PNG
    python3 vox_ar_video.py --captions               # print caption timings

Requirements: Python 3.8+, Pillow built with libraqm, numpy and ffmpeg.
Fonts (Cairo, Noto Kufi Arabic; SIL Open Font License) live in ./fonts.
"""
import argparse
import math
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFont

import vox_video as v
from vox_ai_video import add_buzz, glitch
from vox_video import (CARD, GRID, HL, INK, MUTED, PAPER, RED, TEAL, Canvas, card, ease_back, ease_out, fade,
                       font, highlight, mix, person, prog)

FPS, W, H, S, TRANS = v.FPS, v.W, v.H, v.S, v.TRANS
GREEN = (52, 150, 84)
SCREEN = (54, 54, 62)
HERE = os.path.dirname(os.path.abspath(__file__))
AR_FONTS = {
    "bold": ("Cairo.ttf", 800),
    "reg": ("Cairo.ttf", 500),
    "head": ("NotoKufiArabic.ttf", 800),
}
_ar_cache = {}


def af(kind, size):
    key = (kind, size)
    if key not in _ar_cache:
        name, weight = AR_FONTS[kind]
        f = ImageFont.truetype(os.path.join(HERE, "fonts", name), int(size * S),
                               layout_engine=ImageFont.Layout.RAQM)
        try:
            axes = f.get_variation_axes()
            f.set_variation_by_axes([weight if a["name"] in (b"Weight", "Weight") else a["default"] for a in axes])
        except OSError:
            pass
        _ar_cache[key] = f
    return _ar_cache[key]


def ar(c, x, y, txt, f, color, anchor="rs"):
    c.d.text(c.p(x, y), txt, font=f, fill=color, anchor=anchor, direction="rtl", language="ar")


def atw(txt, f):
    return f.getlength(txt, direction="rtl", language="ar") / S


def ar_rise(c, t, start, x, y, txt, f, color, anchor="rs", dist=24, dur=0.5):
    p = prog(t, start, dur)
    if p > 0:
        ar(c, x, y + (1 - ease_out(p)) * dist, txt, f, fade(color, p), anchor)


def ar_header(c, title, kicker):
    ar(c, 1800, 112, kicker, af("bold", 30), RED)
    ar(c, 1800, 190, title, af("head", 54), INK)
    c.rect(1700, 228, 1800, 234, fill=INK)


def ar_source(c, t, txt, start=1.0):
    p = prog(t, start, 0.6)
    if p > 0:
        ar(c, 120, 112, "المصدر: " + txt, af("reg", 24), fade(MUTED, p), "ls")


def wrap(txt, f, width):
    lines, cur = [], ""
    for word in txt.split():
        trial = (cur + " " + word).strip()
        if cur and atw(trial, f) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def captions(c, t, caps):
    for s, e, txt in caps:
        if s <= t < e:
            p = prog(t, s, 0.25) * (1 - prog(t, e - 0.25, 0.25))
            f = af("bold", 40)
            lines = wrap(txt, f, 1500)
            top = 1025 - 60 * (len(lines) - 1)
            c.rect(150, top - 72, 1770, 1052, fill=fade(mix(PAPER, CARD, 0.75), p), r=18)
            for k, line in enumerate(lines):
                ar(c, 960, top + k * 60, line, f, fade(INK, p), "ms")


def stamp(c, x, y, txt, p, size=34, color=RED):
    """Red rubber-stamp label centred on (x, y)."""
    if p <= 0:
        return
    s = 0.6 + 0.4 * ease_back(p)
    f = af("bold", int(size * s) or 1)
    w = atw(txt, f) + 40 * s
    h = size * 1.7 * s
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=fade(CARD, p), outline=fade(color, p), w=5, r=10)
    ar(c, x, y + size * 0.42 * s, txt, f, fade(color, p), "ms")


# ---------------------------------------------------------------- scenes

CALL_GLITCH = 11.5
CALL_NAMES = ["المدير المالي", "زميلة من الحسابات", "زميل من الإدارة", "إنت"]
CALL_COLORS = [(232, 170, 60), (120, 170, 210), (200, 120, 150), (150, 190, 120)]


def scene_call(c, t):
    x0, x1, y0, y1 = 330, 1590, 120, 880
    pw = ease_back(prog(t, 0.1, 0.6))
    if pw <= 0:
        return
    yo = (1 - pw) * 100
    card(c, x0, y0 + yo, x1 - x0, y1 - y0, min(1, pw))
    c.rect(x0, y0 + yo, x1, y0 + yo + 56, fill=INK, r=24)
    c.rect(x0, y0 + yo + 30, x1, y0 + yo + 56, fill=INK)
    for k, col in enumerate([RED, HL, GREEN]):
        c.circle(x0 + 36 + k * 30, y0 + yo + 28, 9, fill=col)
    ar(c, x1 - 30, y0 + yo + 38, "اجتماع الإدارة المالية", af("bold", 24), CARD)
    tw_, th = 600, 317
    fake = prog(t, CALL_GLITCH + 0.3, 0.4)
    for k in range(4):
        row, col = divmod(k, 2)
        tx = x1 - 20 - (col + 1) * tw_ - col * 20
        ty = y0 + yo + 76 + row * (th + 20)
        pt = ease_out(prog(t, 0.5 + k * 0.2, 0.4))
        if pt <= 0:
            continue
        c.rect(tx, ty, tx + tw_, ty + th, fill=mix(CARD, SCREEN, pt), r=14)
        is_fake = k < 3
        color = mix(CALL_COLORS[k], (96, 96, 104), fake if is_fake else 0)
        person(c, tx + tw_ / 2, ty + th / 2 + 10, color, 2.0 * pt)
        f = af("bold", 22)
        nw = atw(CALL_NAMES[k], f)
        c.rect(tx + tw_ - nw - 44, ty + th - 54, tx + tw_ - 16, ty + th - 16, fill=(30, 30, 34), r=10)
        ar(c, tx + tw_ - 30, ty + th - 27, CALL_NAMES[k], f, CARD)
        if k == 0 and t < CALL_GLITCH:  # speaking indicator
            pulse = 0.5 + 0.5 * math.sin(t * 6)
            c.rect(tx, ty, tx + tw_, ty + th, outline=mix(SCREEN, GREEN, pulse), w=6, r=14)
        if is_fake:
            stamp(c, tx + tw_ / 2, ty + 60, "مزيّف", prog(t, CALL_GLITCH + 0.6 + k * 0.35, 0.35), 34)
    # bank transfer overlay
    pt = ease_back(prog(t, 5.6, 0.5)) * (1 - prog(t, CALL_GLITCH - 0.1, 0.1))
    if pt > 0:
        bx0, bx1, by0, by1 = 560, 1360, 690 + (1 - pt) * 60, 850 + (1 - pt) * 60
        card(c, bx0, by0, bx1 - bx0, by1 - by0, min(1, pt))
        ar(c, bx1 - 30, by0 + 56, "تحويل بنكي", af("bold", 32), INK)
        amount = 25_000_000 * ease_out(prog(t, 6.0, 2.8))
        c.text(bx0 + 30, by0 + 64, f"${int(amount):,}", font("sans", 54), INK, "ls")
        pb = prog(t, 6.0, 2.8)
        c.rect(bx0 + 30, by0 + 100, bx1 - 30, by0 + 118, fill=GRID, r=9)
        c.rect(bx1 - 30 - (bx1 - bx0 - 60) * pb, by0 + 100, bx1 - 30, by0 + 118, fill=GREEN, r=9)
        if t > 9.0:
            ar(c, bx1 - 30, by0 + 145, "✓ تم التحويل", af("bold", 24), GREEN)


CAPS_CALL = [
    (0.4, 5.4, "موظف في هونج كونج دخل اجتماع فيديو عادي جدًا. المدير المالي موجود، وزمايله موجودين."),
    (5.4, 11.3, "طلبوا منه يحوّل فلوس، فحوّل. حوالي خمسة وعشرين مليون دولار."),
    (12.0, 15.4, "المشكلة؟ ولا واحد في الاجتماع ده كان حقيقي."),
    (15.4, 18.8, "كلهم كانوا وشوش وأصوات معمولة بالذكاء الاصطناعي."),
]

PEW = [("قلقانين أكتر ما هم متحمسين", 52, RED), ("مشاعرهم مختلطة", 36, MUTED), ("متحمسين أكتر", 10, TEAL)]


def scene_pew(c, t):
    ar_header(c, "مش إحساس فردي", "الخوف")
    big = font("serif", 200)
    pn = prog(t, 4.6, 0.5)
    if pn > 0:
        w = v.tw("52%", big)
        highlight(c, 1800 - w - 10, 360, 1812, 440, prog(t, 5.2, 0.6))
        c.text(1800, 445 + (1 - ease_out(pn)) * 30, "52%", big, fade(INK, pn), "rs")
    ar_rise(c, t, 5.0, 1800, 540, "من الأمريكان قلقانين من", af("reg", 44), INK)
    ar_rise(c, t, 5.15, 1800, 605, "الذكاء الاصطناعي أكتر ما هم متحمسين", af("reg", 44), INK)
    for i, (label, pct, color) in enumerate(PEW):
        y = 330 + i * 150
        pl = prog(t, 5.6 + i * 0.3, 0.4)
        if pl <= 0:
            continue
        ar(c, 920, y - 16, label, af("bold", 30), fade(INK, pl))
        pb = ease_out(prog(t, 5.8 + i * 0.3, 0.9))
        left = 920 - pct * 9 * pb
        c.rect(left, y, 920, y + 56, fill=color, r=10)
        if pb > 0.05:
            c.text(left - 14, y + 42, f"{pct}%", font("sans", 34), fade(color, prog(t, 6.3 + i * 0.3, 0.4)), "rs")
    # first beat: a "no thanks" hand-off before the data
    p0 = prog(t, 0.4, 0.5) * (1 - prog(t, 4.2, 0.3))
    if p0 > 0:
        ar(c, 960, 560, "«لا، شكرًا»", af("head", 120), fade(INK, p0), "ms")
    ar_source(c, t, "Pew Research Center، أغسطس 2023", start=6.0)


CAPS_PEW = [
    (0.3, 4.6, "قصص زي دي هي اللي مخلّية ناس كتير تبص للذكاء الاصطناعي وتقول: لا، شكرًا."),
    (4.6, 12.8, "وده مش إحساس فردي. في استطلاع لمركز «بيو» سنة 2023، أكتر من نص الأمريكان قالوا إنهم قلقانين أكتر ما هم متحمسين."),
]


def scene_question(c, t):
    f = af("head", 110)
    ar_rise(c, t, 0.2, 960, 470, "طب الخوف ده", f, INK, anchor="ms", dist=40)
    p2 = prog(t, 0.5, 0.5)
    if p2 > 0:
        line = "جاي منين بالظبط؟"
        w = atw(line, f)
        highlight(c, 960 - w / 2 - 10, 560, 960 + w / 2 + 10, 650, prog(t, 1.0, 0.6))
        ar(c, 960, 640 + (1 - ease_out(p2)) * 40, line, f, fade(INK, p2), "ms")
    for k in range(3):
        pk = ease_back(prog(t, 2.0 + k * 0.25, 0.4))
        if pk > 0:
            x = 1110 - k * 150
            c.circle(x, 820, 46 * pk, fill=RED)
            c.text(x, 820 + 20 * pk, str(k + 1), font("sans", int(52 * pk) or 1), CARD, "ms")


def media_icon(c, kind, x, y, t, p):
    if kind == 0:  # waveform
        for k in range(9):
            hgt = (30 + 60 * abs(math.sin(t * 5 + k * 0.9))) * p
            c.rect(x - 120 + k * 30 - 8, y - hgt, x - 120 + k * 30 + 8, y + hgt, fill=TEAL, r=8)
    elif kind == 1:  # photo
        c.rect(x - 120 * p, y - 85 * p, x + 120 * p, y + 85 * p, fill=CARD, outline=INK, w=6, r=10)
        c.poly([(x - 100 * p, y + 70 * p), (x - 30 * p, y - 20 * p), (x + 20 * p, y + 40 * p),
                (x + 50 * p, y + 10 * p), (x + 100 * p, y + 70 * p)], TEAL)
        c.circle(x + 60 * p, y - 45 * p, 18 * p, fill=HL)
    else:  # video
        c.rect(x - 120 * p, y - 85 * p, x + 120 * p, y + 85 * p, fill=SCREEN, r=14)
        c.poly([(x - 30 * p, y - 45 * p), (x + 45 * p, y), (x - 30 * p, y + 45 * p)], CARD)


def scene_fear1(c, t):
    ar_header(c, "إن حد يضحك عليك", "الخوف رقم ١")
    cw, ch, gap = 440, 440, 60
    x_start = (W - (3 * cw + 2 * gap)) / 2
    for k, label in enumerate(["صوت", "صورة", "فيديو"]):
        x = x_start + (2 - k) * (cw + gap)
        pa = ease_back(prog(t, 0.6 + k * 0.3, 0.5))
        if pa <= 0:
            continue
        y = 280 + (1 - pa) * 100
        card(c, x, y, cw, ch, min(1, pa))
        media_icon(c, k, x + cw / 2, y + 170, t, min(1, pa))
        ar(c, x + cw / 2, y + 360, label, af("bold", 50), INK, "ms")
        stamp(c, x + cw - 70, y + 40, "مزيّف", prog(t, 4.6 + k * 0.4, 0.35), 30)


CAPS_FEAR1 = [
    (0.3, 4.4, "أول حاجة: إن حد يضحك عليك."),
    (4.4, 8.8, "الحاجات اللي كنا بنقول عليها «شفتها بعيني» بقت ممكن تتزيّف."),
]

CASES = [
    ("Varghese v. China Southern Airlines", "11th Cir. 2019"),
    ("Shaboon v. Egyptair", "Ill. App. 2013"),
    ("Petersen v. Iran Air", "D.D.C. 2012"),
    ("Martinez v. Delta Air Lines", "Tex. App. 2019"),
]


def scene_fear2(c, t):
    ar_header(c, "إن الآلة تغلط وهي واثقة", "الخوف رقم ٢")
    x0, x1, y0, y1 = 420, 1500, 250, 860
    pd = ease_back(prog(t, 0.4, 0.6))
    if pd <= 0:
        return
    yo = (1 - pd) * 100
    card(c, x0, y0 + yo, x1 - x0, y1 - y0, min(1, pd))
    ar(c, x1 - 50, y0 + yo + 70, "مذكرة قانونية", af("bold", 38), INK)
    c.rect(x0 + 50, y0 + yo + 95, x1 - 50, y0 + yo + 99, fill=GRID)
    for k, (name, cite) in enumerate(CASES):
        y = y0 + yo + 170 + k * 110
        p = prog(t, 5.0 + k * 0.9, 0.8)
        if p <= 0:
            continue
        shown = name[:max(1, int(len(name) * p))]
        c.text(x0 + 50, y, shown, font("serif", 34), INK, "ls")
        if p >= 1:
            c.text(x0 + 52, y + 36, cite, font("sansr", 24), MUTED, "ls")
        ps = prog(t, 10.2 + k * 0.4, 0.3)
        if ps > 0:
            wname = v.tw(name, font("serif", 34))
            c.line([(x0 + 44, y - 12), (x0 + 44 + (wname + 12) * ps, y - 12)], RED, 5)
            ar(c, x1 - 50, y, "غير موجودة", af("bold", 28), fade(RED, ps))
    stamp(c, x1 - 190, y1 - 40, "غرامة 5,000 دولار", prog(t, 12.8, 0.4), 36)
    ar_source(c, t, "قضية Mata v. Avianca، نيويورك 2023", start=1.0)


CAPS_FEAR2 = [
    (0.3, 4.9, "تاني حاجة: إن الآلة تغلط وهي واثقة."),
    (4.9, 10.0, "في نيويورك، محامي استخدم «تشات جي بي تي» عشان يجهّز مذكرة لقضية. البرنامج طلّع له قضايا قديمة بأسامي وتواريخ."),
    (10.0, 14.8, "شكلها مقنع جدًا. بس ولا قضية فيهم كانت موجودة أصلًا. والمحكمة غرّمته."),
]


def briefcase(c, x, y, color, p):
    if p <= 0:
        return
    c.rect(x - 22 * p, y - 46 * p, x + 22 * p, y - 26 * p, outline=color, w=6, r=6)
    c.rect(x - 50 * p, y - 32 * p, x + 50 * p, y + 34 * p, fill=color, r=10)
    c.rect(x - 50 * p, y - 4 * p, x + 50 * p, y + 2 * p, fill=CARD)


def scene_fear3(c, t):
    ar_header(c, "الشغل", "الخوف رقم ٣")
    big = font("serif", 190)
    pn = prog(t, 4.4, 0.5)
    if pn > 0:
        w = v.tw("~40%", big)
        highlight(c, 1800 - w - 10, 370, 1812, 450, prog(t, 5.0, 0.6))
        c.text(1800, 450 + (1 - ease_out(pn)) * 30, "~40%", big, fade(INK, pn), "rs")
    ar_rise(c, t, 4.8, 1800, 545, "من الوظايف في العالم", af("reg", 44), INK)
    ar_rise(c, t, 4.95, 1800, 605, "معرّضة إنها تتأثر بالذكاء الاصطناعي", af("reg", 44), INK)
    for k in range(10):
        row, col = divmod(k, 5)
        x = 860 - col * 135
        y = 340 + row * 150
        pb = ease_back(prog(t, 0.8 + k * 0.08, 0.35))
        turn = prog(t, 5.6 + k * 0.12, 0.3) if k < 4 else 0
        briefcase(c, x, y, mix(INK, RED, turn), pb)
    pe = ease_back(prog(t, 9.8, 0.5))
    if pe > 0:
        card(c, 560, 680 + (1 - pe) * 60, 800, 170, min(1, pe))
        f = af("head", 64)
        yb = 790 + (1 - pe) * 60
        ar(c, 1260, yb, "تتأثر", f, INK)
        c.text(960, yb, "≠", font("sym", 80), RED, "ms")
        ar(c, 820, yb, "تختفي", f, INK)
    ar_source(c, t, "صندوق النقد الدولي، يناير 2024", start=5.0)


CAPS_FEAR3 = [
    (0.3, 4.4, "وتالت حاجة، ودي أكتر حاجة بتقلق الناس: الشغل."),
    (4.4, 9.6, "صندوق النقد الدولي قال إن حوالي أربعين في المية من الوظايف في العالم معرّضة إنها تتأثر بالذكاء الاصطناعي."),
    (9.6, 14.8, "بس خلّي بالك: «تتأثر» مش معناها «تختفي». في وظايف ممكن تتضرر، وفي وظايف تانية الأداة دي هتساعدها."),
]

GUESSES = [("أزرق", 92, TEAL), ("رمادي", 6, MUTED), ("برتقاني", 2, MUTED)]


def scene_predict(c, t):
    ar_header(c, "مش عقل… ده تخمين ذكي", "إزاي بيشتغل")
    pb = ease_back(prog(t, 0.4, 0.5))
    if pb > 0:
        card(c, 360, 260 + (1 - pb) * 60, 1200, 140, min(1, pb))
        f = af("bold", 60)
        y = 350 + (1 - pb) * 60
        txt = "السما لونها"
        ar(c, 1500, y, txt, f, INK)
        bx1 = 1500 - atw(txt, f) - 30
        if t < 7.6:
            c.rect(bx1 - 220, y + 4, bx1, y + 10, fill=INK)
        else:
            pf = prog(t, 7.6, 0.4)
            ww = atw("أزرق", f)
            highlight(c, bx1 - ww - 10, y - 62, bx1 + 8, y + 10, pf)
            ar(c, bx1, y, "أزرق", f, fade(INK, pf))
    for i, (word, pct, color) in enumerate(GUESSES):
        y = 500 + i * 110
        pl = prog(t, 2.4 + i * 0.3, 0.4)
        if pl <= 0:
            continue
        ar(c, 1500, y + 40, word, af("bold", 40), fade(INK, pl))
        pw = ease_out(prog(t, 2.6 + i * 0.3, 0.9))
        right = 1320
        left = right - max(8, pct * 8) * pw
        c.rect(left, y, right, y + 56, fill=color, r=10)
        c.text(left - 14, y + 42, f"{pct}%", font("sans", 32), fade(color, pl), "rs")
    pe = prog(t, 3.5, 0.5)
    if pe > 0:
        ar(c, 1800, 880, "مثال توضيحي", af("reg", 24), fade(MUTED, pe))


CAPS_PREDICT = [
    (0.3, 4.6, "لكن هنا الصورة بتبدأ توضح. الذكاء الاصطناعي اللي بنكلّمه مش عقل بيفكّر."),
    (4.6, 9.4, "هو أقرب لطالب حافظ ملايين الصفحات، وبيخمّن الكلمة الجاية الأقرب للصح."),
    (9.4, 13.8, "أغلب الوقت تخمينه ممتاز. وساعات بيخمّن غلط، بنفس الثقة بالظبط."),
]


def old_car(c, x, y):
    c.rect(x, y - 70, x + 230, y, fill=INK, r=10)
    c.rect(x + 120, y - 130, x + 220, y - 70, fill=INK, r=8)
    c.rect(x + 132, y - 118, x + 208, y - 82, fill=CARD, r=4)
    c.rect(x + 20, y - 120, x + 40, y - 70, fill=INK)
    c.circle(x + 50, y + 8, 36, fill=INK)
    c.circle(x + 50, y + 8, 14, fill=CARD)
    c.circle(x + 185, y + 8, 36, fill=INK)
    c.circle(x + 185, y + 8, 14, fill=CARD)


def traffic_light(c, x, y):
    c.rect(x - 34, y - 80, x + 34, y + 80, fill=INK, r=14)
    for k, col in enumerate([RED, HL, GREEN]):
        c.circle(x, y - 48 + k * 48, 18, fill=col)


def doc_icon(c, x, y):
    c.rect(x - 56, y - 76, x + 56, y + 76, fill=CARD, outline=INK, w=6, r=8)
    for k in range(4):
        c.line([(x - 34, y - 40 + k * 28), (x + 34, y - 40 + k * 28)], INK, 6)


def license_icon(c, x, y):
    c.rect(x - 90, y - 58, x + 90, y + 58, fill=CARD, outline=INK, w=6, r=12)
    person(c, x + 45, y + 4, TEAL, 0.9)
    for k in range(3):
        c.line([(x - 66, y - 26 + k * 26), (x + 4, y - 26 + k * 26)], INK, 6)


def scene_history(c, t):
    ar_header(c, "الخوف ده مش جديد", "والغريب إن")
    py = prog(t, 0.3, 0.5)
    if py > 0:
        c.text(140, 330, "1865", font("serif", 150), fade(INK, py), "ls")
        ar(c, 140 + 0, 390, "بريطانيا", af("bold", 40), fade(RED, py), "ls")
    road_y = 600
    pr = prog(t, 0.4, 0.6)
    if pr > 0:
        c.rect(80, road_y + 44, 80 + 1760 * ease_out(pr), road_y + 52, fill=GRID)
    pg = prog(t, 0.8, 9.0)
    if pg > 0:
        gx = 1650 - 820 * pg
        old_car(c, gx, road_y)
        mx = gx - 170
        bob = 6 * abs(math.sin(t * 6))
        person(c, mx, road_y - 10 - bob, INK, 1.4)
        c.line([(mx + 30, road_y - 30 - bob), (mx + 30, road_y - 190 - bob)], INK, 6)
        wave = 10 * math.sin(t * 8)
        c.poly([(mx + 30, road_y - 190 - bob), (mx - 60, road_y - 170 - bob + wave),
                (mx + 30, road_y - 140 - bob)], RED)
    cw, ch, gap = 440, 200, 40
    x_start = (W - (3 * cw + 2 * gap)) / 2
    for k, (label, icon) in enumerate([("إشارات", traffic_light), ("قوانين", doc_icon),
                                       ("رخصة سواقة", license_icon)]):
        pa = ease_back(prog(t, 12.0 + k * 0.7, 0.5))
        if pa <= 0:
            continue
        x = x_start + (2 - k) * (cw + gap)
        y = 690 + (1 - pa) * 60
        card(c, x, y, cw, ch, min(1, pa))
        icon(c, x + cw - 115, y + ch / 2)
        ar(c, x + cw - 228, y + ch / 2 + 14, label, af("bold", 36), INK)


CAPS_HISTORY = [
    (0.3, 5.6, "والغريب إن الخوف ده مش جديد. سنة 1865، بريطانيا عملت قانون إن أي عربية بمحرك لازم يمشي قدامها راجل شايل علم أحمر."),
    (5.6, 11.6, "الخوف ساعتها ماكانش غلط كله، العربيات فعلًا ممكن تكون خطر. بس الحل في الآخر ماكانش إننا نمنع العربيات."),
    (11.6, 16.8, "الحل كان إشارات، وقوانين، ورخصة سواقة."),
]


def scene_twist(c, t):
    f1 = af("head", 72)
    l1 = "أكبر خطر مش إنك تستخدمه"
    ar_rise(c, t, 0.4, 960, 400, l1, f1, MUTED, anchor="ms")
    ps = prog(t, 2.4, 0.5)
    if ps > 0:
        w = atw(l1, f1)
        c.line([(960 + w / 2 + 10, 375), (960 + w / 2 + 10 - (w + 20) * ease_out(ps), 375)], RED, 8)
    f2 = af("head", 110)
    l2 = "أكبر خطر إنك ماتفهموش"
    p2 = prog(t, 3.0, 0.5)
    if p2 > 0:
        w = atw(l2, f2)
        highlight(c, 960 - w / 2 - 10, 540, 960 + w / 2 + 10, 630, prog(t, 3.8, 0.6))
        ar(c, 960, 620 + (1 - ease_out(p2)) * 40, l2, f2, fade(INK, p2), "ms")


CAPS_TWIST = [
    (0.3, 5.4, "وهنا المفاجأة. أكبر خطر مش إنك تستخدم الذكاء الاصطناعي. أكبر خطر إنك ماتفهموش."),
    (5.4, 10.8, "لأن اللي ضحك على موظف هونج كونج كان فاهم الأداة دي كويس جدًا."),
]


def scene_end(c, t):
    ar_rise(c, t, 0.4, 960, 330, "السؤال الحقيقي مش: هل الذكاء الاصطناعي خطر؟", af("reg", 48), MUTED, anchor="ms")
    ar_rise(c, t, 2.4, 960, 540, "السؤال: مين فاهمه أكتر…", af("head", 92), INK, anchor="ms", dist=40)
    f = af("head", 80)
    l3 = "إنت، ولا اللي بيحاول يستخدمه ضدك؟"
    p3 = prog(t, 3.6, 0.5)
    if p3 > 0:
        w = atw(l3, f)
        right = 960 + w / 2
        wf = atw("إنت،", f)
        highlight(c, right - wf - 12, 640, right + 10, 722, prog(t, 4.6, 0.5))
        ar(c, 960, 710 + (1 - ease_out(p3)) * 40, l3, f, fade(INK, p3), "ms")


SOURCES = [
    "شرطة هونج كونج، فبراير 2024 (احتيال بالتزييف العميق، حوالي 25 مليون دولار، شركة Arup)",
    "Pew Research Center، أغسطس 2023: ‏52% قلقانين أكتر ما هم متحمسين",
    "قضية Mata v. Avianca، محكمة نيويورك الفيدرالية، 2023 (غرامة 5,000 دولار)",
    "صندوق النقد الدولي، يناير 2024: حوالي 40% من الوظايف معرّضة لتأثير الذكاء الاصطناعي",
    "قانون Locomotive Act البريطاني، 1865 (قانون «العلم الأحمر»)",
]


def scene_sources(c, t):
    ar_header(c, "المصادر", "للتوثيق")
    for k, line in enumerate(SOURCES):
        ar_rise(c, t, 0.3 + k * 0.12, 1800, 320 + k * 90, line, af("reg", 32), INK)


SCENES = [
    (scene_call, 19.0, CAPS_CALL),
    (scene_pew, 13.0, CAPS_PEW),
    (scene_question, 5.0, []),
    (scene_fear1, 9.0, CAPS_FEAR1),
    (scene_fear2, 15.0, CAPS_FEAR2),
    (scene_fear3, 15.0, CAPS_FEAR3),
    (scene_predict, 14.0, CAPS_PREDICT),
    (scene_history, 17.0, CAPS_HISTORY),
    (scene_twist, 11.0, CAPS_TWIST),
    (scene_end, 10.0, []),
    (scene_sources, 6.0, []),
]

STARTS = []
_s = 0.0
for _sc in SCENES:
    STARTS.append(_s)
    _s += _sc[1] - TRANS
TOTAL = _s + TRANS
GLITCHES = [(CALL_GLITCH, 0.5)]
MUTES = [(CALL_GLITCH + 0.1, CALL_GLITCH + 2.0)]


def draw_scene(c, idx, local):
    fn, _, caps = SCENES[idx]
    fn(c, local)
    captions(c, local, caps)


_tex = None


def render_frame(i):
    return render_at(i / FPS, i)


def render_at(t, seed, total=None):
    """Render the frame at story time t; total sets where the fade-out happens."""
    global _tex
    if _tex is None:
        _tex = v.make_textures()
    vignette, grains = _tex
    i = seed
    img = Image.new("RGB", (W * S, H * S), PAPER)
    c = Canvas(img)
    idx = max(k for k, s in enumerate(STARTS) if t >= s)
    dur = SCENES[idx][1]
    local = t - STARTS[idx]
    if idx + 1 < len(SCENES) and local > dur - TRANS:
        e = v.ease_in_out(prog(local, dur - TRANS, TRANS))
        c.dx = W * e  # right-to-left story: scenes slide in from the left
        draw_scene(c, idx, local)
        c.dx = -W * (1 - e)
        draw_scene(c, idx + 1, local - (dur - TRANS))
    else:
        draw_scene(c, idx, local)
    img = img.resize((W, H), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) * vignette + grains[0]
    for g0, gd in GLITCHES:
        if g0 <= t < g0 + gd:
            p = (t - g0) / gd
            arr = glitch(arr, math.sin(math.pi * p) * (0.6 + 0.4 * ((i * 7919) % 5) / 4), i)
    fio = min(prog(t, 0, 0.4), prog(TOTAL - t, 0, 0.6)) if total is None else 1.0
    if fio < 1:
        arr = arr * fio
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def caption_table():
    for idx, (fn, _, caps) in enumerate(SCENES):
        for s, e, txt in caps:
            a, b = STARTS[idx] + s, STARTS[idx] + e
            print(f"{int(a // 60)}:{a % 60:05.2f} - {int(b // 60)}:{b % 60:05.2f}  {txt}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="vox_ar_fear.mp4")
    ap.add_argument("--voice", help="voiceover audio to mix over the music")
    ap.add_argument("--preview", type=float, help="render only the frame at this second to a PNG")
    ap.add_argument("--captions", action="store_true", help="print caption timings and exit")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    if args.captions:
        caption_table()
        return
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
        music = os.path.join(tmp, "music.wav")
        v.make_music(music, TOTAL, chords=[[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]],
                     starts=STARTS[1:], mute=MUTES)
        add_buzz(music, [g0 for g0, _ in GLITCHES])
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", music]
        if args.voice:
            cmd += ["-i", args.voice, "-filter_complex",
                    "[1:a]volume=0.3[m];[m][2:a]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.output]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with mp.Pool(args.workers) as pool:
            for k, data in enumerate(pool.imap(render_frame, range(frames), chunksize=4)):
                ff.stdin.write(data)
                if k % (FPS * 10) == 0:
                    print(f"rendering {k / FPS:6.1f}s / {TOTAL:.1f}s", flush=True)
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
        print(f"saved {args.output} ({TOTAL:.1f}s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
