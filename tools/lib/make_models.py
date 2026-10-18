# Recreate the 3D models of the bought parts as simplified solids from their
# public datasheet dimensions (build123d / OpenCascade -> STEP with colours), so
# the repository needs no vendor CAD files. Each model uses the same coordinate
# frame as the vendor model it replaces (measured once from it), so the offsets in
# the footprints stay valid.
#
# Usage (build123d, e.g. B3D_DIR from tools/step.sh):
#   python tools/lib/make_models.py "kicad-libraries/3dmodels"
#
# Sources (datasheets/, see datasheets/LINKS.md):
#   KS-33 switch     KS-33E10B055NN-Y24 drawing: 15.00 top / 14.00 bottom housing,
#                    12.15 overall, 5.75 above / 2.50 below the plate top, pins at
#                    (2.60, 5.75) and (4.40, 4.70), post 5.05, stem cross 4.00 x 1.10,
#                    LED window 5.00 x 3.20.
#   KS-2P02B01-02    socket drawing: body 11.85 x 5.40 x 1.87, cups 2.90 (3.00 total),
#                    terminals 1.74 wide, 15.1 tip to tip, holes 7.00 apart.
#   KS-57B210T       stabilizer drawing: housings 6.00 x 17.00, 24.00 apart, 15.16 /
#                    12.40 long above / below the plate, 4.05 above / 4.45 below the
#                    plate top, wire 1.00.
#   SK6812MINI-E     OPSCO datasheet (C5149201): body 3.2 x 2.8 x 1.78, leads 0.68
#                    wide, 5.88 tip to tip, 1.5 lead pitch.
#   Molex 505278     sales drawing 5052781004: housing A = 10.7 wide, 1.9 high,
#                    3.95 / 4.1 deep, 5.3 with the tails; contacts 0.3 at 0.5 pitch;
#                    fitting nails at x = +-5.05 (simplified).
#   Cirque TM040040  40 mm circle trackpad, flats 39.4 apart, 5.15 thick, FFC
#                    connector 15.4 mm south of the centre, 2.5 mm below the pad.
import sys, os, math
from build123d import (Box, Cylinder, Pos, Rot, Color, Compound, export_step, Location,
                       fillet, Axis, Sphere)

OUT = sys.argv[1] if len(sys.argv) > 1 else 'models_out'
os.makedirs(OUT, exist_ok=True)
BLACK, GREY, CLEAR, BROWN = Color(0.12, 0.12, 0.13), Color(0.55, 0.55, 0.57), Color(0.85, 0.88, 0.9, 0.6), Color(0.55, 0.35, 0.2)
GOLD, COPPER, WHITE, STEEL = Color(0.83, 0.69, 0.22), Color(0.72, 0.45, 0.2), Color(0.95, 0.95, 0.93), Color(0.7, 0.7, 0.72)
PCB_GREEN, TP_BLACK = Color(0.1, 0.35, 0.15), Color(0.08, 0.08, 0.08)

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
def cyl(x, y, z0, z1, d):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)
def part(shape, color, label):
    shape.color = color; shape.label = label; return shape
def save(name, parts):
    c = Compound(children=parts); c.label = name
    export_step(c, os.path.join(OUT, name + '.step'))
    b = c.bounding_box()
    print('%-34s x %7.2f..%7.2f  y %7.2f..%7.2f  z %6.2f..%6.2f' % (name, b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z))

# ---- Gateron KS-33 switch: frame of the vendor model (key centre at x = 60,
# pin tips at z = 0, PCB top at z = 3.25, plate top at z = 5.75; pins toward -y)
X = 60.0
PCB, PLATE = 3.25, 5.75
lower = box(X - 7.0, X + 7.0, -6.9, 6.9, PCB, PLATE)                          # 14.00 x 13.8 below the plate
top = box(X - 7.5, X + 7.5, -7.5, 7.5, PLATE, PLATE + 2.4)                    # 15.00 x 15.00 top housing
upper = box(X - 6.35, X + 6.35, -4.25, 4.25, PLATE + 2.4, PLATE + 4.0)        # 12.7 x 8.5
holder = box(X - 4.7, X + 4.7, -3.15, 3.15, PLATE + 4.0, PLATE + 5.0)          # 9.4 x 6.3 stem holder
window = box(X - 0.69 - 2.5, X - 0.69 + 2.5, 5.16 - 1.6, 5.16 + 1.6, PCB - 0.1, PLATE + 2.5)   # LED window 5.00 x 3.20
housing = (lower + top + upper + holder) - window
post = cyl(X, 0, 0.0, PCB, 5.05)                                              # bottom post
stem = (box(X - 2.0, X + 2.0, -0.55, 0.55, PLATE + 4.0, 12.15) + box(X - 0.55, X + 0.55, -2.0, 2.0, PLATE + 4.0, 12.15))
pins = box(X - 4.4 - 0.15, X - 4.4 + 0.15, -4.7 - 0.3, -4.7 + 0.3, 0.6, PCB) + box(X + 2.6 - 0.15, X + 2.6 + 0.15, -5.75 - 0.3, -5.75 + 0.3, 0.6, PCB)
save('Gateron_KS-33_switch', [part(housing, BLACK, 'housing'), part(post, BLACK, 'post'), part(stem, BROWN, 'stem'), part(pins, GOLD, 'pins')])

# ---- Gateron KS-2P02B01-02 hot-swap socket: footprint frame (top view, x / y as
# the pads; body z 0..1.87 away from the PCB, cups -1.13..0 into the pin holes)
body = box(-6.82, 5.03, 2.53, 7.92, 0.0, 1.87)
for cx, cy in ((-4.4, 4.7), (2.6, 5.75)):
    body = body - cyl(cx, cy, 0.4, 1.9, 2.0)                                 # cup openings from the top
cups = cyl(-4.4, 4.7, -1.13, 0.0, 2.90) + cyl(2.6, 5.75, -1.13, 0.0, 2.90)
term = box(-8.44, -6.82, 4.7 - 0.87, 4.7 + 0.87, 0.0, 1.2) + box(5.03, 6.65, 5.75 - 0.87, 5.75 + 0.87, 0.0, 1.2)
save('Gateron_KS-2P02B01-02_socket', [part(body, BLACK, 'base'), part(cups, GOLD, 'cups'), part(term, GOLD, 'terminals')])

# ---- Gateron KS-57 2U plate-mounted stabilizer: switch frame (housings at x = 60 +- 12)
ps = []
for cx in (X - 12.0, X + 12.0):
    low = box(cx - 2.925, cx + 2.925, -4.3, 4.3, PLATE - 4.45, PLATE - 1.2)   # 12.40 long below the plate (simplified 8.6 + lever)
    lever = box(cx - 2.925, cx + 2.925, -7.9, -4.3, PLATE - 3.0, PLATE - 1.2)
    up = box(cx - 3.0, cx + 3.0, -7.9, 7.25, PLATE - 1.2, PLATE + 1.2)         # 6.00 x 15.16 at / above the plate
    clip = box(cx - 3.0, cx + 3.0, -5.0, 5.0, PLATE + 1.2, PLATE + 4.05)
    stemb = box(cx - 2.0, cx + 2.0, -3.1, 3.1, PLATE + 1.2, PLATE + 4.05)
    cross = box(cx - 1.95, cx + 1.95, -0.54, 0.54, PLATE + 4.05, 13.05) + box(cx - 0.54, cx + 0.54, -1.95, 1.95, PLATE + 4.05, 13.05)
    ps += [part(low + lever + up + clip, BLACK, 'housing'), part(stemb, BLACK, 'insert'), part(cross, BLACK, 'stem')]
wire = Pos(X, -8.4, PLATE - 2.4) * Rot(0, 90, 0) * Cylinder(0.5, 24.0 + 2.0)
ps.append(part(wire, STEEL, 'wire'))
save('Gateron_KS-57_stabilizer', ps)

# ---- SK6812MINI-E: frame of the vendor model (body centred 5.08 mm south, z -2.69..-0.91)
cy, z0, z1 = -5.08, -2.69, -0.91
led = box(-1.6, 1.6, cy - 1.4, cy + 1.4, z0, z1)
led = led - box(1.6 - 0.45, 1.65, cy - 1.45, cy - 1.4 + 0.45, z0 - 0.1, z1 + 0.1)   # chamfered pin-1 (GND) corner
lens = cyl(0, cy, z0 - 0.02, z0 + 0.02, 1.9)
leads = None
for sx in (-1, 1):
    for sy in (-0.75, 0.75):
        l = box(sx * 1.6 if sx > 0 else -2.94, 2.94 if sx > 0 else -1.6, cy + sy - 0.34, cy + sy + 0.34, -1.9, -1.7)
        leads = l if leads is None else leads + l
save('SK6812MINI-E', [part(led, WHITE, 'body'), part(lens, Color(0.98, 0.98, 0.85), 'lens'), part(leads, STEEL, 'leads')])

# ---- Molex 505278-1270 (0.5 mm, 12 pin, flip lock): frame of the vendor model
mbody = box(-5.35, 5.35, 0.43, 4.45, 0.0, 1.88)
lid = box(-4.63, 4.63, -1.2, 1.57, 0.6, 1.88)
tabs = box(-5.75, -4.41, 0.75, 1.65, 0.0, 0.3) + box(4.41, 5.75, 0.75, 1.65, 0.0, 0.3)
cont = None
for i in range(12):
    cx = -2.75 + 0.5 * i
    c = box(cx - 0.125, cx + 0.125, -1.2, 0.5, 0.0, 0.15)
    cont = c if cont is None else cont + c
save('Molex_505278-1270', [part(mbody, Color(0.85, 0.82, 0.72), 'housing'), part(lid, BLACK, 'actuator'), part(tabs, STEEL, 'tabs'), part(cont, GOLD, 'contacts')])

# ---- Cirque TM040040: centred, mid-height origin (top z +2.575, underside -2.575),
# flats north / south, FFC connector 15.4 mm south, reaching 2.5 mm below the pad
def flat_disc(d, z0, z1, flat):
    return cyl(0, 0, z0, z1, d) & box(-d, d, -flat, flat, z0 - 1, z1 + 1)
top_ = flat_disc(40.0, 1.585, 2.575, 19.7)                                   # overlay + board (0.99)
parts_ = flat_disc(36.0, -2.575, 1.585, 18.0)                                # component zone (parts-free 2 mm rim)
conn = box(-5.0, 5.0, -15.4 - 1.5, -15.4 + 1.5, -5.075, -2.575)
save('Cirque_TM040040', [part(top_, TP_BLACK, 'overlay'), part(parts_, PCB_GREEN, 'board'), part(conn, Color(0.9, 0.9, 0.85), 'connector')])
