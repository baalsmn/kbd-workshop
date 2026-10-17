# Usage (KiCad python, after tools/build.sh): python tools/lib/crosses.py out/pcbs/<name>.kicad_pcb out/points/points.yaml crosses_yaml.txt
# Prints the arm lengths and writes the cross_lower / cross_upper rectangle lists to paste into the design yaml (the crosses list below is kugo82's).
# Support crosses: 2 mm walls along the key gaps at a switch corner crossing.
# lower = floor -> PCB bottom (avoid back parts, socket bodies, cutouts, posts)
# upper = plate -> PCB top   (avoid switch bodies, stab housings/cutouts, front pads, spacers)
# Arm length = how far the 2 mm wall runs (max 9 mm) before coming within 0.3 mm of
# an obstacle (max 5 mm, user's choice), the same on both halves (mirrored). Arms < 2 mm are dropped.
import sys, math, re, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
HALF, CLR, LMAX, LMIN, STEP = 1.0, 0.3, 5.0, 2.0, 0.25

def segdist(p, a, c):
    ax, ay = a; cx, cy = c; px, py = p; dx, dy = cx-ax, cy-ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)
def polydist(p, poly):
    inside = False; d = 1e9
    for i in range(len(poly)):
        a, c = poly[i], poly[(i+1) % len(poly)]; d = min(d, segdist(p, a, c))
        if (a[1] > p[1]) != (c[1] > p[1]) and p[0] < (c[0]-a[0])*(p[1]-a[1])/(c[1]-a[1])+a[0]: inside = not inside
    return 0 if inside else d
def outline(sp):
    o = sp.Outline(0); return [(o.CPoint(j).x/1e6, o.CPoint(j).y/1e6) for j in range(o.PointCount())]

back, front = [], []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        for layer, lst in ((pcbnew.B_Cu, back), (pcbnew.F_Cu, front)):
            if pad.IsOnLayer(layer):
                sp = pad.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
                for k in range(sp.OutlineCount()):
                    o = sp.Outline(k); lst.append([(o.CPoint(j).x/1e6, o.CPoint(j).y/1e6) for j in range(o.PointCount())])
    if fp.IsFlipped() and fp.GetReference()[0] in 'CDLRM':
        cy = fp.GetCourtyard(pcbnew.B_CrtYd)
        if cy.OutlineCount(): back.append(outline(cy))
    if not fp.IsFlipped() and fp.GetReference().startswith('DISP'):
        pass
# switch footprints: socket body (back) and switch body (front), from the two socket pads
sw_front = []
for fp in b.GetFootprints():
    r = fp.GetReference()
    if not (r.startswith('S') and r[1:].isdigit()): continue
    P0 = (fp.GetPosition().x/1e6, fp.GetPosition().y/1e6)
    pads = {p.GetNumber(): (p.GetPosition().x/1e6, p.GetPosition().y/1e6) for p in fp.Pads() if p.GetNumber() in ('1', '2')}
    L1, L2 = (-8.2, 4.7), (6.35, 5.75)
    best = None
    for s in (1, -1):
        for th10 in range(0, 3600):
            th = math.radians(th10/10)
            def T(l, s=s, th=th): x, y = s*l[0], l[1]; return (P0[0] + x*math.cos(th) - y*math.sin(th), P0[1] + x*math.sin(th) + y*math.cos(th))
            e = math.hypot(*[a-b for a, b in zip(T(L1), pads['1'])]) + math.hypot(*[a-b for a, b in zip(T(L2), pads['2'])])
            if best is None or e < best[0]: best = (e, s, th)
    _, s, th = best
    T = lambda l: (P0[0] + s*l[0]*math.cos(th) - l[1]*math.sin(th), P0[1] + s*l[0]*math.sin(th) + l[1]*math.cos(th))
    back.append([T(q) for q in ((-8.6, 2.3), (6.8, 2.3), (6.8, 8.1), (-8.6, 8.1))])        # socket body
    sw_front.append([T(q) for q in ((-7.05, -7.05), (7.05, -7.05), (7.05, 7.05), (-7.05, 7.05))])  # switch under the plate
# cutouts (board + footprint Edge.Cuts) and the PCB outline
cuts = []
def add_shape(it):
    sh = it.GetShapeStr()
    if sh == 'Rect':
        pts = [(q.x/1e6, q.y/1e6) for q in it.GetCorners()]
    elif sh == 'Polygon':
        pts = outline(it.GetPolyShape())
    elif sh == 'Circle':
        c = (it.GetCenter().x/1e6, it.GetCenter().y/1e6); rr = it.GetRadius()/1e6
        pts = [(c[0] + rr*math.cos(a/16*math.pi), c[1] + rr*math.sin(a/16*math.pi)) for a in range(32)]
    else:
        cuts.append([(it.GetStart().x/1e6, it.GetStart().y/1e6), (it.GetEnd().x/1e6, it.GetEnd().y/1e6)]); return
    cuts.append(pts)
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, False); outer = outline(ps)
for d in b.GetDrawings():
    if d.GetLayerName() == 'Edge.Cuts' and d.GetShapeStr() == 'Circle': add_shape(d)   # screw holes
for fp in b.GetFootprints():
    for it in fp.GraphicalItems():
        if it.GetLayerName() == 'Edge.Cuts': add_shape(it)
screws = [((d.GetCenter().x/1e6, d.GetCenter().y/1e6)) for d in b.GetDrawings() if d.GetLayerName() == 'Edge.Cuts' and d.GetShapeStr() == 'Circle' and abs(d.GetRadius()/1e6 - 1.2) < 0.01]

def dmin(p, polys): return min(polydist(p, q) if len(q) > 2 else segdist(p, q[0], q[1]) for q in polys)
def free(p, layer):
    if polydist(p, outer) > 0: return False
    edge = min(segdist(p, outer[k], outer[(k+1) % len(outer)]) for k in range(len(outer)))
    if edge < HALF + CLR: return False
    if dmin(p, cuts) < HALF + CLR: return False
    if min(math.hypot(p[0]-q[0], p[1]-q[1]) for q in screws) < 2.75 + HALF + CLR: return False
    if layer == 'lower': return dmin(p, back) >= HALF + CLR
    return dmin(p, sw_front) >= HALF + CLR and dmin(p, front) >= HALF + CLR

P = {}; cur = None
for l in open(sys.argv[2]).read().split('\n'):
    m = re.match(r'^(hand-zone_c\d_r\d):', l)
    if m: cur = m.group(1); P[cur] = {}; continue
    if re.match(r'^\S', l): cur = None
    if cur:
        m = re.match(r"^    (x|'y'|r): ([-\d.e]+)", l)
        if m: P[cur][m.group(1).strip("'")] = float(m.group(2))
# mirror axis from the points: midpoint of the c9_r2 pair (works for any design / sheet position)
_pts = open(sys.argv[2]).read()
_mx = float(re.search(r"^mirror_hand-zone_c9_r2:\s*\n\s+x: ([-\d.e]+)", _pts, re.M).group(1))
X2 = P["hand-zone_c9_r2"]["x"] + _mx
def to_board(key, lx, ly):
    k = P['hand-zone_' + key]; a = math.radians(k['r'])
    return (k['x'] + lx*math.cos(a) - ly*math.sin(a), -(k['y'] + lx*math.sin(a) + ly*math.cos(a)))

SP = 19.0
crosses = [('c1_r1', 0.5, 0.5), ('c1_r3', 0.5, 0.5), ('c4_r1', 0.5, 0.5), ('c4_r3', 0.5, 0.5), ('c4_r4', 0.5, 0.5),
           ('c7_r1', 0.0, 0.5), ('c8_r3', 0.5, 0.5)]
dirs = {'E': (1, 0), 'N': (0, 1), 'W': (-1, 0), 'S': (0, -1)}
result = []
for key, fx, fy in crosses:
    cx, cy = fx*SP, fy*SP
    row = {'key': key, 'c': (cx, cy)}
    for layer in ('lower', 'upper'):
        arms = {}
        ok_c = all(free(p, layer) for p in (to_board(key, cx, cy), (X2 - to_board(key, cx, cy)[0], to_board(key, cx, cy)[1])))
        if ok_c:
            for dn, (ux, uy) in dirs.items():
                L = 0.0; t = STEP
                while t <= LMAX + 1e-9:
                    pl = to_board(key, cx + ux*t, cy + uy*t); pm = (X2 - pl[0], pl[1])
                    if free(pl, layer) and free(pm, layer): L = t; t += STEP
                    else: break
                if L >= LMIN: arms[dn] = L
        row[layer] = (ok_c, arms)
    result.append(row)
    def fmt(v): ok, a = v; return ('centre blocked' if not ok else (' '.join('%s %.2f' % (k, x) for k, x in a.items()) or 'no arm >= 2 mm'))
    print('%-6s corner [%5.1f, %5.1f]  lower: %-38s upper: %s' % (key, cx, cy, fmt(row['lower']), fmt(row['upper'])))

# YAML for the two outlines (rectangles in the key frame, one entry per half)
def yaml(layer):
    out = []
    for r in result:
        ok, arms = r[layer]
        if not ok or not arms: continue
        cx, cy = r['c']
        parts = [('2, 2', cx, cy)]
        for dn, L in arms.items():
            ux, uy = dirs[dn]
            if ux: parts.append(('%.2f, 2' % (L + 1), cx + ux*(L - 1)/2 + ux*1, cy) if False else ('%.2f, 2' % L, cx + ux*L/2, cy))
            else: parts.append(('2, %.2f' % L, cx, cy + uy*L/2))
        for m in ('', 'mirror_'):
            for size, x, y in parts:
                out.append('    - what: rectangle\n      size: [%s]\n      where:\n        ref: %shand-zone_%s\n        shift: [%.3f, %.3f]' % (size, m, r['key'], x, y))
    return '\n'.join(out)
open(sys.argv[3], 'w').write('LOWER\n' + yaml('lower') + '\nUPPER\n' + yaml('upper') + '\n')
