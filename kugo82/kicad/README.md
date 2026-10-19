# kugo82 KiCad project

Open `kugo82.kicad_pro` in KiCad 10. The folder is self-contained and portable:
every symbol, footprint and 3D model path is `${KIPRJMOD}/libraries/...`.

| File | What |
|---|---|
| `kugo82.kicad_pcb` | the Ergogen board (not routed yet), footprints linked to `Keyboard:<name>` and to their schematic symbols |
| `kugo82.kicad_sch` | schematic generated from the board's netlist (net labels on every pin) |
| `kugo82.kicad_dru` | custom DRC rule (0.2 mm LED pad-to-cutout, JLCPCB routed-edge minimum) |
| `libraries/` | project copy of `../../kicad-libraries` (symbols `keyboard-workshop`, footprints `Keyboard`, 3D models) |
| `sym-lib-table`, `fp-lib-table` | project library tables |

Checked when generated (2026-10-19): ERC 0 violations; DRC with schematic parity:
only the expected 5 silkscreen overlaps and 499 unrouted connections; all 504 3D
model links resolve. 341 symbols: 82 switches, 82 diodes, 84 LEDs, 85 capacitors,
the resistor, Molex connector, OLED and Helios. Every assembled part carries its
LCSC number; the Helios, the OLED and the trackpad model are excluded from the
BOM and position files. Unused pins (GP13-15, D+/D-, RST, the last LED's DOUT)
carry no-connect flags.

This project is now the master for routing and schematic edits. Regenerating it
(`tools/lib/kicad_project.py ... --force`) overwrites the PCB and schematic.
