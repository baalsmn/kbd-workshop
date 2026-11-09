# Parametric low-profile keycap for the Gateron KS-33 (and KS-57 stabilizer), after the
# user's keycap-10-13.step: 3 deg sloped top (north up), 5 deg drafted skirt (16 in the original), 1.5 walls,
# a north roll-off ("fade") and a dish: one smooth top surface (plane - dish - roll-off). Thumb caps keep
# a flat centre (their south part rolls down from its south edge). Monolithic caps (no insert: user
# 2026-11-09, the insert caps were dropped); legend_cap.py builds them (blank, for solvent-transfer
# legends) and the two-colour (double-shot) legend caps, and is the command line for both.
#
# Cap frame: z = 0 at the skirt bottom, +y = north, origin at the key centre.
# Seating (KS-33 drawing / Gateron STEP, heights above the PCB top): cup floor 5.55, cup
# and cross top 8.55, 3.0 travel. The stem reaches --stem-drop below the skirt and sits on
# the cup floor, so the skirt is at 5.55 + drop at rest and clears the switch housing over
# the full travel (drop 1.3: checked by check_fit.py). The KS-57 stem cross is 1.25 higher
# than the switch's, so stabilizer stems start 1.25 higher and their cross hole runs up
# into the top wall.
# Sizes ("units" specs, legend_cap.py --units): 1 / 1.25 / 2, s = with stabilizer stems, t = thumb
# version (the south part of the top rolls down to the south edge), v = tall (2U deep over two
# switches of a column, a stem on each).
import os, sys, math
from build123d import (Pos, Rot, Box, Cylinder, RectangleRounded, Rectangle,
                       Align, Axis, Wire, Line, Spline, ThreePointArc, Face, extrude, loft, scale, revolve, fillet)

P = dict(
    pitch=19.0, gap=0.8, depth=18.2,      # cap = u * pitch - gap wide, depth deep (Ergogen kc 18.2)
    draft=5.0,                            # skirt angle from vertical, deg (user: closer to 90 deg to the
                                          # plate; the original keycap-10-13 had 16)
    r_bottom=2.0, r_inner=0.8,            # corner radii at the skirt bottom, outside / inside (they shrink
                                          # upwards with the draft, like a tapered extrude)
    top_fillet=0.6,                       # fillet along the top outer edge outline
    cap_source='fusion',                  # fit checks / 3MF meshes from the KeycapBuilder exports in
                                          # build/work/fusion when there; 'build123d' = build_cap() here
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
                                          # thumb version: the south face is one arc, tangent to the flat
                                          # centre's plane at its south edge and to the south skirt face
    valley=0.6, valley_r=8.6,             # dish depth at the centre (user: the valley continues to the centre)
                                          # and its radius, where it meets the top plane (stretched along the
                                          # long side on wide / tall caps)
    valley_style='dish',                  # 'dish': one smooth dish from the centre, z = -valley (1 - (r /
                                          # valley_r)^2)^2; 'flat': a flat floor (flat_r) rising smoothly
                                          # (smoothstep) to the top plane at valley_r (the thumb caps)
    thumb_valley=0.5, flat_r=5.4,         # thumb caps: flat centre 0.5 below the top plane, radius 5.4 (their
                                          # roll-down starts at its south edge; from the old insert caps)
    ceiling=-2.1,                         # cavity ceiling below the top plane (0.2 lower (dish 0.7 with the
                                          # ceiling following) touched the switch at 3.0 mm travel)
    stem_d=5.0, stem_drop=1.3,            # stem diameter (user: 5.22 was too wide; 0.45 wall at the cross
                                          # hole's arm ends), stem below the skirt
    stems_y=(0.0,),                       # switch stems' y (tall caps: one per switch, see tall_params)
    cross=(4.10, 1.20),                   # switch cross hole (KS-33 cross 4.00 x 1.10; 0.2 nozzle FDM)
    stab_x=12.0, stab_rise=1.25,          # KS-57 stems at +-12, cross 1.25 higher than the switch's
    stab_cross=(4.00, 1.10), stab_cross_top=2.95, # KS-57 cross 3.90 x 1.00, top at cap z 2.95 when seated
    stab_recess=(3.4, -4.9, 4.6, 3.0),    # ceiling recess over each KS-57 housing (top 6.55 above the PCB):
                                          # half width, y from / to, flat top at cap z (0.3 clear bottomed out)
)


def top_frame(p):
    """Location of the sloped top plane (origin above the key centre at h_centre)."""
    return Pos(0, 0, p['h_centre']) * Rot(p['slope'], 0, 0)


def flat_r(p):
    """Radius of the flat valley floor ('flat' style: the thumb caps)."""
    return p['flat_r']


def valley_z(p, r):
    """Top surface height (top frame) at radius r (y direction): flat, smoothstep, plane."""
    r0, r1 = flat_r(p), p['valley_r']
    if p.get('valley_style') == 'dish':          # level at the centre and at valley_r
        u = min(abs(r) / r1, 1.0)
        return -p['valley'] * (1 - u * u) ** 2
    if r <= r0: return -p['valley']
    if r >= r1: return 0.0
    u = (r - r0) / (r1 - r0)
    return -p['valley'] * (1 - (3 * u * u - 2 * u ** 3))


def valley_tool(p, sx):
    """Solid above the valley surface (revolved profile, stretched sx in x), in the top frame."""
    r0, r1, R = flat_r(p), p['valley_r'], p['valley_r'] * 3
    st = (sx, 1, 1) if sx >= 1 else (1, 1 / sx, 1)   # wide caps stretch in x, tall caps in y
    if p.get('valley_style') == 'dish':
        pts = [(r1 * k / 24, 0, valley_z(p, r1 * k / 24)) for k in range(25)]
        w = Wire([Spline(*pts, tangents=((1, 0, 0), (1, 0, 0))),
                  Line((r1, 0, 0), (R, 0, 0)), Line((R, 0, 0), (R, 0, 10)),
                  Line((R, 0, 10), (0, 0, 10)), Line((0, 0, 10), (0, 0, -p['valley']))])
        return scale(revolve(Face(w), Axis.Z), st)
    pts = [(r0 + (r1 - r0) * k / 16, 0, valley_z(p, r0 + (r1 - r0) * k / 16)) for k in range(17)]
    w = Wire([Line((0, 0, -p['valley']), (r0, 0, -p['valley'])),
              Spline(*pts, tangents=((1, 0, 0), (1, 0, 0))),
              Line((r1, 0, 0), (R, 0, 0)), Line((R, 0, 0), (R, 0, 10)),
              Line((R, 0, 10), (0, 0, 10)), Line((0, 0, 10), (0, 0, -p['valley']))])
    return scale(revolve(Face(w), Axis.Z), st)


def z_ceiling(p):
    """Cavity ceiling, in the top frame (below the top plane)."""
    return p['ceiling']


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


def thumb_profile(p, D):
    """Top of a thumb cap: one north-south profile (cap frame, (y, z)), straight east-west (user: no
    valley in the east-west line). South to north: a line meeting the south skirt thumb_meet high at
    thumb_angle, an arc tangent to it and to the flat centre's plane, the flat band (its level,
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
    n1 = (sn, -cs)                                            # into the cap, normal to the flat centre's plane
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
    y-z section at the key centre an arc tangent to the flat centre's plane at the flat centre's south edge,
    then a short line meeting the south skirt thumb_meet high at thumb_angle; every east-west slice
    is that profile scaled so it starts at the top surface's own height on the start line (continuous
    with the valley) and ends on the skirt's bottom edge: z(x, y) = arc(y) * (1 + rise(x) / z_start).
    Starts 0.002 above the top (no step face)."""
    sl, dr = math.radians(p['slope']), math.radians(p['draft'])
    z_ins = p['h_centre'] - p['valley']                       # flat centre's plane at y = 0
    t1 = (-flat_r(p), z_ins - flat_r(p) * math.tan(sl))       # tangent point on the flat centre's plane
    n1 = (math.sin(sl), -math.cos(sl))                        # into the cap, normal to the flat centre's plane
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
    # each east-west slice starts at the top's own height (flat level + rise) and still ends on the
    # skirt's bottom edge (user: no skirt left on the south side): the arc scaled per slice
    # (the 0.002 start offset fades out towards the bottom)
    if not scaled:                                            # (earlier form: raised by the valley)
        return [[(x, y, arc(y) + rise(x) + 0.002) for x in xs] for y in ys]
    return [[(x, y, arc(y) * (1 + rise(x) / t1[1]) + 0.002 * max(arc(y), 0) / t1[1]) for x in xs] for y in ys]


def top_points(p, W, D, sx, nx=49, ny=49):
    """Grid points (rows at one cap-frame y each, cap frame) of the whole top for valley_style 'dish':
    the sloped plane minus the dish minus the north roll-off, added up (user: no edge where the dish
    met the roll-off; separate cuts take the lower of the two and leave a ridge). Both dips are level
    where they start, so the sum is smooth everywhere."""
    sl = math.radians(p['slope'])
    t = math.tan(math.radians(p['draft']))
    d_top = D - 2 * p['h_centre'] * t
    L, drop = p['fade_len'], p['fade_drop']
    Rf, yf = L * L / (2 * drop), d_top / 2 - L
    def zt(x, yt):                               # top-frame height at top-frame (x, yt)
        z = valley_z(p, math.hypot(x / sx, yt) if sx >= 1 else math.hypot(x, yt * sx))
        if yt > yf:
            z -= Rf - math.sqrt(max(Rf * Rf - (yt - yf) ** 2, 0))
        return z
    xs = [-W / 2 - 1.5 + (W + 3) * k / (nx - 1) for k in range(nx)]
    ys = [-D / 2 - 1.5 + (D + 3) * k / (ny - 1) for k in range(ny)]
    rows = []
    for y in ys:
        row = []
        for x in xs:
            yt = y / math.cos(sl)
            for _ in range(6):                   # cap y = yt cos - z sin: solve for yt
                yt = (y + zt(x, yt) * math.sin(sl)) / math.cos(sl)
            z = zt(x, yt)
            row.append((x, y, p['h_centre'] + yt * math.sin(sl) + z * math.cos(sl)))
        rows.append(row)
    return rows


def top_tool(p, W, D, sx):
    """Solid above the 'dish' top surface (top_points)."""
    return extrude(Face.make_surface_from_array_of_points(top_points(p, W, D, sx), tol=1e-4), amount=15, dir=(0, 0, 1))


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


def wall_inside(u, p=P):
    """The solid inside the skirt walls (the skirt offset inwards by the wall), from below the skirt
    bottom to above the top: the cavity before the ceiling cut."""
    W, D = u * p['pitch'] - p['gap'], p['depth']
    t = math.tan(math.radians(p['draft']))
    H = p['h_centre'] + D / 2 * math.tan(math.radians(p['slope'])) + 2
    inset, tw = H * t, p['wall'] / math.cos(math.radians(p['draft']))
    return loft([Pos(0, 0, -1) * RectangleRounded(W - 2 * tw + 2 * t, D - 2 * tw + 2 * t, p['r_inner']),
                 Pos(0, 0, H) * RectangleRounded(W - 2 * tw - 2 * inset, D - 2 * tw - 2 * inset,
                                                 max(p['r_inner'] - (H + 1) * t, 0.05))])


def cap_params(thumb=False, tall=False, p=P):
    """The parameters a cap is built with: thumb caps get the flat centre their roll-down starts from,
    tall caps tall_params()."""
    if thumb:
        p = dict(p, valley_style='flat', valley=p['thumb_valley'])
    return tall_params(p) if tall else p


def build_cap(u, stab=False, thumb=False, p=P):
    """The monolithic cap (p from cap_params())."""
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
        # top: sloped plane (dish tops: part of the one top surface; a plane cut too leaves coincident faces)
        dish = p.get('valley_style') == 'dish' and not thumb
        cap = outer if dish else outer - tf * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # north roll-off: a cylinder (axis x) tangent to the top plane fade_len inside the north edge
        L, drop = p['fade_len'], p['fade_drop']
        Rf = L * L / (2 * drop)
        yf = d_top / 2 - L
        roll = (Pos(0, yf, -Rf) * Box(big, 30, 40, align=(Align.CENTER, Align.MIN, Align.MIN))
                - Pos(0, yf, -Rf) * Rot(0, 90, 0) * Cylinder(Rf, big))
        if dish:                                 # one smooth surface: plane - dish - roll-off
            cap = cap - top_tool(p, W, D, w_top / d_top)
        else:
            cap = cap - tf * roll
            # valley: flat floor, rising smoothly to the top plane (stretched in x on wide caps)
            cap = cap - tf * valley_tool(p, w_top / d_top)
        if thumb:                                # 'valley' thumb: the south part rolls down from the flat
            cap = cap - thumb_valley_tool(p, W, D, w_top / d_top, u in p['thumb_scaled_units'])
    z_ceil = z_ceiling(p)
    # inside: the skirt offset by the wall, up to the ceiling (parallel to the top; tall caps: level at the
    # centre's height, as a sloped one would come down onto the south switch's housing); cavity=False: none
    ceil_c = p['h_centre'] + z_ceil                  # ceiling at the key centre (cap z)
    cf = (lambda dz: Pos(0, 0, ceil_c + dz)) if p.get('ceiling_level') else (lambda dz: tf * Pos(0, 0, z_ceil + dz))
    inner = wall_inside(u, p) - cf(0) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if p.get('cavity', True):
        cap = cap - inner
    if stab:
        hw, y0, y1, zr = p['stab_recess']
        for x in (-p['stab_x'], p['stab_x']):
            cap = cap - Pos(x, (y0 + y1) / 2, 0) * Box(2 * hw, y1 - y0, zr, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # stems: down to -stem_drop (switch) / -stem_drop + stab_rise (stabilizer), up into the ceiling
    def stem(x, bottom, cross, cross_top, top=None, y=0.0):
        st = Pos(x, y, bottom) * Cylinder(p['stem_d'] / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        st = st - (Pos(0, 0, top) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)) if top is not None
                   else cf(0.5) * Box(big, big, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        hole = (Pos(x, y, bottom - 1) * Box(cross[0], cross[1], cross_top - bottom + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
                + Pos(x, y, bottom - 1) * Box(cross[1], cross[0], cross_top - bottom + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        return st, hole
    parts = [stem(0, -p['stem_drop'], p['cross'], ceil_c, y=y) for y in p['stems_y']]
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


# folders (user 2026-11-09): keycaps/build = the scripts + work/ (generated, not in git); keycaps/results =
# the models (print 3MF, Fusion .f3d) and profiles/ (Bambu presets), in git
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
CAPS_DIR = os.path.join(WORK, 'caps')                  # build123d STEP + the Fusion recipes
FUSION_DIR = os.path.join(WORK, 'fusion')              # Fusion's STEP and 3MF (the print 3MF's mesh source)
RESULTS = os.path.join(os.path.dirname(HERE), 'results')
PROFILES = os.path.join(RESULTS, 'profiles')


def cap_name(u, stab=False, thumb=False, tall=False):
    return 'cap_%gu%s%s%s' % (u, '_tall' if tall else '', '_stab' if stab else '', '_thumb' if thumb else '')


def parse_units(spec):
    """'2st' -> (2.0, stab, thumb, tall): s = stabilizer stems, t = thumb, v = tall."""
    return float(spec.rstrip('stv')), 's' in spec, 't' in spec, 'v' in spec


def tall_params(p=P, rows=2):
    """A cap over `rows` switches of one column (user 2026-11-08: 2U tall, one stem on each switch):
    rows * pitch - gap deep, a stem every pitch along y, the ceiling level at the centre's height (one
    parallel to the sloped top came down onto the south switch's housing at 2.7 mm travel). The top
    (dish stretched in y) and walls are the usual ones on the longer outline."""
    return dict(p, depth=rows * p['pitch'] - p['gap'], ceiling_level=True,
                stems_y=tuple((k - (rows - 1) / 2) * p['pitch'] for k in range(rows)))


def get_cap(u, stab=False, thumb=False, tall=False, p=P):
    """The blank cap as used by the fit checks: Fusion's export (build/work/fusion/<cap>_blank.step,
    KeycapBuilder) when cap_source is 'fusion' and the file is there, else build_cap(). Returns (shape, source)."""
    f = os.path.join(FUSION_DIR, '%s_blank.step' % cap_name(u, stab, thumb, tall))
    if p['cap_source'] == 'fusion' and os.path.exists(f):
        from build123d import import_step
        return import_step(f).solids()[0], 'fusion'
    return build_cap(u, stab, thumb, cap_params(thumb, tall, p)), 'build123d'


def recipe(u, stab=False, thumb=False, p=P):
    """Every number the Fusion builder (keycaps/build/fusion/KeycapBuilder) needs for one cap, in mm in the
    cap frame, mirroring build_cap step by step (each step becomes a timeline feature there);
    p from cap_params()."""
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
    z_ceil = z_ceiling(p)
    tw = p['wall'] / math.cos(math.radians(p['draft']))
    ceil_c = p['h_centre'] + z_ceil
    stems = [{'x': 0, 'y': y, 'bottom': -p['stem_drop'], 'top': ceil_c + 0.5, 'cross': list(p['cross']), 'cross_top': ceil_c}
             for y in p['stems_y']]
    if stab:
        for x in (-p['stab_x'], p['stab_x']):
            stems.append({'x': x, 'y': 0, 'bottom': -p['stem_drop'] + p['stab_rise'], 'top': p['stab_recess'][3] + 0.5,
                          'cross': list(p['stab_cross']), 'cross_top': p['stab_cross_top'] + 0.35})
    r = {'u': u, 'stab': stab, 'thumb': thumb, 'W': W, 'D': D, 'H': H,
         'skirt': {'r': p['r_bottom'], 'draft': p['draft'], 'square_south': thumb},
         'top': {'h_centre': p['h_centre'], 'slope': p['slope']},
         'roll': roll,
         'valley': {'flat': [0, -p['valley'], r0], 'profile': vprof, 'R': r1 * 3, 'sx': w_top / d_top},
         'z_ceil': z_ceil, 'ceiling_level': bool(p.get('ceiling_level')),   # (level: a horizontal plane at
                                                                           # the centre's ceiling height)
         'cavity': {'w': W - 2 * tw + 2 * t, 'd': D - 2 * tw + 2 * t, 'r': p['r_inner']},
         'recess': ([[x, (p['stab_recess'][1] + p['stab_recess'][2]) / 2, 2 * p['stab_recess'][0],
                      p['stab_recess'][2] - p['stab_recess'][1], p['stab_recess'][3]] for x in (-p['stab_x'], p['stab_x'])]
                    if stab else []),
         'stems': stems, 'stem_r': p['stem_d'] / 2,
         'fillet': (p['thumb_fillet'] if u in p['thumb_fillet_units'] else 0) if thumb else p['top_fillet']}
    if p.get('valley_style') == 'dish' and not thumb:   # (one loft cut instead of roll + valley)
        r['roll'], r['valley'] = None, None
        r['top_surface'] = top_points(p, W, D, w_top / d_top, nx=33, ny=33)
    if thumb:
        r['thumb'] = (thumb_profile(p, D) if p['thumb_style'] == 'straight' else
                      thumb_points(p, W, D, w_top / d_top, nx=33, ny=9, scaled=u in p['thumb_scaled_units']))
        r['thumb_style'] = p['thumb_style']
    return r
