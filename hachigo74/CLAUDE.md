# hachigo74

Shared rules, build and tools: `../CLAUDE.md`. Everything not listed here
(switches, LEDs, MCU, matrix pins, OLED, trackpad, screws, case stack-up) is the
same as kugo82: see `../kugo82/CLAUDE.md`.

- **`ergogen/hachigo74.yaml`** (74 keys, 37 per half, from `kle/hachigo74.json`): a
  variant of kugo82 with the outer column c1 removed (column names c2–c9 kept,
  so every reference stays valid; the board sits 1 sp further left on the sheet).
  - c2 is all 1U at KLE 2.0; c3 r1–r4 are 1U at 3.0 with Esc 1.25U; c4 is all 1U.
  - The PCB outline and the outer case-wall screws follow c2.
  - LED chain: 2 indicators + 74 keys = 76. **Re-chained in the KiCad project on
    2026-10-20** (user's order, `tools/lib/led_rechain.py`): MCU -> R1 -> LED1 (right
    c9_r5, next to the Helios) -> the right half in its old snake order -> LED37 (right
    c2, outer top) -> LED38 (right indicator) -> LED39 (left indicator) -> LED40 (left
    c2_r4) -> the left half -> LED76 (left c9_r5, end). Nets: R1 -> LED1 = LED_DATA,
    LEDk -> LEDk+1 = LED_k; each LED's cap is Ck. For the firmware (0-based): keys of the
    right half 0-36, right indicator 37, left indicator 38, left half 39-75.
    Only the KiCad project has this: `ergogen/hachigo74.yaml` still describes the old
    chain (indicators first), so don't regenerate the project from Ergogen without
    re-running led_rechain.py.
  - Crosses (user's choice, upper right corners): c4_r1, c3_r4, c7_r4, plus c7_r1
    top middle. Only spots with a lower cross are used (c6_r4 and c8_r3 were dropped:
    their lower corner is blocked). c4_r1 east arms are 2.5 mm (c5_r1 stabilizer).
    Regenerate with `crosses.py ... "c4_r1,c3_r4,c7_r4,c7_r1:0:0.5"`.
  - The c2_r2 screw is at [9.5, 9.0] (room 3.62).
  - Bottom edge (2026-10-20, user's request, more room for routing): the c2–c4 keycap
    bottom line runs straight on until it meets the c7_r1 keycap's bottom edge (38 %
    along it), point `c4_r1 [57.016, -0.5kc]`; the step under the 2U c5_r1 is gone.
    The case-wall screw under c5_r1 moved with it (`c4_r1 [28.5, -(0.5kc + 6)]`).
    Carried into the routed KiCad board with `tools/lib/kicad_outline_sync.py`.
- **KLE files (`kle/`):** `hachigo74_keys.json` (Hungarian) and `hachigo74_jis_keys.json`
  (Japanese JIS) map key name → label; `hachigo74_exact.json` / `hachigo74_jis.json` are
  exact exports (Ergogen positions and angles) made from them with
  `kle_export.py <name> <keys map> <out>` after building hachigo74.
  - JIS: kana bottom-right (blue), small kana top-right, QMK keycode front-left.
    半角/全角 = left c9_r5 (GRV), 英数 = left c9_r3 (CAPS), 無変換 = left c9_r2 (INT5),
    変換 = right c9_r2 (INT4), かな = right c9_r5 (INT2); ¥/ー = right c3_r2 (INT3),
    \/ろ = left c3_r3 (INT1), 0/わ on right c4_r5. F11/F12 moved to the Fn layer of
    半角 / かな.
- Build: `bash tools/build.sh hachigo74`, then `tools/case.sh hachigo74` and
  `tools/step.sh hachigo74` → `case/`, `case/step/`, `case/fusion/` here.
- Expected DRC: 2 `silk_overlap`, 499 unconnected pads; 74 switches, 76 LEDs.
- **KiCad project `kicad/`** (portable, see its README): PCB + generated schematic +
  `.kicad_dru` + a copy of `../kicad-libraries` in `kicad/libraries/`, all paths
  `${KIPRJMOD}/libraries/...`. Made by `tools/lib/kicad_project.py` (KiCad python)
  from `out/pcbs/hachigo74.kicad_pcb`; it refuses to overwrite unless `--force`.
  Verified: ERC 0, DRC schematic parity 0, netlist = Ergogen board (808 pads).
  - Unused pins (C1/GP0, GP13-15, D+/D-, RST, LED_END) have no-connect flags; their
    pads carry KiCad's `unconnected-(...)` net names, so parity holds.
  - Footprints carry the same fields as their symbols (Description, LCSC, ...); the
    Helios symbol is out of the BOM like its footprint (hand-soldered module).
  - The project is the master from now on: an Ergogen rebuild + `--force` regenerate
    would lose routing done in KiCad.
