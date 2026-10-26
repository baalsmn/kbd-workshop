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
from build123d import (Pos, Rot, Box, Cylinder, RectangleRounded, Rectangle, Circle,
                       Text, Align, Axis, Plane, Polygon, Wire, Line, Spline, ThreePointArc, Face, extrude, loft, scale, revolve, fillet,
                       export_step, export_stl)

P = dict(
    pitch=19.0, gap=0.8, depth=18.2,      # cap = u * pitch - gap wide, depth deep (Ergogen kc 18.2)
    draft=5.0,                            # skirt angle from vertical, deg (user: closer to 90 deg to the
                                          # plate; the original keycap-10-13 had 16)
    r_bottom=2.0, r_inner=0.8,            # corner radii at the skirt bottom, outside / inside (they shrink
                                          # upwards with the draft, like a tapered extrude)
    top_fillet=0.6,                       # fillet along the top outer edge outline
    cap_source='fusion',                  # caps come from build/fusion/<cap>.step (KeycapBuilder export) when
                                          # there; 'build123d' = build_cap() here (also the fallback)
    thumb_scaled_units=(1.25,),           # thumb curve scaled per slice down through the bottom edge (no south
                                          # skirt left); the others (2U: its cut fails that way) keep the curve
                                          # raised by the valley, meeting the bottom edge at the centre only
    thumb_fillet=0.6, thumb_fillet_units=(1.25, 2),  # thumb caps: north / west / east top edges only (not
                                          # along the thumb surface), and only where OCC manages it: the
                                          # 1.25U (the 2U thumb's fillet fails; user: leave it for now)
    thumb_style='valley',                 # thumb top: 'valley' (the thumb roll-off follows the valley's
                                          # east-west line) or 'straight' (no east-west valley; WIP)
    thumb_meet=-0.05, thumb_angle=15.0,   # thumb surface runs down through the skirt's bottom edge (aims 0.05
                                          # below it at 15 deg, so it leaves through the underside: no skirt
                                          # strip left on the south side)
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
        if d[0].isascii() and d[0].isalnum() and all(m in ACCENTS for m in d[1:]):
            out.append(d[0] + ''.join('_' + ACCENTS[m] for m in d[1:]))
        else:                                    # symbols: their code (safe in every file name)
            out.append('u%04x' % ord(ch))
    return '_'.join(out) if len(legend) > 1 and any(len(o) > 1 for o in out) else ''.join(out)


def insert_face(p, grow=0.0):
    s = p['insert_size'] + 2 * grow
    if p['insert'] == 'circle':
        return Circle(s / 2)
    return RectangleRounded(s, s, min(1.0 + grow, s / 2 - 0.01))


def thumb_profile(p, D):
    """Top of a thumb cap: one north-south profile (cap frame, (y, z)), straight east-west (user: no
    valley in the east-west line). South to north: a line meeting the south skirt thumb_meet high at
    thumb_angle, an arc tangent to it and to the insert plane, the flat insert band (insert level,
    full width), the valley's north rise (smoothstep), until it meets the north roll-off arc.
    Returns segments ('line', [a, b]) / ('arc', [a, mid, b]) / ('spline', [pts]), south to north."""
    sl, dr = math.radians(p['slope']), math.radians(p['draft'])
    cs, sn = math.cos(sl), math.sin(sl)
    tf = lambda yp, zp: (yp * cs - zp * sn, p['h_centre'] + yp * sn + zp * cs)
    d_top = D - 2 * p['h_centre'] * math.tan(dr)
    L, drop = p['fade_len'], p['fade_drop']
    Rf, yf = L * L / (2 * drop), d_top / 2 - L
    fr, v = flat_r(p), p['valley']
    t1 = tf(-fr, -v)                                          # south edge of the flat band
    n1 = (sn, -cs)                                            # into the cap, normal to the insert plane
    zm, dv = p['thumb_meet'], dr + math.radians(p['thumb_angle'])
    p0 = (-D / 2 + zm * math.tan(dr), zm)                     # the skirt face, thumb_meet high
    n2 = (math.cos(dv), -math.sin(dv))                        # inward normal of the meeting line
    r = ((t1[0] - p0[0]) * n2[0] + (t1[1] - p0[1]) * n2[1]) / (1 - (n1[0] * n2[0] + n1[1] * n2[1]))
    c = (t1[0] + r * n1[0], t1[1] + r * n1[1])
    t2 = (c[0] - r * n2[0], c[1] - r * n2[1])                 # where the arc turns into the line
    s_end = (t2[0] - (t2[1] + 0.3) * math.tan(dv), -0.3)      # the line, 0.3 below the skirt bottom
    a1, a2 = math.atan2(t1[1] - c[1], t1[0] - c[0]), math.atan2(t2[1] - c[1], t2[0] - c[0])
    mid = (c[0] + r * math.cos((a1 + a2) / 2), c[1] + r * math.sin((a1 + a2) / 2))
    roll = lambda yp: -(Rf - math.sqrt(max(Rf * Rf - (yp - yf) ** 2, 0))) if yp > yf else 0.0
    yc = fr                                                   # where the rising valley meets the roll-off
    while yc < p['valley_r'] and valley_z(p, yc) < roll(yc):
        yc += 0.001
    n = 16
    rise = [tf(fr + (yc - fr) * k / n, valley_z(p, fr + (yc - fr) * k / n)) for k in range(n + 1)]
    ye = d_top / 2 + 1.5                                      # the roll-off arc on past the north edge
    rm = (yc + ye) / 2
    return [('line', [s_end, t2]), ('arc', [t2, mid, t1]), ('line', [t1, tf(fr, -v)]), ('spline', rise),
            ('arc', [rise[-1], tf(rm, roll(rm)), tf(ye, roll(ye))])]          # (starts where the rise ends)


def thumb_tool(p, W, D):
    """Solid above the thumb-cap top profile, through the whole width."""
    pt = lambda q: (0, q[0], q[1])
    segs = thumb_profile(p, D)
    edges = []
    for kind, q in segs:
        if kind == 'line': edges.append(Line(pt(q[0]), pt(q[1])))
        elif kind == 'arc': edges.append(ThreePointArc(pt(q[0]), pt(q[1]), pt(q[2])))
        else: edges.append(Spline(*[pt(a) for a in q]))
    a, b = segs[0][1][0], segs[-1][1][-1]
    edges += [Line(pt(b), (0, b[0], 20)), Line((0, b[0], 20), (0, a[0], 20)), Line((0, a[0], 20), pt(a))]
    return extrude(Face(Wire(edges)), amount=W, both=True, dir=(1, 0, 0))


def thumb_points(p, W, D, sx, nx=97, ny=31, scaled=True):
    """Grid points (rows along y) of the thumb surface (cap frame), thumb_style 'valley': in the
    y-z section at the key centre an arc tangent to the insert plane at the insert's south edge,
    then a short line meeting the south skirt thumb_meet high at thumb_angle; every east-west slice
    is that profile scaled so it starts at the top surface's own height on the start line (continuous
    with the valley) and ends on the skirt's bottom edge: z(x, y) = arc(y) * (1 + rise(x) / z_start).
    Starts 0.002 above the top (no step face)."""
    sl, dr = math.radians(p['slope']), math.radians(p['draft'])
    z_ins = p['h_centre'] - p['valley']                       # insert plane at y = 0
    t1 = (-flat_r(p), z_ins - flat_r(p) * math.tan(sl))       # tangent point on the insert plane
    n1 = (math.sin(sl), -math.cos(sl))                        # into the cap, normal to the insert plane
    zm = p['thumb_meet'] if scaled else 0.0
    dv = dr + math.radians(p['thumb_angle'])
    p0 = (-D / 2 + zm * math.tan(dr), zm)
    n2 = (math.cos(dv), -math.sin(dv))                        # inward normal of the meeting line
    r = ((t1[0] - p0[0]) * n2[0] + (t1[1] - p0[1]) * n2[1]) / (1 - (n1[0] * n2[0] + n1[1] * n2[1]))
    c = (t1[0] + r * n1[0], t1[1] + r * n1[1])
    t2 = (c[0] - r * n2[0], c[1] - r * n2[1])

    def arc(y):                                               # beyond t2: down along the line
        if y >= t2[0]:
            return c[1] + math.sqrt(max(r * r - (y - c[0]) ** 2, 0))
        return t2[1] - (t2[0] - y) / math.tan(dv)

    fr = flat_r(p)
    rise = lambda x: valley_z(p, math.hypot(x / sx, fr)) - valley_z(p, fr)
    xs = [-W / 2 - 1.5 + (W + 3) * k / (nx - 1) for k in range(nx)]
    y_end = t2[0] - (t2[1] + 0.3) * math.tan(dv)             # the line 0.3 below the skirt bottom
    ys = [t1[0] + (y_end - t1[0]) * k / (ny - 1) for k in range(ny)]
    # each east-west slice starts at the top's own height (insert level + rise) and still ends on the
    # skirt's bottom edge (user: no skirt left on the south side): the arc scaled per slice
    # (the 0.002 start offset fades out towards the bottom)
    if not scaled:                                            # (earlier form: raised by the valley)
        return [[(x, y, arc(y) + rise(x) + 0.002) for x in xs] for y in ys]
    return [[(x, y, arc(y) * (1 + rise(x) / t1[1]) + 0.002 * max(arc(y), 0) / t1[1]) for x in xs] for y in ys]


def thumb_valley_tool(p, W, D, sx, scaled=True):
    """Solid above the 'valley' thumb surface (thumb_points)."""
    pts = thumb_points(p, W, D, sx, scaled=scaled)
    return extrude(Face.make_surface_from_array_of_points(pts, tol=1e-4), amount=15, dir=(0, 0, 1))


def top_edge_fillet(cap, W, D, rad, draft, skip_south_of=None):
    """Fillet the outline where the top faces meet the outer skirt faces (the skirt faces lean in by
    exactly the draft; every face above them facing up counts as top, e.g. the thumb's short line);
    edges where it fails are left and counted."""
    side, top, sd = [], [], math.sin(math.radians(draft))
    for f in cap.faces():
        n, c = f.normal_at(), f.center()
        outer = abs(c.X) > W / 2 - 1.2 or abs(c.Y) > D / 2 - 1.2
        if outer and abs(abs(n.Z) - sd) < 0.03 and c.Z > 0:
            side.append(f)
        elif n.Z > 0.15 and c.Z > 0.3:
            top.append(f)
    if skip_south_of is not None:                # leave out every edge touching a face south of this y
        south = [f for f in top if f.center().Y < skip_south_of]
        top = [f for f in top if f not in south]
        skip = {e for f in south for e in f.edges()}
    else:
        skip = set()
    side_edges = {e for f in side for e in f.edges()}
    edges = [e for f in top for e in f.edges() if e in side_edges and e not in skip]
    edges = list({e: None for e in edges})
    try:
        return fillet(edges, rad), len(edges), 0
    except Exception:
        out, skipped = cap, 0
        for e in edges:
            try:
                out = fillet([o for o in out.edges() if o.center().distance_to(e.center()) < 1e-4][:1], rad)
            except Exception:
                skipped += 1
        return out, len(edges), skipped


def build_cap(u, stab=False, thumb=False, p=P):
    W, D = u * p['pitch'] - p['gap'], p['depth']
    t = math.tan(math.radians(p['draft']))
    H = p['h_centre'] + D / 2 * math.tan(math.radians(p['slope'])) + 2     # above the highest top point
    inset = H * t
    def outline(w, d, r):                        # thumb caps: square south corners (user: no rounded
        f = RectangleRounded(w, d, r)            # west-south / east-south corners under the thumb curve)
        return (f + Pos(0, -d / 4) * Rectangle(w, d / 2)).faces()[0] if thumb else f
    outer = loft([Pos(0, 0, 0) * outline(W, D, p['r_bottom']),
                  Pos(0, 0, H) * outline(W - 2 * inset, D - 2 * inset, max(p['r_bottom'] - inset, 0.05))])
    tf = top_frame(p)
    big = 4 * W + 40
    # top outline size where the plane meets the skirt (for the valley / fade)
    w_top, d_top = W - 2 * p['h_centre'] * t, D - 2 * p['h_centre'] * t
    if thumb and p['thumb_style'] == 'straight':  # straight east-west top: one profile (thumb_profile)
        cap = outer - thumb_tool(p, W, D)
    else:
        # top: sloped plane
        cap = outer - tf * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # north roll-off: a cylinder (axis x) tangent to the top plane fade_len inside the north edge
        L, drop = p['fade_len'], p['fade_drop']
        Rf = L * L / (2 * drop)
        yf = d_top / 2 - L
        roll = (Pos(0, yf, -Rf) * Box(big, 30, 40, align=(Align.CENTER, Align.MIN, Align.MIN))
                - Pos(0, yf, -Rf) * Rot(0, 90, 0) * Cylinder(Rf, big))
        cap = cap - tf * roll
        # valley: flat insert floor, rising smoothly to the top plane (stretched in x on wide caps)
        cap = cap - tf * valley_tool(p, w_top / d_top)
        if thumb:                                # 'valley' thumb: the south part rolls down from the insert
            cap = cap - thumb_valley_tool(p, W, D, w_top / d_top, u in p['thumb_scaled_units'])
    # legend insert pocket and pin holes
    z_top, z_pocket, z_ceil = insert_levels(p, w_top, d_top)
    cap = cap - tf * Pos(0, 0, z_pocket) * extrude(insert_face(p, p['insert_clear']), amount=10)
    for x, y, d in p['pins']:
        cap = cap - tf * Pos(x, y, z_ceil - 3) * Cylinder(d / 2 + p['pin_clear'], 3 + p['floor'] + 0.01,
                                                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    # inside: the skirt offset by the wall, up to the ceiling (parallel to the top)
    tw = p['wall'] / math.cos(math.radians(p['draft']))
    inner = loft([Pos(0, 0, -1) * RectangleRounded(W - 2 * tw + 2 * t, D - 2 * tw + 2 * t, p['r_inner']),
                  Pos(0, 0, H) * RectangleRounded(W - 2 * tw - 2 * inset, D - 2 * tw - 2 * inset,
                                                  max(p['r_inner'] - (H + 1) * t, 0.05))])
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
    cap = cap.clean()
    rad = (p['thumb_fillet'] if u in p['thumb_fillet_units'] else 0) if thumb else p['top_fillet']
    if rad > 0:
        cap, n, skipped = top_edge_fillet(cap, W, D, rad, p['draft'])
        if skipped:
            print('  top fillet: %d of %d edges skipped' % (skipped, n))
    return cap


FUSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'fusion')
INSERT_DIR = os.path.join(FUSION_DIR, 'inserts')       # the inserts' Fusion exports and 3MF files
LEGEND_LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inserts.txt')


def read_legends(path=LEGEND_LIST):
    """The legends to make inserts for: keycaps/inserts.txt, one per line (# comments; a backslash + # = a # legend)."""
    out = []
    for line in open(path, encoding='utf-8'):
        t = line.strip()
        if not t or t.startswith('#'):
            continue
        out.append('#' if t == chr(92) + '#' else t)
    return out


LEGENDS = read_legends() if os.path.exists(LEGEND_LIST) else []
HU = LEGENDS                                           # (older name)


def cap_name(u, stab=False, thumb=False):
    return 'cap_%gu%s%s' % (u, '_stab' if stab else '', '_thumb' if thumb else '')


def get_cap(u, stab=False, thumb=False, p=P):
    """The cap as used everywhere (files, fit checks, assembly, Bambu project): Fusion's export
    (build/fusion/<cap>.step, made by keycaps/fusion/KeycapBuilder from the recipe) when cap_source is
    'fusion' and the file is there, else build_cap(). Returns (shape, source)."""
    f = os.path.join(FUSION_DIR, cap_name(u, stab, thumb) + '.step')
    if p['cap_source'] == 'fusion' and os.path.exists(f):
        from build123d import import_step
        return import_step(f).solids()[0], 'fusion'
    return build_cap(u, stab, thumb, p), 'build123d'


def get_insert(legend=None, p=P):
    """The legend insert as used everywhere: Fusion's export (build/fusion/insert_<name>.step: the insert
    and the legend body) when cap_source is 'fusion' and it is there, else build_insert().
    Returns (insert, legend or None, source)."""
    f = os.path.join(INSERT_DIR, 'insert_%s.step' % (file_name(legend) if legend else 'blank'))
    if p['cap_source'] == 'fusion' and os.path.exists(f):
        from build123d import import_step
        from build123d import Compound
        sol = sorted(import_step(f).solids(), key=lambda s: -s.volume)      # insert, then the legend pieces
        return sol[0], (Compound(sol[1:]) if len(sol) > 1 else None), 'fusion'
    ins, leg = build_insert(legend, p)
    return ins, leg, 'build123d'


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


def legend_cap_height(p=P):
    """Height of a capital in build123d's legend text (font size legend_size): Fusion's sketch text
    height is the capital height, so the Fusion inserts use this to match."""
    t = Text('H', p['legend_size'], font=p['legend_font'])
    return round(t.bounding_box().size.Y, 4)


def recipe(u, stab=False, thumb=False, p=P):
    """Every number the Fusion builder (keycaps/fusion/KeycapBuilder) needs for one cap, in mm in the
    cap frame, mirroring build_cap step by step (each step becomes a timeline feature there)."""
    W, D = u * p['pitch'] - p['gap'], p['depth']
    t = math.tan(math.radians(p['draft']))
    H = p['h_centre'] + D / 2 * math.tan(math.radians(p['slope'])) + 2
    w_top, d_top = W - 2 * p['h_centre'] * t, D - 2 * p['h_centre'] * t
    sl = math.radians(p['slope'])
    tfp = lambda y, z: (y * math.cos(sl) - z * math.sin(sl), p['h_centre'] + y * math.sin(sl) + z * math.cos(sl))
    L, drop = p['fade_len'], p['fade_drop']
    Rf = L * L / (2 * drop); yf = d_top / 2 - L
    q = math.sqrt(0.5)
    roll = [tfp(yf, 0), tfp(yf, 5), tfp(yf + Rf + 1, 5), tfp(yf + Rf + 1, -Rf), tfp(yf + Rf, -Rf),
            tfp(yf + Rf * q, -Rf + Rf * q)]           # T, A, B, C, E, arc midpoint (E -> mid -> T)
    r0, r1 = flat_r(p), p['valley_r']
    vprof = [(r0 + (r1 - r0) * k / 16, valley_z(p, r0 + (r1 - r0) * k / 16)) for k in range(17)]
    z_top, z_pocket, z_ceil = insert_levels(p)
    tw = p['wall'] / math.cos(math.radians(p['draft']))
    ceil_c = p['h_centre'] + z_ceil
    stems = [{'x': 0, 'bottom': -p['stem_drop'], 'top': ceil_c + 0.5, 'cross': list(p['cross']), 'cross_top': ceil_c}]
    if stab:
        for x in (-p['stab_x'], p['stab_x']):
            stems.append({'x': x, 'bottom': -p['stem_drop'] + p['stab_rise'], 'top': p['stab_recess'][3] + 0.5,
                          'cross': list(p['stab_cross']), 'cross_top': p['stab_cross_top'] + 0.35})
    r = {'u': u, 'stab': stab, 'thumb': thumb, 'W': W, 'D': D, 'H': H,
         'skirt': {'r': p['r_bottom'], 'draft': p['draft'], 'square_south': thumb},
         'top': {'h_centre': p['h_centre'], 'slope': p['slope']},
         'roll': roll,
         'valley': {'flat': [0, -p['valley'], r0], 'profile': vprof, 'R': r1 * 3, 'sx': w_top / d_top},
         'pocket': {'z': z_pocket, 'r': p['insert_size'] / 2 + p['insert_clear'], 'square': p['insert'] != 'circle',
                    'size': p['insert_size'] + 2 * p['insert_clear']},
         'pins': [[x, y, d / 2 + p['pin_clear']] for x, y, d in p['pins']], 'floor': p['floor'], 'z_ceil': z_ceil,
         'cavity': {'w': W - 2 * tw + 2 * t, 'd': D - 2 * tw + 2 * t, 'r': p['r_inner']},
         'recess': ([[x, (p['stab_recess'][1] + p['stab_recess'][2]) / 2, 2 * p['stab_recess'][0],
                      p['stab_recess'][2] - p['stab_recess'][1], p['stab_recess'][3]] for x in (-p['stab_x'], p['stab_x'])]
                    if stab else []),
         'stems': stems, 'stem_r': p['stem_d'] / 2,
         'fillet': (p['thumb_fillet'] if u in p['thumb_fillet_units'] else 0) if thumb else p['top_fillet'],
         'insert': {'d': p['insert_size'], 't': p['insert_t'], 'square': p['insert'] != 'circle',
                    'legend_depth': p['legend_depth'], 'legend_size': p['legend_size'], 'font': p['legend_font'],
                    'z': z_pocket, 'pins': [[x, y, d] for x, y, d in p['pins']], 'pin_len': p['floor'],
                    'legend_height': legend_cap_height(p)}}   # (Fusion text height = capital height)
    if thumb:
        r['thumb'] = (thumb_profile(p, D) if p['thumb_style'] == 'straight' else
                      thumb_points(p, W, D, w_top / d_top, nx=33, ny=9, scaled=u in p['thumb_scaled_units']))
        r['thumb_style'] = p['thumb_style']
    return r


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build'))
    ap.add_argument('--units', default='1,1.25,1.25t,2s,2st')
    ap.add_argument('--legend', nargs='*', default=[])
    ap.add_argument('--fusion', action='store_true', help='also write build/keycaps_fusion.json for KeycapBuilder')
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    recipes = []
    for spec in A.units.split(','):
        stab, thumb = 's' in spec, 't' in spec
        u = float(spec.rstrip('st'))
        name = cap_name(u, stab, thumb)
        if A.fusion:                             # the recipe for Fusion, with build123d's volume as a check
            ref = build_cap(u, stab, thumb)
            rec = recipe(u, stab, thumb); rec['name'] = name; rec['volume'] = ref.volume; recipes.append(rec)
        cap, src = get_cap(u, stab, thumb)
        export_step(cap, os.path.join(A.out, name + '.step')); export_stl(cap, os.path.join(A.out, name + '.stl'))
        b = cap.bounding_box()
        print('%-18s from %-9s %d solid(s) valid %s volume %6.1f mm3  %.2f x %.2f x %.2f (z %.2f..%.2f)'
              % (name, src, len(cap.solids()), cap.is_valid, cap.volume, b.size.X, b.size.Y, b.size.Z, b.min.Z, b.max.Z))
    if A.fusion:
        import json
        ins_rec = recipe(1)['insert']
        json.dump({'params': {k: v for k, v in P.items()}, 'caps': recipes, 'insert': ins_rec,
                   'legends': [[c, file_name(c)] for c in LEGENDS]},
                  open(os.path.join(A.out, 'keycaps_fusion.json'), 'w'), indent=1)
        print('wrote', os.path.join(A.out, 'keycaps_fusion.json'))
    for leg in (A.legend or [None]):
        ins, lg, isrc = get_insert(leg)
        name = 'insert' + ('_' + file_name(leg) if leg else '')
        export_step(ins, os.path.join(A.out, name + '.step')); export_stl(ins, os.path.join(A.out, name + '.stl'))
        if lg is not None:
            export_stl(lg, os.path.join(A.out, name + '_legend.stl'))
        print('%-18s from %-9s valid %s volume %.1f mm3' % (name, isrc, ins.is_valid, ins.volume))
