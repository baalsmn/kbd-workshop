# kugo82

Mirrored two-half keyboard on a single PCB (each half rotated −15°), with a
Cirque trackpad and an OLED in the centre and an RP2040 (0xCB Helios) MCU.
Shared rules, build and tools: `../CLAUDE.md`. The hardware notes below are shared
with hachigo74 (its differences are in `../hachigo74/CLAUDE.md`).

- **`ergogen/kugo82.yaml`** (82 keys, 41 per half): the larger version of
  hachigo74, rebuilt from it on 2026-10-19. The old kugo82 / kugo80 designs were
  removed (they are in git history).
  - hachigo74 plus the outer column c1 (4 keys, r1–r4), with the original kugo82
    columns c1–c4: 1.25U keys c2_r3 (Shift), c2_r4 (Tab), c3_r2, c3_r5 (Esc) and
    c4_r1 (Ctrl).
  - Everything else is hachigo74's: thumb key c9_r1, angled 1.25U c7_r1, c7 without
    stagger, indicators anchored on c9_r2, centre, keycap-hugging outline
    (2.0 mm from every keycap), case-wall screws (anchored on c1 instead of c2).
  - LED chain: 2 indicators + 82 keys = 84; left c1_r1 takes LED_DATA, right c1_r1
    gives LED_END. Matrix column C1 (GP0) is used again.
  - Key-area screw c2_r2 back at [10.5, 8.5] (the c2 / c3 keys are the original ones).
  - Support crosses: hachigo74's set plus the original c1 ones (see Support).
- **KLE (`kle/`):** `kugo82_keys.json` (key name → label; c1–c4 from the original
  kugo82 layout, c5–c9 from hachigo74), `kugo82_exact.json` (exact export with
  angles), `kugo82_legends.json` (for `printview.py`).
- Outputs: `case/` (STL), `case/step/`, `case/fusion/kugo82_case.json`, `kicad/`
  (portable KiCad project, see its README). Checked 2026-10-19: DRC 5 silk_overlap
  only; every keycap 2.0 mm from the PCB edge; case-wall screws as on hachigo74;
  STEP volumes = STL within 1%; KiCad project ERC 0, schematic parity clean.

## Hardware (kugo82)

- **Switches:** Gateron KS-33 low profile on KS-2P02B01-02 hot-swap sockets, back
  side (`ergogen/footprints/ks33_hotswap.js`).
  - The 2U keys (c5_r1, both halves) use KS-57 plate-mounted stabilizers. The PCB has
    stabilizer cutouts; the wire runs between plate and PCB.
- **Diodes:** SOD-123, COL2ROW.
- **Key LEDs:** SK6812MINI-E (OPSCO SK6812MINI-E-012, LCSC/JLCPCB **C5149201**,
  datasheet `../datasheets/C5149201_SK6812MINI-E.pdf`), reverse-mounted on the back
  through PCB cutouts, with a 100 nF 0603 cap per LED.
  - **Pins (datasheet):** 1 GND, 2 DIN, 3 VDD, 4 DOUT; the chamfered corner is pin 1
    (GND). The footprint pads follow this (renumbered; positions were already right,
    checked against the datasheet's bottom view and KiCad's ReverseMount footprint).
  - 12 mA per colour (≈ 37 mA per LED at full white), VDD 3.7–5.5 V, data
    800 kbps, GRB order. Input high ≥ 0.65 × VDD = 3.25 V at 5 V, so a 3.3 V GPIO is
    not enough: GP25's 5 V level-shifted output is the right choice.
  - Custom DRC rule `../keyboard.kicad_dru`: 0.2 mm LED pad-to-cutout clearance, which is
    JLCPCB's routed-edge minimum.
- **MCU:** 0xCB Helios (RP2040), on the back, upside down (component side facing the
  case floor), USB-C at the north edge.
  - Footprint `ergogen/footprints/helios.js` (castellated). Model `kicad-libraries/3dmodels/Helios_0xCB_rev1.0.step`.
- **Matrix:** 10 rows × 9 columns, COL2ROW. Left half R1–R5, right half R6–R10;
  columns are shared by both halves.
  - **Rows:** R1 GP29, R2 GP28, R3 GP27, R4 GP26, R5 GP22, R6 GP4, R7 GP5, R8 GP6,
    R9 GP7, R10 GP8.
  - **Columns:** C1 GP0, C2 GP1, C3 GP10, C4 GP11, C5 GP16, C6 GP9, C7 GP21, C8 GP23,
    C9 GP20.
  - **Other pins:** I2C SDA GP2, SCL GP3 (OLED 0x3C + Cirque 0x2A share the bus);
    CIRQUE_DR GP12. Spare: GP13, GP14, GP15.
- **RGB:** GP25 (the Helios' 5 V level-shifted output) → 330 Ω (R1, back) → chain of
  **84 LEDs**.
  - LED 0 = function-lock indicator (right, green).
  - LED 1 = layout-layer indicator (left).
  - LEDs 2–83 = keys, snake order: left c1…c9, then right c9…c1. The C9 columns
    run r1…r5 on the left, then r5…r1 on the right.
  - Caps Lock is shown on the Caps Lock key's own LED.
  - There's a 10 µF 0805 bulk cap at the Helios 5 V pin.
  - Power: at full white 84 LEDs draw about 3.1 A (hachigo74's 76: 2.8 A), from the
    datasheet's 12 mA per colour; USB gives 0.5–0.9 A. Cap the firmware brightness
    at about 15–25% (0.5 A port: ~15%, 0.9 A: ~25%, leaving room for the rest).
- **Indicators:** anchored on c9_r2 at [0.125sp + 19.5, −sp] (where they were next
  to c9_r1 before the thumb key moved; left = layer LED 1, right = fn LED 0). 0603 caps 4 mm below them. 3 mm light holes in the plate
  (outside the centre cover).
- **OLED:** 0.96" SSD1306 128×64 I2C module, rotated 180°, on bare header pins
  ~1.2 mm above the PCB, header at y 23.5, VDD = 3V3.
  - Plate cutout / cover pocket `oled` at (0, 35.7), bottom edge at y 21.7, 1.5 mm
    above the trackpad ring. The screen window `oled_window` is at (0, 36.35).
  - The 2 bottom corner holes take bottom-up screws (`oled_screw` at (±11.176,
    24.135)). Each runs from the floor through a post, the PCB, a 5.5 mm spacer
    (`oled_spacers`) and the OLED board into an insert in a boss under the centre
    cover (see Support).
  - The 2 top holes (±11.176, 47.25) stay unused: the Helios castellation pads are
    0.7 mm away, and a stud's Ø5 base needs 2.8 mm.
- **Trackpad:** Cirque TM040040 in I2C mode (R1 removed on the module), centre at
  (0, −2). It **lies directly on the switch plate**, level, with no pocket in the
  plate (user's design). **The pad is 5 mm thick without the connector (user
  measured)**: underside z 12.6, top z 17.6. That's 2.1 mm above the centre cover
  top and ~2.4 mm below the keycap tops.
  - Parts stay inside Ø36.01 (2 mm parts-free edge ring). The datasheet's 0.99 mm
    board + overlay and 5.15 mm totals don't match the user's part; use the
    measured values. **The user measured the connector sticking out 2.5 mm
    below the pad**, so it ends at the PCB top (z 10.1), exactly the plate 1.2 + gap
    1.3 mm. The datasheet's 4.1 mm connector height does not apply.
  - **Plate:** opening `tp_plate_opening` (r 18.1) under the parts zone. The pad
    rests on its parts-free rim around it.
  - **PCB:** cutout `tp_cable_slot` (12 × 5, r 1, at (0, −17.4)). It's big enough for
    the connector body to fit comfortably (12-pin 0.5 mm vertical, ~10 × 3 mm; check
    against the real part), and the FFC goes straight down through it.
  - The pad is cut flat top and bottom (39.40 across, 6.90 mm flats at r 19.70). The
    user calls the south flat the "south notch".
  - **"Centerplate"** = the user's word for the centre cover (around the OLED and
    the trackpad).
  - **Anti-rotation:** a peg on the centre cover (`tp_cover_peg`, 5 × 3.4 mm,
    z 12.6–15.5 up to the cover top, at (0, −23.45)). It reaches from the cover
    opening edge into the pad's south flat.
  - **Snap ring** `trackpad_ring`, a separate printed part (print top down). It
    stands on the plate around the pad:
    - wall r 22.2 outside, round pocket r 20.2 (`tp_pad_pocket`) with a notch for the
      cover peg (`tp_key_notch`, through the full wall height); z 12.6–17.7;
    - 0.8 mm lip at z 17.7–18.5, inner r 19.3 (outside the r 19.0 sensor area);
    - **2 claws** (east / west), 8 mm wide, **flush with the ring wall**, nothing
      sticking out:
      - an 8 mm arc of the wall's outer 1 mm is cut free by two 0.5 mm slits
        (z 12.6–16.0, `tp_claw_slit`); the inner wall behind it is relieved
        (`tp_claw_relief`), so it flexes inward;
      - below the ring it continues (`tp_claw_arm`, z 11.9–12.6) with a hook
        reaching 0.5 mm past the cover opening edge (r 22.5 → 23.0, `tp_claw_hook`,
        z 11.9–12.55) that catches under the cover bottom;
      - the plate has a cutout under each claw for the hook (`tp_claw_plate_cut`);
      - the claw shapes are arc segments (ring shapes cut to the claw zone), so
        nothing bulges past the round edge.
  - The centre cover opening `cirque_flush` is r 22.5 around the ring, with no slots.
    The cover's circle around the trackpad is r 25.
  - Molex 505278-1270 on the back at (0, 5.5), facing south. The cable drops 1.6 mm
    from the connector (z 10.1) to the PCB bottom, leaving a flat run of ~19.3 mm for
    the 30 mm cable.
  - Trackpad pin n = Molex pin n. **Pin 1 verified** from the user's photos of the
    real module (`drafts/cirque back.jpg`, `cirque connector close.jpg`): the
    trackpad's J1 pin 1 is at the east end (+x, top view), and so is Molex J1 pin 1
    (pad x +2.75 in the board); the cable runs straight north, so the order holds.
    Module test pads match the pinout: 4 DR, 9 SCL, 10 SDA, 11 GND, 12 VDD.
  - Molex 505278-1270 at JLCPCB: **C47149418** (Extended, ~$1.16; only 4 in stock
    and listed as "Wave Soldering" when checked on 2026-10-17). Backup in the same
    series: 505278-1233, C3169674 (pre-order, SMT); check the suffix difference first.
  - Cable: **12-pin 0.5 mm, opposite-side (Type D), 30 mm**. The trackpad's
    connector has its contacts on the outer wall.
  - **R1 on the module must be removed for I2C** (silkscreen table: SPI 470K,
    I2C DNP). In the user's photo R1 still looked fitted.
- **Reset:** there's no separate button. A 1.3 mm pin channel through the case floor
  plus a 1.8 mm boss (top z 4.8) sits under the Helios' own reset switch at
  (−4.885, 44.10); double-tap it with a SIM tool or paperclip for the UF2 bootloader.
- **Centre frame** (used for all centre parts): the midpoint of the c9_r2 pair,
  unrotated, y up.
- **Support:**
  - **Screws and posts.** The rule: every post keeps ≥ 0.2 mm clear of back-side
    pads, courtyards and cutouts, on both halves. Check it after any move; the
    marker circles must show no silk_over_copper.
    - **All screws go into M2 heat-set inserts** (3.0 mm hole). Posts and bosses are
      5.5 mm (the user tested 5 mm); 5.5 is used where it fits with ≥ 0.2 mm to spare.
    - **Key-area screws, top-down:** plate → 5.5 mm spacer (`spacer_disc_key`) → PCB
      → insert in the 5.5 mm post under the PCB (`insert_post`, `insert_hole`).
    - **Centre-cover screws, bottom-up** (`cover_screw` = the 2 OLED screws + the 2
      south of the trackpad), so **no screw shows on the centre cover**:
      - floor counterbore Ø4.4 × 1.6 (`cover_counterbore`), then a 5.5 mm post with
        a 2.4 mm clearance hole, then the PCB;
      - south screws: a 5.5 mm boss under the cover (`cover_boss_south`) reaches
        down through a Ø6 plate hole to the PCB top. It replaces the lid spacer, and
        its insert sits at z 10.1–13.6 with 1.9 mm of solid cover above;
      - OLED screws: a 5.5 mm spacer (separate `oled_spacers` part, PCB top → OLED
        board), the OLED south hole, then a **Ø5** boss under the cover standing on
        the OLED board (`cover_boss_oled`, z 12.5–13.95; 5.5 would touch the glass
        edge). Its insert hole is only **2.7 mm deep** (0.3 mm top skin), so use
        **short M2 inserts** there.
    - Screws, 8 in total:
      - 2 cover screws south of the trackpad (±11, −29.5), in `pcb_mounting_std`;
      - 2 OLED screws (`oled_screw`);
      - 2 key-area screws per half (`c9r5_screw`, the name is historical), chosen
        by the user, at switch corner crossings:
        - c2_r2 [10.5, 8.5] (north-east corner, C2/C3 at R2/R3);
        - c5_r3 [9.0, −10.5] (south-east corner, C5/C6 at R2/R3; the west
          corners have only 1.1 mm room).
      - Nothing else under the keys, no screws and no studs: the case-wall screws
        hold the lid and the tub together all around.
    - Case-wall screws (`edge_mounting`, 7 per half) go through the plate into
      3.0 mm insert holes in the 8 mm wall (`edge_insert`).
  - Centre cover (`cirque_cover` = `center_cover_raw` filleted r3, from the user's
    draft): a 33 mm strip parallel to the OLED widening into a circle r25 around the
    trackpad.
    - The strip runs y −33.1…52.1: 2.4 mm past the south screw holes, and 2.4 mm
      above the OLED cutout top (49.7). That's the same 2.4 mm wall as at the sides.
    - It's held by the 2 OLED screws (±11.176, 24.135) and the 2 screws south of the
      trackpad (±11, −29.5).
  - No screwless studs any more. The user removed all of them from the key area.
  - **Support crosses** (`cross_lower`, `cross_upper`; no PCB holes needed): 2 mm
    walls along the key gaps at a switch corner crossing.
    - Lower cross: floor → PCB bottom, in the tubs. Upper cross: plate → PCB top,
      in the lids. Together they back the PCB against pressure from above.
    - kugo82 positions (all mirrored): upper right of c1_r1, c1_r3 (c1/c2) and
      c3_r4; c4_r1 at its 1.25U corner (`c4_r1:0.625:0.5`); upper left of c7_r4
      (c6/c7); lower left of c8_r2 (c7/c8 at the r1/r2 gap). Command:
      `crosses.py ... "c1_r1,c1_r3,c4_r1:0.625:0.5,c3_r4,c7_r4:-0.5:0.5,c8_r2:-0.5:-0.5"`.
      hachigo74 uses the same list without the c1 crosses (its c4_r1 is 1U: plain corner).
    - Arms are **5 mm** (user's choice). An arm stops 0.3 mm before the first
      obstacle if that comes sooner, the same on both halves. Arms under 2 mm are
      dropped, which makes half crosses.
      - Lower obstacles: back pads, socket bodies (x −8.6…6.8, 2.3…8.1 south in the
        footprint frame, measured from the STEP), diodes, LEDs, caps, cutouts.
      - Upper obstacles: switch bodies (14.1 mm), stabilizer housings, front pads.
    - Result (kugo82): every arm is 5 mm except the c4_r1 east arms (2.5 mm, the
      c5_r1 stabilizer) and the c8_r2 south arms (lower 4.0, upper 3.75). The lower
      crosses are T-shapes (E, W, S: the north arm is blocked by the next key's
      socket body); the upper crosses are full (c4_r1 too).
    - Generated by `tools/lib/crosses.py` from the built board. Re-run it and paste
      the result if keys or parts move. It reads the mirror line from
      `out/points/points.yaml`, so it works for any design. The built-in list is
      kugo82's; pass another design's list as the 4th argument
      (`key[:fx:fy],...`, default corner 0.5:0.5 = upper right).
  - **Silkscreen markers (always keep them):** every case support that touches the
    PCB is drawn on the silkscreen. Back (B.SilkS, `support_marks_back`): all screw
    posts and the lower crosses. Front (F.SilkS, `support_marks_front`): OLED
    spacers, the upper crosses and the
    trackpad outline (`tp_outline`: 40 mm round with the two flats). They're
    built from the same outlines as the case, so they always match. Add every new
    support to these.
  - Case-wall holes in `edge_mounting`.

## Case stack-up (z in mm, case coordinates)

| Layer | z (mm) |
|---|---|
| Floor | 0–3 |
| Under-PCB clearance (Helios 1.6 + ~3.3 USB-C hang below) | 3–8.5 (5.5) |
| PCB | 8.5–10.1 |
| Gap to plate | 10.1–11.4 |
| Plate | 11.4–12.6 |
| Centre cover, low layer (OLED pocket) | 12.6–13.95 |
| Centre cover, top layer | 13.95–15.5 |
| Trackpad connector (2.5 mm below the pad, user measured) | 10.1–12.6 |
| Trackpad (on the plate, 5 mm) | 12.6–17.6 |
| Trackpad snap ring (wall / lip) | 12.6–17.7 / 17.7–18.5 |
| Snap ring claw hooks (under the cover) | 11.9–12.55 |

- **Parts:**
  - `tub_left` / `tub_right`: floor (with counterbores for the cover screws), walls, posts, lower crosses, reset boss, USB opening
    13 mm wide at z 1.5–9.
  - `lid_left` / `lid_right`: plate, upper spacers and upper crosses. Print plate-side
    down.
  - `center_cover`: includes the trackpad anti-rotation peg and the 4 screw bosses
    with blind insert holes (no holes on the top).
  - `trackpad_ring`: the trackpad snap ring. Its 2 claws hook under the centre cover. Print top down.
  - `oled_spacers`: 2 × 1.2 mm, Ø5.5 spacers for the OLED screws (PCB top to module).
- **Printing:** STLs keep case coordinates, so drop to bed and centre them in the
  slicer.

## Open / next

- **QMK firmware.** Still needed from the user:
  1. Layer list and purposes, which layer is function lock, and the layout-LED colour
     per layout layer.
  2. OS, and whether the host uses the Hungarian layout (`keymap_hungarian.h`,
     `HU_*` keycodes).
  3. Build path: a local QMK toolchain, or GitHub Actions.
  4. Later: Cirque features, OLED content, RGB defaults, VIA/Vial, home-row mods.
- **Routing in KiCad.** A Freerouting test was inconclusive: v2.5 mis-rotates
  back-side pad shapes at 15°, and v1.9 crashed. Route by hand, starting with the
  Helios fan-out and the centre area.
- **Assembly panel:** `kicad/kugo82_panel.kicad_pcb` (`tools/panel.sh kugo82`,
  recipe `panel.json`, 428.7 × 159.2 mm). Re-run it after routing.
