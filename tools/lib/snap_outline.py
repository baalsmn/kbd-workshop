# Close sub-micron gaps in a board's Edge.Cuts outline (Ergogen's rounding leaves a
# few ~0.0001 mm gaps between line ends; KiCad accepts them, KiKit refuses a
# "discontinuous outline"). Every line / arc end point within TOL of another end
# point is moved onto it. Writes a copy; the input board is not changed.
# Usage (KiCad python): python tools/lib/snap_outline.py <in.kicad_pcb> <out.kicad_pcb>
import sys, math, pcbnew

TOL = pcbnew.FromMM(0.01)
b = pcbnew.LoadBoard(sys.argv[1])
shapes = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
          and d.GetShape() in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_ARC)]
ends = [(d, 's') for d in shapes] + [(d, 'e') for d in shapes]
pos = lambda de: de[0].GetStart() if de[1] == 's' else de[0].GetEnd()
moved = 0
for i, a in enumerate(ends):
    pa = pos(a)
    for bb in ends[:i]:                       # snap onto an earlier end point (stays fixed)
        pb = pos(bb)
        dist = math.hypot(pa.x - pb.x, pa.y - pb.y)
        if 0 < dist < TOL:
            if a[0].GetShape() == pcbnew.SHAPE_T_ARC:     # keep the arc's mid point
                m = a[0].GetArcMid()
                s, e = (pb, a[0].GetEnd()) if a[1] == 's' else (a[0].GetStart(), pb)
                a[0].SetArcGeometry(s, m, e)
            elif a[1] == 's': a[0].SetStart(pb)
            else: a[0].SetEnd(pb)
            moved += 1
            break
b.Save(sys.argv[2])
print('snap_outline: %d end points moved (< %.3f mm)' % (moved, pcbnew.ToMM(TOL)))
