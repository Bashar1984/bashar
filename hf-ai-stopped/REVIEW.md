# Review: What if AI stopped working?

## Check
`npx hyperframes check`: ok. 0 errors, 0 warnings, 6 info notes. The info notes are the intentional off-canvas moves: the card leaving the frame, the phone sinking out, and the whip.

Fixed along the way:
- A repeated-fromTo baseline problem, and a hidden-element reveal on a cold seek.
- Overlapping sound effects.
- Phone UI text under 28 px.
- A 3.75 s dead stretch in the people scene. Fixed by adding the "Station" label and Sam walking the route.
- The closing line was held too briefly.

## Frames checked (snapshot sheets)
- 0.0: thumbnail is blue ground, "8:00 a.m." crisp, phone with 08:00. Fixed: the title was a faint blur at frame 0.
- 4.9: camera push into the Maps notification is mid-flight.
- 10.0: map grey, "Live traffic unavailable", car stopped.
- 15.8: 45.6% landed, spam rows stacking, badge climbing.
- 21.85: whip.
- 24.6 / 26.0: card tapped, then "Held for manual review". Fixed: the card used to stay on screen after its exit.
- 33.6: "Translation unavailable".
- 42.5 / 43.5: paper map with route, "Station" label, walker dot, speech bubble. Fixed: the map overlapped the title.
- 49.0 / 52.15: claim held.

## Banned-list audit
No dark void, glow, gradients, cream-paper-serif look, three-cards row, docked logo, or idle floating loops. Titles land and hold still. The entrances vary: per letter, per-word blur, line blur, grey-to-ink.

## Sound
Measured, not heard (see the delivery note).
