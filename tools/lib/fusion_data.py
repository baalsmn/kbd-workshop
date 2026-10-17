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

def main():
    cases_json, outlines_dir, out_json, name = sys.argv[1:5]
    cases = json.load(open(cases_json))
    parts = sys.argv[5:] or list(cases)
    cases = {p: cases[p] for p in parts if p in cases}
    names = sorted({it['name'] for r in cases.values() for it in r})
    outlines = {n: outline(os.path.join(outlines_dir, n + '.dxf')) for n in names}
    json.dump({'design': name, 'units': 'mm', 'cases': cases, 'outlines': outlines}, open(out_json, 'w'), separators=(',', ':'))
    print('%s: %d parts, %d outlines, %d loops, %d segments -> %s' % (
        name, len(cases), len(outlines), sum(len(v) for v in outlines.values()),
        sum(len(l['segs']) for v in outlines.values() for l in v), out_json))

if __name__ == '__main__':
    main()
