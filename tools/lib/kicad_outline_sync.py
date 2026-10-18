# Carry board-outline (Edge.Cuts) changes from an Ergogen rebuild into a KiCad
# project board that has been edited since (moved / rotated as a whole, routed...),
# without regenerating it.
#
# Usage (KiCad python; close the board in KiCad first):
#   python tools/lib/kicad_outline_sync.py <old ergogen pcb> <new ergogen pcb> <project pcb> [<out pcb>]
# The rigid transform (rotation + shift) between the Ergogen build and the project
# board is fitted from the footprint positions; the Edge.Cuts shapes that differ
# between the old and new Ergogen boards are removed from / added to the project
# board through that transform. Nothing else on the project board is touched.
import sys, math, pcbnew

old_f, new_f, proj_f = sys.argv[1:4]
out_f = sys.argv[4] if len(sys.argv) > 4 else proj_f
old, new, proj = (pcbnew.LoadBoard(f) for f in (old_f, new_f, proj_f))

def key(d):
    s = d.GetShapeStr()
    k = (s, d.GetStart().x, d.GetStart().y, d.GetEnd().x, d.GetEnd().y)
    if s == 'Arc': k += (d.GetArcMid().x, d.GetArcMid().y)
    return k
def edges(b): return [d for d in b.GetDrawings() if d.GetClass() == 'PCB_SHAPE' and d.GetLayerName() == 'Edge.Cuts']

# rigid transform old Ergogen -> project, from the footprints
fo = {f.GetReference(): f for f in old.GetFootprints()}; fp = {f.GetReference(): f for f in proj.GetFootprints()}
refs = sorted(set(fo) & set(fp))
rots = {round((fp[r].GetOrientationDegrees() - fo[r].GetOrientationDegrees()) % 360, 3) for r in refs}
if len(rots) != 1: sys.exit('footprints were not rotated as one block (%s) - not a rigid move' % sorted(rots)[:5])
ang = pcbnew.EDA_ANGLE(rots.pop(), pcbnew.DEGREES_T)
def rot(p):                                    # rotate a point about the origin the way KiCad rotates items
    s = pcbnew.PCB_SHAPE(old); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(p); s.SetEnd(p)
    s.Rotate(pcbnew.VECTOR2I(0, 0), ang); return s.GetStart()
d = [(fp[r].GetPosition().x - rot(fo[r].GetPosition()).x, fp[r].GetPosition().y - rot(fo[r].GetPosition()).y) for r in refs]
t = pcbnew.VECTOR2I(round(sum(x for x, _ in d) / len(d)), round(sum(y for _, y in d) / len(d)))
res = max(math.hypot(x - t.x, y - t.y) for x, y in d) / 1e6
if res > 0.01: sys.exit('footprints moved individually (residual %.3f mm) - not a rigid move' % res)
def place(item):                               # Ergogen coordinates -> project coordinates
    item.Rotate(pcbnew.VECTOR2I(0, 0), ang); item.Move(t); return item

ko, kn = {key(e): e for e in edges(old)}, {key(e): e for e in edges(new)}
removed = [ko[k] for k in ko if k not in kn]; added = [kn[k] for k in kn if k not in ko]
pk = {}
for e in edges(proj): pk.setdefault(key(e), e)
gone = 0
for e in removed:
    c = place(e.Duplicate()); k = key(c)
    hit = next((pk[q] for q in pk if q[0] == k[0] and all(abs(a - b) <= 2 for a, b in zip(q[1:], k[1:]))), None)
    if hit is None: sys.exit('an outline segment to replace was not found on the project board (edited there?) - stopping')
    proj.Remove(hit); gone += 1
for e in added:
    c = e.Duplicate(); c.SetParent(proj); proj.Add(place(c))
ok = proj.GetBoardPolygonOutlines(pcbnew.SHAPE_POLY_SET(), False)
pcbnew.SaveBoard(out_f, proj)
print('transform: rotate %.3f deg, shift (%.3f, %.3f) mm, fit residual %.4f mm' % (ang.AsDegrees(), t.x / 1e6, t.y / 1e6, res))
print('Edge.Cuts: %d removed, %d added; outline closed: %s -> %s' % (gone, len(added), ok, out_f))
