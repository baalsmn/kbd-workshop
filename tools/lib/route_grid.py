# Angle-keeping grid router for the keyboard boards (KiCad python + shapely / numpy,
# e.g. the KiKit venv from tools/panel.sh: %LOCALAPPDATA%/kugo-kikit/Scripts/python.exe).
#
# Auto-routers work on one 0 / 45 / 90 deg grid for the whole board; the key halves are
# turned +-15 deg, so their tracks come out as staircases. This router searches on a
# grid turned to a frame angle (the half's key angle, or 0 for the centre) and only
# moves straight or diagonally in it, so every track is at the frame angle or 45 deg to
# it. Obstacles come from the board itself: copper of other nets (pads, tracks, vias)
# grown by the copper clearance, every drill grown by the hole clearance, and the
# Edge.Cuts outline / cutouts grown by the edge clearance; outside the board is blocked.
#
# Usage:
#   python tools/lib/route_grid.py <board.kicad_pcb> <region> <net spec> [<net spec> ...]
#     region     left | right | centre | all (left / right = pads on that side of the
#                board's centre line; the grid angle is that half's switch angle)
#     net spec   <regex>=<layers>[:<width mm>], layers F, B, FB (first = preferred),
#                e.g. "^R[0-9]+$=B" "^C[0-9]+$=FB" "_c[0-9]+_r[0-9]+$=B"
#   options: --grid 0.1  --via-cost 3.0 (mm)  --chains trunks.json  --dry (route, report, don't save)
# Copper a net already has (tracks, vias) is part of its tree, so pads connect to it.
# Each net is connected pad by pad (nearest unconnected pad to the routed tree), with
# A* on the grid. Existing tracks are kept and treated as obstacles / as part of
# their net's tree. Prints what it could not connect.
import sys, re, math, heapq, time, argparse
import numpy as np
import pcbnew
import shapely
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ap = argparse.ArgumentParser()
ap.add_argument('board'); ap.add_argument('region'); ap.add_argument('nets', nargs='+')
ap.add_argument('--grid', type=float, default=0.1)
ap.add_argument('--via-cost', type=float, default=3.0)
ap.add_argument('--wrong-layer', type=float, default=4.0, help='cost factor on a non-preferred layer')
ap.add_argument('--turn-cost', type=float, default=0.6, help='mm added per 45 deg turn')
ap.add_argument('--window', type=float, default=12.0, help='search margin around a connection (mm)')
ap.add_argument('--hweight', type=float, default=1.6, help='A* heuristic weight (>1: faster, slightly longer paths)')
ap.add_argument('--max-nodes', type=int, default=2000000)
ap.add_argument('--chains', help='JSON {net: [{"width": w, "points": [[x, y], ...]}, ...]} (board mm): '
                'waypoint chains routed first (e.g. power trunks); they join the tree of their net')
ap.add_argument('--components', action='store_true', help='join the existing connected pieces of each net (centre step) instead of connecting pads')
ap.add_argument('--via-in-pad', action='append', default=[], help='REF.PAD: exception, this pad may take its via in the pad (e.g. LED33.2)')
ap.add_argument('--conn-time', type=float, default=240.0, help='give up on one connection after this many seconds')
ap.add_argument('--centre-width', type=float, default=60.0, help='centre region: pads within this many mm of the centre line')
ap.add_argument('--safe', type=float, default=None, help='rasterisation margin in mm (default 0.75 x grid); smaller lets tracks pass fine-pitch pins')
ap.add_argument('--stop-on-timeout', action='store_true', help='when one spot hits --conn-time, save and stop the run')
ap.add_argument('--chains-only', action='store_true', help='route only the --chains (e.g. trunks before the signals)')
ap.add_argument('--dry', action='store_true')
A = ap.parse_args()

MM = 1e6
b = pcbnew.LoadBoard(A.board)
ds = b.GetDesignSettings()
nc = ds.m_NetSettings.GetDefaultNetclass()
CLR = max(nc.GetClearance(), ds.m_MinClearance) / MM          # copper to copper
HOLE_CLR = ds.m_HoleClearance / MM                             # copper to drill
EDGE_CLR = ds.m_CopperEdgeClearance / MM                       # copper to Edge.Cuts
VIA_D, VIA_DRILL = nc.GetViaDiameter() / MM, nc.GetViaDrill() / MM
G = A.grid
SAFE = A.safe if A.safe is not None else G * 0.75             # rasterisation margin
LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
LI = {'F': 0, 'B': 1}

# ---- region and frame angle
fps = list(b.GetFootprints())
switches = [f for f in fps if f.GetReference().startswith('S') and f.GetFPIDAsString().split(':')[-1].startswith('Gateron')]
bb = b.GetBoardEdgesBoundingBox()
CX = (bb.GetX() + bb.GetWidth() / 2) / MM
def side(x): return 'left' if x < CX else 'right'
if A.region in ('left', 'right'):
    angs = sorted(f.GetOrientationDegrees() for f in switches if side(f.GetPosition().x / MM) == A.region)
    ANG = angs[len(angs) // 2]            # median: the half's key angle (thumb keys differ)
else:
    ANG = 0.0
ca, sa = math.cos(math.radians(ANG)), math.sin(math.radians(ANG))
def to_local(x, y):  return (x * ca - y * sa, x * sa + y * ca)      # same as the footprint frame
def to_board(u, v):  return (u * ca + v * sa, -u * sa + v * ca)
def in_region(x, y):
    if A.region == 'all': return True
    if A.region == 'centre': return abs(x - CX) <= A.centre_width
    return side(x) == A.region

# ---- board outline (local frame)
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, False)
def sp_to_poly(o): return [to_local(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
outline = unary_union([Polygon(sp_to_poly(ps.Outline(i)), [sp_to_poly(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]) for i in range(ps.OutlineCount())])
edges = outline.boundary

# ---- items: (net, layer index or None for both, geometry in local frame)
def pad_geom(p, layer):
    sh = p.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
    polys = []
    for i in range(sh.OutlineCount()):
        polys.append(Polygon(sp_to_poly(sh.Outline(i))))
    return unary_union(polys)
pads = []        # (net, li, geom, pad)
holes = []       # geometry of drills (local)
for f in fps:
    for p in f.Pads():
        net = p.GetNetname()
        for L, lid in LAYERS.items():
            if p.IsOnLayer(lid):
                pads.append((net, LI[L], pad_geom(p, lid), p))
        if p.GetDrillSize().x > 0:
            c = p.GetPosition(); u, v = to_local(c.x / MM, c.y / MM)
            dx, dy = p.GetDrillSize().x / MM, p.GetDrillSize().y / MM
            holes.append(Point(u, v).buffer(max(dx, dy) / 2, 16))
tracks = []      # (net, li or None, geom)
for t in b.GetTracks():
    net = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        c = t.GetPosition(); u, v = to_local(c.x / MM, c.y / MM)
        tracks.append((net, None, Point(u, v).buffer(t.GetWidth(pcbnew.F_Cu) / MM / 2, 16)))
    else:
        s, e = t.GetStart(), t.GetEnd()
        g = LineString([to_local(s.x / MM, s.y / MM), to_local(e.x / MM, e.y / MM)]).buffer(t.GetWidth() / MM / 2, 8)
        for L, lid in LAYERS.items():
            if t.GetLayer() == lid: tracks.append((net, LI[L], g))

# ---- grid over the region
reg_pts = [to_local(p.GetPosition().x / MM, p.GetPosition().y / MM) for (_, _, _, p) in pads if in_region(p.GetPosition().x / MM, p.GetPosition().y / MM)]
U0 = min(u for u, v in reg_pts) - 15; U1 = max(u for u, v in reg_pts) + 15
V0 = min(v for u, v in reg_pts) - 15; V1 = max(v for u, v in reg_pts) + 15
NU, NV = int((U1 - U0) / G) + 1, int((V1 - V0) / G) + 1
print('frame %.1f deg, grid %d x %d cells (%.1f x %.1f mm) at %.2f mm' % (ANG, NU, NV, U1 - U0, V1 - V0, G))
def cell(u, v): return int(round((u - U0) / G)), int(round((v - V0) / G))
def ctr(i, j):  return U0 + i * G, V0 + j * G

def raster(geom):
    """cells (flat indices) whose centre lies in geom (bbox-limited)."""
    if geom.is_empty: return np.zeros(0, dtype=np.int64)
    x0, y0, x1, y1 = geom.bounds
    i0 = max(int(math.floor((x0 - U0) / G)), 0); i1 = min(int(math.ceil((x1 - U0) / G)), NU - 1)
    j0 = max(int(math.floor((y0 - V0) / G)), 0); j1 = min(int(math.ceil((y1 - V0) / G)), NV - 1)
    if i1 < i0 or j1 < j0: return np.zeros(0, dtype=np.int64)
    I, J = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
    X, Y = U0 + I * G, V0 + J * G
    m = shapely.contains_xy(geom, X, Y)
    return (I[m] * NV + J[m]).astype(np.int64)

t0 = time.time()
TW = {}   # width per net (filled from the specs)
def width_of(net): return TW.get(net, 0.25)
# blocked counts per layer for tracks (half width 0.125 nominal; per-net width handled by an
# extra margin below) and for vias
HW = 0.125
blk = [np.zeros(NU * NV, dtype=np.int16), np.zeros(NU * NV, dtype=np.int16)]
vblk = np.zeros(NU * NV, dtype=np.int16)
own = {}  # net -> list of (layer or None, cells, via cells) to subtract while routing that net
def add_item(net, li, geom, grow_track, grow_via, sign=1, is_pad=False):
    ct = raster(geom.buffer(grow_track + SAFE, 8))
    cv = raster(geom.buffer(grow_via + SAFE, 8))
    for L in ([0, 1] if li is None else [li]):
        np.add.at(blk[L], ct, sign)
    np.add.at(vblk, cv, sign)
    if net and sign > 0: own.setdefault(net, []).append((li, ct, cv, is_pad))

# outside the board and near edges / cutouts: blocked for everything
I, J = np.meshgrid(np.arange(NU), np.arange(NV), indexing='ij')
X, Y = U0 + I * G, V0 + J * G
inside = shapely.contains_xy(outline.buffer(-(EDGE_CLR + HW + SAFE)), X, Y).ravel()
inside_v = shapely.contains_xy(outline.buffer(-(EDGE_CLR + VIA_D / 2 + SAFE)), X, Y).ravel()
for L in (0, 1): blk[L][~inside] += 1
vblk[~inside_v] += 1
del I, J, X, Y
win = box(U0, V0, U1, V1)
for h in holes:
    if h.intersects(win): add_item(None, None, h, HOLE_CLR + HW, max(HOLE_CLR + VIA_D / 2, ds.m_HoleToHoleMin / MM + VIA_DRILL / 2))
for net, li, g, p in pads:
    vip = ('%s.%s' % (p.GetParentFootprint().GetReference(), p.GetNumber())) in A.via_in_pad
    if g.intersects(win): add_item(net, li, g, CLR + HW, CLR + VIA_D / 2, is_pad=not vip)
for net, li, g in tracks:
    if g.intersects(win): add_item(net, li, g, CLR + HW, CLR + VIA_D / 2)
print('obstacles rasterised in %.1f s' % (time.time() - t0))

# ---- A*
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
def route(starts, targets, layers, pref, extra_hw, deadline=None):
    """starts / targets: sets of (li, i, j). Returns list of (li, i, j) from start to target."""
    tgt = set(targets)
    ti = np.array([t[1] for t in tgt]); tj = np.array([t[2] for t in tgt])
    allpts = [(s[1], s[2]) for s in starts] + [(t[1], t[2]) for t in tgt]
    w = int(A.window / G)
    i0 = max(min(p[0] for p in allpts) - w, 0); i1 = min(max(p[0] for p in allpts) + w, NU - 1)
    j0 = max(min(p[1] for p in allpts) - w, 0); j1 = min(max(p[1] for p in allpts) + w, NV - 1)
    ext = int(math.ceil(extra_hw / G))
    def free(L, i, j):
        if not (i0 <= i <= i1 and j0 <= j <= j1): return False
        if blk[L][i * NV + j] > 0: return False
        if ext:
            for di in (-ext, 0, ext):
                for dj in (-ext, 0, ext):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < NU and 0 <= jj < NV and blk[L][ii * NV + jj] > 0: return False
        return True
    tlay = {t[0] for t in tgt}
    def h(L, i, j):
        k = np.argmin(np.abs(ti - i) + np.abs(tj - j)); di, dj = abs(ti[k] - i), abs(tj[k] - j)
        return A.hweight * (G * (max(di, dj) + 0.4142 * min(di, dj)) + (0 if L in tlay else A.via_cost))
    lay_cost = {L: (1.0 if L == pref else A.wrong_layer) for L in layers}
    openq = []; gs = {}; came = {}; tstart = time.time()
    if deadline is None: deadline = tstart + A.conn_time
    for s in starts:
        st = (s[0], s[1], s[2], -1)
        gs[st] = 0.0; heapq.heappush(openq, (h(s[0], s[1], s[2]), 0.0, st))
    n = 0
    while openq:
        f, g, st = heapq.heappop(openq)
        if g > gs.get(st, 1e18): continue
        L, i, j, d = st
        if (L, i, j) in tgt:
            path = [(L, i, j)]
            while st in came:
                st = came[st]; path.append((st[0], st[1], st[2]))
            return path[::-1], n
        n += 1
        if n > A.max_nodes: break
        if (n & 4095) == 0 and time.time() > deadline:
            TIMEOUTS.append(n); break
        for k, (di, dj) in enumerate(DIRS):
            ii, jj = i + di, j + dj
            if not free(L, ii, jj): continue
            if di and dj and not (free(L, i + di, j) and free(L, i, j + dj)): continue
            step = G * (1.4142 if di and dj else 1.0) * lay_cost[L]
            if d >= 0 and d != k:
                turn = min((k - d) % 8, (d - k) % 8)
                step += A.turn_cost * turn
            ns = (L, ii, jj, k); ng = g + step
            if ng < gs.get(ns, 1e18):
                gs[ns] = ng; came[ns] = st; heapq.heappush(openq, (ng + h(L, ii, jj), ng, ns))
        for L2 in layers:                      # via
            if L2 == L or vblk[i * NV + j] > 0: continue
            ns = (L2, i, j, -1); ng = g + A.via_cost
            if ng < gs.get(ns, 1e18):
                gs[ns] = ng; came[ns] = st; heapq.heappush(openq, (ng + h(L2, i, j), ng, ns))
    return None, n

# ---- path -> tracks / vias on the board
def emit(net, path, width):
    netinfo = b.FindNet(net)
    segs, vias = [], []
    run = [path[0]]
    for a, c in zip(path, path[1:]):
        if c[0] != a[0]:                       # layer change at the same cell
            vias.append(a); segs.append(run); run = [c]; continue
        run.append(c)
    segs.append(run)
    out = []
    for run in segs:
        if len(run) < 2: continue
        L = run[0][0]; pts = [run[0]]
        for k in range(1, len(run) - 1):
            d1 = (run[k][1] - run[k - 1][1], run[k][2] - run[k - 1][2]); d2 = (run[k + 1][1] - run[k][1], run[k + 1][2] - run[k][2])
            if d1 != d2: pts.append(run[k])
        pts.append(run[-1])
        for a, c in zip(pts, pts[1:]):
            out.append((L, a, c))
    for (L, a, c) in out:
        t = pcbnew.PCB_TRACK(b)
        x, y = to_board(*ctr(a[1], a[2])); t.SetStart(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
        x, y = to_board(*ctr(c[1], c[2])); t.SetEnd(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
        t.SetWidth(int(width * MM)); t.SetLayer(pcbnew.F_Cu if L == 0 else pcbnew.B_Cu); t.SetNet(netinfo)
        b.Add(t)
        g = LineString([ctr(a[1], a[2]), ctr(c[1], c[2])]).buffer(width / 2, 8)
        PENDING.append((net, L, g, CLR + HW, CLR + VIA_D / 2))
    for v in vias:
        via = pcbnew.PCB_VIA(b)
        x, y = to_board(*ctr(v[1], v[2])); via.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
        via.SetWidth(int(VIA_D * MM)); via.SetDrill(int(VIA_DRILL * MM)); via.SetNet(netinfo)
        b.Add(via)
        g = Point(ctr(v[1], v[2])).buffer(VIA_D / 2, 16)
        PENDING.append((net, None, g, CLR + HW, CLR + VIA_D / 2))
        # its drill: no other via within hole-to-hole of it (tracks of this net may pass)
        PENDING.append(('#drill', None, Point(ctr(v[1], v[2])).buffer(VIA_DRILL / 2, 16), 0.0, ds.m_HoleToHoleMin / MM + VIA_DRILL / 2))
    return len(out), len(vias)

# ---- nets to route
specs = []
for s in A.nets:
    rx, _, rest = s.partition('=')
    lay, _, wd = rest.partition(':')
    specs.append((re.compile(rx), [LI[c] for c in lay], float(wd) if wd else 0.25))
netpads = {}
for net, li, g, p in pads:
    c = p.GetPosition()
    if not net or not in_region(c.x / MM, c.y / MM): continue
    if A.region in ('left', 'right') and p.GetParentFootprint().GetReference().startswith(('MCU', 'J', 'DISP')): continue
    for rx, lays, wd in specs:
        if rx.search(net):
            netpads.setdefault(net, {}).setdefault(p.m_Uuid.AsString(), (p, set()))[1].add(li)
            TW[net] = wd; break
fails = []; nseg = nvia = 0
TIMEOUTS = []
STOPPED = []
if A.components:
    b.BuildConnectivity(); CONN = b.GetConnectivity()
nseg_v = [0, 0]
import json
CHAINS = json.load(open(A.chains, encoding='utf-8')) if A.chains else {}
PENDING = []
import os
DBG = os.environ.get('ROUTE_DEBUG')
def dump(net, p):
    c = p.GetPosition(); i, j = cell(*to_local(c.x / MM, c.y / MM))
    for L in (1, 0):
        print('layer', 'B' if L else 'F', 'around', p.GetParentFootprint().GetReference(), net, '(# blocked, o pad centre)')
        for jj in range(j - 40, j + 41, 2):
            print(''.join('o' if (ii, jj) == (i, j) else ('#' if blk[L][ii * NV + jj] > 0 else '.') for ii in range(i - 60, i + 61, 2)))
    print('via map (# no via possible)')
    for jj in range(j - 40, j + 41, 2):
        print(''.join('o' if (ii, jj) == (i, j) else ('#' if vblk[ii * NV + jj] > 0 else '.') for ii in range(i - 60, i + 61, 2)))
order = sorted(netpads, key=lambda n: (len(netpads[n]), n))
for net in order:
    if STOPPED and A.stop_on_timeout: break
    rx, lays, wd = next(s for s in specs if s[0].search(net))
    pref = lays[0]
    plist = list(netpads[net].values())
    if len(plist) < 2 and net not in CHAINS: continue
    # release this net's own items
    for (li, ct, cv, isp) in own.get(net, []):
        for L in ([0, 1] if li is None else [li]): np.add.at(blk[L], ct, -1)
        if not isp: np.add.at(vblk, cv, -1)
    def pad_cells(p, pls):
        c = p.GetPosition(); u, v = to_local(c.x / MM, c.y / MM); i, j = cell(u, v)
        if not (0 <= i < NU and 0 <= j < NV): return set()
        return {(L, i, j) for L in pls if L in lays}
    def pad_xy(p):
        c = p.GetPosition(); return to_local(c.x / MM, c.y / MM)
    n_own = len(own.get(net, []))
    tree = set()
    for (tn, tli, tg) in tracks:                      # existing copper of this net in the grid
        if tn == net and tg.intersects(win):
            for c in raster(tg.buffer(-0.05) if tg.area > 0.02 else tg):
                for L in ([0, 1] if tli is None else [tli]):
                    if L in lays: tree.add((L, int(c // NV), int(c % NV)))
    for ch in CHAINS.get(net, []):                   # waypoint chains (power trunks)
        prev = None
        for (x, y) in ch['points']:
            u, v = to_local(x, y); i, j = cell(u, v)
            cand = [(pref, i + di, j + dj) for r in range(0, 16) for di in range(-r, r + 1) for dj in range(-r, r + 1)
                    if max(abs(di), abs(dj)) == r and 0 <= i + di < NU and 0 <= j + dj < NV and blk[pref][(i + di) * NV + j + dj] == 0]
            if not cand: fails.append((net, 'chain point (%.1f, %.1f)' % (x, y), 'blocked')); prev = None; continue
            pt = cand[0]
            if prev is not None:
                path, n = route({prev}, {pt}, lays, pref, max(0.0, ch['width'] / 2 - HW))
                if path is None: fails.append((net, 'chain to (%.1f, %.1f)' % (x, y), 'no path (%d nodes)' % n))
                else:
                    s_, v_ = emit(net, path, ch['width']); nseg_v[0] += s_; nseg_v[1] += v_; tree |= set(path)
            tree.add(pt); prev = pt
    if A.components:
        # join the net's existing connected pieces (KiCad connectivity: pads + the
        # tracks / vias connected to them), nearest piece first
        uf = {}
        def find(x):
            while uf.setdefault(x, x) != x: x = uf[x]
            return x
        pid = {pp.m_Uuid.AsString(): (pp, pls) for (pp, pls) in plist}
        pieces_items = {}
        for key, (pp, pls) in pid.items():
            find(key)
            for it in CONN.GetConnectedItems(pp):
                k2 = it.m_Uuid.AsString()
                if k2 in pid: uf[find(k2)] = find(key)
        for key, (pp, pls) in pid.items():
            pieces_items.setdefault(find(key), set()).add(key)
        comps = []
        for root, members in pieces_items.items():
            cells, pts = set(), []
            for key in members:
                pp, pls = pid[key]
                pc = pad_cells(pp, pls); cells |= pc
                if pc: pts.append(pad_xy(pp))
                for it in CONN.GetConnectedItems(pp):
                    if it.GetClass() == 'PCB_VIA':
                        c = it.GetPosition(); u, v = to_local(c.x / MM, c.y / MM); i, j = cell(u, v)
                        if 0 <= i < NU and 0 <= j < NV:
                            cells |= {(L, i, j) for L in lays}; pts.append((u, v))
                    elif it.GetClass() in ('PCB_TRACK', 'PCB_ARC'):
                        s0, e0 = it.GetStart(), it.GetEnd()
                        a0, a1 = to_local(s0.x / MM, s0.y / MM), to_local(e0.x / MM, e0.y / MM)
                        L = 0 if it.GetLayer() == pcbnew.F_Cu else 1
                        if L in lays:
                            for c in raster(LineString([a0, a1]).buffer(0.05, 4)):
                                cells.add((L, int(c // NV), int(c % NV)))
                        pts += [q for q in (a0, a1) if U0 <= q[0] <= U1 and V0 <= q[1] <= V1]
            if not cells or not pts: continue        # piece entirely outside this grid
            comps.append((cells, pts, any(pid[k][0].GetParentFootprint().GetReference().startswith('MCU') for k in members)))
        comps.sort(key=lambda c: not c[2])                 # start from the MCU's piece
        if comps:
            tree = set(comps[0][0]); tpts = list(comps[0][1]); rest = comps[1:]
        else:
            tree, tpts, rest = set(), [], []
        while rest:
            def dist(c):
                return min(math.hypot(a - x, b_ - y) for (a, b_) in c[1] for (x, y) in tpts[::max(1, len(tpts) // 400)])
            k = min(range(len(rest)), key=lambda q: dist(rest[q]))
            cells, pts, _ = rest.pop(k)
            # nearest pair of points between the tree and this piece
            pa, pb = min(((a, t) for a in pts for t in tpts[::max(1, len(tpts) // 400)]), key=lambda q: math.hypot(q[0][0] - q[1][0], q[0][1] - q[1][1]))
            dmin = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
            near = {t for t in tree if math.hypot(ctr(t[1], t[2])[0] - pa[0], ctr(t[1], t[2])[1] - pa[1]) <= dmin + 4.0}
            tg = {t for t in cells if math.hypot(ctr(t[1], t[2])[0] - pb[0], ctr(t[1], t[2])[1] - pb[1]) <= dmin + 4.0} or set(cells)
            t1 = time.time(); dl = t1 + A.conn_time; nto = len(TIMEOUTS)
            path, n = route(near, tg, lays, pref, max(0.0, wd / 2 - HW), dl)
            if path is None and time.time() < dl:
                path, n2 = route(tg, near, lays, pref, max(0.0, wd / 2 - HW), dl); n += n2
                if path is not None: path = path[::-1]
            where = 'piece at (%.1f, %.1f)' % to_board(*pts[0])
            print('  %-12s %-26s %s %5.1f s' % (net, where, 'ok  ' if path else 'FAIL', time.time() - t1), flush=True)
            if path is None and len(TIMEOUTS) > nto:
                STOPPED.append((net, where))
                print('  TIMEOUT at %s %s after %.0f s' % (net, where, time.time() - t1), flush=True)
                if A.stop_on_timeout: tree |= cells; break
            if path is None:
                fails.append((net, 'piece at (%.1f, %.1f)' % to_board(*pts[0]), 'no path (%d nodes)' % n))
            else:
                s_, v_ = emit(net, path, wd); nseg += s_; nvia += v_
                tree |= set(path); tpts += [ctr(p_[1], p_[2]) for p_ in path[::10]]
            tree |= cells; tpts += pts
        todo = []
    elif A.chains_only:
        todo = []
    elif tree:
        todo = plist[:]
    else:
        first = plist[0]; tree |= pad_cells(*first); todo = plist[1:]
    while todo:
        tx = [ctr(t[1], t[2]) for t in tree]
        k = min(range(len(todo)), key=lambda q: min(math.hypot(pad_xy(todo[q][0])[0] - a, pad_xy(todo[q][0])[1] - c) for a, c in tx))
        p, pls = todo.pop(k)
        tg = pad_cells(p, pls)
        if not tg: fails.append((net, p.GetParentFootprint().GetReference(), 'pad not on an allowed layer')); continue
        tu, tv = pad_xy(p)
        dmin = min(math.hypot(ctr(t[1], t[2])[0] - tu, ctr(t[1], t[2])[1] - tv) for t in tree)
        near = {t for t in tree if math.hypot(ctr(t[1], t[2])[0] - tu, ctr(t[1], t[2])[1] - tv) <= dmin + 4.0}
        t1 = time.time(); dl = t1 + A.conn_time; nto = len(TIMEOUTS)
        path, n = route(near, tg, lays, pref, max(0.0, wd / 2 - HW), dl)
        if path is None and time.time() < dl:   # pad in a pocket: search outward from the pad instead
            wide = {t for t in tree if math.hypot(ctr(t[1], t[2])[0] - tu, ctr(t[1], t[2])[1] - tv) <= dmin + 12.0}
            path, n2 = route(tg, wide, lays, pref, max(0.0, wd / 2 - HW), dl); n += n2
            if path is not None: path = path[::-1]
        where = p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
        print('  %-12s %-10s %s %5.1f s' % (net, where, 'ok  ' if path else 'FAIL', time.time() - t1), flush=True)
        if path is None and len(TIMEOUTS) > nto:
            STOPPED.append((net, where))
            print('  TIMEOUT at %s %s after %.0f s' % (net, where, time.time() - t1), flush=True)
            if A.stop_on_timeout: break
        if path is None and DBG and p.GetParentFootprint().GetReference() == DBG:
            dump(net, p)
            for (q, _) in plist:
                if q is not p: dump(net, q)
        if path is None:
            fails.append((net, p.GetParentFootprint().GetReference(), 'no path (%d nodes)' % n)); continue
        s_, v_ = emit(net, path, wd); nseg += s_; nvia += v_
        tree |= set(path)
    # put this net's items back, then add its new copper as obstacles for the others
    for (li, ct, cv, isp) in own.get(net, [])[:n_own]:
        for L in ([0, 1] if li is None else [li]): np.add.at(blk[L], ct, 1)
        if not isp: np.add.at(vblk, cv, 1)
    for it in PENDING:
        if it[0] == '#drill':
            np.add.at(vblk, raster(it[2].buffer(it[4] + SAFE, 8)), 1)
        else:
            add_item(*it)
    PENDING.clear()
print('routed %d nets: %d segments, %d vias in %.1f s' % (len(order), nseg + nseg_v[0], nvia + nseg_v[1], time.time() - t0))
for f in fails: print('  FAILED %s at %s: %s' % f)
if STOPPED: print('  STOPPED: %d spot(s) hit the %.0f s limit: %s' % (len(STOPPED), A.conn_time, STOPPED))
if not A.dry:
    b.Save(A.board); print('saved', A.board)
