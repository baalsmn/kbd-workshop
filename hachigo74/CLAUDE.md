# hachigo74

Shared rules, build and tools: `../CLAUDE.md`. Everything not listed here
(switches, LEDs, MCU, matrix pins, OLED, trackpad, screws, case stack-up) is the
same as kugo82: see `../kugo/CLAUDE.md`.

- **`hachigo74.yaml`** (74 keys, 37 per half, from `kle/hachigo74.json`): a
  variant of kugo82 with the outer column c1 removed (column names c2–c9 kept,
  so every reference stays valid; the board sits 1 sp further left on the sheet).
  - c2 is all 1U at KLE 2.0; c3 r1–r4 are 1U at 3.0 with Esc 1.25U; c4 is all 1U.
  - The PCB outline and the outer case-wall screws follow c2.
  - LED chain: 2 indicators + 74 keys = 76. Left c2_r4 takes LED_DATA, right c2_r4
    gives LED_END.
  - Crosses (user's choice, upper right corners): c4_r1, c3_r4, c6_r4, c8_r3, plus
    c7_r1 top middle. c4_r1 east arms are 2.5 mm (c5_r1 stabilizer); c6_r4 and
    c8_r3 have only an upper cross (the lower corner is blocked). Regenerate with
    `crosses.py ... "c4_r1,c3_r4,c6_r4,c7_r1:0:0.5,c8_r3"`.
  - The c2_r2 screw is at [9.5, 9.0] (room 3.62).
- Build: `bash tools/build.sh hachigo74`, then `tools/case.sh hachigo74` and
  `tools/step.sh hachigo74` → `case/`, `case/step/`, `case/fusion/` here.
- Expected DRC: 2 `silk_overlap`, 499 unconnected pads; 74 switches, 76 LEDs.
