# Rebuild the Ergogen case parts as true solids (OpenCascade via build123d) and
# export STEP files that Autodesk Fusion opens as editable bodies (real arcs and
# planar faces, not a mesh like the STL).
#
# Usage: python step_case.py <cases.json> <outlines dir> <out dir> [part ...]
#   cases.json   the design yaml's "cases" section as JSON (tools/step.sh makes it)
#   outlines dir out/outlines (Ergogen's absolute-coordinate DXF per outline)
# Each case part is rebuilt like Ergogen's JSCAD: the first entry is the base,
# every next entry is extruded (shift z, extrude height) and added / subtracted
# / intersected in order.
import sys, os, json, math
import ezdxf
from build123d import (Line, CenterArc, Edge, Wire, Face, Plane, Location, Pos, extrude,
                       export_step, Vector, Compound)

TOL = 1e-4

SNAP = 2e-3   # endpoints closer than this are the same point (Ergogen rounds its DXF)

def dxf_edges(path):
    """Edges of the DXF with all endpoints snapped together, so every loop closes.
    Arcs are rebuilt through their (snapped) end points and true mid point."""
    doc = ezdxf.readfile(path); segs = []; circles = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t == 'LINE':
            a, b = e.dxf.start, e.dxf.end; segs.append(('L', (a.x, a.y), (b.x, b.y), None))
        elif t == 'ARC':
            c = e.dxf.center; r = e.dxf.radius; s0 = math.radians(e.dxf.start_angle); s1 = math.radians(e.dxf.end_angle)
            if s1 <= s0: s1 += 2 * math.pi
            p = lambda t: (c.x + r * math.cos(t), c.y + r * math.sin(t))
            segs.append(('A', p(s0), p(s1), p((s0 + s1) / 2)))
        elif t == 'CIRCLE':
            circles.append(((e.dxf.center.x, e.dxf.center.y), e.dxf.radius))
        elif t == 'LWPOLYLINE':
            pts = [(q[0], q[1]) for q in e.get_points()]
            if e.closed: pts.append(pts[0])
            segs += [('L', p, q, None) for p, q in zip(pts, pts[1:])]
    # snap endpoints into clusters
    reps = []
    def snap(p):
        for q in reps:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < SNAP: return q
        reps.append(p); return p
    edges = []
    for kind, a, b, m in segs:
        a, b = snap(a), snap(b)
        if a == b: continue                       # collapsed (tiny) segment: its ends are merged
        if kind == 'L': edges.append(Line(a, b))
        else:
            chord = math.hypot(a[0] - b[0], a[1] - b[1])
            # tiny arcs (chord < 0.5 mm, the ones OpenJSCAD mis-draws) become straight lines
            edges.append(Line(a, b) if chord < 0.5 else Edge.make_three_point_arc(Vector(*a), Vector(*m), Vector(*b)))
    for c, r in circles:
        edges.append(CenterArc(c, r, 0, 360))
    return edges

def outline_face(path):
    """Even-odd region of all closed loops in the DXF (outer boundaries and holes)."""
    edges = dxf_edges(path)
    if not edges: return None
    wires = Wire.combine(edges, tol=1e-3)
    faces = []
    for w in wires:
        if not w.is_closed: raise RuntimeError(f'open loop in {os.path.basename(path)} ({len(w.edges())} edges)')
        faces.append(Face(w))
    faces.sort(key=lambda f: -f.area)
    region = None
    for f in faces:                       # symmetric difference = even-odd fill
        if region is None: region = f; continue
        a, b = norm(region - f), norm(f - region)
        region = a if b is None else (b if a is None else norm(a + b))
    return region

def norm(s):
    """build123d boolean results can be a Shape, a ShapeList or empty: -> Shape or None."""
    from build123d import ShapeList
    if s is None: return None
    if isinstance(s, (list, ShapeList)):
        s = [x for x in s if x is not None and getattr(x, 'area', 0) > 1e-9]
        if not s: return None
        return s[0] if len(s) == 1 else Compound(s)
    return s if getattr(s, 'area', 1) > 1e-9 else None

def build_part(recipe, outlines_dir, cache):
    solid = None
    for i, item in enumerate(recipe):
        name = item['name']
        if name not in cache: cache[name] = outline_face(os.path.join(outlines_dir, name + '.dxf'))
        face = cache[name]
        if face is None: continue
        sx, sy, sz = (list(item.get('shift') or []) + [0, 0, 0])[:3]
        body = Pos(sx, sy, sz) * extrude(face, amount=item['extrude'], dir=(0, 0, 1))   # always upwards (face normals can come out flipped)
        op = item.get('operation', 'add')
        if solid is None: solid = body
        elif op == 'add': solid = solid + body
        elif op == 'subtract': solid = solid - body
        elif op == 'intersect': solid = solid & body
        else: raise RuntimeError('unknown operation ' + op)
    return solid

def main():
    cases_json, outlines_dir, out_dir = sys.argv[1:4]
    only = set(sys.argv[4:])
    cases = json.load(open(cases_json))
    os.makedirs(out_dir, exist_ok=True)
    cache = {}
    for part, recipe in cases.items():
        if only and part not in only: continue
        solid = build_part(recipe, outlines_dir, cache)
        path = os.path.join(out_dir, part + '.step')
        export_step(solid, path)
        bb = solid.bounding_box()
        print('%-14s %3d solid(s)  volume %9.0f mm3  x %.1f..%.1f  z %.2f..%.2f  -> %s' % (
            part, len(solid.solids()), solid.volume, bb.min.X, bb.max.X, bb.min.Z, bb.max.Z, os.path.basename(path)))

if __name__ == '__main__':
    main()
