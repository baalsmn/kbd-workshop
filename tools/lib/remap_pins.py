# Move nets to other pins of one footprint (e.g. the Helios) on a routed KiCad board
# (KiCad python + shapely, e.g. the KiKit venv), keeping the routing: for every pad whose
# net changes, only the track segments / vias whose copper touches the pad or comes within
# the copper clearance of it are removed (in practice the first segment of each track,
# sometimes the second), so the rest of the routing stays; the pad then gets its new net.
# Usage:
#   python tools/lib/remap_pins.py <board.kicad_pcb> <ref> <pad>=<net>[,<pad>=<net>...] [--dry]
#   <net> empty = the pad becomes free (no net; tools/lib/kicad_project.py marks it as a
#   no-connect). Pads not listed keep their nets.
# Run tools/lib/kicad_project.py on the board afterwards for a matching schematic.
import sys, pcbnew
from shapely.geometry import Polygon, LineString, Point
board_f, ref, spec = sys.argv[1:4]
dry = '--dry' in sys.argv
b = pcbnew.LoadBoard(board_f)
fp = b.FindFootprintByReference(ref)
want = {}
for item in spec.split(','):
    pad, _, net = item.strip().partition('=')
    want[pad] = net
pads = [p for p in fp.Pads() if p.GetNumber() in want]
changes = [(p, p.GetNetname(), want[p.GetNumber()]) for p in pads if p.GetNetname() != want[p.GetNumber()]]
CLR = b.GetDesignSettings().m_NetSettings.GetDefaultNetclass().GetClearance() / 1e6
def padpoly(p, layer):
    sh = p.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE); o = sh.Outline(0)
    return Polygon([(o.CPoint(k).x / 1e6, o.CPoint(k).y / 1e6) for k in range(o.PointCount())])
def touches(t, p):
    # copper of t touches the pad, or is closer than the clearance (on a shared layer)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        if not p.IsOnLayer(layer) or not t.IsOnLayer(layer): continue
        if t.GetClass() == 'PCB_VIA':
            c = t.GetPosition(); g = Point(c.x / 1e6, c.y / 1e6).buffer(t.GetWidth(layer) / 2e6)
        else:
            a, e = t.GetStart(), t.GetEnd()
            g = LineString([(a.x / 1e6, a.y / 1e6), (e.x / 1e6, e.y / 1e6)]).buffer(t.GetWidth() / 2e6)
        if g.distance(padpoly(p, layer)) < CLR - 1e-4: return True
    return False
gone = []
for p, old, new in changes:
    hit = [t for t in b.GetTracks() if t.GetNetname() != new and touches(t, p)]
    gone += hit
    print('pad %-3s %-14s -> %-14s (%d segment(s) / via(s) on the pad removed)' % (p.GetNumber(), old or '-', new or '(free)', len(hit)))
same = len(pads) - len(changes)
print('%d pad(s) change, %d already right' % (len(changes), same))
if dry: sys.exit(0)
for t in {id(t): t for t in gone}.values(): b.Remove(t)
for p, old, new in changes:
    if new:
        ni = b.FindNet(new)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, new); b.Add(ni)
        p.SetNet(ni)
    else:
        p.SetNet(b.FindNet(''))
b.BuildConnectivity()
pcbnew.SaveBoard(board_f, b)
print('saved %s; unconnected now %d' % (board_f, b.GetConnectivity().GetUnconnectedCount(True)))
