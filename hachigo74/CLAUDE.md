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
- **Tub joint reinforcement** (user, 2026-11-03; hachigo74 only so far; PCB unchanged):
  - **PCB gap** (user, 2026-11-04): the tub's inner wall is `tub_cavity` = `pcb_core` expanded 2.25, so
    0.25 clearance per side round the PCB (it was 0: the wall followed `pcb_outline` exactly) and a 7.75 wall;
    the lower posts are clipped to `tub_cavity` so they stay joined to the wall. Thinnest wall at an
    edge insert hole 2.05 (hole to cavity). Only hachigo74: kugo82's yaml still has no gap.
  - Dovetails, tails on `tub_right`, sockets in `tub_left` (0.10 larger per side; user: 0.15 was too loose on the printed test strip, 2026-11-04), engaged by
    dropping one half straight down, before the PCB goes in. Floor tails (`dovetail_floor`, z 0-3,
    neck 8, head 12, 8 long) at centre-frame y 60 / 32 / -4; south wall tail (`dovetail_wall`, z 0-11.4,
    neck 4, head 5.6, 6 long, centred in the wall at y -39.195, about 0.96 mm of wall left each side of the socket head). No tail in the north
    wall: the USB opening takes it. `tub_right` prints 209 mm wide; it is cut with `cut_right_tails`
    (`cut_right` + the tails), so the tails come out of its floor and wall.
  - Bridge plate `center_bridge` (new part, z 3-4.5 on the floor, glue optional; user: wide, for
    stiffness when glued): 138 wide (+-69, 0.72 clear of the crosses at +-69.72; 28 g), clipped 0.75 inside
    the walls (`bridge_inside`), a 20 wide notch north of y 60 for the USB plug, close holes (0.1
    clearance) around the 4 centre posts, a hole round the reset boss and an 11 x 3 slot for the OLED's
    4 header pins, which hang to z 3.3 if not trimmed. Print flat.
  - Checked against the routed board's 3D model: no overlap; next lowest part over the plate z 5.36
    (dx +-5.8, y -66.6 .. -59.4, in the USB notch), then z 5.89. Floor openings under it: only the tails' clearance.
  - Fusion (KeyboardCase `build_design`, Fusion 2706.1.17, 2026-11-03): all 10 parts build, all 234
    timeline items healthy, volumes = the STEP files to the mm3, tilt_angle 3 / 15 / 6 deg recompute cleanly
    (tilt checked with the 36 wide plate).
- **Plate ribs in the lids** (user, 2026-11-04: part of the final design): outline `plate_ribs` in the lid recipes
  (z 10.4-11.4, 0.3 above the PCB), so the STLs, STEP and Fusion all have them and the Fusion script no longer
  asks (no `rib` data; depth is not a Fusion parameter here, change it in the yaml). Relief 1 round each cutout, frame 1.5
  (1.55 in the yaml: neighbours overlap 0.1, touching edges are fragile in maker.js), clipped 0.5 inside the PCB outline, the plate's
  holes cut through. The 2U relief goes round the stabilizer housings as they are in Gateron's STEP (y down to -9.74, relief -10.75):
  the old Fusion option's 30 x 15.1 hit both housings (about 2 mm3 each, up to z 11.25). Checked 2026-11-04 against the routed board's model:
  no contact. With the later support ring, half crosses and 14.06 cutouts: lids 21491 mm3 each, about 27 g; rechecked 2026-11-04, no contact.
- **Trackpad support ring** (user, 2026-11-04, so the pad doesn't wobble when pushed; hachigo74 only): `tp_support` in the lid recipes,
  plate underside to PCB top (z 10.1-11.4), r 18.2-20 round the pad centre, cut round the FFC slot, on the front silkscreen marks. No pads there on the routed board, but it rests on tracks and vias under the solder mask.
- **Half crosses beside the Helios** (user, 2026-11-04): 2 T shapes in `cross_upper` (added by hand, not from crosses.py), plate to PCB top, centre x +-11, y 62, arms 5 north / south / outward. No lower crosses under them.
- **USB opening** (user, 2026-11-04): floor under it stays 3 thick and a 1.5 strip of tub wall stays over it (z 9.9-11.4, the plate on top of that): `usb_cutout` z 3-9.9, 13 wide. A 0.3 lip on the lid was tried first and dropped. Plug axis about z 5.3, so 2.3 below the axis (was 3.8) and 4.6 above; a plug body centred on its axis fits up to about 4.6 tall.
- **Top fillets, Fusion only** (user, 2026-11-04; `TOP_FILLETS` in KeyboardCase.py, the STL / STEP files stay square): top outside edge of the lid plate 1.0 (`lid_fillet`) and of the
  wedge rim 1.5 (`wedge_fillet`, leaves 0.5 flat on the 2 wide rim), last step of each part, not along the joint or round the centre openings. Print these from a Fusion export.
- **The 4 centre posts** (user, 2026-11-04; the cover-screw posts in the tubs): inner hole Ø3.0 from the floor top to the PCB (z 3-8.5), 1.25 wall in the Ø5.5 post. The floor below keeps its Ø2.4 hole and Ø4.4 head counterbore, so there's a 0.3 step at z 3.
- **Switch cutout** (user, 2026-11-04): `sw` 14.06. 14.1 printed too big; `case/test/switch_cutout_14.06_strip` (3 cutouts, the lid's plate + rib section, at 15 deg on the bed) fits. The cutout is an Ergogen outline only, no footprint or PCB geometry depends on it.
- Lid plate's OLED opening `oled_plate` (user, 2026-11-04): 0.5 further north than the cover's pocket `oled` (28.2 x 28.5), square corners; the pocket is unchanged.
- OLED module (user measured, 2026-11-04): board 28 x 27.2 (the vendor model is 28.4 x 27.4), so it fits
  the `oled` opening 28.2 x 28. Back of its board to the glass top 3.1, so with the 1.2 spacers the glass top is
  z 14.4: the cover's pocket ceiling is z 14.5 here (kugo82 still 13.95), low layer 12.6-14.5, top layer 1.0, `cover_boss_oled` 12.5-14.5.
  Glass starts about 4.7 from the board's header-side edge (user measured; vendor model 4.0). The Ø5 bosses have a flat
  on the glass side, 2.05 north of the screw (y 26.185, 0.55 wall left round the insert hole), reaching about 4.2 from that edge
  if the screw hole is 2.135 from it as in the vendor model (not measured on the real module).
- **OLED screw holes don't match the module (known issue, not fixed; user measured, 2026-11-04):** the module's two holes are 23.6 apart
  horizontally, the board and case have them 22.352 apart (`oled_screw`, footprint `oled_i2c`, x +-11.176), 1.25 too close. Two screws can't both go in:
  use one, or drill the PCB out a bit. On the next PCB revision move them to about x +-11.8 (the spacers, bosses and insert posts move with `oled_screw`; check the room first).
- Build: `bash tools/build.sh hachigo74`, then `tools/case.sh hachigo74` and
  `tools/step.sh hachigo74` → `case/`, `case/step/`, `case/fusion/` here.
- Expected DRC: 5 `silk_overlap`, 499 unconnected pads; 74 switches, 76 LEDs.
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
  - Updated 2026-11-04 (user) for the next board, as text edits + zone refill: switch centre holes 5.15 (placed footprints and
    `libraries/`), front silkscreen marks for the trackpad ring and the right half cross (user: no mark for the left one, it would cross the logo; that cross is still in the lid). Tracks and vias unchanged (2930, compared), the pour only grew
    (F.Cu +165, B.Cu +118 mm2), DRC: 0 violations, 0 unconnected, parity 0.
    `production/` still holds the first order's files (Ø5.25): re-export before ordering. 2 lower-cross marks on the back (around (133, 125) and its mirror) stay about 0.6 off
    the case on purpose (user: moved by hand to avoid DRC warnings).

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
  `keyboards/` and builds the `.uf2` as a download. Flash: hold reset ~1 s and release (> 500 ms; a double-tap does nothing), copy the `.uf2`
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
