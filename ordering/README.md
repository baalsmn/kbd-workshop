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
the Cirque trackpad.

## Trackpad flat cable (FFC), from LCSC

Needed: 12 pin, 0.5 mm pitch, contacts on opposite ends ("Reverse", type B / D), 30 mm,
0.3 mm thick. The Molex 505278 drawing recommends a finished FFC thickness of
0.3 ± 0.05 mm.

| LCSC | Part | Stock (2026-10-21) | Price |
|---|---|---|---|
| **C54950533** | GUOCONN 0.5\*12P\*30\*B\*3/3\*5/5, Reverse, 3 cm | 925 | about $0.07 each from 5 |
| C5248013 | JUSHUO JS05B-12P-030-3-4, Reverse, 3 cm | 325 | about $0.10 each from 5 |

Don't use the "Same Side" (A-type) cables listed next to them. Order a few spares.

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

- Route only the design board (`<keyboard>/kicad/<keyboard>.kicad_pcb`). Then rebuild
  the panel with `bash tools/panel.sh <keyboard>` and run the Fabrication Toolkit on
  `<keyboard>_panel.kicad_pcb`.
- At JLC choose "Panel by Customer", 1 board per panel, no extra edge rails. Use
  Standard PCBA, assembly on the bottom side.
- Upload the Gerbers, BOM and position file from the same (panel) board. Check the
  part rotations in JLC's placement preview: everything is on the back at 15° steps.

## Sources

- [LCSC FAQ: combine LCSC / JLCPCB orders](https://www.lcsc.com/zh-TW/faqs/ordering-quotation/combine-lcsc-jlcpcb-orders)
- [LCSC help center: combine LCSC / JLCPCB orders](https://fat.lcsc.com/help-center/ordering-quotation/combine-lcsc-jlcpcb-orders)
- [EasyEDA forum: combining PCB and parts orders (2019)](https://easyeda.com/forum/topic/Combine_PCB_and_Parts_Order-DQECYkFfd)
- JLCPCB part pages: [C18212911](https://jlcpcb.com/partdetail/C18212911), [C47149418](https://jlcpcb.com/partdetail/C47149418), [C5149201](https://jlcpcb.com/partdetail/C5149201)
- LCSC flat flex cables: [search](https://www.lcsc.com/search?q=FFC%2012P%200.5mm%2030mm)
