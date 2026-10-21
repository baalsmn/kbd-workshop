# SVG artwork (paths only: export text as outlines) -> KiCad silkscreen footprint
# (KiCad python + shapely, e.g. the KiKit venv %LOCALAPPDATA%/kugo-kikit).
# Every closed sub-path becomes a loop; loops inside loops are holes (non-zero / even-odd
# artwork alike: nesting depth decides), and each filled shape with its holes is written
# as one fp_poly, the holes joined to the outline by hairline slits (KiCad graphic polygons
# have no holes). The footprint origin is the artwork's top centre, so it can be placed
# straight below an edge.
# Usage:
#   python tools/lib/svg_logo.py <art.svg> <height mm> <out.kicad_mod> [--layer F.SilkS]
#   [--samples 16] (points per curve)
#   [--thicken 0.03 --small 0.15 --below 0.8]: grow the small shapes (height under --small of
#   the logo, centre in its lowest 1 - --below part, e.g. a line of fine text) by --thicken mm
#   on every side, so their strokes stay above the silkscreen minimum
import sys, argparse, re, math, uuid
from shapely.geometry import Polygon
sys.path.insert(0, __import__('os').path.dirname(__file__))
from svg_outline import path_points

ap = argparse.ArgumentParser()
ap.add_argument('svg'); ap.add_argument('height', type=float); ap.add_argument('out')
ap.add_argument('--layer', default='F.SilkS'); ap.add_argument('--samples', type=int, default=16)
ap.add_argument('--thicken', type=float, default=0.0); ap.add_argument('--small', type=float, default=0.15)
ap.add_argument('--below', type=float, default=0.8)
A = ap.parse_args()
svg = open(A.svg, encoding='utf-8').read()
ds = re.findall(r'\sd="([^"]+)"', svg)
loops = []
for d in ds: loops += path_points(d, A.samples)
polys = [Polygon(l).buffer(0) for l in loops if len(l) >= 3]
polys = [p for p in polys if p.area > 1e-6]
# nesting depth: how many other loops contain this one; even = filled, odd = hole
depth = [sum(1 for j, q in enumerate(polys) if j != i and q.contains(p.representative_point()) and q.area > p.area) for i, p in enumerate(polys)]
shapes = []
for i, p in enumerate(polys):
    if depth[i] % 2: continue
    holes = [q for j, q in enumerate(polys) if depth[j] == depth[i] + 1 and p.contains(q.representative_point())]
    s = p
    for h in holes: s = s.difference(h)
    shapes.append(s)
x0 = min(s.bounds[0] for s in shapes); x1 = max(s.bounds[2] for s in shapes)
y0 = min(s.bounds[1] for s in shapes); y1 = max(s.bounds[3] for s in shapes)
k = A.height / (y1 - y0); cx = (x0 + x1) / 2
if A.thicken:
    from shapely.ops import unary_union
    from shapely.geometry import Polygon as _P
    grown = [i for i, sh in enumerate(shapes)
             if (sh.bounds[3] - sh.bounds[1]) < A.small * (y1 - y0) and (sh.bounds[1] + sh.bounds[3]) / 2 > y0 + A.below * (y1 - y0)]
    orig = {i: shapes[i] for i in grown}
    gap = 0.1 / k                                   # keep 0.1 mm between neighbouring letters
    for i in grown:
        g = orig[i].buffer(A.thicken / k, join_style=2, mitre_limit=2.0)
        for part in getattr(orig[i], 'geoms', [orig[i]]):     # counters keep their original size
            for h in part.interiors: g = g.difference(_P(h))
        others = unary_union([orig[j] for j in grown if j != i])
        # trim against the neighbours' grown size so the final gap is >= 0.1 mm wherever the
        # artwork had that much; the letter's own original outline is always kept
        if not others.is_empty: g = g.difference(others.buffer(gap + A.thicken / k, join_style=2, mitre_limit=2.0)).union(orig[i])
        shapes[i] = g
    print('thickened %d small shape(s) by %.3f mm per side' % (len(grown), A.thicken))
T = lambda x, y: (round((x - cx) * k, 4), round((y - y0) * k, 4))     # origin: top centre, mm
def keyhole(poly):
    """outline with its holes joined by zero-width slits, as one point list."""
    ext = list(poly.exterior.coords)[:-1]
    for h in sorted(poly.interiors, key=lambda r: -max(c[0] for c in r.coords)):
        hc = list(h.coords)[:-1]
        hi = max(range(len(hc)), key=lambda i: hc[i][0])       # rightmost hole point
        ei = min(range(len(ext)), key=lambda i: (ext[i][0] - hc[hi][0]) ** 2 + (ext[i][1] - hc[hi][1]) ** 2 if ext[i][0] >= hc[hi][0] else 1e18)
        ring = hc[hi:] + hc[:hi] + [hc[hi]]
        ext = ext[:ei + 1] + ring + ext[ei:]
    return ext
polys_out = []
for s in shapes:
    for g in getattr(s, 'geoms', [s]):
        polys_out.append(keyhole(g))
name = re.sub(r'\.kicad_mod$', '', A.out.replace('\\', '/').split('/')[-1])
lines = ['(footprint "%s"' % name, '  (version 20241229)', '  (generator "svg_logo.py")', '  (layer "F.Cu")',
         '  (descr "%s, %.1f x %.1f mm, from %s")' % (name, (x1 - x0) * k, A.height, A.svg.replace('\\', '/').split('/')[-1]),
         '  (attr board_only exclude_from_pos_files exclude_from_bom allow_missing_courtyard)',
         '  (property "Reference" "LOGO1" (at 0 -1 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))' % uuid.uuid4(),
         '  (property "Value" "%s" (at 0 %.2f 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))' % (name, A.height + 1, uuid.uuid4())]
for pts in polys_out:
    xy = ' '.join('(xy %s %s)' % T(x, y) for x, y in pts)
    lines.append('  (fp_poly (pts %s) (stroke (width 0) (type solid)) (fill yes) (layer "%s") (uuid "%s"))' % (xy, A.layer, uuid.uuid4()))
lines.append(')')
open(A.out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
# thinnest feature (a feature of width w survives a -w/2 buffer): estimate stroke and gap
minw = None
for w in (0.10, 0.12, 0.15, 0.18, 0.20, 0.25):
    lost = sum(1 for s in shapes for g in getattr(s, 'geoms', [s]) if g.buffer(-w / 2 / k).is_empty)
    if lost: minw = w; break
print('%s: %d filled shapes, %d holes, %.2f x %.2f mm -> %s' % (name, len(shapes), sum(len(g.interiors) for s in shapes for g in getattr(s, 'geoms', [s])), (x1 - x0) * k, A.height, A.out))
print('narrowest stroke: %s' % ('under %.2f mm (%d shape(s) vanish)' % (minw, lost) if minw else 'over 0.25 mm'))
