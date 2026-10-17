# keyboard-workshop

Split-style ergonomic keyboards on one PCB, designed in [Ergogen](https://ergogen.xyz)
4.2.1, finished in KiCad 10, with 3D-printed cases.

| Folder | What |
|---|---|
| `kugo/` | kugo82 (current, 82 keys) and kugo80 (backup) |
| `hachigo74/` | hachigo74, 74 keys (kugo82 without the outer column) |
| `tools/` | build, case (STL), STEP and render scripts; Fusion script |
| `footprints/` | Ergogen footprints |
| `3dmodels/`, `keyboard.pretty/`, `keyboard.kicad_dru` | KiCad models, footprints, DRC rules |
| `datasheets/`, `drafts/` | part datasheets, sketches |

```bash
bash tools/build.sh kugo82     # Ergogen -> out/pcbs/kugo82.kicad_pcb + DRC
bash tools/case.sh kugo82      # -> kugo/case/*.stl
bash tools/step.sh kugo82      # -> kugo/case/step/*.step + case/fusion/kugo82_case.json
```

**Autodesk Fusion:** open the STEP files directly, or add `tools/fusion/KeyboardCase`
under Utilities → Scripts and Add-Ins and run it on a `case/fusion/*_case.json` to
get a parametric design (sketches + extrudes per part).

Needs: Node + `npm i -g ergogen@4.2.1`, KiCad 10, Python 3 (build123d installs itself
on first `step.sh`).
