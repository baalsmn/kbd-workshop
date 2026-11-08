# keyboard-workshop

Split-style ergonomic keyboards on a single PCB, designed in [Ergogen](https://ergogen.xyz)
4.2.1, finished in KiCad 10 and housed in 3D-printed cases. Developed with the help of
Anthropic's Claude Code.

## Why

Most open-source ergonomic keyboards are built around the English alphabet and keep
the key count low. Languages with a larger alphabet run out of keys quickly: Hungarian
alone needs nine accented vowels (á é í ó ö ő ú ü ű) on top of the Latin letters, and
these end up on layers or awkward key combinations.

This project aims for a keyboard with enough dedicated keys for such languages, while
keeping a split, angled, ergonomic layout. Each design is a mirrored two-half layout on
one PCB, with a Cirque trackpad and an OLED in the centre, an RP2040 controller (0xCB
Helios), low-profile Gateron KS-33 hot-swap switches and per-key RGB.

The layouts are designed primarily for Hungarian. The extra keys suit many other
languages too, for example Czech, Slovak, Polish, Turkish, Icelandic, the Nordic
languages and Japanese (a JIS layout with the kana switching keys is included for
hachigo74).

## Contents

| Folder | What |
|---|---|
| `kugo82/` | kugo82, 82 keys: hachigo74 plus an outer column and 1.25U modifiers |
| `hachigo74/` | hachigo74, 74 keys (kugo82 without the outer column); `kicad/` = its KiCad project |
| `tools/` | build, case (STL), STEP and render scripts; Fusion script; KiCad library / project scripts |
| `ergogen/` | Ergogen inputs: the design yamls (`kugo82`, `hachigo74`) and `footprints/` |
| `kicad-libraries/` | KiCad libraries: symbols (`keyboard-workshop`), footprints (`Keyboard`), and the 3D models (the one place they live: Ergogen builds and renders use them too) |
| `keyboard.kicad_dru` | DRC rules for every design |
| `datasheets/`, `drafts/` | part datasheets, sketches |

```bash
bash tools/build.sh kugo82     # Ergogen -> out/pcbs/kugo82.kicad_pcb + DRC
bash tools/case.sh kugo82      # -> kugo82/case/*.stl
bash tools/step.sh kugo82      # -> kugo82/case/step/*.step + case/fusion/kugo82_case.json
```

**Autodesk Fusion:** open the STEP files directly, or add `tools/fusion/KeyboardCase`
under Utilities → Scripts and Add-Ins and run it on a `case/fusion/*_case.json` to
get a parametric design (sketches + extrudes per part).

**KiCad project (hachigo74):** open `hachigo74/kicad/hachigo74.kicad_pro`. It is
portable (its own copy of the libraries in `libraries/`, every path
`${KIPRJMOD}`-relative), with the PCB and a schematic generated from it (ERC clean,
schematic parity clean). It is the master for routing from now on. The scripts that
made it, run with KiCad's Python after `tools/build.sh hachigo74`:

```bash
python tools/lib/kicad_footprints.py out/pcbs/hachigo74.kicad_pcb kicad-libraries --force   # footprints + 3D models
python tools/lib/kicad_symbols.py kicad-libraries                                           # symbol library (plain Python)
python tools/lib/kicad_project.py out/pcbs/hachigo74.kicad_pcb kicad-libraries hachigo74/kicad hachigo74   # project (--force to overwrite)
```

Needs: Node + `npm i -g ergogen@4.2.1`, KiCad 10, Python 3 (build123d installs itself
on first `step.sh`).

## Cost

First hachigo74 order (JLCPCB, 2026-10-23): 5 PCBs, 4 of them assembled by JLC (LEDs,
diodes, capacitors, resistor, FFC connector), delivered to Hungary by DHL Express with
duties paid: **EUR 221.84 in total**, about EUR 55 per assembled board. Not included:
the hand-soldered parts (hot-swap sockets, Helios, OLED), switches, keycaps, trackpad
and case. Breakdown: [ordering/README.md](ordering/README.md#orders).

All parts of one hachigo74 (PCB share, Helios, OLED, switches, sockets, stabilizers, trackpad, cable,
screws, filament): about EUR 131 (133 with the tilt wedge), without the shops' shipping, the wedge magnets and keycaps: [ordering/README.md](ordering/README.md#hachigo74-all-parts-of-one-keyboard-as-built-2026-11).
