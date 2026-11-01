# SPEC: The interview (What if AI stopped working? Story version, storyline A)

GOAL:    the viewer roots for Sam, feels the clock, is surprised by the twist, and leaves with "The AI stopped. People didn't."
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    66 s x 30 = 1980 frames. Music in three parts (morning, tense, warm return); ticking carries the middle.

LOOK:    flat picture-book city: solid colour blocks, no gradients, glow or grain. Buildings are rectangles with window grids;
         2 px darker roof edges. Each scene is one ground colour:
         bedroom #BFD0FF, street sky #9DD3FF, bus stop sky #FFD9A8, run sky #FFB38A, plaza sky #FFE7A0,
         walk sky #C9F0D2, office wall #E9E4FF, ending #2348F2.
         Ink #121317. The sun accent #FFC93C marks only the payoff line. Clock red #F2553C appears from 8:45.
         Narration: Nunito 900, 54 px, top-left (x 192, y 120–240), word by word from 20% to 100% ink, 0.08 s apart.
         Display: Archivo Black 150–190 px for the ending only.
OBJECTS: Sam (round head, dark hair cap, eyes that blink, mouth states smile/flat/o/frown/grin, blue coat, dark trousers,
         520 px tall); the tourist (grey hair, maroon beret, orange coat, suitcase); a big alarm clock that becomes the corner
         clock badge; a phone with a map; a bus with a card reader; a city skyline; a hand-drawn paper map; Tower 12;
         an office desk with a "Head of Hiring" nameplate and a swivel chair.
MOTION:  character acting: mood changes go through a take (head squash 0.92, then back.out). Legs swing ±28° (walk) or ±40° (run),
         and arms swing opposite, offset from the legs. Blinks every 2–4 s. Props arrive with expo.out; the camera pans power2.inOut.
         Narration lands and holds still. The clock badge is linear time inside each scene.

SHOTS:
  S1 wake 0–7       bedroom; the alarm clock rings (shake); Sam yawns, then looks determined. "Sam had one job today." /
                    "Be at the interview by 9:00." 4.6: the alarm clock flies to the top-right and becomes the clock badge.
  S2 outage 7–14    street; Sam checks the phone map (inset). 10.0 GLITCH: map grey, "Live routes unavailable", Sam confused.
                    "At 8:12, every AI helper went quiet." / "The map just stopped."
  S3 bus 14–22      the bus pulls in; Sam taps her card; 17.2 GLITCH "Card declined: manual check"; the bus leaves (whoosh).
                    "The bus wouldn't take her card." / "So she ran."
  S4 run 22–29      parallax city; Sam runs, sweating; the clock spins to 8:47 and turns red; ticks speed up.
                    "8:47." / "Thirteen minutes left."
  S5 tourist 29–40  plaza; the tourist arrives with a suitcase, phone reads "Translation unavailable"; bubble
                    "Excusez-moi… Tower 12 ?". Sam looks at the clock, then at the tourist. The music drops out (33.0). Hold.
                    Sam smiles: bubble "Follow me." "Sam was already late." / "She stopped anyway."
  S6 walk 40–50     both walk; Sam draws the route on paper (inset); Tower 12 arrives; the clock reads 9:04.
                    "She walked them all the way there." / "9:04. Four minutes late."
  S7 twist 50–60    office; Sam enters, nervous. The chair turns: it's the tourist, with the "Head of Hiring" plate. Bubbles
                    "You got me here without a single app." / "When can you start?" Sam: o, then a grin with a jump.
                    The music returns warm (52.5).
  S8 end 60–66      blue; "The AI stopped." / "People didn't." (sun), held 3 s+. Small: "A story, not a prediction."

SOUND:   bright bed 0–10 cut at the first glitch; a tense low pad 10–33 under accelerating clock ticks (S4); silence at the choice
         33–40 except street air; footsteps (soft taps) while walking or running; glitch ×2, bus whoosh, pops on speech bubbles;
         the warm bed returns 52.5–66. Mix −15 LUFS, true peak ≤ −1 dBTP.

BANNED:  the defaults in spec.md; the cream-paper-serif look; narration repeating what the action already shows word for word;
         characters moving every part in unison; floating idle loops on props; three cards in a row.

QA:      0.0 thumbnail (Sam + ringing clock + line), 4.9 (clock flying to the badge), 10.2 (glitch), 17.5 (declined),
         25.5 (running, red clock), 35.5 (the choice), 46 (walk + paper map), 53.5 (the reveal), 63 (ending).
