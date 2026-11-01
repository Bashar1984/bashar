# SPEC: لو الذكاء الاصطناعي وقف فجأة (What if AI suddenly stopped?), Egyptian Arabic, 2 min

GOAL:    the viewer discovers the invisible AI layer inside ordinary life, sees that the world slows down rather than
         collapsing, and leaves asking whether they could still manage without it.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, right-to-left.
TIME:    about 131.5 s. Each scene's length = its words ÷ 2.4 words a second + 1 s (build.py); animations are placed as fractions of each scene.
SOURCE:  the user's script, verbatim, shown as captions (Cairo 800, 44 px, white band, bottom centre, max 1500 px wide).
LOOK:    flat colour-block scenes, one ground each (blue, sky, ink, tomato, green, amber, mint, sun, peach).
         Motif: everything AI-powered is teal #00897B. When the AI stops it shakes, turns grey and fades.
         Display face: Noto Kufi Arabic 900 for the few big words; body: Cairo.
SCENES:  map (route suggestion dies) → street (power, internet, cars and people fine; the teal network vanishes unseen) →
         rules (what still works vs what stopped) → inbox (spam filter dies, spam floods) → apps (recommendations and
         chatbot die; queue number) → zoom (phone → city: bank, shipping, hospital) → bank (fraud radar off, manual review) →
         shipping (optimised route → pencil route, truck follows) → x-ray (AI box gone, the doctor's eye remains) →
         slow (speed needle drops: "not a collapse… slowness") → lift (broken lift, person climbs the stairs) →
         ask (blank signpost, "turn right" ghost fades) → end (the closing two lines as a poster).
SOUND:   minor-key bed under everything; a whoosh at each scene change; a glitch on every teal shutdown; pops on ticks and
         labels; blips as spam lands; a riser into the final line. Mix about -15 LUFS, true peak ≤ -1.5 dBTP.
VOICE:   none yet. To sync a recording, measure each scene's spoken length and run `python3 build.py --durations d.json`.
