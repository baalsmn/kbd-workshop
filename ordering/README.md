# Ordering (JLCPCB / LCSC)

Shared by hachigo74 and kugo82. Stock and prices were checked on jlcpcb.com and
lcsc.com on 2026-10-21. Check them again before ordering.

## Pre-order on JLCPCB (Parts Manager, before the assembly order)

| Part | LCSC | Status (2026-10-21) | Notes |
|---|---|---|---|
| Gateron KS-2P02B01-02 hot-swap socket | C18212911 | **0 in stock**, pre-order only, est. about $0.04 each (was $0.02 on 2026-10-19) | "Standard" PCBA only. 74 per hachigo74, 82 per kugo82. Minimum pre-order was 441 pieces on 2026-10-18. |
| Molex 505278-1270 FFC connector (trackpad) | C47149418 | **4 in stock**, about $1.16 | Pre-order when assembling more than 4 boards. Listed as "Wave Soldering" although it is SMD: confirm JLC places it on the back side. |

Stocked on 2026-10-19, no pre-order needed: SK6812MINI-E LED (C5149201, ~155k in stock),
100 nF 0603 (C14663), 10 µF 0805 (C15850), 330 Ω 0603 (C23138) and 1N4148W SOD-123
(C81598), all basic parts.

Not assembled by JLC: the 0xCB Helios, the OLED module (hand-mounted on header pins) and
the Cirque trackpad. On hachigo74 also the hot-swap sockets (user's decision, 2026-10-21:
JLC could not supply them): the switch footprints are excluded from the BOM and position
files in the KiCad project, so solder the 74 sockets by hand. kugo82 still lists them
for assembly.

## Hot-swap sockets, bought separately (hachigo74: 74, plus spares)

**Gateron part no. KS-2P02B01-02**: the low-profile hot-swap socket for KS-27 / KS-33
switches (3-pin, the two 3.0 mm pin holes 7.00 mm apart, as in our footprint).

- From Gateron directly: [gateron.com](https://www.gateron.com/products/gateron-hot-swap-pcb-socket)
  lists "GATERON Low Profile switch Hot-swap" and "GATERON Upgrade Low Profile Switch
  Hot-swap PCB 2.0 Socket". The store pages don't show part numbers (checked
  2026-10-21), so confirm with Gateron that the one you order is KS-2P02B01-02, not the
  MX-style "Hot-swap PCB 2.0 Socket".
- Other sources: LCSC C18212911 (same part, pre-order), or resellers such as
  [beekeeb](https://shop.beekeeb.com/products/gateron-low-profile-hotswap-socket-compatible-with-gateron-ks-27-switches-5pcs)
  (packs of 5).

## Trackpad flat cable (FFC), from LCSC

Needed: 12 pin, 0.5 mm pitch, contacts on opposite ends ("Reverse", type B / D), 30 mm,
0.3 mm thick. The Molex 505278 drawing recommends a finished FFC thickness of
0.3 ± 0.05 mm.

| LCSC | Part | Stock (2026-10-21) | Price |
|---|---|---|---|
| **C54950533** | GUOCONN 0.5\*12P\*30\*B\*3/3\*5/5, Reverse, 3 cm | 925 | about $0.07 each from 5 |
| C5248013 | JUSHUO JS05B-12P-030-3-4, Reverse, 3 cm | 325 | about $0.10 each from 5 |

Don't use the "Same Side" (A-type) cables listed next to them. Order a few spares.

**From a European distributor instead** (user, 2026-11-07: the cable costs cents, but LCSC's shipping to Hungary
is about EUR 15): **GCT 05-12-D-0030-A-4-06-4-T**, 12 positions, 0.5 mm, 30 mm, contacts on opposite sides
("Top on One Side, Bottom on Other" = reverse; the `-A-` variant 05-12-A-0030-... is same-side, don't use it).
DigiKey had 203 in stock (2026-11-07, about EUR 0.90 each). GCT is also sold by Mouser and TME: add it to the order
the Cirque trackpad comes in (Mouser), so it ships for free with it. Check the thickness (0.3 mm) on the datasheet.

## Shipping the cable with the boards

- JLCPCB's parts library won't ship it. Parts bought there are "stored in your
  JLCPCB parts library for future PCBA orders only, and cannot be shipped separately",
  and a cable isn't soldered onto the board.
- Buy the cable on LCSC and combine the shipment with the JLCPCB order:
  - **New LCSC order:** at LCSC checkout, select your JLCPCB order to combine with.
  - **LCSC order already placed:** email support@lcsc.com before it ships, with both
    order numbers, and they merge them.
  - **Requirements:** both orders need the same currency and customer account. The
    JLCPCB order must use LCSC's forwarding address (see their FAQ before ordering).
    Once combined, the orders can't be split, and shipping is recalculated.
  - A 2019 forum thread says combining was stopped back then; the current LCSC FAQ says
    it is supported. Ask LCSC support if it matters.
- Fallback: a separate LCSC order (a small, cheap parcel).

## Board order

- Route the design board (`<keyboard>/kicad/<keyboard>.kicad_pcb`), refill the pours (B)
  and run the Fabrication Toolkit on it.
- At JLC choose "Edge Rails: Added by JLCPCB" (or "Panel by JLCPCB"): JLC builds the panel,
  which keeps the board under the 650 cm² "Large Size" fee (our own panel, removed on
  2026-10-23, was over it). Standard PCBA, assembly on the bottom side. Tick "Confirm
  Production file" to check their tabs and V-cuts. File any tab nubs flush (the case has
  no clearance around the board edge).
- Marking: since May 2026 JLC prints no order number, and by default nothing at all
  ([how to mark on PCB](https://jlcpcb.com/help/article/how-to-mark-on-pcb)). Don't put
  `JLCJLCJLCJLC` on the silkscreen; it would be printed as is. The only (free) options are
  a QR / Data Matrix code or a serial number, placed in a solid silkscreen square for
  "Specify Position" (JLC put theirs on the rail for the first order).
- Upload the Gerbers, BOM and position file from the same board. Check the part rotations
  in JLC's placement preview: everything is on the back at 15° steps.

## Orders

### hachigo74, JLCPCB, invoice of 2026-10-23

5 PCBs of `hachigo74_v1.0` (2 layers), 4 of them assembled by JLC (Standard PCBA,
bottom side: SK6812MINI-E, 1N4148W, 100 nF / 10 µF, 330 Ω, Molex FFC connector). The
hot-swap sockets, Helios, OLED and trackpad are not included (hand-soldered or bought
separately). Shipped by DHL Express, DDP (duties paid at checkout).

| Item | Qty | Unit (EUR) | Total (EUR) |
|---|---|---|---|
| 2-layer bare PCB (the 5th, unassembled board) | 1 | 5.95 | 5.95 |
| Populated PCB (PCB + assembly + parts) | 4 | 24.72 | 98.89 |
| **Merchandise total** | | | **104.84** |
| Shipping (DHL Express, DDP) | | | 63.69 |
| Discount (coupon) | | | −7.35 |
| **Subtotal** | | | **161.18** |
| Import taxes (VAT) | | | 51.11 |
| Duty and tax disbursement fee | | | 7.35 |
| Payment fee | | | 2.20 |
| **Grand total** | | | **221.84** |

About EUR 55 per assembled board, everything included. Shipping, import tax and fees
came to EUR 124.35, more than the boards themselves (EUR 104.84).

### hachigo74, all parts of one keyboard (as built, 2026-11)

Prices are what the user paid where known, else shop list prices looked up on 2026-11-07
(marked *list*); **TBD** = not found yet, fill in from the invoice. USD converted at about
0.86 EUR (an assumption, check the rate). Shop shipping is not included unless stated.

| Part | Source | Qty | Price | EUR (about) |
|---|---|---|---|---|
| PCB, JLC-assembled (LEDs, diodes, caps, resistor, FFC connector) | JLCPCB, invoice above | 1 of 4 | EUR 221.84 / 4, shipping and VAT included | 55.46 |
| 0xCB Helios (RP2040) | [keeb.supply](https://keeb.supply/products/0xcb-helios) | 1 | EUR 16.00 incl. DE VAT, *list* (MillMax pins +3.60) | 16.00 |
| OLED 0.96" 128 x 64 I2C, D096-12864-I2C-GV-WH | hestore.hu | 1 | EUR 3 (user) | 3.00 |
| Gateron KS-33 Low Profile 2.0 switches (white bottom housing, Blue) | [gateron.com](https://www.gateron.com/products/gateron-ks-33-low-profile-20-switch-set) | 74 (pack of 110) | EUR 23.51 per 110 (user) | 23.51 |
| Gateron Upgrade Low Profile Hot-swap PCB 2.0 Socket (KS-2P02B01-02) | [gateron.com](https://www.gateron.com/products/gateron-low-profile-switch-hot-swap-pcb-socket) | 74 (pack of 110) | EUR 8.40 per 110 (user) | 8.40 |
| Gateron Low Profile Plate Mounted Stabilizer 2U (KS-57B210T) | [gateron.com](https://www.gateron.com/products/gateron-low-profile-plate-mounted-stabilizer) | 2 | EUR 0.92 each (user) | 1.84 |
| Cirque TM040040-2024-303 (40 mm, curved overlay) | [Mouser](https://www.trustedparts.com/en/part/cirque-corporation/TM040040-2024-303) | 1 | USD 9.62, *list* (Mouser data via TrustedParts) | 8.30 |
| Trackpad FFC, 12 pin 0.5 mm, reverse, 30 mm (GCT 05-12-D-0030-A-4-06-4-T) | DigiKey / Mouser, with the trackpad | 1 | about EUR 0.90, *list* (LCSC: USD 0.07 + about EUR 15 shipping) | 0.90 |
| Screws (M2 for the cover etc.) | | 1 lot | about EUR 20 with shipping (user's estimate) | 20.00 |
| **Total** | | | | **about 137** |

Not in the table: the printed case (filament), the 3 x 1 magnets of the tilt wedge, keycaps
(borrowed Keychron low-profile US caps for now; the Hungarian caps are still to be made, see
`keycaps/`), and the shops' shipping for Gateron and Mouser. The switch and socket packs of 110 leave 36 of each
as spares.

## Sources

- [LCSC FAQ: combine LCSC / JLCPCB orders](https://www.lcsc.com/zh-TW/faqs/ordering-quotation/combine-lcsc-jlcpcb-orders)
- [LCSC help center: combine LCSC / JLCPCB orders](https://fat.lcsc.com/help-center/ordering-quotation/combine-lcsc-jlcpcb-orders)
- [EasyEDA forum: combining PCB and parts orders (2019)](https://easyeda.com/forum/topic/Combine_PCB_and_Parts_Order-DQECYkFfd)
- JLCPCB part pages: [C18212911](https://jlcpcb.com/partdetail/C18212911), [C47149418](https://jlcpcb.com/partdetail/C47149418), [C5149201](https://jlcpcb.com/partdetail/C5149201)
- LCSC flat flex cables: [search](https://www.lcsc.com/search?q=FFC%2012P%200.5mm%2030mm)
