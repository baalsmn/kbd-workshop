# Third-party notices

The repository's own work is licensed as described in [LICENSE](LICENSE)
(hardware: CERN-OHL-S-2.0, software: GPL-3.0-or-later). The files below come
from, or are derived from, other projects and keep their own licences. Licence
texts are in [LICENSES/](LICENSES/).

## KiCad libraries — CC-BY-SA-4.0 (with the KiCad library exception)

Source: KiCad 10 symbol, footprint and 3D model libraries, https://www.kicad.org/libraries/license/
© the KiCad library contributors. Licence: Creative Commons Attribution-ShareAlike
4.0 International (`LICENSES/CC-BY-SA-4.0.txt`), with KiCad's exception: designs
made with the libraries, and files generated from them, are not bound by it
(no share-alike, no attribution required in the design). Library files that are
redistributed, as here, stay under CC-BY-SA-4.0 with this attribution.

- `footprints/c_0603.js`, `c_0805.js`, `r_0603.js`, `sod123.js`, `ts1187a.js`
  (converted from Capacitor_SMD / Resistor_SMD / Diode_SMD / button footprints)
- `3dmodels/Diode_SOD-123.step`; `kicad libraries/3dmodels/C_0603_1608Metric.step`,
  `C_0805_2012Metric.step`, `R_0603_1608Metric.step`, `Diode_SOD-123.step`
- `kicad libraries/Symbols/keyboard-workshop.kicad_sym`: the symbols derived from
  KiCad's Device (D, C, R), Switch (SW_Push_45deg), Connector (Conn_01x12_Socket,
  Conn_01x12_Pin, Conn_01x04_Socket) and power libraries

## 0xCB Helios — CERN-OHL-S-2.0

Source: https://github.com/0xCB-dev/0xCB-Helios, © 0xCB. Hardware licence:
CERN Open Hardware Licence Version 2 – Strongly Reciprocal (`LICENSES/CERN-OHL-S-2.0.txt`;
OSHWA certification DE000131).

- `keyboard.pretty/Helios_*.kicad_mod` (0xCB's Helios footprints)
- `footprints/helios.js` (pad geometry from Helios_ACH.kicad_mod, 0xCB pinout)
- `3dmodels/Helios_0xCB_rev1.0.step` and its copy in `kicad libraries/3dmodels/`
  (exported with kicad-cli from 0xCB's KiCad design)

## ceoloide / ergogen-footprints — MIT

Source: https://github.com/ceoloide/ergogen-footprints, Copyright (c) 2023 Marco
Massarelli. Licence: MIT (`LICENSES/MIT-ergogen-footprints-ceoloide.txt`).

- `footprints/sk6812mini_e.js`: pad layout of the reverse-mount SK6812MINI-E
  (from `led_sk6812mini-e`)

## Not included

- Vendor datasheets (`datasheets/*.pdf`) belong to their manufacturers; see
  `datasheets/LINKS.md`.
- Vendor 3D models and vendor footprints of unknown licence are kept out of git
  (`3dmodels/vendor/`, `footprints/vendor/`, gitignored); the repository uses
  models recreated from datasheet dimensions (`tools/lib/make_models.py`) and
  footprints drawn from the datasheets instead.
