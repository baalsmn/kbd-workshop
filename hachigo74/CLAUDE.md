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
  - Crosses (user's choice, upper right corners): c4_r1, c3_r4, c7_r4, plus c7_r1
    top middle. Only spots with a lower cross are used (c6_r4 and c8_r3 were dropped:
    their lower corner is blocked). c4_r1 east arms are 2.5 mm (c5_r1 stabilizer).
    Regenerate with `crosses.py ... "c4_r1,c3_r4,c7_r4,c7_r1:0:0.5"`.
  - The c2_r2 screw is at [9.5, 9.0] (room 3.62).
- Build: `bash tools/build.sh hachigo74`, then `tools/case.sh hachigo74` and
  `tools/step.sh hachigo74` → `case/`, `case/step/`, `case/fusion/` here.
- Expected DRC: 2 `silk_overlap`, 499 unconnected pads; 74 switches, 76 LEDs.
- **KiCad project `kicad/`** (portable, see its README): PCB + generated schematic +
  `.kicad_dru` + a copy of `../kicad libraries` in `kicad/libraries/`, all paths
  `${KIPRJMOD}/libraries/...`. Made by `tools/lib/kicad_project.py` (KiCad python)
  from `out/pcbs/hachigo74.kicad_pcb`; it refuses to overwrite unless `--force`.
  Verified: ERC 0, DRC schematic parity 0, netlist = Ergogen board (808 pads).
  - Unused pins (C1/GP0, GP13-15, D+/D-, RST, LED_END) have no-connect flags; their
    pads carry KiCad's `unconnected-(...)` net names, so parity holds.
  - Footprints carry the same fields as their symbols (Description, LCSC, ...); the
    Helios symbol is out of the BOM like its footprint (hand-soldered module).
  - The project is the master from now on: an Ergogen rebuild + `--force` regenerate
    would lose routing done in KiCad.
