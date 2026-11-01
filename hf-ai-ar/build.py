#!/usr/bin/env python3
"""Build "لو الذكاء الاصطناعي وقف فجأة" (What if AI suddenly stopped?), a 2-minute Egyptian-Arabic explainer.

Each scene narrates part of the script as right-to-left captions. Scene length comes from its word count
(WPS words a second), and every animation is placed as a fraction of the scene, so re-timing to a recorded
voice only means changing scene durations: pass a JSON list of scene durations with --durations.

Motif: anything AI-powered is drawn in teal (#00A896); when the AI stops it turns grey and fades.

Run: python3 build.py [--durations durations.json]
"""
import json
import subprocess
import sys

INK, SUN, RED, BLUE, TEAL, GREY = "#121317", "#FFC93C", "#F2553C", "#2348F2", "#00897B", "#A9AEB8"
GREEN, AMBER = "#1E6B52", "#FFE3A3"
WPS = 2.4  # spoken words a second, Egyptian narration

FONT_CSS = """
@font-face { font-family: "Cairo"; src: url("assets/fonts/Cairo.ttf") format("truetype"); font-weight: 200 1000; }
@font-face { font-family: "Noto Kufi Arabic"; src: url("assets/fonts/NotoKufiArabic.ttf") format("truetype"); font-weight: 100 900; }
"""

COMMON_CSS = FONT_CSS + """
#root { position: absolute; inset: 0; overflow: hidden; font-family: "Cairo", sans-serif; direction: rtl; }
.cap { position: absolute; left: 50%; bottom: 70px; transform: translateX(-50%); width: max-content; max-width: 1500px; padding: 18px 40px; border-radius: 20px;
  background: rgba(255,255,255,0.94); color: #121317; font-weight: 800; font-size: 44px; line-height: 1.45; text-align: center; opacity: 0;
  box-shadow: 0 8px 20px rgba(18,19,23,0.12); }
.phone { position: absolute; width: 440px; height: 820px; border-radius: 66px; background: #1B1C20; padding: 14px; box-shadow: 0 30px 60px rgba(0,0,0,0.25); }
.screen { position: relative; width: 100%; height: 100%; border-radius: 54px; overflow: hidden; background: #EEF0F4; direction: rtl; }
.lbl { position: absolute; font-weight: 800; font-size: 34px; color: #121317; white-space: nowrap; }
.tick { position: absolute; width: 64px; height: 64px; border-radius: 50%; background: #34A853; color: #FFFFFF; font-size: 40px; font-weight: 900;
  display: flex; align-items: center; justify-content: center; opacity: 0; }
.cross { position: absolute; width: 64px; height: 64px; border-radius: 50%; background: #F2553C; color: #FFFFFF; font-size: 40px; font-weight: 900;
  display: flex; align-items: center; justify-content: center; opacity: 0; }
.card { position: absolute; border-radius: 26px; background: #FFFFFF; box-shadow: 0 16px 34px rgba(18,19,23,0.16); }
.bld { position: absolute; bottom: 0; border-radius: 6px 6px 0 0; }
.win { position: absolute; width: 26px; height: 34px; border-radius: 4px; background: rgba(255,255,255,0.65); }
"""

COMMON_JS = """
const tl = gsap.timeline({ paused: true });
const D = __D__;
const at = (f) => f * D;
function pop(sel, f, s0) {
  tl.fromTo(sel, { opacity: 0, scale: s0 || 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.7)" }, at(f));
}
function show(sel, f, dur) { tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: dur || 0.3, ease: "power2.out" }, at(f)); }
function rise(sel, f) { tl.fromTo(sel, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, at(f)); }
function aiOff(sel, f) {  // the teal AI layer greys out and fades
  tl.to(sel, { keyframes: [{ x: 8, duration: 0.04 }, { x: -10, duration: 0.05 }, { x: 0, duration: 0.05 }] }, at(f));
  tl.to(sel, { filter: "grayscale(1)", opacity: 0.25, duration: 0.5, ease: "power2.out" }, at(f) + 0.12);
}
function captions(prefix, spans) {  // spans: [[startFrac, endFrac], ...]
  spans.forEach(([a, b], i) => {
    const id = "#" + prefix + "-cap" + i;
    if (a === 0) tl.set(id, { opacity: 1 }, 0);
    else tl.fromTo(id, { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "power2.out" }, at(a));
    if (b < 0.999) tl.to(id, { opacity: 0, duration: 0.18, ease: "power2.in" }, at(b) - 0.18);
  });
}
"""

# ------------------------------------------------------------------ script, split into scenes and captions
SCENES = [
    ("map", ["الخريطة لسه مفتوحة على موبايلك. الشوارع موجودة، والنقطة الزرقا اللي هي إنت موجودة.",
             "بس فيه حاجة غريبة. مبقتش بتتوقع الزحمة.",
             "مبقتش بتقولك: \"اطلع يمين، فيه طريق أسرع\". الخريطة بقت… مجرد خريطة."]),
    ("street", ["إنت فاكر إن النت فاصل. بس النت شغال. الكهربا شغالة.",
                "العربيات ماشية، والناس رايحة شغلها عادي.",
                "اللي اختفى حاجة ماكانش حد شايفها أصلًا."]),
    ("rules", ["النهارده الصبح، كل أنظمة الذكاء الاصطناعي في العالم وقفت. من غير إنذار، ومن غير تفسير.",
               "البرامج العادية شغالة، والآلات شغالة، والبشر شغالين.",
               "اللي وقف بس هو الحاجة اللي كانت بتتعلم، وبتخمّن، وبتقرر بالنيابة عننا."]),
    ("inbox", ["وهنا تبدأ الاكتشافات الصغيرة.",
               "الإيميل بتاعك اتملى رسايل نصب، كان فيه فلتر بيصطادها من غير ما تحس."]),
    ("apps", ["التطبيق اللي كان بيختارلك تتفرج على إيه، بقى بيعرض كل حاجة بنفس الترتيب الممل.",
              "ولو كلمت خدمة العملاء، مفيش شات بوت يرد… لازم تستنى دورك مع إنسان."]),
    ("zoom", ["لكن القصة أكبر من موبايلك."]),
    ("bank", ["في البنوك، فيه أنظمة كانت بتبص على كل عملية بالكارت، وتشم ريحة الاحتيال في لحظة.",
              "من غيرها، غالبًا الحماية هتبقى أبطأ، وعمليات كتير ممكن تتأخر لحد ما حد يراجعها بإيده."]),
    ("ship", ["في شركات الشحن، خطوط السير اللي كانت بتتحسب أوتوماتيك، يمكن ترجع تتحسب بالورقة والقلم."]),
    ("xray", ["وفي بعض المستشفيات، البرامج اللي بتساعد الدكاترة يقروا الأشعة هتسكت…",
              "بس الدكتور نفسه لسه موجود، وعينه لسه شغالة."]),
    ("slow", ["وهنا المفاجأة.", "العالم ماوقعش. العالم بقى أبطأ.", "وأغلى شوية، وأزحم شوية، وأقرب للغلط."]),
    ("lift", ["يعني الذكاء الاصطناعي ماكانش الأساس اللي البيت واقف عليه… كان أقرب للأسانسير.",
              "تقدر تطلع من غيره، بس هتتعب. وهتكتشف إنك نسيت السلم من زمان."]),
    ("ask", ["والسؤال الحقيقي مش عن الآلة. السؤال عننا.",
             "إحنا لسه بنعرف نعمل اللي كانت بتعمله؟",
             "لسه بنعرف نلاقي طريقنا من غير ما حد يقولنا \"اطلع يمين\"؟"]),
    ("end", ["يمكن الخطر عمره ما كان إن الذكاء الاصطناعي يقف…",
             "الخطر إنه يقف في يوم، نكون فيه نسينا إزاي نمشي من غيره."]),
]


def words(s):
    return len(s.replace("…", " ").split())


def default_durations():
    return [round(sum(words(c) for c in caps) / WPS + 1.0, 2) for _, caps in SCENES]


def spans(caps):
    """Caption windows as fractions of the scene, proportional to words, with 0.4 s lead-in."""
    total = sum(words(c) for c in caps)
    out, acc = [], 0.0
    for c in caps:
        w = words(c) / total
        out.append([round(0.03 + acc * 0.95, 4), round(min(1.0, 0.03 + (acc + w) * 0.95), 4)])
        acc += w
    out[-1][1] = 1.0
    return out


def city(blds, colour):
    out = []
    for x, w, h in blds:
        wins = "".join(f'<div class="win" style="left:{20 + c * 46}px;top:{24 + r * 58}px"></div>'
                       for r in range(max(1, (h - 40) // 58)) for c in range(max(1, (w - 30) // 46)))
        out.append(f'<div class="bld" style="left:{x}px;width:{w}px;height:{h}px;background:{colour}">{wins}</div>')
    return "".join(out)


# ------------------------------------------------------------------ scene visuals: (background, html, js)
def v_map(s):
    html = f"""
    <div class="phone" style="left:1180px;top:50px"><div class="screen">
      <svg width="412" height="872" viewBox="0 0 412 872" style="position:absolute;inset:0">
        <rect x="0" y="520" width="412" height="80" fill="#CFE0F7"/><rect x="250" y="110" width="140" height="160" rx="14" fill="#CFE8D5"/>
        <g stroke="#FFFFFF" stroke-width="30"><line x1="0" y1="300" x2="412" y2="300"/><line x1="0" y1="700" x2="412" y2="700"/>
          <line x1="110" y1="0" x2="110" y2="872"/><line x1="300" y1="0" x2="300" y2="872"/></g>
        <g id="map-ai">
          <line x1="110" y1="300" x2="110" y2="700" stroke="{RED}" stroke-width="14"/><line x1="0" y1="700" x2="110" y2="700" stroke="#F5A623" stroke-width="14"/>
          <polyline points="110,780 110,700 300,700 300,300 300,120" fill="none" stroke="{TEAL}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
        <circle id="map-me" cx="110" cy="780" r="20" fill="{BLUE}" stroke="#FFFFFF" stroke-width="7"/>
      </svg>
      <div id="map-tip" class="card" style="left:20px;right:20px;top:40px;padding:20px 24px;background:{TEAL};color:#FFFFFF;font-weight:800;font-size:30px">اطلع يمين: فيه طريق أسرع</div>
    </div></div>
    <div id="map-dot" style="position:absolute;left:440px;top:300px;width:300px;height:300px;border-radius:50%;background:{BLUE};opacity:0;display:flex;align-items:center;justify-content:center">
      <div id="map-q" style="font-family:'Noto Kufi Arabic';font-weight:900;font-size:180px;line-height:1;color:#FFFFFF;opacity:0;margin-top:-20px">؟</div></div>"""
    js = """
    tl.fromTo("#map-me", { attr: { cx: 110, cy: 780 } }, { keyframes: [{ attr: { cx: 110, cy: 700 }, duration: D * 0.08, ease: "none" },
      { attr: { cx: 300, cy: 700 }, duration: D * 0.16, ease: "none" }, { attr: { cx: 300, cy: 560 }, duration: D * 0.1, ease: "power1.out" }] }, at(0.04));
    tl.fromTo("#map-tip", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, at(0.05));
    aiOff("#map-ai", 0.38);
    aiOff("#map-tip", 0.66);
    tl.to("#map-tip", { opacity: 0, duration: 0.3 }, at(0.85));
    pop("#map-dot", 0.42); show("#map-q", 0.46);
    """
    return "#9DB8FF", html, js


def v_street(s):
    html = f"""
    {city([(0, 300, 560), (330, 260, 420), (620, 320, 640), (1400, 260, 480), (1690, 240, 560)], "#7C8DB5")}
    <div style="position:absolute;left:0;right:0;bottom:0;height:230px;background:#5E6A82"></div>
    <div id="street-car" style="position:absolute;left:-420px;top:740px;width:340px;height:120px;border-radius:40px 60px 16px 16px;background:{SUN}">
      <div style="position:absolute;left:40px;bottom:-30px;width:70px;height:70px;border-radius:50%;background:{INK}"></div>
      <div style="position:absolute;right:40px;bottom:-30px;width:70px;height:70px;border-radius:50%;background:{INK}"></div></div>
    <div id="street-wifi" style="position:absolute;left:700px;top:240px;width:150px;height:150px;border-radius:30px;background:#FFFFFF;display:flex;align-items:center;justify-content:center"><svg width="100" height="80" viewBox="0 0 100 80"><g fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"><path d="M10 30 Q50 -6 90 30"/><path d="M26 46 Q50 24 74 46"/></g><circle cx="50" cy="64" r="9" fill="{INK}"/></svg></div>
    <div id="street-bulb" style="position:absolute;left:400px;top:300px;width:110px;height:110px;border-radius:50%;background:{SUN};border:10px solid #FFFFFF"></div>
    <div id="street-t1" class="tick" style="left:480px;top:280px">✓</div><div id="street-t2" class="tick" style="left:820px;top:220px">✓</div>
    <div id="street-t3" class="tick" style="left:1040px;top:640px">✓</div><div id="street-t4" class="tick" style="left:1480px;top:560px">✓</div>
    <div style="position:absolute;left:1420px;top:630px;width:60px;height:60px;border-radius:50%;background:{INK}"></div>
    <div style="position:absolute;left:1405px;top:700px;width:90px;height:170px;border-radius:40px 40px 14px 14px;background:{INK}"></div>
    <svg id="street-net" width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0;opacity:0">
      <g stroke="{TEAL}" stroke-width="6" stroke-dasharray="14 14" fill="none"><path d="M455 355 C 700 200, 900 200, 775 315"/><path d="M775 315 C 900 600, 1100 650, 1450 660"/>
        <path d="M455 355 C 600 700, 900 800, 1000 790"/><path d="M1000 790 C 1200 700, 1300 690, 1450 660"/></g>
      <g fill="{TEAL}"><circle cx="455" cy="355" r="14"/><circle cx="775" cy="315" r="14"/><circle cx="1000" cy="790" r="14"/><circle cx="1450" cy="660" r="14"/></g></svg>"""
    js = """
    tl.fromTo("#street-car", { x: 0 }, { x: 2600, duration: D * 0.9, ease: "none" }, at(0.05));
    pop("#street-t2", 0.12); pop("#street-t1", 0.2); pop("#street-t3", 0.38); pop("#street-t4", 0.46);
    show("#street-net", 0.6, 0.5);
    aiOff("#street-net", 0.8);
    tl.to("#street-net", { opacity: 0, duration: 0.4 }, at(0.93));
    """
    return "#9DD3FF", html, js


def v_rules(s):
    html = f"""
    <div style="position:absolute;left:960px;top:0;width:960px;height:1080px;background:#EDEFF4"></div>
    <div class="lbl" style="right:220px;top:150px;font-size:54px;font-family:'Noto Kufi Arabic';font-weight:900">لسه شغال</div>
    <div id="rules-a" class="lbl" style="right:330px;top:300px">البرامج العادية</div><div id="rules-ta" class="tick" style="right:220px;top:290px">✓</div>
    <div id="rules-b" class="lbl" style="right:330px;top:420px">الآلات</div><div id="rules-tb" class="tick" style="right:220px;top:410px">✓</div>
    <div id="rules-c" class="lbl" data-hold style="right:330px;top:540px">البشر</div><div id="rules-tc" class="tick" style="right:220px;top:530px">✓</div>
    <div class="lbl" style="right:1180px;top:150px;font-size:54px;font-family:'Noto Kufi Arabic';font-weight:900;color:#FFFFFF">وقف</div>
    <svg id="rules-brain" width="420" height="320" viewBox="0 0 420 320" style="position:absolute;left:290px;top:270px">
      <g stroke="{TEAL}" stroke-width="8"><line x1="60" y1="60" x2="210" y2="160"/><line x1="60" y1="260" x2="210" y2="160"/><line x1="210" y1="160" x2="360" y2="60"/>
        <line x1="210" y1="160" x2="360" y2="260"/><line x1="60" y1="60" x2="60" y2="260"/><line x1="360" y1="60" x2="360" y2="260"/></g>
      <g fill="{TEAL}"><circle cx="60" cy="60" r="30"/><circle cx="60" cy="260" r="30"/><circle cx="210" cy="160" r="40"/><circle cx="360" cy="60" r="30"/><circle cx="360" cy="260" r="30"/></g>
      <circle id="rules-pulse" cx="60" cy="60" r="14" fill="#FFFFFF"/></svg>
    <div id="rules-x" class="cross" style="left:660px;top:250px">✕</div>
    <div class="lbl" data-hold style="right:1190px;top:650px;color:#FFFFFF;font-size:38px">بيتعلم · بيخمّن · بيقرر</div>"""
    js = """
    rise("#rules-brain", 0.05);
    tl.fromTo("#rules-pulse", { attr: { cx: 60, cy: 60 } }, { keyframes: [{ attr: { cx: 210, cy: 160 }, duration: 0.5 }, { attr: { cx: 360, cy: 60 }, duration: 0.5 },
      { attr: { cx: 360, cy: 260 }, duration: 0.5 }, { attr: { cx: 210, cy: 160 }, duration: 0.5 }, { attr: { cx: 60, cy: 260 }, duration: 0.5 }, { attr: { cx: 60, cy: 60 }, duration: 0.5 }], ease: "none" }, at(0.08));
    aiOff("#rules-brain", 0.3); pop("#rules-x", 0.34);
    rise("#rules-a", 0.5); pop("#rules-ta", 0.53); rise("#rules-b", 0.58); pop("#rules-tb", 0.61); rise("#rules-c", 0.66); pop("#rules-tc", 0.69);
    """
    return INK, html, js


def v_inbox(s):
    rows = ["مبروك! كسبت جايزة", "شحنتك متوقفة", "أكّد حسابك فورًا", "ضاعف فلوسك في يوم", "استرد ضريبتك دلوقتي", "آخر فرصة!!!", "حسابك اتقفل", "عرض النهارده بس"]
    rh = "".join(f'<div id="inbox-r{i}" style="position:absolute;left:0;right:0;top:{i * 92}px;height:92px;padding:16px 30px;border-bottom:2px solid #ECEEF2;background:#FFFFFF;font-weight:800;font-size:30px;color:{INK};opacity:0">{t}</div>' for i, t in enumerate(rows))
    html = f"""
    <div class="phone" style="left:1180px;top:50px"><div class="screen" style="background:#FFFFFF">
      <div style="position:absolute;right:34px;top:60px;font-weight:900;font-size:48px;color:{INK}">البريد</div>
      <div id="inbox-shield" style="position:absolute;left:30px;top:56px;width:120px;height:58px;border-radius:16px;background:{TEAL};color:#FFFFFF;font-weight:900;font-size:28px;display:flex;align-items:center;justify-content:center">فلتر</div>
      <div style="position:absolute;left:0;right:0;top:150px;bottom:0;overflow:hidden">{rh}</div>
    </div></div>
    <div id="inbox-big" style="position:absolute;left:300px;top:250px;width:520px;height:380px;border-radius:30px;background:#FFFFFF;box-shadow:0 20px 40px rgba(0,0,0,0.2);opacity:0">
      <div style="position:absolute;left:0;right:0;top:0;height:120px;border-radius:30px 30px 0 0;background:{RED}"></div>
      <div style="position:absolute;left:150px;top:30px;width:220px;height:150px;border-left:110px solid transparent;border-right:110px solid transparent;border-top:120px solid #FFFFFF;width:0;height:0"></div>
      <div style="position:absolute;right:40px;bottom:50px;font-weight:900;font-size:60px;color:{RED}">نصب؟</div></div>"""
    js = """
    aiOff("#inbox-shield", 0.3);
    for (let i = 0; i < 8; i++) tl.fromTo("#inbox-r" + i, { opacity: 0, x: 60 }, { opacity: 1, x: 0, duration: 0.25, ease: "expo.out" }, at(0.36 + i * 0.06));
    pop("#inbox-big", 0.5);
    """
    return RED, html, js


def v_apps(s):
    th = "".join(f'<div id="apps-t{i}" style="position:absolute;left:{110 + (i % 3) * 230}px;top:{200 + (i // 3) * 170}px;width:210px;height:150px;border-radius:14px;background:{["#F28C28", "#8A2E3B", "#2348F2", "#1E6B52", "#5E3D6B", "#F2553C"][i]}">'
                 f'<div id="apps-b{i}" style="position:absolute;right:8px;top:8px;padding:2px 12px;border-radius:10px;background:{TEAL};color:#FFFFFF;font-weight:800;font-size:28px">ليك</div></div>' for i in range(6))
    html = f"""
    <div class="card" style="left:80px;top:120px;width:760px;height:600px;background:#1B1C20">
      <div style="position:absolute;right:40px;top:28px;font-weight:900;font-size:40px;color:#FFFFFF">مقترح لك</div></div>
    {th}
    <div class="card" style="left:1060px;top:120px;width:700px;height:600px">
      <div style="position:absolute;right:36px;top:28px;font-weight:900;font-size:40px;color:{INK}">خدمة العملاء</div>
      <div id="apps-bot" style="position:absolute;right:36px;top:130px;padding:20px 26px;border-radius:22px;background:{TEAL};color:#FFFFFF;font-weight:800;font-size:32px">أهلًا! أقدر أساعدك إزاي؟</div>
      <div id="apps-q" style="position:absolute;left:0;right:0;top:300px;text-align:center;font-weight:800;font-size:34px;color:#5A5F6B;opacity:0">دورك في الانتظار</div>
      <div id="apps-n" style="position:absolute;left:0;right:0;top:350px;text-align:center;font-family:'Archivo Black',sans-serif;font-size:150px;color:{INK};opacity:0;direction:ltr">57</div></div>"""
    js = """
    for (let i = 0; i < 6; i++) aiOff("#apps-b" + i, 0.18 + i * 0.03);
    tl.to(["#apps-t0", "#apps-t1", "#apps-t2", "#apps-t3", "#apps-t4", "#apps-t5"], { backgroundColor: "#6B6F7A", duration: 0.6, stagger: 0.05 }, at(0.3));
    aiOff("#apps-bot", 0.58);
    show("#apps-q", 0.66); show("#apps-n", 0.68);
    const n = { v: 57 }, el = document.querySelector("#apps-n");
    tl.fromTo(n, { v: 57 }, { v: 54, duration: D * 0.28, ease: "none", onUpdate: () => { el.textContent = String(Math.round(n.v)); } }, at(0.7));
    """
    return GREEN, html, js


def v_zoom(s):
    html = f"""
    <svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">
      <g stroke="#FFFFFF" stroke-width="26" opacity="0.7"><line x1="0" y1="330" x2="1920" y2="330"/><line x1="0" y1="760" x2="1920" y2="760"/>
        <line x1="480" y1="0" x2="480" y2="1080"/><line x1="1300" y1="0" x2="1300" y2="1080"/></g>
      <g id="zoom-net" stroke="{TEAL}" stroke-width="8" stroke-dasharray="16 14" fill="none"><path d="M960 540 L480 330"/><path d="M960 540 L1500 330"/><path d="M960 540 L1300 780"/></g></svg>
    <div id="zoom-ph" class="phone" style="left:740px;top:90px;transform-origin:220px 450px"></div>
    <div id="zoom-p1" class="card" style="left:330px;top:230px;padding:18px 30px;font-weight:900;font-size:40px">بنك</div>
    <div id="zoom-p2" class="card" style="left:1400px;top:230px;padding:18px 30px;font-weight:900;font-size:40px">شحن</div>
    <div id="zoom-p3" class="card" style="left:1200px;top:700px;padding:18px 30px;font-weight:900;font-size:40px">مستشفى</div>"""
    js = """
    tl.fromTo("#zoom-ph", { scale: 1 }, { scale: 0.12, duration: D * 0.4, ease: "power3.inOut" }, at(0.02));
    tl.fromTo("#zoom-net", { opacity: 0 }, { opacity: 1, duration: 0.4 }, at(0.35));
    pop("#zoom-p1", 0.45); pop("#zoom-p2", 0.55); pop("#zoom-p3", 0.65);
    """
    return "#9DB8FF", html, js


def v_bank(s):
    rows = "".join(f'<div id="bank-r{i}" data-layout-allow-overlap style="position:absolute;left:30px;right:30px;top:{120 + i * 96}px;height:80px;border-radius:14px;background:#F3F5F9;padding:0 24px;display:flex;align-items:center;justify-content:space-between;font-weight:800;font-size:32px;color:{INK}">'
                   f'<span>عملية كارت</span><span id="bank-s{i}" style="color:#1E7B3A">تمام</span></div>' for i in range(5))
    html = f"""
    <div class="card" style="left:1000px;top:110px;width:720px;height:640px">{rows}
      <div style="position:absolute;right:34px;top:30px;font-weight:900;font-size:40px;color:{INK}">العمليات</div></div>
    <svg id="bank-radar" width="520" height="520" viewBox="0 0 520 520" style="position:absolute;left:240px;top:170px">
      <circle cx="260" cy="260" r="240" fill="none" stroke="{TEAL}" stroke-width="10"/><circle cx="260" cy="260" r="160" fill="none" stroke="{TEAL}" stroke-width="6"/>
      <circle cx="260" cy="260" r="80" fill="none" stroke="{TEAL}" stroke-width="6"/><line id="bank-arm" x1="260" y1="260" x2="260" y2="30" stroke="{TEAL}" stroke-width="12" stroke-linecap="round"/></svg>
    <div id="bank-hand" class="card" data-layout-allow-overlap style="left:300px;top:300px;padding:26px 34px;font-weight:900;font-size:40px;opacity:0">مراجعة باليد</div>"""
    js = """
    tl.fromTo("#bank-arm", { rotation: 0, svgOrigin: "260 260" }, { rotation: 720, svgOrigin: "260 260", duration: D * 0.4, ease: "none" }, 0);
    aiOff("#bank-radar", 0.42);
    const s = [0, 1, 2, 3, 4].map((i) => "#bank-s" + i);
    tl.to(s, { color: "#F2553C", duration: 0.1, stagger: 0.25 }, at(0.5));
    show("#bank-hand", 0.62);
    tl.to("#bank-hand", { keyframes: [{ x: 640, y: -170, duration: 0.6, ease: "power2.inOut" }, { y: -74, duration: 0.7, ease: "power1.inOut" },
      { y: 22, duration: 0.7, ease: "power1.inOut" }, { y: 118, duration: 0.7, ease: "power1.inOut" }, { y: 214, duration: 0.7, ease: "power1.inOut" }] }, at(0.66));
    const labels = document.querySelectorAll("[id^=bank-s]"), st = { k: 0 };
    tl.fromTo(st, { k: 0 }, { k: 5, duration: 1.25, ease: "none", onUpdate: () => labels.forEach((l, i) => { l.textContent = i < st.k ? "مستني مراجعة" : "تمام"; }) }, at(0.5));
    """
    return AMBER, html, js


def v_ship(s):
    html = f"""
    <div class="card" style="left:200px;top:110px;width:1520px;height:640px;background:#EEF0F4">
      <svg width="1520" height="640" viewBox="0 0 1520 640"><g stroke="#FFFFFF" stroke-width="30"><line x1="0" y1="200" x2="1520" y2="200"/><line x1="0" y1="460" x2="1520" y2="460"/>
        <line x1="380" y1="0" x2="380" y2="640"/><line x1="900" y1="0" x2="900" y2="640"/><line x1="1260" y1="0" x2="1260" y2="640"/></g>
        <polyline id="ship-ai" points="120,560 380,460 900,460 900,200 1400,120" fill="none" stroke="{TEAL}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
        <path id="ship-pen" d="M120 560 C 260 520, 330 420, 380 380 S 640 330, 700 300 S 1000 200, 1100 220 S 1300 140, 1400 120" fill="none" stroke="{INK}" stroke-width="8" stroke-dasharray="1600" stroke-dashoffset="1600" stroke-linecap="round"/>
        <g fill="{SUN}" stroke="{INK}" stroke-width="5"><rect x="1370" y="90" width="70" height="50" rx="8"/></g>
        <rect id="ship-truck" x="90" y="530" width="70" height="50" rx="8" fill="{SUN}" stroke="{INK}" stroke-width="5"/></svg></div>
    <div id="ship-tag" class="card" style="left:240px;top:150px;padding:16px 26px;font-weight:900;font-size:36px;background:#FFF6D6">ورقة وقلم</div>"""
    js = """
    aiOff("#ship-ai", 0.3);
    tl.fromTo("#ship-pen", { attr: { "stroke-dashoffset": 1600 } }, { attr: { "stroke-dashoffset": 0 }, duration: D * 0.45, ease: "power1.inOut" }, at(0.45));
    pop("#ship-tag", 0.42);
    tl.fromTo("#ship-truck", { attr: { x: 90, y: 530 } }, { keyframes: [{ attr: { x: 345, y: 355 }, duration: D * 0.12 }, { attr: { x: 670, y: 275 }, duration: D * 0.12 },
      { attr: { x: 1070, y: 195 }, duration: D * 0.12 }, { attr: { x: 1300, y: 100 }, duration: D * 0.1 }], ease: "none" }, at(0.5));
    """
    return "#C9F0D2", html, js


def v_xray(s):
    html = f"""
    <div class="card" style="left:960px;top:100px;width:620px;height:680px;background:#1B1C20">
      <svg width="620" height="680" viewBox="0 0 620 680"><g stroke="#DCE4F2" stroke-width="12" fill="none" stroke-linecap="round">
        <line x1="310" y1="80" x2="310" y2="600"/>
        <path d="M310 170 C 220 160, 160 200, 150 250"/><path d="M310 170 C 400 160, 460 200, 470 250"/>
        <path d="M310 250 C 210 240, 140 290, 130 340"/><path d="M310 250 C 410 240, 480 290, 490 340"/>
        <path d="M310 330 C 210 320, 140 370, 135 420"/><path d="M310 330 C 410 320, 480 370, 485 420"/>
        <path d="M310 410 C 220 400, 160 440, 160 490"/><path d="M310 410 C 400 400, 460 440, 460 490"/></g>
        <rect id="xray-ai" x="380" y="270" width="140" height="120" rx="10" fill="none" stroke="{TEAL}" stroke-width="8"/></svg>
      <div id="xray-tag" style="position:absolute;right:30px;top:20px;padding:8px 18px;border-radius:12px;background:{TEAL};color:#FFFFFF;font-weight:800;font-size:28px">منطقة تحتاج نظرة</div></div>
    <div id="xray-eye" style="position:absolute;left:360px;top:300px;width:360px;height:200px;opacity:0">
      <svg width="360" height="200" viewBox="0 0 360 200"><path d="M10 100 Q180 -40 350 100 Q180 240 10 100 Z" fill="#FFFFFF" stroke="{INK}" stroke-width="10"/>
        <circle cx="180" cy="100" r="54" fill="{BLUE}"/><circle cx="180" cy="100" r="24" fill="{INK}"/></svg></div>
    <div id="xray-dr" class="lbl" style="left:420px;top:540px;font-size:44px;opacity:0">الدكتور لسه هنا</div>"""
    js = """
    aiOff("#xray-ai", 0.35); aiOff("#xray-tag", 0.37);
    pop("#xray-eye", 0.62); show("#xray-dr", 0.7);
    tl.to("#xray-eye", { x: 40, duration: D * 0.2, ease: "sine.inOut" }, at(0.75));
    """
    return "#BFD0FF", html, js


def v_slow(s):
    html = f"""
    <svg width="760" height="460" viewBox="0 0 760 460" style="position:absolute;left:580px;top:160px">
      <path d="M60 400 A320 320 0 0 1 700 400" fill="none" stroke="#FFFFFF" stroke-width="40" stroke-linecap="round"/>
      <path d="M60 400 A320 320 0 0 1 380 80" fill="none" stroke="{SUN}" stroke-width="40" stroke-linecap="round"/>
      <line id="slow-needle" x1="380" y1="400" x2="380" y2="120" stroke="{INK}" stroke-width="18" stroke-linecap="round"/>
      <circle cx="380" cy="400" r="34" fill="{INK}"/></svg>
    <div id="slow-a" style="position:absolute;left:0;right:0;top:640px;text-align:center;font-family:'Noto Kufi Arabic';font-weight:900;font-size:96px;color:{INK};opacity:0">مش انهيار…</div>
    <div id="slow-b" style="position:absolute;left:0;right:0;top:640px;text-align:center;font-family:'Noto Kufi Arabic';font-weight:900;font-size:96px;color:#FFFFFF;opacity:0">بُطء</div>"""
    js = """
    tl.fromTo("#slow-needle", { rotation: 50, svgOrigin: "380 400" }, { rotation: -55, svgOrigin: "380 400", duration: D * 0.3, ease: "power2.inOut" }, at(0.25));
    show("#slow-a", 0.22); tl.to("#slow-a", { opacity: 0, duration: 0.2 }, at(0.5));
    pop("#slow-b", 0.52);
    """
    return SUN, html, js


def v_lift(s):
    steps = "".join(f'<div style="position:absolute;left:{1040 + i * 70}px;top:{860 - i * 60}px;width:70px;height:{60 + i * 60}px;background:#C8CCD6"></div>' for i in range(10))
    html = f"""
    <div style="position:absolute;left:300px;top:120px;width:420px;height:880px;background:#E3E6EE;border-radius:12px"></div>
    <div id="lift-car" style="position:absolute;left:360px;top:560px;width:300px;height:340px;border-radius:14px;background:{TEAL}">
      <div style="position:absolute;left:146px;top:20px;width:8px;height:300px;background:#FFFFFF"></div></div>
    <div id="lift-sign" class="card" style="left:330px;top:180px;padding:16px 30px;font-weight:900;font-size:40px;color:{RED};opacity:0">عطلان</div>
    {steps}
    <div id="lift-man" style="position:absolute;left:1040px;top:640px;width:90px;height:220px">
      <div style="position:absolute;left:15px;top:0;width:60px;height:60px;border-radius:50%;background:{INK}"></div>
      <div style="position:absolute;left:0;top:70px;width:90px;height:150px;border-radius:40px 40px 14px 14px;background:{BLUE}"></div></div>"""
    js = """
    aiOff("#lift-car", 0.3); pop("#lift-sign", 0.34);
    const k = [];
    for (let i = 0; i < 8; i++) k.push({ x: (i + 1) * 70, y: -(i + 1) * 60, duration: (D * 0.45) / 8, ease: "power1.inOut" });
    tl.to("#lift-man", { keyframes: k }, at(0.5));
    """
    return "#FFD9A8", html, js


def v_ask(s):
    html = f"""
    <div style="position:absolute;left:940px;top:300px;width:30px;height:660px;background:{INK}"></div>
    <div id="ask-a1" style="position:absolute;left:970px;top:330px;width:380px;height:100px;background:#FFFFFF;clip-path:polygon(0 0,85% 0,100% 50%,85% 100%,0 100%)"></div>
    <div id="ask-a2" style="position:absolute;left:560px;top:480px;width:380px;height:100px;background:#FFFFFF;clip-path:polygon(15% 0,100% 0,100% 100%,15% 100%,0 50%)"></div>
    <div id="ask-ghost" class="card" style="left:1080px;top:150px;padding:18px 30px;background:{TEAL};color:#FFFFFF;font-weight:800;font-size:36px">اطلع يمين</div>
    <div id="ask-q" style="position:absolute;left:880px;top:90px;font-family:'Noto Kufi Arabic';font-weight:900;font-size:180px;color:{INK};opacity:0">؟</div>"""
    js = """
    rise("#ask-a1", 0.05); rise("#ask-a2", 0.1);
    aiOff("#ask-ghost", 0.45); tl.to("#ask-ghost", { opacity: 0, duration: 0.4 }, at(0.75));
    pop("#ask-q", 0.78);
    """
    return "#C9F0D2", html, js


def v_end(s):
    html = f"""
    <div id="end-a" data-hold style="position:absolute;right:192px;top:250px;max-width:1500px;font-family:'Noto Kufi Arabic';font-weight:800;font-size:66px;line-height:1.5;color:#DCE4FF;opacity:0">يمكن الخطر عمره ما كان إن الذكاء الاصطناعي يقف…</div>
    <div id="end-b" data-hold style="position:absolute;right:192px;top:470px;max-width:1540px;font-family:'Noto Kufi Arabic';font-weight:900;font-size:84px;line-height:1.45;color:{SUN};opacity:0">الخطر إنه يقف في يوم، نكون فيه نسينا إزاي نمشي من غيره.</div>"""
    js = """
    tl.fromTo("#end-a", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.3, ease: "power4.out" }, at(0.04));
    tl.fromTo("#end-b", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.3, ease: "power4.out" }, at(0.42));
    """
    return BLUE, html, js


VIS = dict(map=v_map, street=v_street, rules=v_rules, inbox=v_inbox, apps=v_apps, zoom=v_zoom, bank=v_bank, ship=v_ship,
           xray=v_xray, slow=v_slow, lift=v_lift, ask=v_ask, end=v_end)


def build(durs):
    starts, t = [], 0.0
    for d in durs:
        starts.append(round(t, 2)); t += d
    total = round(t + 1.0, 2)
    for (sid, caps), d in zip(SCENES, durs):
        bg, html, js = VIS[sid](sid)
        caph = "" if sid == "end" else "\n    ".join(f'<div id="{sid}-cap{i}" class="cap">{c}</div>' for i, c in enumerate(caps))
        sp = spans(caps)
        if sid == SCENES[0][0]:
            sp[0][0] = 0
        capjs = "" if sid == "end" else f'captions("{sid}", {json.dumps(sp)});'
        open(f"compositions/{sid}.html", "w").write(f"""<template>
  <style>{COMMON_CSS}
    #root {{ background: {bg}; }}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    {html}
    {caph}
  </div>
  <script>{COMMON_JS.replace("__D__", str(d))}
{js}
    {capjs}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
""")
    last_d = durs[-1] + 1.0
    hosts = "\n".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{s}" data-duration="{(last_d if i == len(SCENES) - 1 else d)}" '
        f'data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{i + 1}"></div>'
        for i, ((sid, _), s, d) in enumerate(zip(SCENES, starts, durs)))
    S = dict(zip([s for s, _ in SCENES], starts))
    D = dict(zip([s for s, _ in SCENES], durs))
    sfx = [("whoosh", S[s] - 0.15, 0.4) for s in ["street", "rules", "inbox", "apps", "zoom", "bank", "ship", "xray", "slow", "lift", "ask", "end"]]
    for sid, f in [("map", 0.38), ("street", 0.8), ("rules", 0.3), ("inbox", 0.3), ("apps", 0.58), ("bank", 0.42), ("ship", 0.3), ("xray", 0.35), ("lift", 0.3), ("ask", 0.45)]:
        sfx.append(("glitch", round(S[sid] + f * D[sid] + 0.03, 2), 0.55))
    for sid, f in [("street", 0.12), ("street", 0.2), ("street", 0.38), ("street", 0.46), ("rules", 0.53), ("rules", 0.61), ("rules", 0.69),
                   ("zoom", 0.45), ("zoom", 0.55), ("zoom", 0.65), ("ship", 0.42), ("xray", 0.62), ("lift", 0.34), ("ask", 0.78), ("slow", 0.52)]:
        sfx.append(("pop", round(S[sid] + f * D[sid] + 0.03, 2), 0.5))
    for i in range(8):
        sfx.append(("blip-a" if i % 2 else "blip-b", round(S["inbox"] + (0.36 + i * 0.06) * D["inbox"] + 0.03, 2), 0.45))
    sfx.append(("riser", round(S["end"] + 0.42 * D["end"] - 0.33, 2), 0.7))

    def fdur(f):
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                    capture_output=True, text=True).stdout)
    aud = [f'      <audio id="mu-0" class="clip" src="assets/music-bed.wav" data-start="0" data-duration="{total}" data-track-index="2" data-volume="0.45"></audio>']
    lanes = {}
    for i, (n, st, v) in enumerate(sorted(sfx, key=lambda x: x[1])):
        st = max(0.0, round(st, 2)); d = fdur(f"assets/sfx-{n}.wav")
        lane = next(k for k in range(3, 30) if lanes.get(k, -1) <= st)
        lanes[lane] = st + d
        aud.append(f'      <audio id="fx-{i}" class="clip" src="assets/sfx-{n}.wav" data-start="{st}" data-duration="{d:.2f}" data-track-index="{lane}" data-volume="{v}"></audio>')
    open("index.html", "w").write(f"""<!doctype html>
<html lang="ar" dir="rtl" data-composition-variables='{json.dumps([{"id": "color-ai", "type": "color", "label": "AI teal", "default": TEAL},
                                                                    {"id": "color-accent", "type": "color", "label": "Accent", "default": SUN}])}'>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #9DB8FF; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
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
    json.dump({"scenes": [s for s, _ in SCENES], "starts": starts, "durations": durs, "total": total}, open("timing.json", "w"), indent=2)
    print(f"built {len(SCENES)} scenes, total {total}s")
    return total


if __name__ == "__main__":
    durs = default_durations()
    if "--durations" in sys.argv:
        durs = json.load(open(sys.argv[sys.argv.index("--durations") + 1]))
    build(durs)
