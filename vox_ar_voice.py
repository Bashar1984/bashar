#!/usr/bin/env python3
"""Sync vox_ar_video.py to a recorded voiceover, then add music and sound effects.

The animation is time-warped so each sentence's scene and caption starts
when that sentence starts in the recording. The voice is cleaned (hum and
hiss reduction, gate, EQ, de-ess, compression, loudness normalisation),
the music ducks under the voice, and procedural sound effects are added
(whooshes, glitch buzz, stamp hits, typing, pops, dings, impacts).

Usage:
    python3 vox_ar_voice.py voice.m4a                       # -> vox_ar_fear_voice.mp4
    python3 vox_ar_voice.py voice.m4a --starts starts.json  # your own sentence times
    python3 vox_ar_voice.py voice.m4a --preview 40          # one frame (voice time)

--starts is a JSON list of 25 numbers: the time in seconds where each
script sentence starts in the recording (see SENTENCE_ORIG below for order).
"""
import argparse
import json
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

import vox_ar_video as a
import vox_video as v
from vox_ai_video import add_buzz

FPS, W, H = v.FPS, v.W, v.H
SR = 48000

# Story time (in the un-synced video) where each of the 25 script sentences starts.
SENTENCE_ORIG = [0.4, 5.4, 12.0, 15.4, 18.7, 23.0, 31.0, 35.5, 39.6, 43.9, 48.5, 53.6, 58.3,
                 62.4, 67.6, 72.7, 77.0, 81.8, 86.1, 91.4, 97.4, 102.5, 107.6, 113.0, 115.0]
LAST_LINE_DONE = 117.6  # story time when the final line has fully landed

# Sentence starts found in the supplied recording (pause-based alignment).
DEFAULT_STARTS = [0.5, 8.42, 12.82, 15.51, 18.61, 26.1, 33.13, 35.38, 37.43, 42.08, 44.06, 52.33,
                  56.66, 60.28, 67.9, 74.24, 80.74, 85.47, 90.84, 103.26, 112.42, 115.77, 122.51,
                  127.22, 131.57]

VOICE_FILTER = ("highpass=f=80,afftdn=nf=-42:nr=20:tn=1,"
                "agate=threshold=0.02:ratio=4:attack=5:release=120:range=0.1,"
                "equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=2.5,deesser=i=0.3,"
                "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2dB,"
                "loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.89")


class Warp:
    def __init__(self, starts, speech_end):
        self.new = [0.0] + list(starts) + [speech_end]
        self.orig = [0.0] + SENTENCE_ORIG + [LAST_LINE_DONE]
        tail = a.TOTAL - LAST_LINE_DONE
        self.new.append(speech_end + tail)
        self.orig.append(a.TOTAL)
        self.total = self.new[-1]

    def to_orig(self, t):
        return float(np.interp(t, self.new, self.orig))

    def to_new(self, t):
        return float(np.interp(t, self.orig, self.new))


WARP = None


def render_frame(i):
    t = i / FPS
    arr = np.frombuffer(a.render_at(WARP.to_orig(t), i, total=WARP.total), np.uint8)
    fio = min(v.prog(t, 0, 0.4), v.prog(WARP.total - t, 0, 0.8))
    if fio < 1:
        arr = (arr.astype(np.float32) * fio).astype(np.uint8)
    return arr.tobytes()


# ---------------------------------------------------------------- sound effects

def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


def sfx_pop(rng):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 700 * np.exp(-t * 25) + 180
    return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.04)


def sfx_stamp(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 140 * np.exp(-t * 18) + 45
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 0.09)
    click = rng.normal(0, 1, n) * _env(n, 0.0005, 0.012)
    return 0.9 * body + 0.35 * click


def sfx_tick(rng):
    n = int(0.03 * SR)
    return 0.25 * np.diff(rng.normal(0, 1, n + 1)) * _env(n, 0.0002, 0.004)


def sfx_ding(rng):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)
    return 0.28 * tone * _env(n, 0.002, 0.35)


def sfx_typing(rng, seconds):
    out = np.zeros(int(seconds * SR) + SR // 10)
    tt = 0.0
    while tt < seconds:
        k = sfx_tick(rng) * rng.uniform(0.6, 1.2)
        a0 = int(tt * SR)
        out[a0:a0 + len(k)] += k
        tt += rng.uniform(0.05, 0.13)
    return out


def sfx_scratch(rng):
    n = int(0.28 * SR)
    noise = np.diff(rng.normal(0, 1, n + 1))
    noise = np.convolve(noise, np.ones(6) / 6, "same")
    return 0.35 * noise * np.sin(np.linspace(0, np.pi, n)) ** 0.5


def sfx_boom(rng):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 70 * np.exp(-t * 3) + 32
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.003, 0.45)
    hit = np.convolve(rng.normal(0, 1, n), np.ones(40) / 40, "same") * _env(n, 0.001, 0.06)
    return 0.9 * body + 0.6 * hit


def sfx_riser(rng, seconds=1.4):
    n = int(seconds * SR)
    t = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    win = 60
    for k in range(0, n, 2048):  # sweep from dark to bright noise
        w = max(2, int(win * (1 - t[k]) + 2))
        seg = noise[k:k + 2048]
        out[k:k + 2048] = np.convolve(seg, np.ones(w) / w, "same")
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR)
    return (0.5 * out + 0.12 * tone) * t ** 2


def sfx_whoosh(rng):
    n = int(0.7 * SR)
    noise = np.convolve(rng.normal(0, 1, n), np.ones(18) / 18, "same")
    return 0.6 * noise * np.sin(np.linspace(0, np.pi, n)) ** 2


def sfx_events():
    """(story_time, kind, gain) in un-synced video time."""
    S = a.STARTS
    ev = [(6.0, "typing_ticks", 0.5), (9.0, "ding", 0.8)]
    ev += [(a.CALL_GLITCH + 0.6 + k * 0.35, "stamp", 0.8) for k in range(3)]
    ev += [(S[1] + 4.6, "pop", 0.7)] + [(S[1] + 5.8 + i * 0.3, "pop", 0.45) for i in range(3)]
    ev += [(S[2] + 0.2, "boom", 0.55)] + [(S[2] + 2.0 + k * 0.25, "pop", 0.6) for k in range(3)]
    ev += [(S[3] + 0.6 + k * 0.3, "pop", 0.4) for k in range(3)]
    ev += [(S[3] + 4.6 + k * 0.4, "stamp", 0.7) for k in range(3)]
    ev += [(S[4] + 5.0 + k * 0.9, "typing", 0.6) for k in range(4)]
    ev += [(S[4] + 10.2 + k * 0.4, "scratch", 0.6) for k in range(4)]
    ev += [(S[4] + 12.8, "stamp", 0.9)]
    ev += [(S[5] + 0.8 + k * 0.08, "pop", 0.2) for k in range(10)]
    ev += [(S[5] + 5.6 + k * 0.12, "pop", 0.45) for k in range(4)]
    ev += [(S[5] + 9.8, "stamp", 0.6)]
    ev += [(S[6] + 2.4 + i * 0.3, "pop", 0.4) for i in range(3)] + [(S[6] + 7.6, "ding", 0.6)]
    ev += [(S[7] + 12.0 + k * 0.7, "pop", 0.55) for k in range(3)]
    ev += [(S[8] - 1.6, "riser", 0.5), (S[8] + 2.4, "scratch", 0.7), (S[8] + 3.0, "boom", 0.9)]
    ev += [(S[9] + 2.4, "pop", 0.5), (S[9] + 3.6, "boom", 0.8)]
    ev += [(s, "whoosh", 0.35) for s in S[1:]]
    return ev


def make_sfx(path, warp):
    rng = np.random.default_rng(5)
    n = int(warp.total * SR) + SR
    out = np.zeros(n)
    for t_orig, kind, gain in sfx_events():
        t = warp.to_new(t_orig)
        if kind == "typing":
            dur = 0.8 * (warp.to_new(t_orig + 0.8) - t) / 0.8
            snd = sfx_typing(rng, max(0.3, dur))
        elif kind == "typing_ticks":  # counter ticking during the transfer
            dur = warp.to_new(t_orig + 2.8) - t
            snd = np.zeros(int(dur * SR) + SR // 10)
            for k in range(int(dur * 14)):
                tk = sfx_tick(rng)
                a0 = int(k / 14 * SR)
                snd[a0:a0 + len(tk)] += tk
        elif kind == "riser":
            snd = sfx_riser(rng)
        else:
            snd = {"pop": sfx_pop, "stamp": sfx_stamp, "ding": sfx_ding, "scratch": sfx_scratch,
                   "boom": sfx_boom, "whoosh": sfx_whoosh}[kind](rng)
        a0 = max(0, int(t * SR))
        seg = snd[:max(0, n - a0)] * gain
        out[a0:a0 + len(seg)] += seg
    out /= max(1e-6, np.abs(out).max()) / 0.8
    write_wav(path, out)


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def speech_end(voice_wav):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", voice_wav, "-f", "f32le", "-ac", "1",
                                      "-ar", "16000", "-"], capture_output=True).stdout, np.float32)
    hop = 160
    n = len(x) // hop
    e = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    loud = np.where(e > np.percentile(e, 10) + 12)[0]
    return (loud[-1] + 1) / 100 if len(loud) else len(x) / 16000


def main():
    global WARP
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("voice")
    ap.add_argument("-o", "--output", default="vox_ar_fear_voice.mp4")
    ap.add_argument("--starts", help="JSON file with 25 sentence start times (seconds)")
    ap.add_argument("--preview", type=float)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()
    starts = json.load(open(args.starts)) if args.starts else DEFAULT_STARTS
    if len(starts) != len(SENTENCE_ORIG):
        sys.exit(f"--starts needs {len(SENTENCE_ORIG)} values")

    tmp = tempfile.mkdtemp()
    try:
        voice = os.path.join(tmp, "voice.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.voice, "-af", VOICE_FILTER,
                        "-ar", str(SR), "-ac", "1", voice], check=True)
        WARP = Warp(starts, speech_end(voice))
        if args.preview is not None:
            out = os.path.splitext(args.output)[0] + f"_{args.preview:.1f}s.png"
            Image.frombytes("RGB", (W, H), render_frame(int(args.preview * FPS))).save(out)
            print("saved", out)
            return
        print(f"voice-synced length {WARP.total:.1f}s")

        music = os.path.join(tmp, "music.wav")
        glitch_t = WARP.to_new(a.CALL_GLITCH)
        v.make_music(music, WARP.total, chords=[[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]],
                     starts=[], mute=[(glitch_t + 0.1, glitch_t + 2.0)])
        add_buzz(music, [glitch_t])
        sfx = os.path.join(tmp, "sfx.wav")
        make_sfx(sfx, WARP)
        mix = os.path.join(tmp, "mix.wav")
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", voice, "-i", music, "-i", sfx, "-filter_complex",
            "[0:a]asplit=2[vo][sc];"
            "[1:a]volume=0.32[mu];"
            "[mu][sc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=450[duck];"
            "[2:a]volume=0.55[fx];"
            "[vo][duck][fx]amix=inputs=3:duration=longest:normalize=0,"
            f"atrim=0:{WARP.total:.3f},loudnorm=I=-14:TP=-1.0:LRA=11,alimiter=limit=0.9[out]",
            "-map", "[out]", "-ar", str(SR), mix], check=True)

        frames = int(WARP.total * FPS)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", mix, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", args.output]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with mp.Pool(args.workers) as pool:
            for k, data in enumerate(pool.imap(render_frame, range(frames), chunksize=4)):
                ff.stdin.write(data)
                if k % (FPS * 10) == 0:
                    print(f"rendering {k / FPS:6.1f}s / {WARP.total:.1f}s", flush=True)
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
        print(f"saved {args.output} ({WARP.total:.1f}s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
