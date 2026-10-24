# Parametric low-profile keycap for the Gateron KS-33 (and KS-57 stabilizer), after the
# user's keycap-10-13.step: 3 deg sloped top (north up), 5 deg drafted skirt (16 in the original), 1.5 walls,
# plus a north roll-off ("fade"), a slightly concave (spherical) top and a flat centre
# pocket for a separately printed legend insert held by two keyed pins.
#
# Cap frame: z = 0 at the skirt bottom, +y = north, origin at the key centre.
# Seating (KS-33 drawing / Gateron STEP, heights above the PCB top): cup floor 5.55, cup
# and cross top 8.55, 3.0 travel. The stem reaches --stem-drop below the skirt and sits on
# the cup floor, so the skirt is at 5.55 + drop at rest and clears the switch housing over
# the full travel (drop 1.3: checked by check_fit.py). The KS-57 stem cross is 1.25 higher
# than the switch's, so stabilizer stems start 1.25 higher and their cross hole runs up
# into the top wall.
#
# Usage (build123d, see tools/step.sh for the install):
#   python keycaps/keycap.py [--out keycaps/build] [--units 1,1.25,1.25t,2s,2st] [--legend A ...]
#   units: 1 / 1.25 / 2 (s = with stabilizer stems, t = thumb version: the south part of the
#   top rolls down from the insert level to the south edge); writes cap_<u>u[_stab][_thumb] and
#   insert.step/.stl (blank) or insert_<legend>.step/.stl.
import os, sys, math, argparse
from build123d import (Pos, Rot, Box, Cylinder, RectangleRounded, Circle,
                       Text, Align, Axis, Plane, Polygon, Wire, Line, Spline, Face, extrude, loft, scale, revolve,
                       export_step, export_stl)

P = dict(
    pitch=19.0, gap=0.8, depth=18.2,      # cap = u * pitch - gap wide, depth deep (Ergogen kc 18.2)
    draft=5.0,                            # skirt angle from vertical, deg (user: closer to 90 deg to the
                                          # plate; the original keycap-10-13 had 16)
    r_bottom=2.0, r_top=1.2,              # outer corner radii at the skirt bottom / top
    h_centre=4.5, slope=3.0,              # top plane height at the centre, slope (north up)
    wall=1.5,                             # side wall (measured square to the skirt face)
    fade_len=4.0, fade_drop=0.8,          # north roll-off: starts fade_len from the north top edge
                                          # thumb version: the south face is one arc, tangent to the insert
                                          # plane at the insert's south edge and to the south skirt face
    valley=0.5, valley_r=8.6,             # valley: the insert plane valley below the top plane, rising
                                          # smoothly (smoothstep, no crease) from the insert edge to the
                                          # top plane at valley_r (stretched in x on wide caps)
    insert='circle', insert_size=10.0,    # 'circle' (diameter) or 'square' (side)
    insert_t=0.8, insert_clear=0.1,       # insert thickness (4 x 0.2 layers), radial pocket gap
    floor=0.8,                            # top wall under the pocket (= pin length)
    pins=((-2.8, 2.8, 1.0), (2.8, -2.8, 1.4)),   # x, y, diameter: keyed (one way round)
    pin_clear=0.1,
    stem_d=5.22, stem_drop=1.3,           # stem below the skirt
    cross=(4.10, 1.20),                   # switch cross hole (KS-33 cross 4.00 x 1.10; 0.2 nozzle FDM)
    stab_x=12.0, stab_rise=1.25,          # KS-57 stems at +-12, cross 1.25 higher than the switch's
    stab_cross=(4.00, 1.10), stab_cross_top=2.95, # KS-57 cross 3.90 x 1.00, top at cap z 2.95 when seated
    stab_recess=(3.4, -4.9, 4.6, 3.0),    # ceiling recess over each KS-57 housing (top 6.55 above the PCB):
                                          # half width, y from / to, flat top at cap z (0.3 clear bottomed out)
    legend_depth=0.16, legend_size=5.0, legend_font='Arial',  # legend = the first 2 layers (0.10 first
                                          # layer + one 0.06 layer; match the slicer's layer heights)
)


def top_frame(p):
    """Location of the sloped top plane (origin above the key centre at h_centre)."""
    return Pos(0, 0, p['h_centre']) * Rot(p['slope'], 0, 0)


def flat_r(p):
    """Radius of the flat valley floor: the insert (circle, or the square's corners) plus its gap."""
    h = p['insert_size'] / 2 + p['insert_clear'] + 0.3      # 0.3 flat ring: the pocket edge never meets
    return h if p['insert'] == 'circle' else h * math.sqrt(2)   # the valley's own edge (tangent seams crack meshes)


def valley_z(p, r):
    """Top surface height (top frame) at radius r (y direction): flat, smoothstep, plane."""
    r0, r1 = flat_r(p), p['valley_r']
    if r <= r0: return -p['valley']
    if r >= r1: return 0.0
    u = (r - r0) / (r1 - r0)
    return -p['valley'] * (1 - (3 * u * u - 2 * u ** 3))


def valley_tool(p, sx):
    """Solid above the valley surface (revolved profile, stretched sx in x), in the top frame."""
    r0, r1, R = flat_r(p), p['valley_r'], p['valley_r'] * 3
    pts = [(r0 + (r1 - r0) * k / 16, 0, valley_z(p, r0 + (r1 - r0) * k / 16)) for k in range(17)]
    w = Wire([Line((0, 0, -p['valley']), (r0, 0, -p['valley'])),
              Spline(*pts, tangents=((1, 0, 0), (1, 0, 0))),
              Line((r1, 0, 0), (R, 0, 0)), Line((R, 0, 0), (R, 0, 10)),
              Line((R, 0, 10), (0, 0, 10)), Line((0, 0, 10), (0, 0, -p['valley']))])
    return scale(revolve(Face(w), Axis.Z), (sx, 1, 1))


def insert_levels(p, w_top=None, d_top=None):
    z_top = -p['valley']                         # the insert is the valley floor
    z_pocket = z_top - p['insert_t']
    z_ceil = z_pocket - p['floor']
    return z_top, z_pocket, z_ceil


ACCENTS = {'́': 'acute', '̈': 'uml', '̋': 'dacute'}


def file_name(legend):
    """ASCII file name part for a legend: 'Á' -> 'A_acute', 'Ő' -> 'O_dacute'."""
    import unicodedata
    out = []
    for ch in legend:
        d = unicodedata.normalize('NFD', ch)
        out.append(d[0] + ''.join('_' + ACCENTS.get(m, 'x%04x' % ord(m)) for m in d[1:]) if d[0].isascii() else 'u%04x' % ord(ch))
    return ''.join(out)


def insert_face(p, grow=0.0):
    s = p['insert_size'] + 2 * grow
    if p['insert'] == 'circle':
        return Circle(s / 2)
    return RectangleRounded(s, s, min(1.0 + grow, s / 2 - 0.01))


def thumb_tool(p, D, big):
    """Solid outside the thumb arc (cap frame, along x): the arc is tangent to the insert plane at
    the insert's south edge and to the outer south skirt face (2D in the y-z section)."""
    sl, dr = math.radians(p['slope']), math.radians(p['draft'])
    z_ins = p['h_centre'] - p['valley']                       # insert plane at y = 0
    t1 = (-flat_r(p), z_ins - flat_r(p) * math.tan(sl))       # tangent point on the insert plane
    n1 = (math.sin(sl), -math.cos(sl))                        # into the cap, normal to the insert plane
    p0 = (-D / 2, 0.0)                                        # skirt face through the bottom edge,
    n2 = (math.cos(dr), -math.sin(dr))                        # inward normal (the face leans in by draft)
    r = ((t1[0] - p0[0]) * n2[0] + (t1[1] - p0[1]) * n2[1]) / (1 - (n1[0] * n2[0] + n1[1] * n2[1]))
    c = (t1[0] + r * n1[0], t1[1] + r * n1[1])
    u1, u2 = (-n1[0], -n1[1]), (-n2[0], -n2[1])               # centre -> tangent points
    k = 30
    sector = Plane.YZ * Polygon(c, (c[0] + k * u1[0], c[1] + k * u1[1]),
                                (c[0] + k * (u1[0] + u2[0]), c[1] + k * (u1[1] + u2[1])),
                                (c[0] + k * u2[0], c[1] + k * u2[1]), align=None)
    return extrude(sector, amount=big, both=True) - Pos(0, c[0], c[1]) * Rot(0, 90, 0) * Cylinder(r, 2 * big)


def build_cap(u, stab=False, thumb=False, p=P):
    W, D = u * p['pitch'] - p['gap'], p['depth']
    t = math.tan(math.radians(p['draft']))
    H = p['h_centre'] + D / 2 * math.tan(math.radians(p['slope'])) + 2     # above the highest top point
    inset = H * t
    outer = loft([Pos(0, 0, 0) * RectangleRounded(W, D, p['r_bottom']),
                  Pos(0, 0, H) * RectangleRounded(W - 2 * inset, D - 2 * inset, p['r_top'])])
    tf = top_frame(p)
    big = 4 * W + 40
    # top: sloped plane
    cap = outer - tf * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # top outline size where the plane meets the skirt (for the valley / fade)
    w_top, d_top = W - 2 * p['h_centre'] * t, D - 2 * p['h_centre'] * t
    # north roll-off: a cylinder (axis x) tangent to the top plane fade_len inside the north edge
    L, drop = p['fade_len'], p['fade_drop']
    Rf = L * L / (2 * drop)
    yf = d_top / 2 - L
    roll = (Pos(0, yf, -Rf) * Box(big, 30, 40, align=(Align.CENTER, Align.MIN, Align.MIN))
            - Pos(0, yf, -Rf) * Rot(0, 90, 0) * Cylinder(Rf, big))
    cap = cap - tf * roll
    if thumb:                                    # south face rounded for a thumb press
        cap = cap - thumb_tool(p, D, big)
    # valley: flat insert floor, rising smoothly to the top plane (stretched in x on wide caps)
    cap = cap - tf * valley_tool(p, w_top / d_top)
    # legend insert pocket and pin holes
    z_top, z_pocket, z_ceil = insert_levels(p, w_top, d_top)
    cap = cap - tf * Pos(0, 0, z_pocket) * extrude(insert_face(p, p['insert_clear']), amount=10)
    for x, y, d in p['pins']:
        cap = cap - tf * Pos(x, y, z_ceil - 3) * Cylinder(d / 2 + p['pin_clear'], 3 + p['floor'] + 0.01,
                                                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    # inside: the skirt offset by the wall, up to the ceiling (parallel to the top)
    tw = p['wall'] / math.cos(math.radians(p['draft']))
    inner = loft([Pos(0, 0, -1) * RectangleRounded(W - 2 * tw + 2 * t, D - 2 * tw + 2 * t, max(p['r_bottom'] - tw, 0.5)),
                  Pos(0, 0, H) * RectangleRounded(W - 2 * tw - 2 * inset, D - 2 * tw - 2 * inset, 0.5)])
    inner = inner - tf * Pos(0, 0, z_ceil) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cap = cap - inner
    if stab:
        hw, y0, y1, zr = p['stab_recess']
        for x in (-p['stab_x'], p['stab_x']):
            cap = cap - Pos(x, (y0 + y1) / 2, 0) * Box(2 * hw, y1 - y0, zr, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # stems: down to -stem_drop (switch) / -stem_drop + stab_rise (stabilizer), up into the ceiling
    def stem(x, bottom, cross, cross_top, top=None):
        st = Pos(x, 0, bottom) * Cylinder(p['stem_d'] / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        st = st - (Pos(0, 0, top) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)) if top is not None
                   else tf * Pos(0, 0, z_ceil + 0.5) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        hole = (Pos(x, 0, bottom - 1) * Box(cross[0], cross[1], cross_top - bottom + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
                + Pos(x, 0, bottom - 1) * Box(cross[1], cross[0], cross_top - bottom + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        return st, hole
    ceil_c = p['h_centre'] + z_ceil                  # ceiling at the key centre (cap z)
    parts = [stem(0, -p['stem_drop'], p['cross'], ceil_c)]
    if stab:
        for x in (-p['stab_x'], p['stab_x']):
            parts.append(stem(x, -p['stem_drop'] + p['stab_rise'], p['stab_cross'], p['stab_cross_top'] + 0.35,
                              top=p['stab_recess'][3] + 0.5))
    for st, hole in parts:
        cap = cap + st
    for st, hole in parts:
        cap = cap - hole
    return cap.clean()


def build_insert(legend=None, p=P):
    """Legend insert in its own frame (top face at z = insert_t, pins down): print it face down."""
    face = insert_face(p)
    ins = extrude(face, amount=p['insert_t'])            # top at z = insert_t
    for x, y, d in p['pins']:
        ins = ins + Pos(x, y, -p['floor']) * Cylinder(d / 2, p['floor'] + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    leg = None
    if legend:
        txt = Text(legend, p['legend_size'], font=p['legend_font'], align=(Align.CENTER, Align.CENTER))
        leg = Pos(0, 0, p['insert_t'] - p['legend_depth']) * extrude(txt, amount=p['legend_depth'])
        leg = leg & ins
        ins = ins - leg
    return ins.clean(), leg


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build'))
    ap.add_argument('--units', default='1,1.25,1.25t,2s,2st')
    ap.add_argument('--legend', nargs='*', default=[])
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    for spec in A.units.split(','):
        stab, thumb = 's' in spec, 't' in spec
        u = float(spec.rstrip('st'))
        cap = build_cap(u, stab, thumb)
        name = 'cap_%gu%s%s' % (u, '_stab' if stab else '', '_thumb' if thumb else '')
        export_step(cap, os.path.join(A.out, name + '.step')); export_stl(cap, os.path.join(A.out, name + '.stl'))
        b = cap.bounding_box()
        print('%-14s %d solid(s) valid %s volume %6.1f mm3  %.2f x %.2f x %.2f (z %.2f..%.2f)'
              % (name, len(cap.solids()), cap.is_valid, cap.volume, b.size.X, b.size.Y, b.size.Z, b.min.Z, b.max.Z))
    for leg in (A.legend or [None]):
        ins, lg = build_insert(leg)
        name = 'insert' + ('_' + file_name(leg) if leg else '')
        export_step(ins, os.path.join(A.out, name + '.step')); export_stl(ins, os.path.join(A.out, name + '.stl'))
        if lg is not None:
            export_stl(lg, os.path.join(A.out, name + '_legend.stl'))
        print('%-14s valid %s volume %.1f mm3' % (name, ins.is_valid, ins.volume))
