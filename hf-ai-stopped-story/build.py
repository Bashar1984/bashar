#!/usr/bin/env python3
"""Generate the scene files for "The interview" from one shared character rig.

Run from this folder: python3 build.py  (rewrites compositions/*.html and index.html)
Edit the scene functions below, not the generated HTML, so Sam and the tourist stay consistent.
"""
import json

INK, SUN, RED, BLUE = "#121317", "#FFC93C", "#F2553C", "#2348F2"
SAM = dict(coat=BLUE, skin="#D99A6C", hair="#2B1E1A", pants="#26282E")
TOURIST = dict(coat="#F28C28", skin="#F1C9A5", hair="#A7A7A7", pants="#4A3B33")

COMMON_CSS = """
#root { position: absolute; inset: 0; overflow: hidden; font-family: "Nunito", sans-serif; }
.chr { position: absolute; width: 240px; height: 540px; }
.leg { position: absolute; top: 380px; width: 36px; height: 150px; border-radius: 18px; transform-origin: 18px 10px; }
.shoe { position: absolute; bottom: -6px; left: -6px; width: 52px; height: 22px; border-radius: 12px; background: #121317; }
.body { position: absolute; left: 48px; top: 215px; width: 144px; height: 195px; border-radius: 64px 64px 26px 26px; }
.arm { position: absolute; top: 232px; width: 30px; height: 150px; border-radius: 15px; transform-origin: 15px 12px; }
.hand { position: absolute; bottom: -10px; left: -3px; width: 36px; height: 36px; border-radius: 50%; }
.head { position: absolute; left: 45px; top: 58px; width: 150px; height: 150px; border-radius: 50%; transform-origin: 75px 150px; }
.hair { position: absolute; left: -6px; top: -10px; width: 162px; height: 78px; border-radius: 80px 80px 24px 24px; }
.eye { position: absolute; top: 70px; width: 16px; height: 22px; border-radius: 50%; background: #121317; transform-origin: 8px 11px; }
.mouth { position: absolute; left: 45px; top: 100px; overflow: visible; }
.sweat { position: absolute; left: 150px; top: 40px; width: 18px; height: 26px; border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%; background: #5FB3FF; opacity: 0; }
.narr { position: absolute; left: 192px; font-weight: 900; font-size: 54px; line-height: 1.15; color: #121317; white-space: nowrap; }
.narr span { display: inline-block; margin-right: 0.24em; opacity: 0; }
.ck { position: absolute; left: 1640px; top: 80px; width: 168px; height: 168px; border-radius: 50%; background: #FFFFFF; border: 10px solid #121317;
  display: flex; align-items: center; justify-content: center; font-family: "Archivo Black", sans-serif; font-size: 46px; color: #121317; }
.bubble { position: absolute; padding: 24px 32px; border-radius: 28px; background: #FFFFFF; font-weight: 800; font-size: 40px; color: #121317;
  white-space: nowrap; box-shadow: 0 8px 18px rgba(18,19,23,0.15); opacity: 0; }
.tail { position: absolute; bottom: -24px; width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 26px solid #FFFFFF; }
.bld { position: absolute; bottom: 120px; border-radius: 6px 6px 0 0;
  background-image: repeating-linear-gradient(90deg, transparent 0 22px, rgba(255,255,255,0.55) 22px 44px, transparent 44px 66px),
                    repeating-linear-gradient(0deg, transparent 0 26px, rgba(0,0,0,0) 26px 52px); }
.win { position: absolute; width: 26px; height: 34px; border-radius: 4px; background: rgba(255,255,255,0.6); }
.ground { position: absolute; left: 0; right: 0; bottom: 0; height: 120px; }
.phone { position: absolute; width: 360px; height: 700px; border-radius: 54px; background: #1B1C20; padding: 12px; box-shadow: 0 24px 48px rgba(0,0,0,0.25); opacity: 0; }
.screen { position: relative; width: 100%; height: 100%; border-radius: 44px; overflow: hidden; background: #EEF0F4; }
"""

COMMON_JS = """
const tl = gsap.timeline({ paused: true });
const $ = (p, part) => "#" + p + "-" + part;
function mood(p, t, to, from) {
  tl.to($(p, "m-" + from), { opacity: 0, duration: 0.06 }, t);
  tl.to($(p, "m-" + to), { opacity: 1, duration: 0.06 }, t);
  tl.to($(p, "head"), { scaleY: 0.9, scaleX: 1.05, duration: 0.08, ease: "power2.in" }, t - 0.08);
  tl.to($(p, "head"), { scaleY: 1, scaleX: 1, duration: 0.35, ease: "back.out(2.4)" }, t);
}
function blink(p, t) {
  tl.to([$(p, "eyeL"), $(p, "eyeR")], { scaleY: 0.1, duration: 0.06 }, t);
  tl.to([$(p, "eyeL"), $(p, "eyeR")], { scaleY: 1, duration: 0.08 }, t + 0.07);
}
function stride(p, t0, dur, amp, step) {
  const n = Math.max(2, Math.round(dur / step));
  const kl = [], kr = [], al = [], ar = [];
  for (let i = 0; i < n; i++) {
    const s = i % 2 ? 1 : -1;
    kl.push({ rotation: amp * s, duration: step, ease: "sine.inOut" });
    kr.push({ rotation: -amp * s, duration: step, ease: "sine.inOut" });
    al.push({ rotation: -amp * 0.85 * s, duration: step, ease: "sine.inOut" });
    ar.push({ rotation: amp * 0.85 * s, duration: step, ease: "sine.inOut" });
  }
  [kl, kr, al, ar].forEach((k) => k.push({ rotation: 0, duration: 0.18, ease: "power2.out" }));
  tl.to($(p, "legL"), { keyframes: kl }, t0);
  tl.to($(p, "legR"), { keyframes: kr }, t0);
  tl.to($(p, "armL"), { keyframes: al }, t0 + 0.05);
  tl.to($(p, "armR"), { keyframes: ar }, t0 + 0.05);
  const bob = [];
  for (let i = 0; i < n; i++) bob.push({ y: i % 2 ? -10 : 0, duration: step, ease: "sine.inOut" });
  bob.push({ y: 0, duration: 0.18 });
  tl.to($(p, "bob"), { keyframes: bob }, t0);
}
function narrate(id, t) {
  tl.fromTo("#" + id + " span", { opacity: 0, filter: "blur(5px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.14, stagger: 0.08, ease: "power2.out" }, t);
}
function clock(id, t0, dur, m0, m1) {
  const el = document.querySelector("#" + id), box = document.querySelector("#" + id + "-box"), o = { m: m0 };
  const paint = () => {
    const m = Math.floor(o.m), h = m >= 60 ? 9 : 8, mm = m >= 60 ? m - 60 : m;
    el.textContent = h + ":" + String(mm).padStart(2, "0");
    box.style.background = m >= 45 ? "#F2553C" : "#FFFFFF";
    el.style.color = m >= 45 ? "#FFFFFF" : "#121317";
  };
  paint();
  tl.fromTo(o, { m: m0 }, { m: m1, duration: dur, ease: "none", onUpdate: paint }, t0);
}
function glitch(sel, t) {
  tl.to(sel, { keyframes: [{ x: 14, duration: 0.04 }, { x: -16, duration: 0.05 }, { x: 8, duration: 0.04 }, { x: 0, duration: 0.06 }] }, t);
}
"""


def rig(p, x, y, c, mouth="smile", extra=""):
    paths = {
        "smile": '<path id="{p}-m-smile" d="M8 6 Q30 28 52 6" fill="none" stroke="#121317" stroke-width="6" stroke-linecap="round" opacity="{o}"/>',
        "flat": '<path id="{p}-m-flat" d="M14 14 L46 14" fill="none" stroke="#121317" stroke-width="6" stroke-linecap="round" opacity="{o}"/>',
        "o": '<ellipse id="{p}-m-o" cx="30" cy="16" rx="11" ry="14" fill="#121317" opacity="{o}"/>',
        "frown": '<path id="{p}-m-frown" d="M10 24 Q30 4 50 24" fill="none" stroke="#121317" stroke-width="6" stroke-linecap="round" opacity="{o}"/>',
        "grin": '<path id="{p}-m-grin" d="M4 4 Q30 40 56 4 Z" fill="#121317" opacity="{o}"/>',
    }
    m = "".join(v.format(p=p, o=1 if k == mouth else 0) for k, v in paths.items())
    return f"""
      <div id="{p}" class="chr" style="left:{x}px;top:{y}px"><div id="{p}-bob" style="position:absolute;inset:0">
        <div id="{p}-legL" class="leg" style="left:78px;background:{c['pants']}"><div class="shoe"></div></div>
        <div id="{p}-legR" class="leg" style="left:126px;background:{c['pants']}"><div class="shoe"></div></div>
        <div id="{p}-armL" class="arm" style="left:30px;background:{c['coat']}"><div class="hand" style="background:{c['skin']}"></div></div>
        <div id="{p}-armR" class="arm" style="left:180px;background:{c['coat']}"><div class="hand" style="background:{c['skin']}"></div></div>
        <div id="{p}-body" class="body" style="background:{c['coat']}"></div>
        <div id="{p}-head" class="head" style="background:{c['skin']}">
          <div class="hair" style="background:{c['hair']}"></div>
          <div id="{p}-eyeL" class="eye" style="left:44px"></div><div id="{p}-eyeR" class="eye" style="left:90px"></div>
          <svg class="mouth" width="60" height="40" viewBox="0 0 60 40">{m}</svg>
          <div id="{p}-sweat" class="sweat"></div>{extra}
        </div>
      </div></div>"""


BERET = '<div style="position:absolute;left:10px;top:-34px;width:130px;height:52px;border-radius:65px 65px 16px 16px;background:#8A2E3B"></div>'


def narr(sid, lines, y0=118):
    out = []
    for i, line in enumerate(lines):
        words = "".join(f"<span>{w}</span>" for w in line.split())
        out.append(f'<div id="{sid}-n{i}" class="narr" style="top:{y0 + i * 70}px">{words}</div>')
    return "\n    ".join(out)


def clock_html(sid, start="8:00", hidden=False):
    op = "opacity:0;" if hidden else ""
    return f'<div id="{sid}-ck-box" class="ck" style="{op}"><div id="{sid}-ck">{start}</div></div>'


def city(sid, blds, colour="#7C8DB5"):
    out = []
    for i, (x, w, h) in enumerate(blds):
        wins = "".join(f'<div class="win" style="left:{20 + c * 46}px;top:{24 + r * 58}px"></div>'
                       for r in range(max(1, (h - 40) // 58)) for c in range(max(1, (w - 30) // 46)))
        out.append(f'<div class="bld" style="left:{x}px;width:{w}px;height:{h}px;background-color:{colour}">{wins}</div>')
    return "".join(out)


def scene(sid, bg, html, js, extra_css=""):
    return f"""<template>
  <style>{COMMON_CSS}
    #root {{ background: {bg}; }}
    {extra_css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    {html}
  </div>
  <script>{COMMON_JS}
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


SCENES = []


def s_wake():
    sid = "wake"
    html = f"""
    <div class="ground" style="background:#8FA9F5"></div>
    <div style="position:absolute;left:1180px;top:200px;width:460px;height:380px;border-radius:16px;background:#E8F3FF;border:16px solid #FFFFFF">
      <div style="position:absolute;left:206px;top:0;width:16px;height:100%;background:#FFFFFF"></div><div style="position:absolute;left:0;top:166px;width:100%;height:16px;background:#FFFFFF"></div>
      <div style="position:absolute;left:280px;top:40px;width:80px;height:80px;border-radius:50%;background:#FFD36B"></div></div>
    <div style="position:absolute;left:1220px;top:700px;width:380px;height:260px;border-radius:14px;background:#6B4E3D"></div>
    <div id="wake-alarm" style="position:absolute;left:1300px;top:470px;width:220px;height:220px;border-radius:50%;background:#FFFFFF;border:16px solid {RED};
       display:flex;align-items:center;justify-content:center;font-family:'Archivo Black',sans-serif;font-size:60px;color:{INK}">8:00</div>
    {rig('wake-sam', 640, 420, SAM, mouth='o')}
    {narr(sid, ['Sam had one job today.', 'Be at the interview by 9:00.'])}
    {clock_html(sid, hidden=True)}"""
    js = """
    tl.fromTo("#wake-alarm", { rotation: 0 }, { keyframes: [{ rotation: 8, duration: 0.05 }, { rotation: -8, duration: 0.05 },
      { rotation: 8, duration: 0.05 }, { rotation: -8, duration: 0.05 }, { rotation: 8, duration: 0.05 }, { rotation: -8, duration: 0.05 },
      { rotation: 6, duration: 0.05 }, { rotation: -6, duration: 0.05 }, { rotation: 0, duration: 0.05 }] }, 0.2);
    tl.fromTo("#wake-sam-head", { rotation: -6 }, { rotation: 0, duration: 0.6, ease: "power2.inOut" }, 0.4);
    tl.set("#wake-n0 span", { opacity: 1 }, 0);
    blink("wake-sam", 1.2); blink("wake-sam", 1.45);
    mood("wake-sam", 2.0, "smile", "o");
    narrate("wake-n1", 2.4);
    tl.to("#wake-sam-armR", { rotation: -150, duration: 0.35, ease: "back.out(1.6)" }, 3.2);
    tl.to("#wake-sam-armR", { rotation: 0, duration: 0.3, ease: "power2.inOut" }, 4.2);
    // the alarm clock flies up and becomes the corner clock badge
    tl.to("#wake-alarm", { x: 425, y: -305, scale: 0.68, duration: 0.6, ease: "power3.inOut" }, 4.6);
    tl.to("#wake-alarm", { opacity: 0, duration: 0.06 }, 5.2);
    tl.to("#wake-ck-box", { opacity: 1, duration: 0.06 }, 5.18);
    blink("wake-sam", 5.8);
    clock("wake-ck", 5.2, 1.8, 0, 3);
    """
    return sid, "#BFD0FF", html, js


def s_outage():
    sid = "outage"
    html = f"""
    {city(sid, [(0, 260, 520), (290, 220, 380), (540, 300, 600), (1440, 240, 460), (1700, 260, 560)])}
    <div class="ground" style="background:#B8C2D6"></div>
    {rig('outage-sam', 560, 420, SAM)}
    <div id="outage-ph" class="phone" style="left:1060px;top:250px"><div class="screen">
      <svg width="336" height="676" viewBox="0 0 336 676"><g stroke="#FFFFFF" stroke-width="22"><line x1="0" y1="200" x2="336" y2="200"/><line x1="0" y1="430" x2="336" y2="430"/><line x1="90" y1="0" x2="90" y2="676"/><line x1="250" y1="0" x2="250" y2="676"/></g>
        <polyline id="outage-route" points="90,640 90,430 250,430 250,120" fill="none" stroke="{BLUE}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="90" cy="560" r="16" fill="#FFFFFF" stroke="{INK}" stroke-width="6"/></svg>
      <div style="position:absolute;left:18px;top:28px;right:18px;padding:16px 20px;border-radius:20px;background:#FFFFFF;font-weight:800;font-size:28px;color:{INK}">
        <span id="outage-ok">Tower 12, 22 min</span><span id="outage-bad" style="position:absolute;left:20px;color:{RED};opacity:0">Live routes unavailable</span></div>
    </div>
    {narr(sid, ['At 8:12, every AI helper went quiet.', 'The map just stopped.'])}
    {clock_html(sid, '8:10')}"""
    js = """
    clock("outage-ck", 0, 7, 10, 16);
    tl.to("#outage-sam-armR", { rotation: -60, duration: 0.4, ease: "power2.out" }, 0.3);
    tl.fromTo("#outage-ph", { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.5, ease: "expo.out" }, 0.5);
    blink("outage-sam", 1.6);
    // the outage
    glitch("#outage-ph", 3.0);
    tl.to("#outage-route", { attr: { stroke: "#A9AEB8" }, duration: 0.12 }, 3.05);
    tl.to("#outage-ok", { opacity: 0, duration: 0.05 }, 3.08);
    tl.to("#outage-bad", { opacity: 1, duration: 0.08 }, 3.12);
    narrate("outage-n0", 3.4);
    mood("outage-sam", 3.6, "flat", "smile");
    tl.to("#outage-sam-head", { rotation: 8, duration: 0.4, ease: "power2.inOut" }, 3.7);
    narrate("outage-n1", 5.0);
    blink("outage-sam", 5.6);
    """
    return sid, "#9DD3FF", html, js


def s_bus():
    sid = "bus"
    html = f"""
    {city(sid, [(0, 300, 440), (330, 240, 560), (1500, 420, 500)], colour="#C48F6A")}
    <div class="ground" style="background:#C9B8A6"></div>
    <div style="position:absolute;left:420px;top:540px;width:16px;height:420px;background:{INK}"></div>
    <div style="position:absolute;left:360px;top:500px;width:136px;height:70px;border-radius:12px;background:#1E6B52;color:#FFFFFF;font-weight:900;font-size:34px;display:flex;align-items:center;justify-content:center">BUS</div>
    {rig('bus-sam', 520, 420, SAM)}
    <div id="bus-bus" style="position:absolute;left:820px;top:420px;width:1000px;height:470px;border-radius:40px;background:{SUN}">
      <div style="position:absolute;left:60px;top:60px;width:880px;height:150px;border-radius:18px;background:#8FD3FF"></div>
      <div style="position:absolute;left:40px;top:230px;width:120px;height:200px;border-radius:12px;background:#E0A92D"></div>
      <div id="bus-reader" style="position:absolute;left:180px;top:250px;width:150px;height:120px;border-radius:16px;background:{INK}">
        <div id="bus-rs" style="position:absolute;left:12px;top:12px;width:126px;height:62px;border-radius:8px;background:#9BE3B5"></div></div>
      <div style="position:absolute;left:150px;bottom:-50px;width:110px;height:110px;border-radius:50%;background:{INK}"></div>
      <div style="position:absolute;right:150px;bottom:-50px;width:110px;height:110px;border-radius:50%;background:{INK}"></div>
    </div>
    <div id="bus-card" class="bubble" style="left:760px;top:250px;font-size:38px;color:{RED}">Card declined: manual check<div class="tail" style="left:60px"></div></div>
    {narr(sid, ["The bus wouldn't take her card.", 'So she ran.'])}
    {clock_html(sid, '8:20')}"""
    js = """
    clock("bus-ck", 0, 8, 20, 27);
    tl.fromTo("#bus-bus", { x: 1200 }, { x: 0, duration: 1.4, ease: "power3.out" }, 0.3);
    blink("bus-sam", 1.4);
    stride("bus-sam", 1.8, 0.7, 22, 0.17);
    tl.to("#bus-sam", { x: 120, duration: 0.7, ease: "power1.inOut" }, 1.8);
    tl.to("#bus-sam-armR", { rotation: -80, duration: 0.3, ease: "power2.out" }, 2.7);
    glitch("#bus-reader", 3.2);
    tl.to("#bus-rs", { backgroundColor: "#F2553C", duration: 0.08 }, 3.22);
    tl.fromTo("#bus-card", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, 3.3);
    narrate("bus-n0", 3.5);
    mood("bus-sam", 3.6, "frown", "smile");
    tl.to("#bus-sam-armR", { rotation: 0, duration: 0.3 }, 4.2);
    tl.to("#bus-card", { opacity: 0, duration: 0.2 }, 4.6);
    tl.to("#bus-bus", { x: -2200, duration: 1.2, ease: "power3.in" }, 4.5);
    mood("bus-sam", 5.6, "flat", "frown");
    narrate("bus-n1", 6.0);
    stride("bus-sam", 6.6, 1.4, 40, 0.11);
    tl.to("#bus-sam", { x: 1700, duration: 1.4, ease: "power2.in" }, 6.6);
    """
    return sid, "#FFD9A8", html, js


def s_run():
    sid = "run"
    html = f"""
    <div id="run-far" style="position:absolute;left:0;top:0;width:5760px;height:1080px">{city(sid, [(i * 380, 300, 380 + (i * 97) % 260) for i in range(15)], colour="#E08A6E")}</div>
    <div id="run-near" style="position:absolute;left:0;top:0;width:5760px;height:1080px">{city(sid, [(120 + i * 560, 380, 520 + (i * 131) % 200) for i in range(10)], colour="#B5654F")}</div>
    <div class="ground" style="background:#9E7A6B"></div>
    {rig('run-sam', 820, 420, SAM, mouth='o')}
    {narr(sid, ['8:47.', 'Thirteen minutes left.'])}
    {clock_html(sid, '8:27')}"""
    js = """
    tl.fromTo("#run-far", { x: 0 }, { x: -1400, duration: 7, ease: "none" }, 0);
    tl.fromTo("#run-near", { x: 0 }, { x: -3200, duration: 7, ease: "none" }, 0);
    stride("run-sam", 0, 6.8, 42, 0.11);
    clock("run-ck", 0, 4.2, 27, 47);
    tl.fromTo("#run-ck-box", { scale: 1 }, { keyframes: [{ scale: 1.15, duration: 0.12 }, { scale: 1, duration: 0.25, ease: "back.out(2)" }] }, 4.2);
    tl.fromTo("#run-sam-sweat", { opacity: 0, y: 0 }, { opacity: 1, y: 30, duration: 0.6, ease: "power1.in" }, 2.0);
    tl.to("#run-sam-sweat", { opacity: 0, duration: 0.2 }, 2.6);
    narrate("run-n0", 4.3);
    narrate("run-n1", 5.0);
    """
    return sid, "#FFB38A", html, js


def s_tourist():
    sid = "tourist"
    html = f"""
    {city(sid, [(0, 240, 420), (1580, 340, 480)], colour="#E3B94F")}
    <div class="ground" style="background:#D8C79A"></div>
    <div style="position:absolute;left:820px;top:820px;width:300px;height:110px;border-radius:50%;background:#8FC7E8"></div>
    {rig('tourist-sam', 420, 420, SAM, mouth='o')}
    {rig('tourist-t', 1240, 420, TOURIST, mouth='flat', extra=BERET)}
    <div id="tourist-case" style="position:absolute;left:1500px;top:760px;width:150px;height:190px;border-radius:18px;background:#5E3D6B"></div>
    <div id="tourist-ph" style="position:absolute;left:1000px;top:520px;width:190px;height:290px;border-radius:26px;background:#1B1C20;padding:10px;opacity:0">
      <div style="width:100%;height:100%;border-radius:14px;background:#FFFFFF;color:{RED};font-weight:900;font-size:30px;line-height:1.1;padding:18px 12px">No trans&shy;lation</div></div>
    <div id="tourist-b1" class="bubble" style="left:1020px;top:330px">Excusez-moi… Tower 12 ?<div class="tail" style="left:240px"></div></div>
    <div id="tourist-b2" class="bubble" style="left:330px;top:330px">Follow me.<div class="tail" style="left:120px"></div></div>
    {narr(sid, ['Sam was already late.', 'She stopped anyway.'])}
    {clock_html(sid, '8:47')}"""
    js = """
    clock("tourist-ck", 0, 11, 47, 51);
    tl.fromTo("#tourist-t", { x: 700 }, { x: 0, duration: 1.4, ease: "power2.out" }, 0.2);
    tl.fromTo("#tourist-case", { x: 700 }, { x: 0, duration: 1.4, ease: "power2.out" }, 0.25);
    stride("tourist-t", 0.2, 1.3, 22, 0.18);
    stride("tourist-sam", 0, 0.9, 30, 0.12);
    tl.fromTo("#tourist-sam", { x: -500 }, { x: 0, duration: 0.9, ease: "power2.out" }, 0);
    tl.fromTo("#tourist-ph", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, ease: "expo.out" }, 1.7);
    tl.to("#tourist-t-armL", { rotation: 50, duration: 0.3, ease: "power2.out" }, 1.6);
    tl.fromTo("#tourist-b1", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, 2.1);
    mood("tourist-t", 2.2, "frown", "flat");
    narrate("tourist-n0", 2.9);
    // Sam looks at the clock, then back: the choice
    tl.to("#tourist-sam-head", { rotation: -14, x: 8, duration: 0.35, ease: "power2.inOut" }, 3.5);
    tl.fromTo("#tourist-ck-box", { scale: 1 }, { keyframes: [{ scale: 1.15, duration: 0.12 }, { scale: 1, duration: 0.25, ease: "back.out(2)" }] }, 3.6);
    tl.to("#tourist-sam-head", { rotation: 10, x: 0, duration: 0.45, ease: "power2.inOut" }, 4.6);
    blink("tourist-sam", 5.4);
    tl.to("#tourist-b1", { opacity: 0, duration: 0.2 }, 5.6);
    mood("tourist-sam", 6.3, "smile", "o");
    tl.to("#tourist-sam-head", { rotation: 0, duration: 0.4, ease: "power2.inOut" }, 6.3);
    tl.to("#tourist-sam-armR", { rotation: -110, duration: 0.35, ease: "back.out(1.6)" }, 6.5);
    tl.fromTo("#tourist-b2", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, 6.7);
    narrate("tourist-n1", 7.4);
    mood("tourist-t", 8.2, "smile", "frown");
    blink("tourist-t", 9.2);
    """
    return sid, "#FFE7A0", html, js


def s_walk():
    sid = "walk"
    html = f"""
    <div id="walk-far" style="position:absolute;left:0;top:0;width:4000px;height:1080px">{city(sid, [(i * 420, 320, 360 + (i * 89) % 220) for i in range(9)], colour="#7FBF98")}
      <div style="position:absolute;left:2900px;bottom:120px;width:420px;height:860px;border-radius:10px 10px 0 0;background:#3E6D8E"></div>
      <div style="position:absolute;left:2930px;top:340px;width:360px;height:100px;border-radius:12px;background:#FFFFFF;font-family:'Archivo Black',sans-serif;font-size:50px;color:{INK};display:flex;align-items:center;justify-content:center">TOWER 12</div></div>
    <div class="ground" style="background:#8DB59A"></div>
    {rig('walk-sam', 520, 420, SAM)}
    {rig('walk-t', 800, 420, TOURIST, mouth='smile', extra=BERET)}
    <div id="walk-map" style="position:absolute;left:1180px;top:300px;width:520px;height:380px;border-radius:10px;background:#FAFAF7;box-shadow:0 14px 26px rgba(18,19,23,0.18);opacity:0">
      <svg width="520" height="380" viewBox="0 0 520 380"><g stroke="#C9CBD1" stroke-width="8"><line x1="30" y1="110" x2="490" y2="110"/><line x1="30" y1="260" x2="490" y2="260"/><line x1="140" y1="30" x2="140" y2="350"/><line x1="360" y1="30" x2="360" y2="350"/></g>
        <path id="walk-route" d="M140 340 L140 260 L360 260 L360 110 L450 110" fill="none" stroke="{RED}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="700" stroke-dashoffset="700"/>
        <text x="380" y="80" font-family="Nunito" font-weight="900" font-size="30" fill="{INK}">Tower 12</text></svg></div>
    {narr(sid, ['She walked them all the way there.', '9:04. Four minutes late.'])}
    {clock_html(sid, '8:52')}"""
    js = """
    clock("walk-ck", 0, 8.4, 52, 64);
    tl.fromTo("#walk-far", { x: 0 }, { x: -1650, duration: 8.4, ease: "power1.inOut" }, 0);
    stride("walk-sam", 0, 8.2, 26, 0.2);
    stride("walk-t", 0.07, 8.2, 22, 0.22);
    narrate("walk-n0", 0.5);
    tl.fromTo("#walk-map", { opacity: 0, scale: 0.8, rotation: -4 }, { opacity: 1, scale: 1, rotation: -2, duration: 0.45, ease: "expo.out" }, 1.6);
    tl.fromTo("#walk-route", { attr: { "stroke-dashoffset": 700 } }, { attr: { "stroke-dashoffset": 0 }, duration: 2.2, ease: "power2.inOut" }, 2.0);
    tl.to("#walk-map", { opacity: 0, scale: 0.9, duration: 0.3, ease: "power2.in" }, 5.4);
    blink("walk-sam", 3.1); blink("walk-t", 4.3);
    narrate("walk-n1", 8.4);
    mood("walk-sam", 8.5, "frown", "smile");
    tl.fromTo("#walk-sam-sweat", { opacity: 0, y: 0 }, { opacity: 1, y: 24, duration: 0.6, ease: "power1.in" }, 8.7);
    """
    return sid, "#C9F0D2", html, js


def s_twist():
    sid = "twist"
    html = f"""
    <div class="ground" style="background:#B9B0E8;height:160px"></div>
    <div style="position:absolute;left:1120px;top:300px;width:300px;height:420px;border-radius:30px 30px 10px 10px;background:#3A3D45"></div>
    {rig('twist-t', 1150, 330, TOURIST, mouth='smile', extra=BERET)}
    <div id="twist-chair" style="position:absolute;left:1100px;top:280px;width:340px;height:470px;border-radius:40px 40px 14px 14px;background:#2B2D33"></div>
    <div style="position:absolute;left:900px;top:700px;width:760px;height:60px;border-radius:10px;background:#6B4E3D"></div>
    <div style="position:absolute;left:940px;top:760px;width:40px;height:200px;background:#5A4134"></div>
    <div style="position:absolute;left:1580px;top:760px;width:40px;height:200px;background:#5A4134"></div>
    <div id="twist-plate" style="position:absolute;left:1180px;top:640px;width:280px;height:60px;border-radius:8px;background:{INK};color:#FFFFFF;font-weight:900;font-size:28px;display:flex;align-items:center;justify-content:center">Head of Hiring</div>
    {rig('twist-sam', 300, 420, SAM, mouth='frown')}
    <div id="twist-b1" class="bubble" style="left:760px;top:120px">You got me here without a single app.<div class="tail" style="left:520px"></div></div>
    <div id="twist-b2" class="bubble" style="left:900px;top:120px;font-size:48px">When can you start?<div class="tail" style="left:360px"></div></div>
    """
    js = """
    stride("twist-sam", 0.2, 1.2, 22, 0.2);
    tl.fromTo("#twist-sam", { x: -400 }, { x: 0, duration: 1.2, ease: "power2.out" }, 0.2);
    blink("twist-sam", 1.9);
    // the chair turns: it is the tourist
    tl.fromTo("#twist-chair", { scaleX: 1, opacity: 1 }, { scaleX: 0, opacity: 0, duration: 0.45, ease: "power2.in" }, 2.6);
    tl.fromTo("#twist-t", { scaleX: 0.2, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 0.4, ease: "back.out(1.6)" }, 3.0);
    mood("twist-sam", 3.4, "o", "frown");
    tl.to("#twist-sam-head", { y: -18, duration: 0.15, ease: "power2.out" }, 3.4);
    tl.to("#twist-sam-head", { y: 0, duration: 0.3, ease: "power2.inOut" }, 3.6);
    tl.fromTo("#twist-b1", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, 3.8);
    tl.to("#twist-b1", { opacity: 0, duration: 0.2 }, 6.3);
    tl.fromTo("#twist-b2", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, 6.5);
    blink("twist-sam", 7.0);
    mood("twist-sam", 7.6, "grin", "o");
    tl.to("#twist-sam-bob", { keyframes: [{ y: 20, scaleY: 0.92, duration: 0.12, ease: "power2.in" }, { y: -90, scaleY: 1.06, duration: 0.25, ease: "power2.out" },
      { y: 0, scaleY: 1, duration: 0.3, ease: "power2.in" }, { y: 8, scaleY: 0.95, duration: 0.08 }, { y: 0, scaleY: 1, duration: 0.2, ease: "back.out(2)" }] }, 7.8);
    tl.to(["#twist-sam-armL", "#twist-sam-armR"], { rotation: (i) => (i ? -150 : 150), duration: 0.3, ease: "back.out(1.6)" }, 7.95);
    blink("twist-t", 8.6);
    """
    return sid, "#E9E4FF", html, js


def s_end():
    sid = "end"
    html = f"""
    <div id="end-a" style="position:absolute;left:192px;top:250px;font-family:'Archivo Black',sans-serif;font-size:150px;line-height:1;color:#FFFFFF;letter-spacing:-0.03em;white-space:nowrap">The AI stopped.</div>
    <div id="end-b" style="position:absolute;left:186px;top:450px;font-family:'Archivo Black',sans-serif;font-size:190px;line-height:1;color:{SUN};letter-spacing:-0.03em;white-space:nowrap">People didn't.</div>
    <div id="end-c" style="position:absolute;left:196px;top:860px;font-weight:700;font-size:32px;color:#DCE4FF">A story, not a prediction.</div>"""
    js = """
    tl.fromTo("#end-a", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }, 0.3);
    tl.fromTo("#end-b", { opacity: 0, scale: 1.2, filter: "blur(8px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.22, ease: "power4.out" }, 1.4);
    tl.fromTo("#end-c", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 2.4);
    """
    return sid, BLUE, html, js


TIMING = [(s_wake, 0, 7), (s_outage, 7, 7), (s_bus, 14, 8), (s_run, 22, 7), (s_tourist, 29, 11),
          (s_walk, 40, 10), (s_twist, 50, 10), (s_end, 60, 6)]
TOTAL = 66

# sound: (file, start, volume); peaks land about one frame after their picture
SFX = [("tap-a", 0.22, 0.6), ("tap-b", 0.32, 0.6), ("tap-a", 0.42, 0.6), ("tap-b", 0.52, 0.6), ("whoosh", 11.5 - 0.0 - 6.9, 0.5),
       ("glitch", 10.03, 0.9), ("whoosh", 14.3, 0.5), ("glitch", 17.23, 0.9), ("pop", 17.33, 0.6), ("whoosh", 18.6, 0.8),
       ("pop", 31.13, 0.7), ("pop", 35.73, 0.7), ("pop", 53.83, 0.7), ("pop", 56.53, 0.8), ("riser", 61.04, 0.8)]
# accelerating clock ticks through the run, footsteps while walking
t, gap = 22.0, 0.5
while t < 28.8:
    SFX.append(("tap-b", round(t, 2), 0.45)); t += gap; gap = max(0.13, gap * 0.9)
for k in range(12):
    SFX.append(("tap-a" if k % 2 else "tap-b", round(40.2 + k * 0.4, 2), 0.25))
MUSIC = [("music-morning", 0, 10.0, 0.5), ("music-tense", 10.0, 23.0, 0.4), ("music-warm", 52.5, 13.5, 0.55)]


def main():
    for fn, start, dur in TIMING:
        sid, bg, html, js = fn()
        open(f"compositions/{sid}.html", "w").write(scene(sid, bg, html, js))
    hosts = "\n".join(
        f'      <div id="{fn()[0]}" data-composition-id="{fn()[0]}" data-composition-src="compositions/{fn()[0]}.html" data-start="{s}" '
        f'data-duration="{d}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{i + 1}"></div>'
        for i, (fn, s, d) in enumerate(TIMING))
    import subprocess
    def dur(f):
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                    capture_output=True, text=True).stdout)
    aud = [f'      <audio id="mu-{i}" class="clip" src="assets/{n}.wav" data-start="{s}" data-duration="{d}" data-track-index="2" data-volume="{v}"></audio>'
           for i, (n, s, d, v) in enumerate(MUSIC)]
    lanes = {}
    for i, (n, s, v) in enumerate(sorted(SFX, key=lambda x: x[1])):
        d = dur(f"assets/sfx-{n}.wav")
        lane = next(k for k in range(3, 20) if lanes.get(k, -1) <= s)  # no overlaps within a lane
        lanes[lane] = s + d
        aud.append(f'      <audio id="fx-{i}" class="clip" src="assets/sfx-{n}.wav" data-start="{s}" data-duration="{d:.2f}" data-track-index="{lane}" data-volume="{v}"></audio>')
    open("index.html", "w").write(f"""<!doctype html>
<html lang="en" data-composition-variables='{json.dumps([
        {"id": "color-ink", "type": "color", "label": "Ink", "default": INK},
        {"id": "color-accent", "type": "color", "label": "Accent (payoff)", "default": SUN},
        {"id": "color-sam", "type": "color", "label": "Sam coat colour", "default": BLUE}])}'>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #BFD0FF; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{hosts}
{chr(10).join(aud)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
    print("built", len(TIMING), "scenes,", len(SFX), "sound effects")


if __name__ == "__main__":
    main()
