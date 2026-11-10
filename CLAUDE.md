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
- `keycaps/`: everything keycap-related (user's rule, 2026-10-24), in two folders (user 2026-11-09):
  - **`keycaps/results/`**: the print files `cap_<size>_<legend|blank>.3mf` and `cap_1u_slope_*.3mf`
    (open in Bambu Studio as a project), the Fusion designs `<cap>.f3d` (gitignored, kept locally), and
    `profiles/` (the Bambu Studio user presets). The 3MFs and profiles are in git.
  - **`keycaps/build/`**: everything else: the scripts, `keycap-10-13.step`, `inserts.txt`,
    `fusion/KeycapBuilder/` (tracked), and `work/` (generated, gitignored: `work/caps/` build123d STEP +
    Fusion recipes `<cap>_fusion.json`, `work/fusion/` Fusion's STEP + 3MF (the print 3MF's mesh source),
    `work/slope_test/`). `.gitignore`: `build/` everywhere, but `!keycaps/build/` and `keycaps/build/work/`.
    Paths are set once in `keycap.py` (`WORK`, `CAPS_DIR`, `FUSION_DIR`, `RESULTS`, `PROFILES`).
  **Monolithic caps
  only** (user 2026-11-09: the insert caps (a pocket with a separately printed legend insert) and their
  inserts, assembly and Bambu project were dropped, code and files; they are in git history). Two kinds:
  **blank** (one material; legends go on later by solvent transfer) and **two-colour** (double-shot
  split). **No STL files at all** (user: not needed) and **shell and core always in one file** (user
  2026-11-09: printed together, no separate part files): STEP (both bodies) + 3MF (one object, both
  parts), also for Fusion's exports.
  - `keycap.py`: the shape library, a parametric build123d remake of the user's `keycap-10-13.step`
    (run with the build123d PYTHONPATH): 1U = 18.2 x 18.2 (Ergogen `kc`, 0.8 gap on the 19 pitch),
    1.25U 22.95, 2U 37.2 with KS-57 stems; skirt 5 deg off vertical (user: closer to square to the plate;
    the original had 16); 3 deg sloped top (north up); the whole top **one surface** (`top_points()` /
    `top_tool()`, recipe `top_surface`; Fusion step `surface()`, a loft cut): plane - dish - north
    roll-off added up (user: separate cuts left a ridge where the dish met the roll-off; no plane cut
    before it: coincident faces broke the boolean). Dish (`valley_style='dish'`): z = -0.6 (1 - (r /
    valley_r)^2)^2, valley_r 8.6, stretched along the long side (x on wide caps, y on tall ones).
    Ceiling -2.1 below the top plane (`ceiling`; 0.2 lower touched the switch at 3.0 travel), so the top
    is 1.5 thick at the centre. Stem Ø5.0 (user: 5.22 too wide; 0.45 wall at the cross hole's arm
    ends), 1.3 below the skirt (on the KS-33 cup floor) so the skirt clears the switch over the full
    3.0 travel; cross hole 4.10 x 1.20 (FDM, 0.2 nozzle). KS-57 stems start 1.25 higher (their cross top
    is 9.8 above the PCB, the switch's 8.55) with a ceiling recess over the stabilizer housings (top
    6.55, y -4.9 .. 4.6). Sizes as `--units` specs: `1`, `1.25`, `1.25t`, `2s`, `2st`, `1v`
    (s = stabilizer stems, t = thumb, v = tall); `cap_params()` gives each its parameters.
    **Off-centre caps** (user 2026-11-09): `@x` puts the switch stem at cap x (`1.5@-0.5` ->
    `cap_1.5u_stem-0.5`; `spec_params()`, `spec_name()`, param `stem_x`). Made for a 1.5U at c7_r1: centred,
    1.5U overlaps c5_r1 / c9_r1 (widest centred 1.39U; `cap_1.35u` made too), so the 1.5U body sits 0.5
    toward c9_r1 and the c9_r1 1.25U thumb 1.5 away from c7_r1: gaps 1.07 (c5_r1) / 0.94 (between), both
    designs. Left half stem -x (`1.5@-0.5`, `1.25@-1.5`), right half +x. c9_r1 uses the normal
    (dish) 1.25U shape like every other key (user 2026-11-10); the thumb versions `1.25t@±1.5` are kept as
    backups. All clear over the full travel.
    **Level caps** (`l`, user 2026-11-10, for the thumb cluster c5_r1 / c7_r1 / c9_r1): slope 0, so the
    north and south skirt faces are equally high (5.80 tall); name `_level` before `_stem`:
    `2sl`, `1.25l`, `1.25l@±1.5`, `1.35l`, `1.5l@±0.5` made (blank and A, Fusion recipes written, build123d
    meshes). All clear over the full travel (2U also against the stabilizers); they slice.
  - Thumb versions (1.25U / 2U, `t`, user's request; `thumb_style='valley'`): they keep a **flat centre**
    (`valley_style='flat'`, `thumb_valley` 0.5 below the top plane, `flat_r` 5.4, rising smoothly to the
    top plane at valley_r; the old insert caps' floor) because the south part rolls down from its south
    edge: in the centre section an arc tangent to the flat, then a short line down to the south skirt's
    bottom edge (user: fully down, meets it at 15 deg; at the sides, where the curve is raised, a strip
    of skirt up to 0.66 is left); every east-west slice is that profile raised by the valley's own
    east-west profile at the start line (user: continuous with the top). Point-grid surface starting
    0.002 above the top; ~1 mm wall at the inside corner. Fillet (user, 2026-10-25): only the north,
    west and east top edges (none touching the thumb surface), 0.6, only on the **1.25U thumb**
    (`thumb_fillet_units`; the 2U thumb's fails); thumb caps have square south corners (user's idea).
    The 1.25U thumb curve is scaled per slice down through the skirt's bottom edge
    (`thumb_scaled_units`, user: no skirt left on the south side, aims 0.05 below the edge); the 2U
    thumb keeps the earlier curve (its cut fails the scaled way). `thumb_style='straight'` (WIP, user's
    idea): no east-west valley, one north-south profile pushed across; its fillet failed, not finished.
  - **Tall cap** (user 2026-11-08): `1v` -> `cap_1u_tall`, 1U wide, 2U deep (18.2 x 37.2) over two
    switches of one column (rows 19 apart), a switch stem on each (y +-9.5), no stabilizer
    (`tall_params()`: `depth`, `stems_y`, `ceiling_level`). The ceiling is level at the 1U centre height
    (a sloped one came down onto the south switch's housing at 2.7 travel); clear over the full 3.0 on
    both switches; slices in Bambu Studio (~2 h, 2.7 g).
  - **Slope test caps** (user 2026-11-08, to decide the lean per row): `slope_test.py` ->
    `results/cap_1u_slope_{+3,0,-3}.3mf` (STEP in `build/work/slope_test/`; blank): north up / level / south up (the +3
    cap turned 180 deg, roll-off south). All clear over the full travel. Idea if per-row: rows above
    home +3..+5, home 0, bottom -3.
  - `top_fillet` 0.6 (user) along the top outer edge outline on every non-thumb cap: the edges between
    top faces and the outer skirt faces (picked by their exact draft lean), filleted as one chain (OCC
    needs the whole tangent chain; one bad edge fails it all; the script says what it skipped). With
    the dish top build123d's fillet fails on the 2U caps (10 of 10 edges skipped, 2026-11-09).
  - Corner radii shrink upwards with the draft (outside r_bottom 2.0, inside r_inner 0.8), like a
    tapered extrude, so a Fusion rebuild matches.
  - **`legend_cap.py`: the command line for every cap** (`--units 1,1.25,1.25t,2s,2st,1v`,
    `--legend A` or `--legend ''` for blank, `--fusion`): writes `results/cap_<size>_<legend|blank>.3mf`
    (Bambu Studio, one object, south skirt face on top (see below), shell
    filament 1, core filament 2, print settings and per-object supports as below) and `build/work/caps/<same>.step` (coloured
    bodies). Two-colour split
    like a double-shot moulding (user): a translucent **core** (filament 2: stems, a `core_t` 0.5 layer
    over the cavity ceiling inside the skirt walls (level on the tall cap), the legend reaching up
    through the shell) under an opaque **shell** (filament 1: the rest of the top, 1.0 at the centre, +
    the whole skirt). User: thick shell, thin core (a 0.8 skin over a 0.8 core left the slicer broken
    lines). Legend Arial bold 5.85 (user: 30 % up from 4.5), its box's south-east corner on the top's
    centre point (north-west quadrant, box 4.2 x 4.19). Slice check of 1U 'A' (lying on the north face):
    both filaments on every layer: 246 filament changes, ~19 h, ~94 g of filament (purge) for one cap.
    The blank 1U slices in ~1 h, no filament changes.
  - **Fusion** (`cap_source='fusion'`): `legend_cap.py --fusion` writes
    `build/work/caps/cap_<size>_<legend|blank>_fusion.json` (`keycap.recipe()` + `legend` / `core`,
    None on blank caps); **Fusion builder** `keycaps/build/fusion/KeycapBuilder/` (run, pick one or more
    recipes, or `build_legend_cap(rec)` + `export_legend_cap()` through the bridge) makes one parametric
    design per cap, a timeline group per stage (skirt tapered by user parameter `draft` (thumb caps:
    square south corners), top plane at `slope`, top surface loft cut or roll-off + valley (thumbs),
    thumb loft cut, cavity tapered to the ceiling plane (level on tall caps), stab recesses, stems +
    crosses (with y on tall caps), fillet `top_fillet`, the "double shot" group: core region = cavity
    outline tapered by `draft` up to the core plane + stem ends + sketch text; core = cap & region,
    shell = cap - core) and saves `results/<name>.f3d` and `build/work/fusion/<name>.step/.3mf` (Fusion's 3MF export of
    the occurrence: one file, every body a named object: `shell`, `shell island <n>`, `core`; blank:
    `cap`; millimetres, no transforms; read by `bambu_project.read_3mf()`). The print 3MF takes its
    meshes from it while their volumes match build123d's (0.2 %), else build123d's meshes, with a note to rebuild in Fusion; `keycap.get_cap()` (fit checks) loads the
    blank STEP. Fusion text: `boundingBox` of a sketch text is its glyph box (matches build123d's); the
    text is flipped to read from above by the sketch's x / y directions. Closed counters (A's triangle)
    are shell islands: Fusion won't join bodies that don't touch, so they stay bodies `shell island <n>`
    (joined into the shell part of the print 3MF). Checked (1U A and blank, 2026-10-27): volumes within 0.01 % of
    build123d, meshes closed, letter orientation by point tests. Checked 2026-11-09 (Fusion 2706.1.17, bridge): all 6 sizes blank
    and 'A' built and exported, every feature healthy, volumes within 0.02 % of build123d except the 2U
    thumbs (-0.5 %: Fusion makes their top fillet, build123d's fails; Fusion's 2U fillet works too), all
    clear over the full travel. The print 3MF takes Fusion's meshes within 0.2 % of build123d, or within 1 %
    when its 3MF is newer than the recipe and the recipe's build123d volume still matches (the fillet
    cases). The 2U thumb 'A' slices (~19 h).
  - `check_fit.py` sweeps each blank cap size over the travel against the vendor switch / stabilizer
    STEP models (the tall cap against both switches) and checks the gaps on the Ergogen key points
    (0.80 min, 6.6 to the centre cover). Checked 2026-11-09: every size clear over the full 3.0.
  - `keycaps/build/inserts.txt` (user's legend list, one per line, `#` comments; was read for the inserts) is
    not read by anything now. `keycap.file_name()`: legend file names, letters / digits as is, accented
    letters letter + accent (`O_dacute`), anything else its code (`/` -> `u002f`).
  - `bambu_project.py` is now only the 3MF writer (`write_3mf()`, `mesh()` (welds build123d's per-face tessellation: unwelded, every build123d-meshed cap had open edges in Bambu Studio, fixed 2026-11-10), `read_3mf()`, `read_stl()`, `safe_name()`;
    **Bambu Studio only**, user 2026-10-26). Caps print with the **south skirt face on top and
    horizontal** (user 2026-11-10; was lying on the north face): layer lines across the top, the
    south face prints cleanly, the north face (10 deg off the bed) stands on its bottom edge over
    support (less visible); cavity opening to the back; the `t` thumb caps (south side rolls away) still
    lie on the north face (`print_meshes(south_up=...)`); per-object tree
    supports (inside only: stem underside, cavity roof; threshold 40; on project-wide too since 2026-11-10: a cap
    imported into an open project, geometry only, loses its per-object setting and its stem floats), 4 mm brim, seam back, 8 wall
    loops. Filament: `Generic PLA @BBL A1 0.2 nozzle` on both, unchanged (user 2026-11-10; was PolyTerra) (the user has a
    Bambu A1, prints with a 0.2 nozzle; 256 bed). Prime tower at (195, 60) on every plate
    (`wipe_tower_x/y`, one entry per plate): Bambu's default ran off the A1 bed. Check a 3MF with
    Bambu Studio's CLI (`bambu-studio.exe --slice <plate> --outputdir`, result.json is UTF-8).
    Names: Bambu Studio's GUI refuses `<>:/\|?*"` in any object / part / plate name ("Invalid name",
    then "Invalid configuration file"; the CLI doesn't check), so `write_3mf()` passes every name
    through `safe_name()`. The GUI is stricter than the CLI on `project_settings.config` too (user's
    tests 2026-10-26): it needs the per-filament fields Bambu Studio 2.x writes, one entry per filament
    (`filament_ids`, `filament_self_index`, `filament_map` + `filament_map_mode`, `filament_nozzle_map`,
    `filament_volume_map`, `extruder_ams_count`, colour fields, `flush_volumes_vector` 2 per filament),
    and no preset-only fields (`compatible_printers*`, `compatible_prints*`, `inherits_group`). Preset
    `include` lists (Bambu's templates, e.g. the A1 start / end G-code) are merged in, and keys Bambu
    doesn't write into projects are left out (`NOT_IN_PROJECT`). Reference: compare with a project
    Bambu Studio itself saved (none kept now: save one from the GUI when needed).
  - `bambu_settings.py`: print settings built from the installed Bambu Studio system presets
    (`%APPDATA%/BambuStudio/system/BBL`; A1 0.2 nozzle, Generic PLA x2, `0.06mm High Quality @BBL A1 0.2
    nozzle`) + our changes (0.10 first layer / 0.06 layers, 0.20 outer / 0.22 lines, Arachne + precise
    outer wall, outer wall 40 mm/s, seam back, no scarf, avoid crossing walls, tree supports 40 deg on; no filament changes), embedded as `Metadata/project_settings.config` (shown in Bambu Studio as
    the system presets, modified; the 3MF headers carry Bambu Studio's version from BambuStudio.conf);
    `keycaps/results/profiles/*.json` is the importable process preset (File > Import > Import Configs). Keys are checked
    against the presets; `precise_outer_wall`, `fuzzy_skin`, `brim_type` sit at built-in defaults.
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
  Originals: the user's uploads (most also in the gitignored `vendor/`; the `drafts/` copies
  were removed on 2026-10-24 and never committed). Checked against the drawings: socket 15.08 × 5.39 × 3.0, in the
  footprint frame; switch 15 × 15, origin at the key centre with z 0 = PCB top (offset
  0, 0, −1.6), pins at (2.6, 5.75) / (−4.4, 4.7); stabilizer 30 × 16.97, housings 6.0 at
  ±12, 4.45 below the plate top (offset −60, 0, 1.65); LED pin-1 lead (cut corner) and body
  chamfer on the GND pad.
  - OLED: the vendor STEP as is, offset (0, −12.2, 1.2) (header row at its y +12.2); it
    still shows the plastic header spacer (the module really sits on bare pins). A cleaned
    re-export lost the per-face colours (build123d keeps one colour per part), so it wasn't used.
  - Keycaps: the user's MBK keycap STLs (uploaded to `drafts/`, not kept) -> VRML by `tools/lib/stl2wrl.js` (binary STL now read),
    stem bottom 6.3 / rim 9.6 / top 13.6 above the PCB top (switch stem top 8.55);
    1.25u = the 1u cap stretched 1.25x in x (no MBK 1.25u model).
- Switch footprint (`ks33_hotswap.js`): back silkscreen = the stepped socket body from the
  courtyard of Gateron's KS33 hot-swap footprint (`Gateron_KS33_Hotswap.pretty`, uploaded
  by the user, not kept in the repo),
  mirrored to the back, terminal tabs left out (on the pads); the 14 × 14 switch body is
  drawn as corner marks (Dwgs.User). Pads kept (ours: 2.45 × 2.55, at the drawing's pad
  centres; the uploaded footprint's 2.55 squares sit 0.5 mm further in). Centre hole **Ø5.15**
  (user, 2026-11-03; 0.1 play round the Ø5.05 post, between the socket drawing's Ø5.1 and the switch
  drawing's Ø5.25; not yet tried on a board). It was Ø5.25 (switch drawing), and on the first hachigo74 PCB (ordered with Ø5.25; its KiCad project has Ø5.15 since 2026-11-04)
  the post moves in the hole and only the electrical pins locate the switch.
  Switch heights (Gateron's STEP, above the PCB top): 4 corner feet to about 0.22 ((±4.95, ±6.25), Ø~0.4),
  body floor above them, plate top 2.5 = flange underside. So a pad under the switch fits in about 0.2
  without lifting it; pin tips reach 0.8 below the PCB bottom, so lifting costs socket engagement.
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
  "LED window relief clearance").
- **Track widths** are DRC rules in `keyboard.kicad_dru` (copied into each project's
  `.kicad_dru`): min (DRC error below it) / opt
  (the router's default width): signals 0.2 / 0.25 mm, `VCC` (5 V, LED chain) 0.3 /
  1.0 mm, `GND` 0.5 / 1.0 mm, `3V3` 0.3 / 0.3 mm. 5 V plan (user's): 1 mm stub from the
  Helios pad to C85, then 0.5–0.6 mm trunks (two per half, joined at the outer column),
  0.3 mm allowed for the last hop to an LED pad; 2 vias per power layer change. Net names match by their end (`*VCC`).
  GND is best a pour on both layers.
- `tools/lib/kicad_project.py` copies the footprint's LCSC number into the schematic
  symbol.
- The user exports with the Fabrication Toolkit plugin (bennymeg) in KiCad. Check the
  rotations in JLC's placement preview: everything is on the back at 15° steps. Fix
  them with the plugin's `FT Rotation Offset` / `FT Position Offset` fields.
- **Panelization: JLC does it** (user's decision, 2026-10-23): upload the design board's
  files and choose "Edge Rails: Added by JLCPCB". Our own KiKit panel (rails, fiducials,
  mouse bites, `tools/panel.sh`, `panel.json`) was removed; it pushed the board over JLC's
  650 cm² "Large Size" fee. It is in git history (up to commit 55d6b66) if ever needed.
  JLC's panel for the first hachigo74 order: 5 mm rails top and bottom, V-cut along the
  rails' inner edges (the board only touches them at its outermost points), tabs on the
  routed edges, their QR code on the rail.

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
  - **Tilt wedge** (`tools/lib/wedge_case.py`, run by step.sh; user's design 2026-10-24): a
    separate printed skeleton under the unchanged tub that raises the **south** edge, so the
    case stands on the table with the key plane tilted (negative tilt). 3 mm at the north
    edge, `WEDGE_ANGLE` (default 6 deg) over the 164 mm depth = 20.3 mm at the south.
    - Skeleton (user's request): a 10 mm frame band under the tub's edge (8 mm wall) with a
      1 mm rim around the tub's foot (0.3 clearance, 2 wide), 4 columns per half (Ø10 struts,
      a Ø6.0 x 1.0 column on top with a 3.2 x 1.1 pocket for a 3 x 1 mm magnet), ribs (5 wide)
      joining a half's columns in a ring and each to the frame, and a centre wall (3 mm each
      side of the halves' joint, north to south frame) so the halves butt along the whole
      depth. No screw holes: the cover screws and reset pin stay reachable through the
      openings (1.2 mm clear of the wall).
    - Joint magnets (user's request): 2 facing pairs of horizontal 3.2 x 1.1 pockets in the
      centre wall (spread along it inside the frame, centred in the wall height), each only
      where the wall is tall enough for the magnet + 1 mm above and below (5.2 mm): at 6 deg
      both (y -87.5 / -139.7), at 1.5 deg only the south one. In Fusion the `side_holes`
      step places them for the tilt_angle at build time (log says how many fit); they don't
      move with a later tilt_angle change.
    - Column places = the yaml outlines `wedge_socket` / `wedge_magnet` (key centres c4_r4,
      c3_r2, c8_r4, c8_r2 and mirrors). The tub floor has the matching socket (Ø6.4, 1.1 deep)
      and magnet pocket (Ø3.2, to 2.2: 0.8 floor left) in its recipe, so the STLs, STEP and
      Fusion tub all have them. Glue the magnets with opposite poles facing (0.3 mm air gap).
    - Writes `case/wedge_<a>deg_left/right.stl`, `case/step/wedge_<a>deg_left/right.step`
      (print orientation, table side down) and `..._assembly.step` (tub frame). Fusion data:
      `wedge_left/right`, whose "tilt" step the script turns into a split by a plane at the
      user parameter `tilt_angle` (asked at start, up to 15 deg).
    - build123d gotchas met here: an inward `Kind.ARC` offset of the case leaves 0.1 µm
      edges (invalid solid, booleans come out empty), so the frame opening uses
      `Kind.INTERSECTION`; overlapping 2D pieces don't fuse (flipped normals), so they are
      extruded with `dir=(0, 0, 1)` and fused as solids.
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
  - **Optional tilt wedge** (asked at start if the data has one): `tilt_angle` user parameter;
    built in the tub frame (the table plane is tilted, not the keyboard): `tilt_split` puts a
    plane through the north line at the angle (the sign chosen so it falls to the south),
    splits the wedge and removes the piece under it. The axis line spans only the wedge's
    width (keeps the plane small); the planes and axis sketch are hidden (light bulb off).
  - Nearly straight or dot-sized arcs (offset slivers, e.g. the rib region) are drawn as
    lines or skipped: Fusion refuses a three-point arc on them.
  - **Optional plate ribs** (now kugo82 only: hachigo74's lids have them in the yaml, see its
    CLAUDE.md, so the script doesn't ask; this option's 2U relief hits the stabilizer housings,
    y -8.05 against their -9.74, fix before using it; asked at start, default `1.0, 1.0, 1.5`): a rib frame
    under the plate around every switch cutout. Relief gap (default 1 mm) around the
    switch (on the 2U keys around switch + stabilizer housings + wire, 30 × 15.1) so
    switches and stabs still snap in; frame width (default 1.5, > 1.45 merges the
    neighbours into a web); depth = user parameter `plate_rib` (max 1.3 = to the PCB
    top). Clipped 0.5 mm inside the PCB outline (clear of the tub wall), the plate's
    holes cut through. Data: `rib` in the `_case.json` (key rectangles from
    `switches_outline` + `stab_cutouts`, region from `pcb_outline`). Checked offline
    with the defaults: nearest through-hole pad (Helios) 11.1 mm away.
  - **Fusion-only features** per design: `TOP_EDGES` (chamfer / fillet of a part's top outside edge) and
    `THREADS` (modeled ISO thread on a cylinder face of a given radius, faces then offset by the user
    parameter `thread_play`; Fusion's thread size is the designation's, not the face's). Zero-area sketch
    profiles (an arc meeting a curve within a micron) are skipped: extruding one fails.
- **Fusion test bridge** `tools/fusion/Bridge/` (add-in, start it in Scripts and Add-Ins ->
  Add-Ins, stop it when done; not run on start-up): runs Python sent to 127.0.0.1 (port 8765)
  on Fusion's main thread, token in `~/.fusion_bridge` (new each start, deleted on stop);
  browser requests (Origin header) refused. Client: `python tools/fusion/fusion_run.py
  <file.py> | -c "code" | --ping`. Tested 2026-10-24 (Fusion 2706.1.14): all 9 parts one solid each,
  volumes = the build123d STEP, tilt_angle 3 / 10 / 15 / 6 deg recompute cleanly. KeyboardCase's `build_design(data, ribs, tilt)` builds
  without the dialogs (import the script file and call it). Test in new, unsaved designs only.
- **`render.sh` workarounds:**
  - The user's KiCad 3D settings hide "virtual" footprints, so the render copy
    marks every footprint `smd`, including those with no attr line at all, like the
    switches. Don't change the user's KiCad settings.
  - Run renders one at a time.
- **Firmware (QMK):** `tools/lib/qmk_matrix.py` (KiCad python: matrix + LED chain from a
  routed board) and `tools/lib/qmk_gen.py` (keyboard.json, config, keymap from that and the
  KLE key map) -> `<keyboard>/firmware/`, keymap `vial`; `.github/workflows/firmware.yml` builds
  it with Vial's QMK fork at a pinned commit in GitHub Actions (no fork of our own). See
  `hachigo74/CLAUDE.md`, Firmware.
- **`tools/lib/` scripts:**
  - `vrml.js`, `keycap.js`, `oled.js`: VRML model generators.
  - `stl2wrl.js`: STL → VRML conversion.
  - `kle_parse.js`: KLE parser that decodes legend positions.
- **Routing tools** (KiCad python + shapely: the venv `%LOCALAPPDATA%/kugo-kikit`, a venv on
  KiCad's Python made for KiKit once; it still holds shapely / numpy for these tools):
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

