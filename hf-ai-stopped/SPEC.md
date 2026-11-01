# SPEC: What if AI stopped working? (storyline A, "One ordinary morning")

GOAL:    the viewer realises how much invisible AI sits inside ordinary tools, and leaves with "we'd slow down, not stop".
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    52 s x 30 = 1560 frames. Music bed in two parts with the outage in between, so there's no beat grid; cuts follow the motion.

LOOK:    flat full-bleed colour fields, one per world, with no gradients, glow or grain.
         The fields are signal blue #2348F2 (morning, map), tomato #F2553C (spam), café green #1E6B52 (payment),
         amber #FFE3A3 (translate), sun #FFC93C (people) and ink #121317 (claim).
         Ink #121317 and white #FFFFFF carry the words. The accent is the one coloured word per shot, and the payoff "Not stop." is sun.
         Display: Archivo Black 900, 68–230 px, tracking -2%. UI and body: Outfit 500/700, 28–46 px.
         Medium: real-feeling phone and card-terminal UI drawn large. Phone 450 x 930 px, graphite #1B1C20 body,
         68 px radius, 14 px bezel, screen #FFFFFF with 56 px radius, shadow 0 30 px 60 px at 25% black.
OBJECTS: a phone (graphite body, bezel, lock screen, notifications); a city map (white streets, parks, river,
         blue route, car dot); an inbox list; a card terminal (dark body, screen, keypad, contactless mark) and a
         blue payment card with a chip; a paper map with fold panels and a hand-drawn red route; a person silhouette with a speech bubble.
MOTION:  arrivals expo.out / power4.out; camera and colour floods power2.inOut; zoom-through and exits power3.in;
         titles: per-word blur 6→0 px in 0.13 s, 0.067 s apart, then dead still. A spinner and a clock hand are linear.
         Exits are 40–50% of entrances. Spam rows arrive on an accelerating stagger (0.55 → 0.12 s).

SHOTS:
  S1 lock 0–5.5    blue. Phone at right shows 08:00. "8:00 a.m." per letter, then the subline. 3 notifications drop in
                   (taps). 4.4 camera pushes into the Maps notification, power3.in, so the card becomes the map.
  S2 map 5.5–13    grey map fills the frame. The route draws and the car moves. 8.5 chip changes to "Rerouting…" with a spinner.
                   9.7 GLITCH: jitter and RGB split; the route goes grey, the car stops, the chip reads "Live traffic unavailable".
                   The music cuts out here. 10.4 title "First, the map stops thinking."
  S3 inbox 13–22   tomato irises open from the chip. The inbox fills with 16 spam rows, faster and faster (blips on the first 6).
                   45.6% counts up and lands 15.6 (pop). "of all email sent in 2023 was spam." Then "Filters used to hide it…".
                   Source: Kaspersky. 21.7 whip left.
  S4 cafe 22–30    green; the whip lands. The card taps the terminal (tap), "Processing…", 25.3 GLITCH, screen amber
                   "Held for manual review". Title "Then the fraud check waits for a human." Caveat line.
                   29.3 zoom through the amber screen.
  S5 translate     amber; the phone's translate app. "Où est la gare ?" types in (ticks), "…", 33.3 GLITCH,
     30–37         "Translation unavailable". Titles "A tourist asks for the station." / "Translate says nothing."
  S6 people 37–45  colour flood amber→sun, the phone sinks out. "So Sam looks up and asks a person." A paper map unfolds
                   panel by panel, a red route draws, and a speech bubble (pop) reads "Two blocks down, then left." The music returns.
  S7 claim 45–52   ink. "We'd slow down." per word; "Not stop." lands 46.5 in sun on the riser peak. Then the quiet line, held to the end.

SOUND:   bright pizzicato-style bed 0–9.7, cut dead at the first glitch. A low quiet pad 9.7–37. The bright bed returns 37–52,
         fading out under the claim. Effects are sliced from the registry's assets/vpn-sfx.wav (taps, pops, whoosh, riser),
         plus a noise-crackle glitch. Only on-screen causes, peaks 1 frame after the picture. Mix about -15 LUFS, true peak ≤ -1 dBTP.

BANNED:  defaults list in spec.md; plus the cream-paper-serif look of this repo's earlier videos, emoji, chimes/dings,
         three cards in a row, floating idle loops on the phone, centred-everything layouts.

QA:      0.0 (thumbnail: blue + phone + 08:00, never black); 4.9 (push mid-flight); 10.0 (glitch); 15.8 (45.6% landed + rows);
         21.8 (whip); 26.0 (held for review); 33.6 (translation unavailable); 41.0 (map + bubble); 49.0 (claim held).
