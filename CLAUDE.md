# keyboard-workshop — Ergogen keyboards on one PCB

Split-style ergonomic keyboards, each a mirrored two-half layout on a single PCB,
designed in **Ergogen 4.2.1**, finished in **KiCad 10**, case 3D-printed.

## Layout

- Root = shared: `tools/`, `ergogen/` (every Ergogen input: the design yamls
  `kugo82.yaml`, `hachigo74.yaml` and `footprints/`), `datasheets/`,
  `kicad-libraries/` (KiCad symbols, footprints and **all 3D models**: the Ergogen
  footprints point at `kicad-libraries/3dmodels/` too), `keyboard.kicad_dru` (DRC
  rules for every design), `drafts/` (the user's sketches and photos).
- One folder per keyboard, holding only its own files:
  - `kugo82/`: kugo82 (82 keys), the larger version of hachigo74 (an extra outer
    column c1 and 1.25U modifiers in c2–c4): `kle/`, `case/`, later `kicad/`.
    Shared hardware, stack-up and open items: **`kugo82/CLAUDE.md`**.
  - `hachigo74/`: hachigo74 (74 keys, kugo82 minus column c1): `kle/`,
    `case/`. Details: **`hachigo74/CLAUDE.md`** (hardware otherwise as kugo).
- A new keyboard = `ergogen/<name>.yaml` starting with the line
  `# keyboard: <folder>` (where its outputs go; default a folder named `<name>`),
  plus that folder (with `kle/`). The tools find the yaml by name.
- `kicad-libraries/` (renamed by the user from `kicad project/`): the self-contained
  KiCad libraries: symbols, footprints, 3D models and library tables, everything
  `${KIPRJMOD}`-relative. Where the project file, schematic, PCB and `.kicad_dru` will
  live is still open. Contents (see its README):
  - `Footprints/Keyboard.pretty`: exported from the built boards by
    `tools/lib/kicad_footprints.py` (KiCad python; run per design, `--force` to
    overwrite), exactly as placed, unrotated, on the front side.
  - `Symbols/keyboard-workshop.kicad_sym`: the one symbol library (library name
    `keyboard-workshop`): KiCad built-in symbols with our pin names, prefixes and
    footprints, made by `tools/lib/kicad_symbols.py`, plus the user's Helios symbol,
    renumbered to the footprint's 0xCB pad numbers (it was off by one). The script
    rebuilds its own symbols and keeps every other symbol in the file (Helios, or
    anything added by hand in KiCad).
  - SK6812MINI-E: KiCad's symbol numbering (1 VSS 2 DIN 3 VDD 4 DOUT) is the
    datasheet's (C5149201, `datasheets/`), and the footprint pads were renumbered
    to it (positions unchanged).
  - `tools/lib/kicad_project.py` makes a portable per-design KiCad project from a built
    board (`hachigo74/kicad/`, see `hachigo74/CLAUDE.md`). Shared helpers (S-expression
    reader/writer, footprint names, model renames) live in `tools/lib/kicad_common.py`.
  - pcbnew gotcha: edit 3D model paths by index (`fp.Models()[i].m_Filename = ...`);
    `for m in fp.Models()` yields copies and the edit is silently lost.
  - The schematic is to be generated from the PCB netlist later (see
    `kugo82/CLAUDE.md`, Open / next).

## Licensing and third-party files

- Repo is **private**. LICENSE: hardware CERN-OHL-S-2.0, scripts GPL-3.0-or-later;
  texts in `LICENSES/`; third-party files (KiCad libs CC-BY-SA-4.0, 0xCB Helios
  CERN-OHL-S-2.0, ceoloide MIT) listed in `THIRD_PARTY_NOTICES.md`. Keep both up to
  date when adding parts from elsewhere.
- **Not in git** (gitignored, kept locally): vendor 3D models and vendor
  footprints of unknown licence in `vendor/`. `tools/build.sh` copies
  `ergogen/footprints/local/*.js` (gitignored) over tracked footprints when present.
- **No Claude / Anthropic logos** anywhere (trademarks, not usable here): removed
  from the designs, footprints and drafts, and left out of the public history copy.
- 3D models of bought parts are recreated from datasheet dimensions by
  `tools/lib/make_models.py` (build123d), in the vendor models' coordinate frames,
  so footprint offsets stay valid. Datasheet sources: `datasheets/LINKS.md`.
- **The switch and LED footprints use the manufacturers' STEP models** (user's choice,
  2026-10-22): `vendor_Gateron_KS-2P02B01-02_socket.step`, `vendor_Gateron_KS-33_switch.step`,
  `vendor_Gateron_KS-57B210T_stabilizer.step`, `vendor_SK6812MINI-E.step`,
  `vendor_OLED_128x64.step` and the MBK keycaps `vendor_keycap_MBK_{1,1.25,2}u.wrl`.
  **Committed once in `kicad-libraries/3dmodels/`** (user's request; licence not stated,
  see `THIRD_PARTY_NOTICES.md`); the copies in `<keyboard>/kicad/libraries/3dmodels/` are
  gitignored, so after a fresh clone run
  `cp kicad-libraries/3dmodels/vendor_* <keyboard>/kicad/libraries/3dmodels/`.
  Originals in `vendor/` and `drafts/`. Checked against the drawings: socket 15.08 × 5.39 × 3.0, in the
  footprint frame; switch 15 × 15, origin at the key centre with z 0 = PCB top (offset
  0, 0, −1.6), pins at (2.6, 5.75) / (−4.4, 4.7); stabilizer 30 × 16.97, housings 6.0 at
  ±12, 4.45 below the plate top (offset −60, 0, 1.65); LED pin-1 lead (cut corner) and body
  chamfer on the GND pad.
  - OLED: the vendor STEP as is, offset (0, −12.2, 1.2) (header row at its y +12.2); it
    still shows the plastic header spacer (the module really sits on bare pins). A cleaned
    re-export lost the per-face colours (build123d keeps one colour per part), so it wasn't used.
  - Keycaps: `drafts/MBK_*.stl` -> VRML by `tools/lib/stl2wrl.js` (binary STL now read),
    stem bottom 6.3 / rim 9.6 / top 13.6 above the PCB top (switch stem top 8.55);
    1.25u = the 1u cap stretched 1.25x in x (no MBK 1.25u model).
- Switch footprint (`ks33_hotswap.js`): back silkscreen = the stepped socket body from the
  courtyard of Gateron's KS33 hot-swap footprint (`drafts/Gateron_KS33_Hotswap.pretty`),
  mirrored to the back, terminal tabs left out (on the pads); the 14 × 14 switch body is
  drawn as corner marks (Dwgs.User). Pads kept (ours: 2.45 × 2.55, at the drawing's pad
  centres; the uploaded footprint's 2.55 squares sit 0.5 mm further in). Centre hole kept
  at Ø5.25 (switch drawing; the socket drawing's Ø5.1 leaves 0.05 mm round the Ø5.05 post).
- KS-57 stabilizer PCB cutouts: y −5.2 … +9.8, 6.2 wide (Gateron's STEP: the part below the
  PCB top spans −5.11 … +9.70, 5.85 wide; the old −5.8 … +8.95 hit the lever end).
- Updating placed footprints on a project board: the pcbnew Python bindings lose their
  types after a few footprint edits (`SwigPyObject` errors, crashes on `Flip` of an
  unattached footprint), so the 2026-10-22 update swapped the shapes and model entries
  as text from a fresh Ergogen build (same footprint-local frame as placed back-side
  footprints).
- Footprints cite their datasheet numbers: KS-33 / KS-57 from the Gateron drawings,
  Molex 505278 from its sales drawing (pads matched it exactly, no change).

## JLCPCB assembly

- Every assembled part's Ergogen footprint carries a hidden `LCSC` field (param
  `lcsc`, '' = none), checked on jlcpcb.com on 2026-10-18:

  | Part | LCSC | JLC type |
  |---|---|---|
  | 100 nF 0603 (`c_0603`) | C14663 | basic |
  | 10 µF 0805 (`c_0805`) | C15850 | basic |
  | 330 Ω 0603 (`r_0603`) | C23138 | basic |
  | 1N4148W SOD-123 (`sod123`) | C81598 | basic |
  | SK6812MINI-E (`sk6812mini_e`) | C5149201 | extended |
  | Molex 505278-1270 (`molex_505278`) | C47149418 | extended |
  | Gateron KS-2P02B01-02 socket (`ks33_hotswap`, now `attr smd`) | C18212911 | extended, 0 stock: pre-order, min 441 |

- Not assembled (excluded from BOM and position files): the Helios, the OLED module
  (hand-mounted on header pins) and `mech_model` (trackpad).
- All assembled parts sit on the back side, so it's a one-sided assembly job.
- **LED windows** (SK6812MINI-E, 3.6 × 3.1 mm): JLC mills inner corners at R0.5, which
  left the body (3.2 × 2.8) 0.04 mm, and a +0.1 mm body would not fit (others hit this,
  see Deskthority; ebastler's footprint uses reliefs too). Each corner is an r0.5 relief
  arc (centre ±1.3, ±1.2) tangent to the side edge, 0.11 mm past the end edges; the
  courtyard (y ±1.75) encloses it. Copper may come to 0.4 mm of the window (DRC rule
  "LED window relief clearance", panel copy by courtyard in `panel.sh`).
- **Track widths** are DRC rules in `keyboard.kicad_dru` (copied into each project's
  `.kicad_dru` and, by `panel.sh`, into the panel's): min (DRC error below it) / opt
  (the router's default width): signals 0.2 / 0.25 mm, `VCC` (5 V, LED chain) 0.3 /
  1.0 mm, `GND` 0.5 / 1.0 mm, `3V3` 0.3 / 0.3 mm. 5 V plan (user's): 1 mm stub from the
  Helios pad to C85, then 0.5–0.6 mm trunks (two per half, joined at the outer column),
  0.3 mm allowed for the last hop to an LED pad; 2 vias per power layer change. Net names match by their end (`*VCC`), so
  the panels' `Board_0-` nets match too. GND is best a pour on both layers.
- `tools/lib/kicad_project.py` copies the footprint's LCSC number into the schematic
  symbol.
- The user exports with the Fabrication Toolkit plugin (bennymeg) in KiCad. Check the
  rotations in JLC's placement preview: everything is on the back at 15° steps. Fix
  them with the plugin's `FT Rotation Offset` / `FT Position Offset` fields.
- **Assembly panel:** `bash tools/panel.sh <name>` makes `<keyboard>/kicad/<name>_panel.kicad_pcb`
  from the project board with KiKit (installed on first use into
  `%LOCALAPPDATA%/kugo-kikit`, a venv on KiCad's Python; KiCad itself is untouched).
  - The recipe is `<keyboard>/panel.json`, following JLC's edge rail / fiducial
    guideline (jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order,
    checked 2026-10-19: rails >= 5 mm; fiducials 1 mm bare copper, mask opening 2x,
    3-4 of them, keep-out >= 3.35 mm from the board edge):
    - A closed frame (`RailsFrame` framing plugin in `tools/lib/panel_tabs.py`, 2 mm
      gap): 9 mm rails top and bottom, because a 2 mm keep-out needs 3.35 mm to both
      the outer edge and the rail's inner edge (8.7 mm; with 5 mm rails it was only
      1.55 mm); 5 mm side rails (JLC's rail minimum, no fiducials on them). KiKit's own
      frame has one width for all sides, hence the plugin.
    - 3 fiducials per side (front and back; the back is the assembly side), 1 mm
      copper, 2 mm opening, centred in the rail (4.5 mm in): keep-out 3.5 mm from
      every edge. Tooling holes (3, 1.152 mm) and the texts are centred in the rails too.
    - 5 mm mouse-bite tabs (0.5 mm holes, 0.8 mm pitch, offset 0.25 mm into the board
      so the nubs don't stick out), and `JLCJLCJLCJLC` on the rail (JLC prints the
      order number there, not on the board).
    - JLC ships assembled boards with the rails on; removal is an extra paid option.
  - V-cut can't be used: no straight edge of the outline is the outermost one.
  - Tabs come from `tools/lib/panel_tabs.py` (`FixedTabs` tabs plugin): fixed spots
    where the outline reaches the frame; top / bottom as x (mm from the board bbox's
    left edge), left / right as y (mm from its top edge), `value:width` for a tab of
    its own width. Per board, 14 tabs:
    - 2 on the top edge of each half, 2 at each thumb-key corner / centre bottom edge
      (8, as before);
    - 2 top-centre bridges, 8 mm wide, ~29 mm long down to the recessed edge behind
      the OLED (centre ± 25 mm; it was 236–243 mm between top tabs);
    - 1 side tab at the outer corner of each half (the leftmost / rightmost point).
    - hachigo74: top 51.6 73.6 166.4:8 216.4:8 309.2 331.2, bottom 126.6 161.4 221.4
      256.2, left / right 86 (panel 396.8 × 165.9 mm).
    - kugo82: top 70.6 92.6 189.3:8 239.3:8 336.0 358.0, bottom 149.6 184.3 244.3
      279.0, left / right 82 (panel 442.7 × 167.2 mm; JLC's limit is 460 mm).
  - `tools/lib/snap_outline.py` closes Ergogen's ~0.0001 mm outline gaps in a temp
    copy first; KiKit rejects them, KiCad doesn't.
  - KiKit moves footprint cutouts (LED windows, stabilizer cutouts) into the board
    outline and leaves the panel's `.kicad_dru` empty, so `panel.sh` writes a panel
    rule: 0.2 mm edge clearance for LED pads against Edge.Cuts inside the LED
    courtyard.
  - Expected panel DRC: 5 silk_overlap, plus `lib_footprint_mismatch` for every LED
    and 2U footprint (78 on hachigo74, 86 on kugo82; they lost their cutouts to the
    outline, harmless), plus the unrouted pads.
  - Re-run it after routing, then run the Fabrication Toolkit on the panel board.

## Working with the user

- **No 3D renders unless asked.** For a quick visual check, make the 2D top view:
  `python tools/lib/printview.py <name> <keyboard>/kle/<name>_legends.json <out.pdf>`
  (after building that design; needs PyMuPDF). `topview.js` only works while the
  keys still match an in-half KLE file.
- **The KLE file sets keycap widths and key positions within a half only.**
  Angles, the −15° rotation and the distance between the halves stay as they are
  in Ergogen. Mapping (kugo82): our x = KLE x − 0.5, our row y = 4.75 − KLE y
  (left half); the right half is mirrored in the KLE file (x → 21.5 − x).
- **KLE legends:** front-centre = QMK keycode (for the firmware); centre-left =
  the Hungarian character.
- Make a new yaml for big layout changes (the old kugo82 / kugo80 live in git history).
- **Always add a silkscreen marker circle for new case supports** (studs, posts,
  spacers) via `support_marks_back` / `support_marks_front`, so they show on the PCB.
- **Verify before claiming.** After changes, build and check DRC, part counts and
  clearances, both halves. Right-half parts are not exact mirror copies (the
  switch footprints are not mirrored), so check the mirrored spots separately.
- **Commits:** commit and push only when the user asks. The remote is `origin` =
  github.com/baalsmn/keyboard-workshop (private). The old single-keyboard repo
  github.com/baalsmn/kugo80 is superseded by this one.

## Build

```bash
bash tools/build.sh [name]     # default kugo82; also hachigo74
bash tools/case.sh [name]      # out/cases/*.jscad -> <keyboard>/case/*.stl
bash tools/step.sh [name]      # STEP + Fusion data -> <keyboard>/case/step/, case/fusion/
bash tools/render.sh [name]    # 3D renders -> <keyboard>/renders/ (only when asked)
bash tools/panel.sh [name]     # JLC assembly panel (rails + tabs) -> <keyboard>/kicad/<name>_panel.kicad_pcb
```

- `tools/lib/design.sh` finds `ergogen/<name>.yaml` and its keyboard folder (from
  the yaml's `# keyboard:` first line) for every tool. `build/` and
  `out/` are shared root scratch folders holding the last build only, so build a
  design before running case/step/render for it (they check).
- `build.sh` copies `ergogen/<name>.yaml` → `build/config.yaml` plus `ergogen/footprints/`, runs
  `ergogen build -o out --debug`, copies `keyboard.kicad_dru` to
  `out/pcbs/<name>.kicad_dru` and runs `kicad-cli pcb drc`.
  - Expected result (kugo82 and hachigo74): 5 `silk_overlap` warnings (labels of
    the indicator LEDs and caps, and of the thumb-area LEDs) and 499 unconnected pads. The board is not routed yet.
    - A `silk_over_copper` on a support marker means a post or stud base presses on
      a part: fix it.
    - Any non-silkscreen violation is a real problem.
  - Output must go to `<root>/out`, because 3D model paths are
    `${KIPRJMOD}/../../kicad-libraries/3dmodels/...`.
- **Tools:** `kicad-cli` is at
  `C:/Users/balin/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe`, and KiCad's
  Python (`pcbnew`) is in the same `bin/`. Ergogen is installed globally with npm.
- `case.sh` installs the OpenJSCAD v1 CLI into `tools/jscad` on first use. It fixes
  two arc bugs (`tools/lib/fixarcs.js`, plus `"large":true` → `false` on the r12
  corner arcs) and converts to STL.
- `step.sh` rebuilds every case part as a true solid (build123d / OpenCascade) from the
  outline DXFs and the yaml case recipe, and exports STEP: editable bodies in Fusion
  with real arcs, unlike the STL mesh. build123d (~700 MB) installs on first use into
  `%LOCALAPPDATA%/kugo-build123d`. Build the design first; volumes match the STLs
  within 1%.
  - Converter details (`tools/lib/step_case.py`): DXF endpoints are snapped so loops
    close; tiny arcs become lines; holes come from even-odd filling; every extrude is
    forced upward (+Z), because rebuilt faces can come out flipped.
  - It also writes `<keyboard>/case/fusion/<name>_case.json` (`tools/lib/fusion_data.py`):
    every outline as closed loops of lines / 3-point arcs / circles, with nesting
    depth and exact bounding box, plus the case recipe.
- **Fusion script** `tools/fusion/KeyboardCase/` (add the folder in Fusion's Scripts
  and Add-Ins, run, pick a `_case.json`): a new parametric design, one component per
  case part, one sketch per outline, extrudes (start offset = z, distance = height)
  combined join / cut / intersect in recipe order, a timeline group per part.
  Each outline gets one sketch per loop nesting depth (depth 0 = filled, extruded as
  a new body; depth 1 = holes, cut from it), so no profile picking is needed.
  (Matching profiles by bounding box failed: Fusion's boxes are loose on arcs.)
  - Arc end points are paired by position: Fusion keeps arcs counter-clockwise, so a
    concave arc's "start" is our end point.
  - **Optional plate ribs** (asked at start, default `1.0, 1.0, 1.5`): a rib frame
    under the plate around every switch cutout. Relief gap (default 1 mm) around the
    switch (on the 2U keys around switch + stabilizer housings + wire, 30 × 15.1) so
    switches and stabs still snap in; frame width (default 1.5, > 1.45 merges the
    neighbours into a web); depth = user parameter `plate_rib` (max 1.3 = to the PCB
    top). Clipped 0.5 mm inside the PCB outline (clear of the tub wall), the plate's
    holes cut through. Data: `rib` in the `_case.json` (key rectangles from
    `switches_outline` + `stab_cutouts`, region from `pcb_outline`). Checked offline
    with the defaults: nearest through-hole pad (Helios) 11.1 mm away.
- **`render.sh` workarounds:**
  - The user's KiCad 3D settings hide "virtual" footprints, so the render copy
    marks every footprint `smd`, including those with no attr line at all, like the
    switches. Don't change the user's KiCad settings.
  - Run renders one at a time.
- **`tools/lib/` scripts:**
  - `vrml.js`, `keycap.js`, `oled.js`: VRML model generators.
  - `stl2wrl.js`: STL → VRML conversion.
  - `kle_parse.js`: KLE parser that decodes legend positions.
- **Routing tools** (KiCad python + shapely: the KiKit venv `%LOCALAPPDATA%/kugo-kikit`):
  - `route_grid.py`: angle-keeping grid router (key frame per half, 0 deg centre).
  - `led_rechain.py`: re-orders / renumbers the LED data chain on a routed board.
  - `remap_pins.py`: moves nets to other pins of a footprint (the Helios), removing only
    the segments at the changed pins.
  - `gnd_stitch.py`: GND stitching vias, one or more per back-side pour piece.
  - After any of them on a project board, rebuild its schematic with `kicad_project.py`
    (keep a copy of the `.kicad_pro`, `.kicad_dru` and README and restore them).

## Ergogen gotchas (learned the hard way)

- **Row `shift` carries over** to the rows above it in the same column.
  - Column origins are *not* affected by the previous column's row shifts.
  - Mirrored points negate x shifts and rotations.
- **Outlines are processed in file order.** Define an outline before you use it.
- **Expand inside a multi-part outline:** a part's `expand` applies to the running
  result. Several expanded parts compound (the posts came out at 7.8 mm), and
  subtracting an identical circle fails. Build each expanded shape as its own
  outline, then combine them.
- **`where:` with a list of two refs in one part kept only the last one.** Use one
  part per half.
- **Case and plate expansion:** maker.js `expand` breaks a corner at some values
  (stray full circle, open outline → empty tub or shrunken lid in the STL).
  kugo82 now grows the case (and plate) from `pcb_core` (the PCB polygon before its
  2 mm rounding) with `expand: 10, joints: pointy, fillet: 3`: 8 mm wall, r3 corners
  (concave corners r3 too, were r2). After any outline change:
  - check `out/outlines/case.svg` and `plate_clean.svg` are closed (one `M`, ends in `Z`);
  - check that all 5 STLs have a sensible size and triangle count.
- **Gateron KS-33 / KS-2P02B01-02 drawings are bottom views.** Use the STEP models
  for footprint chirality. Top-view pin holes are at (+2.6, 5.75) and (−4.4, 4.70);
  the LED window is at (−0.69, +5.16 north).

