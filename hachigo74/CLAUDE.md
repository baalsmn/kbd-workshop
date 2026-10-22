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

## Firmware (QMK)

Decided (user, 2026-10-23); kugo82 is discussed separately.
- Host: Windows with the Hungarian layout, so `HU_*` keycodes (`keymap_hungarian.h`).
  Linux behaves the same; a Mac would need Ctrl/Cmd swapped and LANG1/LANG2 for the JIS
  keys (QMK OS detection, later if ever).
- Two layers: 0 = base (the KLE legends), 1 = Fn: F1–F12 (number row, F11/F12 on c9_r5)
  and the characters that need AltGr on Windows' Hungarian layout, each on its usual
  AltGr key (Fn + Q = `\`, Fn + F = `[`, ...); AltGr keeps working. Exceptions, as drawn in
  the KLE: `$` on S and `€` on E (not on É / U).
- Fn key (right half c2_r1, `mirror_hand-zone_c2_r1`): hold = layer 1 (`MO(1)`); no
  Windows key on the keyboard.
- Outer thumb keys (c9_r1, both halves): hold = Shift, tap = one-shot layer 1 (custom
  code: QMK's mod-tap can't send `OSL`).
- Indicator LEDs: off on layer 0, green on layer 1 (also while the one-shot waits).
- Build: GitHub Actions in this repo, with **Vial's QMK fork** (vial-kb/vial-qmk, pinned
  commit dd43959, based on QMK 0.29; user's choice 2026-10-23 over VIA, for the tapping-term
  settings), keymap `vial`. The workflow copies `hachigo74/firmware/hachigo74/` into its
  `keyboards/` and builds the `.uf2` as a download. Flash: double-tap reset, copy the `.uf2`
  to the RP2040 drive.
- Other dual keys, as the KLE legends say: left c5_r1 hold Ctrl / tap Tab; right c3_r1
  hold AltGr / tap Alt; right c7_r1 tap Space / hold Enter; the `(` `)` `@` keys give `{`
  `}` `*` with AltGr. Bootmagic (bootloader while plugging in): hold left c2_r1 (←).
- **Files** (`firmware/`): `matrix.json` from the routed board by `tools/lib/qmk_matrix.py`
  (KiCad python, after `tools/build.sh hachigo74`: switch -> diode -> row, LED by its key's
  LED window, names from `out/points/points.yaml`); `hachigo74/` (keyboard.json, config.h,
  rules.mk, hachigo74.h / .c, keymaps/vial) generated from it and `kle/hachigo74_keys.json`
  by `python tools/lib/qmk_gen.py hachigo74`. Re-run both after rerouting the matrix or
  editing the KLE legends; don't edit the generated files by hand.
- Checked offline (`qmk.info.info_json` on QMK 0.34.7 and on vial-qmk: no errors or
  warnings; 10 x 8 matrix, 74 keys, 76 RGB LEDs, indicators 37 / 38 flagged as indicators;
  Vial's `vial_generate_definition.py` packs our vial.json). **The Vial build
  compiles** in GitHub Actions (commit 0e1cd06, 2026-10-23); not yet tested on the board.
- RGB matrix: brightness capped at 40/255 (USB power), default solid white at 40.
  Cirque: absolute mode, tap to click, circular scroll; its DR pin (GP7) is unused (the
  driver polls). Its axes may need `POINTING_DEVICE_ROTATION_*` / `_INVERT_*` once tested.
- **Vial:** the layout is stored in the firmware (vial.json), so the Vial app (get.vial.today,
  desktop or web) shows it with no file to load. Keymap in the RP2040 flash; 4 layers (0 base,
  1 Fn, 2-3 spare). "QMK Settings" in the app: tapping term, permissive hold, etc., saved on
  the keyboard. Tap dance, combos, key overrides available too. Unlock combo (Vial asks for
  it before some changes): hold left Esc + right Backspace. RGB through VialRGB. The custom
  keys live in the keyboard code (`hachigo74.c`, keycodes `QK_KB_0..2` in `hachigo74.h`), so
  they work whatever Vial stores; the 3 AltGr keys show up as custom keys in the app.
- **OLED:** name, layer (Base / Fn, also during a one-shot) and **KPM**: key presses in
  ten 1 s slots, the last 10 s x 6 (every press counts, modifiers too).
- Later: Cirque features, RGB defaults, home-row mods.
