# GND stitching vias for a two-layer board with a GND pour on both layers
# (KiCad python + shapely, e.g. the KiKit venv %LOCALAPPDATA%/kugo-kikit).
# The back-side pour is cut into strips by the row lines, trunks and key links; a strip
# with no via is a separate piece (or, with island removal on, gets dropped). This
# fills the pours, then puts GND vias where both layers have pour with room for a via:
# at least one in every back-side piece, more along the large ones (about every
# --spacing mm), never under the footprints listed in --avoid. Refills and reports.
# Usage:
#   python tools/lib/gnd_stitch.py <board.kicad_pcb> [--net GND] [--spacing 12]
#          [--avoid MCU1,DISP1,J1] [--dry]
import sys, math, argparse, pcbnew
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely.prepared import prep

ap = argparse.ArgumentParser()
ap.add_argument('board'); ap.add_argument('--net', default='GND')
ap.add_argument('--spacing', type=float, default=12.0)
ap.add_argument('--avoid', default='MCU1,DISP1,J1')
ap.add_argument('--dry', action='store_true')
A = ap.parse_args()
b = pcbnew.LoadBoard(A.board)
ds = b.GetDesignSettings(); nc = ds.m_NetSettings.GetDefaultNetclass()
VIA_D, VIA_DRILL = nc.GetViaDiameter() / 1e6, nc.GetViaDrill() / 1e6
net = b.FindNet(A.net)
zones = [z for z in b.Zones() if z.GetNetCode() == net.GetNetCode()]
if not zones: sys.exit('no %s zone' % A.net)

def fill():
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
def sps_to_shapely(sps):
    polys = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        holes = [[(sps.Hole(i, h).CPoint(k).x / 1e6, sps.Hole(i, h).CPoint(k).y / 1e6) for k in range(sps.Hole(i, h).PointCount())] for h in range(sps.HoleCount(i))]
        polys.append(Polygon([(o.CPoint(k).x / 1e6, o.CPoint(k).y / 1e6) for k in range(o.PointCount())], holes))
    return polys
def fills(layer):
    out = []
    for z in zones:
        if z.IsOnLayer(layer): out += sps_to_shapely(z.GetFilledPolysList(layer))
    return out
def status(tag):
    b.BuildConnectivity(); c = b.GetConnectivity()
    print('%s: %d front / %d back pour pieces, unconnected %d' % (tag, len(fills(pcbnew.F_Cu)), len(fills(pcbnew.B_Cu)), c.GetUnconnectedCount(True)))

fill(); status('before')
F, B = fills(pcbnew.F_Cu), fills(pcbnew.B_Cu)
m = VIA_D / 2 + 0.05                     # the whole via pad inside both pours
f_ok = prep(unary_union([p.buffer(-m) for p in F]))
avoid = []
for r in [x for x in A.avoid.split(',') if x]:
    f = b.FindFootprintByReference(r)
    if f is None: continue
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if cy.OutlineCount(): avoid += sps_to_shapely(cy)
    else:
        bb = f.GetBoundingBox(); avoid.append(Polygon([(bb.GetLeft() / 1e6, bb.GetTop() / 1e6), (bb.GetRight() / 1e6, bb.GetTop() / 1e6), (bb.GetRight() / 1e6, bb.GetBottom() / 1e6), (bb.GetLeft() / 1e6, bb.GetBottom() / 1e6)]))
avoid = prep(unary_union(avoid).buffer(0.5)) if avoid else None
existing = [Point(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == net.GetNetCode()]

new = []
for piece in B:
    region = piece.buffer(-m)
    if region.is_empty: continue
    # candidate points: a 0.5 mm grid over the piece, inside both pours, away from --avoid
    x0, y0, x1, y1 = region.bounds
    cand = []
    reg = prep(region)
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            pt = Point(x, y)
            if reg.contains(pt) and f_ok.contains(pt) and not (avoid and avoid.contains(pt)):
                cand.append(pt)
            y += 0.5
        x += 0.5
    if not cand: continue
    chosen = [q for q in existing + new if piece.contains(q)]
    if not chosen:                         # first via: the candidate nearest the piece's middle
        c0 = piece.representative_point()
        chosen.append(min(cand, key=lambda q: q.distance(c0))); new.append(chosen[-1])
    while True:                            # more along large pieces, about every --spacing mm
        far = max(cand, key=lambda q: min(q.distance(c) for c in chosen))
        if min(far.distance(c) for c in chosen) < A.spacing: break
        chosen.append(far); new.append(far)
print('%d stitching vias to add (%d %s vias already there)' % (len(new), len(existing), A.net))
if A.dry: sys.exit(0)
for q in new:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(round(q.x * 1e6)), int(round(q.y * 1e6))))
    v.SetWidth(int(VIA_D * 1e6)); v.SetDrill(int(VIA_DRILL * 1e6)); v.SetNet(net)
    b.Add(v)
fill(); status('after')
pcbnew.SaveBoard(A.board, b)
print('saved', A.board)
