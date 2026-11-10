# Datasheets and sources

The manufacturers' datasheets are not included in this repository (they are not
covered by its licences). Download them from the sources below; the file names
are the ones the project used.

| Part | Document (file here) | Source |
|---|---|---|
| Gateron KS-33 low-profile 2.0 switch (Brown) | product specification and drawing, `GATERONKS-33LowProfile20BrownSwitchBlackBottomHousingKS-33E10B055NN-Y24.pdf` | Gateron, KS-33 product pages: https://www.gateron.com/products/gateron-ks-33-low-profile-switch-set |
| Gateron KS-2P02B01-02 low-profile hot-swap socket 2.0 | product specification and drawing, `GATERONUpgradeLowProfileswitchHot-swapPCB20SocketKS-2P02B01-02.pdf` | Gateron (https://www.gateron.com), via its low-profile product pages / distributors |
| Gateron KS-57B210T low-profile plate-mounted 2U stabilizer | product specification and drawing, `GATERONLowProfilePlateMountedStabilizer2U-KS-57B210T.pdf` | Gateron (https://www.gateron.com), via its low-profile product pages / distributors |
| OPSCO SK6812MINI-E (key / indicator LEDs, LCSC C5149201) | datasheet, `C5149201_SK6812MINI-E.pdf` | https://www.lcsc.com/datasheet/C5149201.pdf, JLCPCB part page https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK6812MINIE/C5149201 |
| OPSCO SK6803MINI-E (LCSC C5242955; related part, same package, not used) | datasheet, `C5242955.pdf` | https://www.lcsc.com/datasheet/C5242955.pdf |
| Cirque GlidePoint TM040040 circle trackpad | specification v1.2, `TM040040_SPI-I2C-PINNTrackpad_SPEC1-2.pdf` | Cirque: https://cirque.com/glidepoint-circle-trackpads (developer resources: https://www.cirque.com/gen4-dev-resources) |
| Molex 505278-1270 FFC connector, 0.5 mm, 12 pin (JLCPCB C47149418) | sales drawing 5052781004 (5052781270_sd.pdf), `Molex_505278-1270_sales_drawing.pdf` | https://www.molex.com/en-us/products/part-detail/5052781270, JLCPCB https://jlcpcb.com/partdetail/MOLEX-505278_1270/C47149418 |
| 0xCB Helios (RP2040 controller) | design files (CERN-OHL-S-2.0), `helios website.txt` | https://github.com/0xCB-dev/0xCB-Helios |

The simplified 3D models in `kicad-libraries/3dmodels/` (switch, socket, stabilizer, LED, Molex
connector, trackpad) are drawn from these documents by `tools/lib/make_models.py`.
