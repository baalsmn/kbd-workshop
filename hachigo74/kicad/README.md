# hachigo74 KiCad project

Open `hachigo74.kicad_pro` in KiCad 10. The folder is self-contained and portable:
every symbol, footprint and 3D model path is `${KIPRJMOD}/libraries/...`.

| File | What |
|---|---|
| `hachigo74.kicad_pcb` | the Ergogen board (not routed yet), footprints linked to `Keyboard:<name>` and to their schematic symbols |
| `hachigo74.kicad_sch` | schematic generated from the board's netlist (net labels on every pin) |
| `hachigo74.kicad_dru` | custom DRC rule (0.2 mm LED pad-to-cutout, JLCPCB routed-edge minimum) |
| `libraries/` | project copy of `../../kicad libraries` (symbols `keyboard-workshop`, footprints `Keyboard`, 3D models) |
| `sym-lib-table`, `fp-lib-table` | project library tables |

Checked when generated: ERC 0 violations; DRC with schematic parity 0 issues (plus
the expected 2 silkscreen overlaps and 499 unrouted connections); the schematic
netlist matches the Ergogen board pad for pad (808 pads). Unused pins (GP0 = C1,
GP13-15, D+/D-, RST, the last LED's DOUT) carry no-connect flags.

This project is now the master for routing and schematic edits. Regenerating it
(`tools/lib/kicad_project.py ... --force`) overwrites the PCB and schematic.
