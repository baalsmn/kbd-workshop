# Data file for the Fusion script (tools/fusion/KeyboardCase): every outline used
# by the case parts as closed loops of lines / 3-point arcs / circles (mm), with
# each loop's nesting depth and bounding box, plus the cases recipe.
#
# Usage: python fusion_data.py <cases.json> <outlines dir> <out.json> <design name>
# Loops are chained with build123d (same snapping as step_case.py), so the Fusion
# sketches close exactly like the STEP solids.
import sys, os, json, math
if '__file__' in globals(): sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step_case import dxf_edges
from build123d import Wire
from step_case import outline_face

def pt(v): return [round(v.X, 5), round(v.Y, 5)]

def loop_data(w):
    segs, poly = [], []
    for e in w.edges():
        a, b, m = e.position_at(0), e.position_at(1), e.position_at(0.5)
        t = e.geom_type.name if hasattr(e.geom_type, 'name') else str(e.geom_type)
        if t == 'LINE': segs.append({'t': 'L', 'p': [pt(a), pt(b)]})
        elif (a - b).length < 1e-6:                     # full circle
            c = e.arc_center; segs.append({'t': 'C', 'c': pt(c), 'r': round(e.radius, 5)})
        else: segs.append({'t': 'A', 'p': [pt(a), pt(m), pt(b)]})
        n = 1 if t == 'LINE' else 24
        poly += [pt(e.position_at(i / n)) for i in range(n)]
    b = w.bounding_box(optimal=True)                    # exact (arc extremes too), matched to Fusion's profile boxes
    return segs, poly, [b.min.X, b.min.Y, b.max.X, b.max.Y]

def inside(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c

def outline(path):
    edges = dxf_edges(path)
    if not edges: return []
    loops = []
    for w in Wire.combine(edges, tol=1e-3):
        if not w.is_closed: raise RuntimeError(f'open loop in {os.path.basename(path)}')
        loops.append(loop_data(w))
    out = []
    for i, (segs, poly, bb) in enumerate(loops):
        # depth = how many other loops contain this one (even = filled, odd = hole)
        depth = sum(1 for j, (_, q, qb) in enumerate(loops) if j != i
                    and qb[0] <= bb[0] and qb[1] <= bb[1] and qb[2] >= bb[2] and qb[3] >= bb[3] and inside(poly[0], q))
        out.append({'depth': depth, 'bbox': [round(v, 4) for v in bb], 'segs': segs})
    return out

def key_rects(outlines_dir):
    """Switch cutouts (+ the stabilizer cutouts of their key) as rectangles in each
    key's frame: [cx, cy, angle_deg, x0, y0, x1, y1] (mm). The Fusion script grows
    them into the relief gap and the rib frame around each switch."""
    sw = outline(os.path.join(outlines_dir, 'switches_outline.dxf'))
    keys = []
    for l in sw:
        q = [s['p'][0] for s in l['segs'] if s['t'] == 'L']
        if len(q) != 4: continue
        cx, cy = sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4
        a = math.atan2(q[1][1] - q[0][1], q[1][0] - q[0][0])
        a = (a + math.pi / 4) % (math.pi / 2) - math.pi / 4      # the key's own angle (square: any edge)
        keys.append([cx, cy, a, [1e9, 1e9, -1e9, -1e9]])
    def grow(k, pts):
        ca, sa = math.cos(k[2]), math.sin(k[2]); b = k[3]
        for x, y in pts:
            u, v = (x - k[0]) * ca + (y - k[1]) * sa, -(x - k[0]) * sa + (y - k[1]) * ca
            b[0], b[1], b[2], b[3] = min(b[0], u), min(b[1], v), max(b[2], u), max(b[3], v)
    for l, k in zip(sw, keys): grow(k, [s['p'][0] for s in l['segs']])
    st = os.path.join(outlines_dir, 'stab_cutouts.dxf')
    for l in (outline(st) if os.path.exists(st) else []):
        pts = [p for s in l['segs'] for p in s['p']]
        c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        grow(min(keys, key=lambda k: math.hypot(k[0] - c[0], k[1] - c[1])), pts)
    return [[round(k[0], 4), round(k[1], 4), round(math.degrees(k[2]), 4)] + [round(v, 4) for v in k[3]] for k in keys]

def rib_region(outlines_dir, inset=0.5):
    """PCB outline shrunk by `inset`: the ribs stay above the PCB, clear of the tub wall."""
    from build123d import offset
    f = outline_face(os.path.join(outlines_dir, 'pcb_outline.dxf'))
    g = offset(f, amount=-inset)
    out = []
    for face in g.faces():
        out.append({'depth': 0, 'bbox': [], 'segs': loop_data(face.outer_wire())[0]})
        out += [{'depth': 1, 'bbox': [], 'segs': loop_data(w)[0]} for w in face.inner_wires()]
    return out

def main():
    cases_json, outlines_dir, out_json, name = sys.argv[1:5]
    cases = json.load(open(cases_json))
    parts = sys.argv[5:] or list(cases)
    cases = {p: cases[p] for p in parts if p in cases}
    names = sorted({it['name'] for r in cases.values() for it in r})
    outlines = {n: outline(os.path.join(outlines_dir, n + '.dxf')) for n in names}
    data = {'design': name, 'units': 'mm', 'cases': cases, 'outlines': outlines}
    # optional plate ribs (Fusion script; not when the design's lids already have them): key rectangles, region, plate z and gap to the PCB
    lid = cases.get('lid_left') or []
    if lid and not any(i['name'] == 'plate_ribs' for i in lid) and os.path.exists(os.path.join(outlines_dir, 'switches_outline.dxf')):
        plate = lid[0]; z = (list(plate.get('shift') or []) + [0, 0, 0])[2]
        under = [(list(i.get('shift') or []) + [0, 0, 0])[2] for i in lid[1:] if i.get('operation', 'add') == 'add']
        data['rib'] = {'plate_z': z, 'pcb_top': min(under) if under else z - 1.3, 'plate_holes': plate['name'],
                       'keys': key_rects(outlines_dir), 'region': rib_region(outlines_dir)}
    json.dump(data, open(out_json, 'w'), separators=(',', ':'))
    print('%s: %d parts, %d outlines, %d loops, %d segments, %s -> %s' % (
        name, len(cases), len(outlines), sum(len(v) for v in outlines.values()),
        sum(len(l['segs']) for v in outlines.values() for l in v),
        ('ribs: %d keys, plate z %.2f, gap %.2f' % (len(data['rib']['keys']), data['rib']['plate_z'],
         data['rib']['plate_z'] - data['rib']['pcb_top'])) if 'rib' in data else 'no ribs', out_json))

if __name__ == '__main__':
    main()
