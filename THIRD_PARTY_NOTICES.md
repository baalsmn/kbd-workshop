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

- `ergogen/footprints/c_0603.js`, `c_0805.js`, `r_0603.js`, `sod123.js`, `ts1187a.js`
  (converted from Capacitor_SMD / Resistor_SMD / Diode_SMD / button footprints)
- `kicad-libraries/3dmodels/C_0603_1608Metric.step`,
  `C_0805_2012Metric.step`, `R_0603_1608Metric.step`, `Diode_SOD-123.step`
- `kicad-libraries/Symbols/keyboard-workshop.kicad_sym`: the symbols derived from
  KiCad's Device (D, C, R), Switch (SW_Push_45deg), Connector (Conn_01x12_Socket,
  Conn_01x12_Pin, Conn_01x04_Socket) and power libraries

## 0xCB Helios — CERN-OHL-S-2.0

Source: https://github.com/0xCB-dev/0xCB-Helios, © 0xCB. Hardware licence:
CERN Open Hardware Licence Version 2 – Strongly Reciprocal (`LICENSES/CERN-OHL-S-2.0.txt`;
OSHWA certification DE000131).

- `ergogen/footprints/helios.js` (pad geometry from Helios_ACH.kicad_mod, 0xCB pinout)
- `kicad-libraries/3dmodels/Helios_0xCB_rev1.0.step`
  (exported with kicad-cli from 0xCB's KiCad design)

## ceoloide / ergogen-footprints — MIT

Source: https://github.com/ceoloide/ergogen-footprints, Copyright (c) 2023 Marco
Massarelli. Licence: MIT (`LICENSES/MIT-ergogen-footprints-ceoloide.txt`).

- `ergogen/footprints/sk6812mini_e.js`: pad layout of the reverse-mount SK6812MINI-E
  (from `led_sk6812mini-e`)

## Manufacturer 3D models — licence not stated

Kept in this private repository at the owner's request (2026-10-22), for the 3D view;
no licence was given with them, so they are not covered by the repository's
licences and must not be redistributed without the makers' permission.

- `kicad-libraries/3dmodels/vendor_Gateron_KS-2P02B01-02_socket.step`,
  `vendor_Gateron_KS-33_switch.step`, `vendor_Gateron_KS-57B210T_stabilizer.step`:
  Gateron's STEP models (https://www.gateron.com)
- `kicad-libraries/3dmodels/vendor_SK6812MINI-E.step`: SK6812MINI-E model (OPSCO part)
- `kicad-libraries/3dmodels/vendor_OLED_128x64.step`: 0.96" 128x64 OLED module model
- `kicad-libraries/3dmodels/vendor_keycap_MBK_1u.wrl`, `_1.25u.wrl`, `_2u.wrl`: converted
  (`tools/lib/stl2wrl.js`) from MBK keycap STL models supplied by the owner

## Not included

- Vendor datasheets (`datasheets/*.pdf`) belong to their manufacturers; see
  `datasheets/LINKS.md`.
- The originals of the vendor 3D models and the vendor footprints are kept out of git
  (`vendor/`, gitignored); the footprints are drawn from the datasheets, and models
  recreated from datasheet dimensions (`tools/lib/make_models.py`) remain available.
