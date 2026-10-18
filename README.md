# keyboard-workshop

Split-style ergonomic keyboards on one PCB, designed in [Ergogen](https://ergogen.xyz)
4.2.1, finished in KiCad 10, with 3D-printed cases.

| Folder | What |
|---|---|
| `kugo/` | kugo82 (current, 82 keys) and kugo80 (backup) |
| `hachigo74/` | hachigo74, 74 keys (kugo82 without the outer column); `kicad/` = its KiCad project |
| `tools/` | build, case (STL), STEP and render scripts; Fusion script; KiCad library / project scripts |
| `ergogen/` | Ergogen inputs: the design yamls (`kugo82`, `kugo80`, `hachigo74`) and `footprints/` |
| `kicad-libraries/` | KiCad libraries: symbols (`keyboard-workshop`), footprints (`Keyboard`), and the 3D models (the one place they live: Ergogen builds and renders use them too) |
| `keyboard.kicad_dru` | DRC rules for every design |
| `datasheets/`, `drafts/` | part datasheets, sketches |

```bash
bash tools/build.sh kugo82     # Ergogen -> out/pcbs/kugo82.kicad_pcb + DRC
bash tools/case.sh kugo82      # -> kugo/case/*.stl
bash tools/step.sh kugo82      # -> kugo/case/step/*.step + case/fusion/kugo82_case.json
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
