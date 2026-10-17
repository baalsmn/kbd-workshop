# kicad project

Self-contained KiCad 10 project library: everything refers to files in this folder
(`${KIPRJMOD}`), so the folder can be copied or zipped as one package.

| Folder / file | What |
|---|---|
| `Symbols/Keyboard.kicad_sym` | key switch (SW_Push_45deg), D, C, R, SK6812MINI-E, Molex 505278-1270, Cirque TM040040, OLED, power (GND, VCC, +3V3, +5V) |
| `Symbols/helios.kicad_sym` | 0xCB Helios (pin numbers = footprint pads, 0xCB numbering) |
| `Footprints/Keyboard.pretty` | footprints exactly as on the board (KS-33 hot-swap 1U / 1.25U / 2U + KS-57, SOD-123, SK6812MINI-E reverse, 0603/0805, Helios, Molex, OLED, trackpad 3D, logo) |
| `3dmodels/` | every 3D model the footprints use |
| `sym-lib-table`, `fp-lib-table` | project library tables (libraries `Keyboard`, `Helios`) |

Each symbol's Footprint field points at `Keyboard:<footprint>`, and each footprint's
3D model at `${KIPRJMOD}/3dmodels/`. Symbol pin numbers match the footprint pads
(checked: no missing or extra pins on any pair).

Pinouts:
- **Trackpad / Molex** (pin n = pin n, 12-pin 0.5 mm Type D cable): 1 SCK, 2 SO,
  3 SS, 4 DR, 5 SI, 6 B2, 7 B3, 8 B1, 9 SCL, 10 SDA, 11 GND, 12 VDD; Molex 13/14 =
  mounting tabs (GND). The trackpad symbol is not on the board (cabled module).
- **OLED**: 1 GND, 2 VCC (3V3), 3 SCL, 4 SDA.
- **SK6812MINI-E**: 1 VDD, 2 DOUT, 3 VSS, 4 DIN (datasheet numbering; KiCad's
  built-in symbol uses the 5050 SK6812 numbers, so ours is renumbered).
- **Helios**: D+ / D- on pads 32 / 33 are assigned by position and unverified (not
  used on this board).

Regenerate (after `tools/build.sh <name>` for each design):

```bash
"C:/Users/balin/AppData/Local/Programs/KiCad/10.0/bin/python.exe" tools/lib/kicad_footprints.py out/pcbs/<name>.kicad_pcb "kicad project" --force
python tools/lib/kicad_symbols.py "kicad project"
```

Still to come: project file, schematic, PCB and the `.kicad_dru` rules.
