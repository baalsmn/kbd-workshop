# keyboard-workshop — Ergogen keyboards on one PCB

Split-style ergonomic keyboards, each a mirrored two-half layout on a single PCB,
designed in **Ergogen 4.2.1**, finished in **KiCad 10**, case 3D-printed.

## Layout

- Root = shared: `tools/`, `footprints/` (Ergogen), `3dmodels/`, `datasheets/`,
  `keyboard.pretty/` (KiCad footprints), `keyboard.kicad_dru` (DRC rules for every
  design), `drafts/` (the user's sketches).
- One folder per keyboard, holding only its own files:
  - `kugo/`: `kugo82.yaml` (**current**, 82 keys), `kugo80.yaml` (80-key backup,
    don't edit unless asked), `kle/`, `case/` (STL, `step/`, `fusion/`), `renders/`.
    Hardware, stack-up and open items: **`kugo/CLAUDE.md`**.
  - `hachigo74/`: `hachigo74.yaml` (74 keys, kugo82 minus column c1), `kle/`,
    `case/`. Details: **`hachigo74/CLAUDE.md`** (hardware otherwise as kugo).
- A new keyboard = a new folder with `<name>.yaml` (+ `kle/`); the tools find it by
  name.

## Working with the user

- **No 3D renders unless asked.** For a quick visual check, make the 2D top view:
  `node tools/lib/topview.js . kugo/kle/kugo82.json kugo/renders/kugo82_top.svg`
  (after building that design).
- **The KLE file sets keycap widths and key positions within a half only.**
  Angles, the −15° rotation and the distance between the halves stay as they are
  in Ergogen. Mapping (kugo82): our x = KLE x − 0.5, our row y = 4.75 − KLE y
  (left half); the right half is mirrored in the KLE file (x → 21.5 − x).
- **KLE legends:** front-centre = QMK keycode (for the firmware); centre-left =
  the Hungarian character.
- **Keep `kugo/kugo80.yaml` as a backup**, and make a new yaml for big layout changes.
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
bash tools/build.sh [name]     # default kugo82; also kugo80, hachigo74
bash tools/case.sh [name]      # out/cases/*.jscad -> <keyboard>/case/*.stl
bash tools/step.sh [name]      # STEP + Fusion data -> <keyboard>/case/step/, case/fusion/
bash tools/render.sh [name]    # 3D renders -> <keyboard>/renders/ (only when asked)
```

- `tools/lib/design.sh` finds `<keyboard>/<name>.yaml` for every tool. `build/` and
  `out/` are shared root scratch folders holding the last build only, so build a
  design before running case/step/render for it (they check).
  - kugo80 (the backup) writes its case files to `kugo/case/kugo80/`.
- `build.sh` copies `<name>.yaml` → `build/config.yaml` plus `footprints/`, runs
  `ergogen build -o out --debug`, copies `keyboard.kicad_dru` to
  `out/pcbs/<name>.kicad_dru` and runs `kicad-cli pcb drc`.
  - Expected result: 2 silkscreen warnings (overlapping labels of the indicator
    LEDs and caps) and 499 unconnected pads. The board is not routed yet.
    - A `silk_over_copper` on a support marker means a post or stud base presses on
      a part: fix it.
    - Any non-silkscreen violation is a real problem.
  - kugo80 gives 2 `silk_over_copper` instead (unchanged backup).
  - Output must go to `<root>/out`, because 3D model paths are
    `${KIPRJMOD}/../../3dmodels/...`.
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
  Filled profiles = profiles whose box matches a loop of even depth. Untested in
  Fusion so far: the data was checked against the STEP areas (0 mismatches).
- **`render.sh` workarounds:**
  - The user's KiCad 3D settings hide "virtual" footprints, so the render copy
    marks every footprint `smd`, including those with no attr line at all, like the
    switches. Don't change the user's KiCad settings.
  - Run renders one at a time.
- **`tools/lib/` scripts:**
  - `vrml.js`, `keycap.js`, `oled.js`: VRML model generators.
  - `stl2wrl.js`: STL → VRML conversion.
  - `kle_parse.js`: KLE parser that decodes legend positions.

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
  (concave corners r3 too, were r2). kugo80 uses round `expand: 9.99`. After any outline change:
  - check `out/outlines/case.svg` and `plate_clean.svg` are closed (one `M`, ends in `Z`);
  - check that all 5 STLs have a sensible size and triangle count.
- **Gateron KS-33 / KS-2P02B01-02 drawings are bottom views.** Use the STEP models
  for footprint chirality. Top-view pin holes are at (+2.6, 5.75) and (−4.4, 4.70);
  the LED window is at (−0.69, +5.16 north).

