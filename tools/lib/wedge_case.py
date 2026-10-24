# Tilt wedge for a case: a separate printed skeleton under the unchanged tub, so the case
# stands on the table with its key plane tilted (south edge raised = negative tilt).
# Built in the tub's frame (z = 0 at the tub's underside, y = north):
#   - frame: a band under the tub's edge, from the case outline grown by --clear + --rim
#     to --frame mm inside it, from the table plane up to z = 0;
#   - rim: --rim wide, --pocket high around the tub's foot (--clear gap), holds it sideways;
#   - columns: at the circles of the wedge_socket outline (4 per half), a Ø --pillar strut
#     from the table up to z = 0, then a column (socket Ø - 2 x --column-clear) --column mm
#     high that drops into the socket in the tub floor, with a magnet pocket (wedge_magnet
#     circles, --magnet-depth deep) in its top;
#   - ribs (--rib wide): the columns of a half joined in a ring, and each one to the frame;
#   - centre wall: --wall mm each side of the halves' joint, north to south frame, so the
#     halves butt against each other along the whole depth (less wobble);
#   - table plane: --north mm under the tub at its northernmost point, falling towards the
#     south by tan(--angle), so the wedge is thickest at the south edge;
#   - split into the tub's print halves (cut_left / cut_right).
# Writes <name>_<angle>deg_left/right.step + .stl in print orientation (table side down,
# z = 0) and <name>_<angle>deg_assembly.step in the tub's frame.
# With --json <design>_case.json it also adds the wedge to the Fusion data file: outlines
# wedge_skeleton / wedge_rim / wedge_column / wedge_magnet and the parts wedge_left /
# wedge_right, whose last recipe step ("tilt") the Fusion script turns into a split by a
# plane at the user parameter tilt_angle (any angle up to --max-angle).
# Usage (build123d, see tools/step.sh): python tools/lib/wedge_case.py <outlines dir> <out dir>
#        [--angle 6] [--north 3] [--name wedge] [--stl-dir <dir>] [--json <design>_case.json]
import sys, os, math, argparse
import ezdxf
from build123d import (Pos, Rot, Plane, Circle, Cylinder, Polygon, Kind, Axis, Align, Box, extrude, offset,
                       export_step, export_stl)
if '__file__' in globals():                      # (tools/step.sh runs it with exec: tools/lib is on the path)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step_case import outline_face

ap = argparse.ArgumentParser()
ap.add_argument('outlines'); ap.add_argument('out')
ap.add_argument('--angle', type=float, default=6.0, help='key plane tilt, degrees (south edge up)')
ap.add_argument('--north', type=float, default=3.0, help='wedge thickness at the north edge, mm')
ap.add_argument('--rim', type=float, default=2.0, help='rim width around the tub, mm')
ap.add_argument('--pocket', type=float, default=1.0, help='rim height, mm')
ap.add_argument('--clear', type=float, default=0.3, help='gap between tub and rim, mm')
ap.add_argument('--frame', type=float, default=10.0, help='frame band inside the case edge, mm (tub wall 8)')
ap.add_argument('--pillar', type=float, default=10.0, help='strut diameter under each column, mm')
ap.add_argument('--rib', type=float, default=5.0, help='rib width, mm')
ap.add_argument('--wall', type=float, default=3.0, help='centre wall at the joint of the halves, mm per half (0 = none)')
ap.add_argument('--joint-magnets', type=int, default=2, help='magnet pockets per half in the centre wall (0 = none)')
ap.add_argument('--joint-margin', type=float, default=1.0, help='wall left above / below a joint magnet pocket, mm')
ap.add_argument('--column', type=float, default=1.0, help='column height (tub socket 1.1 deep), mm')
ap.add_argument('--column-clear', type=float, default=0.2, help='radial gap column / socket, mm')
ap.add_argument('--magnet-depth', type=float, default=1.1, help='magnet pocket depth in the column, mm')
ap.add_argument('--name', default='wedge')
ap.add_argument('--stl-dir', help='folder for the STL files (default: the out dir)')
ap.add_argument('--json', help='Fusion data file to add the wedge parts to')
ap.add_argument('--max-angle', type=float, default=15.0, help='largest tilt the Fusion wedge allows')
A = ap.parse_args()
O = lambda n: os.path.join(A.outlines, n + '.dxf')
os.makedirs(A.out, exist_ok=True)

def circles(name):
    if not os.path.exists(O(name)): return []
    doc = ezdxf.readfile(O(name))
    return [(e.dxf.center.x, e.dxf.center.y, e.dxf.radius) for e in doc.modelspace() if e.dxftype() == 'CIRCLE']

def union(faces):
    out = faces[0]
    for f in faces[1:]: out = out + f
    return out

def bar(p, q, w):
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2
    return Polygon((p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny),
                   (p[0] - nx, p[1] - ny), align=None)

case = outline_face(O('case'))
bb = case.bounding_box(); ymin, ymax = bb.min.Y, bb.max.Y
t = math.tan(math.radians(A.angle))
H = A.north + (ymax - ymin) * t + 5                       # deeper than the thickest point
outer = offset(case, A.clear + A.rim, kind=Kind.ARC)
inner = offset(case, A.clear, kind=Kind.ARC)
opening = offset(case, -A.frame, kind=Kind.INTERSECTION)  # inside the frame band (ARC leaves 0.1 um edges: invalid solid)
rim = outer - inner
sockets, magnets = circles('wedge_socket'), circles('wedge_magnet')
# struts: per half (either side of the mirror axis) the columns joined in a ring around
# their centre, and each column to the nearest point of the frame's inner edge
xc = (bb.min.X + bb.max.X) / 2
edge = [f.outer_wire().position_at(k / 2000) for f in opening.faces() for k in range(2000)]
struts = []
for half in ([s for s in sockets if s[0] < xc], [s for s in sockets if s[0] >= xc]):
    if not half: continue
    mx, my = sum(s[0] for s in half) / len(half), sum(s[1] for s in half) / len(half)
    ring = sorted(half, key=lambda s: math.atan2(s[1] - my, s[0] - mx))
    for k, (x, y, r) in enumerate(ring):
        struts.append(Pos(x, y) * Circle(A.pillar / 2))
        if len(ring) > 1:
            struts.append(bar((x, y), ring[(k + 1) % len(ring)][:2], A.rib))
        e = min(edge, key=lambda v: (v.X - x) ** 2 + (v.Y - y) ** 2)
        L = math.hypot(e.X - x, e.Y - y)                  # on 3 mm into the frame
        struts.append(bar((x, y), (x + (e.X - x) * (L + 3) / L, y + (e.Y - y) * (L + 3) / L), A.rib))
def up(f, z, h):                                  # always upwards (face normals can come out flipped)
    return Pos(0, 0, z) * extrude(f, amount=h, dir=(0, 0, 1))

xj = outline_face(O('cut_left')).bounding_box().max.X  # the halves' joint
if A.wall > 0:                                        # centre wall along it
    struts.append(bar((xj, ymin - 5), (xj, ymax + 5), 2 * A.wall))
skeleton = [outer - opening] + struts                  # (overlapping 2D pieces, fused as solids)
body = union([up(f, -H, H) for f in skeleton]) & up(outer, -H - 1, H + A.pocket + 2)
body = body + up(rim, 0, A.pocket)
if sockets:
    body = body + union([up(Pos(x, y) * Circle(r - A.column_clear), 0, A.column) for x, y, r in sockets])
    body = body - union([up(Pos(x, y) * Circle(r), A.column - A.magnet_depth, A.magnet_depth + 1) for x, y, r in magnets])
# joint magnets: horizontal pockets in the centre wall, the same on both sides of the joint
# (facing pairs), spread along the wall inside the frame; only where the wall (table to
# z = 0) is tall enough for the magnet plus --joint-margin above and below it
joint, joint_ys, mr = [], [], 0
if A.wall > 0 and A.joint_magnets > 0 and magnets:
    mr = magnets[0][2]
    jb = (up(case, 0, 1) & Pos(xj, 0, 0) * Box(0.01, 1000, 10)).bounding_box()
    yn, ys = jb.max.Y - A.frame, jb.min.Y + A.frame
    for k in range(A.joint_magnets):
        y = yn + (ys - yn) * (k + 0.5) / A.joint_magnets
        joint_ys.append(round(y, 3))
        h = A.north + (ymax - y) * t
        if h >= 2 * mr + 2 * A.joint_margin:
            joint.append((round(y, 3), -h / 2))
            body = body - Pos(xj, y, -h / 2) * Rot(0, 90, 0) * Cylinder(mr, 2 * A.magnet_depth)
body = body.clean()
# keep what is above the table plane (normal tilted towards the north)
s, c = math.sin(math.radians(A.angle)), math.cos(math.radians(A.angle))
table = Plane(origin=(0, ymax, -A.north), x_dir=(1, 0, 0), z_dir=(0, -s, c))
body = body & (table.location * Box(2000, 2000, 1000, align=(Align.CENTER, Align.CENTER, Align.MIN)))
tag = '%s_%gdeg' % (A.name, A.angle)
export_step(body, os.path.join(A.out, tag + '_assembly.step'))
south = A.north + (ymax - ymin) * t
print('%s: tilt %.1f deg, thickness %.1f mm (north) .. %.1f mm (south), depth %.1f mm, %d magnet columns, '
      '%d joint magnet pairs %s' % (tag, A.angle, A.north, south, ymax - ymin, len(sockets), len(joint),
                                    ' '.join('(y %.1f, z %.1f)' % j for j in joint)))
for side in ('left', 'right'):
    cut = up(outline_face(O('cut_' + side)), -H - 2, H + A.pocket + 10)
    half = body & cut
    # print orientation: the table plane onto z = 0
    p = Rot(-A.angle, 0, 0) * half
    p = Pos(0, 0, -p.bounding_box().min.Z) * p
    b2 = p.bounding_box()
    export_step(p, os.path.join(A.out, '%s_%s.step' % (tag, side)))
    export_stl(p, os.path.join(A.stl_dir or A.out, '%s_%s.stl' % (tag, side)))
    print('  %-5s %d solid(s), volume %7.0f mm3, print size %.1f x %.1f x %.1f mm'
          % (side, len(p.solids()), p.volume, b2.size.X, b2.size.Y, b2.size.Z))

if A.json:
    import json
    from fusion_data import loop_data
    def face_loops(face):
        out = []
        for f in face.faces():
            segs, poly, b = loop_data(f.outer_wire()); out.append({'depth': 0, 'bbox': [round(v, 4) for v in b], 'segs': segs})
            for w in f.inner_wires():
                segs, poly, b = loop_data(w); out.append({'depth': 1, 'bbox': [round(v, 4) for v in b], 'segs': segs})
        return out
    def circle_loops(cs, dr=0):
        return [{'depth': 0, 'bbox': [x - r + dr, y - r + dr, x + r - dr, y + r - dr],
                 'segs': [{'t': 'C', 'c': [round(x, 5), round(y, 5)], 'r': round(r - dr, 5)}]} for x, y, r in cs]
    data = json.load(open(A.json, encoding='utf-8'))
    for n in [k for k in data['outlines'] if k.startswith('wedge_')]:
        if n not in ('wedge_socket', 'wedge_magnet'): del data['outlines'][n]   # older wedge versions
    sk2 = union([up(f, 0, 1) for f in skeleton]).clean() & up(outer, -1, 3)
    data['outlines']['wedge_skeleton'] = face_loops(sk2.faces().filter_by(Axis.Z).sort_by(Axis.Z)[0])
    data['outlines']['wedge_rim'] = face_loops(rim)
    data['outlines']['wedge_column'] = circle_loops(sockets, A.column_clear)
    data['outlines']['wedge_magnet'] = circle_loops(magnets)
    for side in ('left', 'right'):
        data['outlines'].setdefault('cut_' + side, [])
    Hf = A.north + (ymax - ymin) * math.tan(math.radians(A.max_angle)) + 5
    obb = outer.bounding_box()
    for side in ('left', 'right'):
        data['cases']['wedge_' + side] = [
            {'name': 'wedge_skeleton', 'shift': [0, 0, round(-Hf, 3)], 'extrude': round(Hf, 3)},
            {'name': 'wedge_rim', 'operation': 'add', 'shift': [0, 0, 0], 'extrude': A.pocket},
            {'name': 'wedge_column', 'operation': 'add', 'shift': [0, 0, 0], 'extrude': A.column},
            {'name': 'wedge_magnet', 'operation': 'subtract', 'shift': [0, 0, round(A.column - A.magnet_depth, 3)],
             'extrude': A.magnet_depth + 1},
            {'name': 'wedge_joint_magnets', 'operation': 'side_holes', 'x': round(xj, 4), 'ys': joint_ys,
             'r': mr, 'depth': A.magnet_depth, 'margin': A.joint_margin, 'north_y': round(ymax, 4), 'north_z': -A.north},
            {'name': 'cut_' + side, 'operation': 'intersect', 'shift': [0, 0, round(-Hf - 2, 3)], 'extrude': round(Hf + A.pocket + 10, 3)},
            {'name': 'wedge_tilt', 'operation': 'tilt', 'north_y': round(ymax, 4), 'north_z': -A.north,
             'x0': round(obb.min.X, 3), 'x1': round(obb.max.X, 3)}]
    data['wedge'] = {'angle': A.angle, 'max_angle': A.max_angle, 'north': A.north}
    json.dump(data, open(A.json, 'w'), separators=(',', ':'))
    print('added wedge_left / wedge_right to %s (Fusion tilt up to %g deg)' % (A.json, A.max_angle))
