# Autodesk Fusion script: rebuild a keyboard case as an editable, parametric
# design (one component per part, sketches + extrudes + combines in the timeline).
#
# Install: Fusion > Utilities > Add-Ins > Scripts and Add-Ins > "+" (or the green
# plus next to "My Scripts") > pick this KeyboardCase folder. Run it and choose a
# data file: <keyboard>/case/fusion/<design>_case.json (made by tools/step.sh).
#
# Every case part is built like Ergogen's JSCAD: the first recipe entry is the
# base body, every next entry is an outline sketch extruded from z = shift[2] by
# `extrude` mm and joined / cut / intersected. Sketches are plain lines, arcs and
# circles in case coordinates (mm), so they can be edited and the timeline replays.
#
# Optional plate ribs (asked at start): a rib frame under the switch plate around
# every switch cutout, leaving a relief gap so the switches and stabilizers still
# snap in; neighbouring frames merge into a web. Clipped 0.5 mm inside the PCB
# outline, with the plate's holes cut through. The depth is the user parameter
# `plate_rib` (Modify > Change Parameters); gap and width are fixed per run.
#
# Optional tilt wedge (asked at start, if the data has one): wedge_left / wedge_right, a
# printed wedge under the tub that raises the south edge so the key plane tilts. Built in
# the tub's frame (the tub floor is z = 0): the "tilt" recipe step splits it along a table
# plane at the user parameter `tilt_angle`, so changing it re-shapes the wedge.
#
# Top edges (TOP_EDGES, per design, Fusion only: the STL / STEP files don't have them): the top
# outside edge of the lid plate (chamfer, user parameter `lid_chamfer`) and of the wedge rim
# (fillet, `wedge_fillet`), and two-distance chamfers (`*_chamfer_h` across the top, `*_chamfer_v` down the side) on
# the trackpad ring's top outer circle and the centre cover's top outline, as the last step of each part. Not along the joint between the halves
# or round the centre openings.
#
# Threads (THREADS, per design, Fusion only): a modeled thread on the cylinder face of the given
# radius (the yaml's plain collar / bore), then its faces offset by the user parameter
# `thread_play` (per side, normal to the faces) so a printed pair turns: hachigo74's trackpad ring
# screws onto the centre cover's collar (M50x1.5, cover external, ring internal).
import adsk.core, adsk.fusion, traceback, json, os, math

MM = 0.1            # Fusion's internal unit is cm
# design -> part name prefix -> (kind, user parameter, size in mm)
TOP_EDGES = {'hachigo74': {'lid': ('chamfer', 'lid_chamfer', 0.5), 'wedge': ('fillet', 'wedge_fillet', 1.5),
                           'trackpad_ring': ('chamfer2', ('ring_chamfer_h', 'ring_chamfer_v'), (3.0, 1.0)),
                           'center_cover': ('chamfer2', ('cover_chamfer_h', 'cover_chamfer_v'), (2.5, 1.0))}}
# 'chamfer2': a two-distance chamfer (horizontal into the top face, vertical down the side; user 2026-11-07) round the
# whole outer loop of the part's largest top face; its direction is checked per edge with probe points afterwards
# and the edge set flipped if it came out the other way round.
# design -> part name prefix -> [(name, (horizontal, vertical) user parameters, sizes mm, hole box (w, h) mm)]: a
# two-distance chamfer round a hole in the part's largest top face (the inner loop whose box matches w x h)
TOP_HOLES = {'hachigo74': {'center_cover': [('OLED window', ('window_chamfer_h', 'window_chamfer_v'), (1.0, 0.5), (24.0, 14.0))]}}
# design -> part -> [(name, (horizontal, vertical) user parameters, sizes mm, z of the face mm)]: two-distance chamfer on the
# straight y-direction edges at the east and west ends of the upward face at that z (the T clip's bar: a lead-in so the
# plates slide over it, user 2026-11-07)
END_CHAMFERS = {'hachigo74': {'cover_clip': [('bar end', ('clip_chamfer_h', 'clip_chamfer_v'), (1.5, 0.5), 11.25)]}}
# design -> part name -> (face radius mm, internal, designation, class); play = THREAD_PLAY mm per side
THREADS = {'hachigo74': {'center_cover': (25.0, False, 'M50x1.5', '6g'),
                         'trackpad_ring': (24.188, True, 'M50x1.5', '6H')}}
THREAD_PLAY = 0.1


def P(x, y):
    return adsk.core.Point3D.create(x * MM, y * MM, 0)


def draw_outline(comp, name, loops, sx, sy):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name if not (sx or sy) else '%s @%g,%g' % (name, sx, sy)
    sk.isComputeDeferred = True
    lines, arcs, circles = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchCircles
    for loop in loops:
        pts = []                                    # shared end points -> connected loops

        def sp(p):                                  # the sketch point already at p (1 um), if any
            for (x, y), o in pts:
                if abs(x - p[0]) < 1e-3 and abs(y - p[1]) < 1e-3: return o
            return None

        def keep(p, o):
            pts.append(((p[0], p[1]), o))

        for s in loop['segs']:
            if s['t'] == 'C':
                circles.addByCenterRadius(P(s['c'][0] + sx, s['c'][1] + sy), s['r'] * MM)
                continue
            q = [[p[0] + sx, p[1] + sy] for p in s['p']]
            a, b = q[0], q[-1]
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-3:
                continue                            # a dot (offset leftovers): the neighbours meet anyway
            m = q[1] if s['t'] == 'A' else None
            # nearly straight arcs (sagitta < 1 um, e.g. 0.1 mm offset slivers) are invalid in Fusion
            if m and abs((m[0] - a[0]) * (b[1] - a[1]) - (m[1] - a[1]) * (b[0] - a[0])) \
                    / math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-3:
                m = None
            arc = None
            if m:
                try: arc = arcs.addByThreePoints(P(*a), P(*m), P(*b))
                except RuntimeError: arc = None
            if arc is None:
                ln = lines.addByTwoPoints(sp(a) or P(*a), sp(b) or P(*b))
                keep(a, ln.startSketchPoint); keep(b, ln.endSketchPoint)
            else:
                # Fusion keeps arcs counter-clockwise: for a clockwise (concave) arc its
                # "start" point is our end point, so pair the points by position
                for e in (arc.startSketchPoint, arc.endSketchPoint):
                    p = (e.geometry.x / MM, e.geometry.y / MM)
                    o = sp(p)
                    if o is None: keep(p, e)
                    else:
                        try: o.merge(e)
                        except Exception: pass
    sk.isComputeDeferred = False
    return sk


def draw_rects(comp, name, keys, grow):
    """Each key rectangle [cx, cy, angle, x0, y0, x1, y1] grown by `grow` mm."""
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for cx, cy, a, x0, y0, x1, y1 in keys:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        q = [(x0 - grow, y0 - grow), (x1 + grow, y0 - grow), (x1 + grow, y1 + grow), (x0 - grow, y1 + grow)]
        q = [P(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in q]
        first = prev = lines.addByTwoPoints(q[0], q[1])
        for k in (2, 3):
            prev = lines.addByTwoPoints(prev.endSketchPoint, q[k])
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    sk.isComputeDeferred = False
    return sk


def rib_extrude(comp, sk, op, top, depth, name, participants=None):
    """Extrude all profiles of sk downward from z = top (mm) by the expression depth."""
    ext = comp.features.extrudeFeatures
    ei = ext.createInput(all_profiles(sk), op)
    ei.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(top * MM))
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(depth)),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if participants is not None: ei.participantBodies = participants
    f = ext.add(ei)
    f.name = name
    return [f.bodies.item(k) for k in range(f.bodies.count)]


def add_ribs(comp, bodies, sketches, rib, opt, log):
    """Rib frames under the plate around every switch cutout, joined to the lid."""
    feats, NEW = comp.features, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    z, gap, width = rib['plate_z'], opt['gap'], opt['width']
    ribs = rib_extrude(comp, draw_rects(comp, 'plate rib frames', rib['keys'], gap + width), NEW, z, 'plate_rib', 'rib frames')
    rib_extrude(comp, draw_rects(comp, 'plate rib relief', rib['keys'], gap), CUT, z + 0.1, 'plate_rib + 0.2 mm', 'rib relief', ribs)
    for d, sk in sketches.get((rib['plate_holes'], 0, 0), []):          # the plate's own holes
        if d % 2 == 1:
            rib_extrude(comp, sk, CUT, z + 0.1, 'plate_rib + 0.2 mm', 'rib plate holes', ribs)
    ribs = [b for b in ribs if b.isValid]
    region = rib_extrude(comp, draw_outline(comp, 'plate rib region', [l for l in rib['region'] if l['depth'] == 0], 0, 0),
                         NEW, z, 'plate_rib', 'rib region')
    for t, target in enumerate(ribs):
        tools = adsk.core.ObjectCollection.create()
        for b in region: tools.add(b)
        ci = feats.combineFeatures.createInput(target, tools)
        ci.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        ci.isKeepToolBodies = t < len(ribs) - 1
        try: feats.combineFeatures.add(ci)
        except Exception as e: log.append('%s: rib clip failed (%s)' % (comp.name, e))
    tools = adsk.core.ObjectCollection.create()
    for b in ribs:
        if b.isValid: tools.add(b)
    if tools.count:
        ci = feats.combineFeatures.createInput(bodies[0], tools)
        ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        try: feats.combineFeatures.add(ci)
        except Exception as e: log.append('%s: rib join failed (%s)' % (comp.name, e))


def side_holes(comp, bodies, item, log):
    """Joint magnet pockets: horizontal holes (radius r, depth on each side) through the plane
    x = item x, at the candidate ys where the wedge wall (table to z = 0, at the tilt_angle
    set now) is tall enough for the hole plus margin above and below; centred in its height.
    Placed at build time: after a smaller tilt_angle, check they still fit."""
    p = adsk.fusion.Design.cast(comp.parentDesign).userParameters.itemByName('tilt_angle')
    if p is None: return
    t = math.tan(p.value)
    holes = []
    for y in item['ys']:
        h = -item['north_z'] + (item['north_y'] - y) * t
        if h >= 2 * item['r'] + 2 * item['margin']: holes.append((y, -h / 2))
    log.append('%s: %d of %d joint magnets fit at %.1f deg' % (comp.name, len(holes), len(item['ys']), math.degrees(p.value)))
    if not holes: return
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.yZConstructionPlane, adsk.core.ValueInput.createByReal(item['x'] * MM))
    pl = planes.add(pi)
    pl.name = 'wedge joint plane'
    sk = comp.sketches.add(pl)
    sk.name = 'wedge joint magnets'
    for y, z in holes:
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(adsk.core.Point3D.create(item['x'] * MM, y * MM, z * MM)), item['r'] * MM)
    feats = comp.features
    ei = feats.extrudeFeatures.createInput(all_profiles(sk), adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByReal(2 * item['depth'] * MM), True)
    ei.participantBodies = [b for b in bodies if b.isValid]
    feats.extrudeFeatures.add(ei).name = 'joint magnet pockets'
    for o in (pl, sk):
        try: o.isLightBulbOn = False
        except Exception: pass


def tilt_split(comp, bodies, item, log):
    """Cut the wedge along the table plane: through the line y = north_y, z = north_z
    (along x), tilted by the user parameter tilt_angle so it falls towards the south
    (the wedge gets thicker there); the part below the plane is removed."""
    feats = comp.features
    y, z = item['north_y'], item['north_z']
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(z * MM))
    base = planes.add(pi)
    base.name = 'wedge north line plane'
    sk = comp.sketches.add(base)
    sk.name = 'wedge tilt axis'
    x0, x1 = item.get('x0', -1000), item.get('x1', 1000)  # the axis only as long as the wedge (plane size)
    a = sk.modelToSketchSpace(adsk.core.Point3D.create(x0 * MM, y * MM, z * MM))
    b = sk.modelToSketchSpace(adsk.core.Point3D.create(x1 * MM, y * MM, z * MM))
    axis = sk.sketchCurves.sketchLines.addByTwoPoints(a, b)
    table = None
    for expr in ('tilt_angle', '-tilt_angle'):           # the sign that makes the plane fall to the south
        pi = planes.createInput()
        pi.setByAngle(axis, adsk.core.ValueInput.createByString(expr), base)
        pl = planes.add(pi)
        n = pl.geometry.normal
        if n.y * n.z < 0:                                 # normal (0, -sin, cos): rises to the north
            table = pl; break
        pl.deleteMe()
    if table is None:
        log.append('%s: could not orient the tilt plane' % comp.name); return
    table.name = 'wedge table plane (tilt_angle)'
    for o in (base, table, sk):                           # hidden by default (Browser: light bulb)
        try: o.isLightBulbOn = False
        except Exception: pass
    for body in [b for b in bodies if b.isValid]:
        si = feats.splitBodyFeatures.createInput(body, table, True)
        try:
            sf = feats.splitBodyFeatures.add(si)
        except Exception as e:
            log.append('%s: tilt split failed (%s)' % (comp.name, e)); continue
        sf.name = 'tilt split'
        parts = [sf.bodies.item(k) for k in range(sf.bodies.count)]
        if len(parts) > 1:                                # drop the piece under the table
            low = min(parts, key=lambda p: p.boundingBox.maxPoint.z)
            feats.removeFeatures.add(low).name = 'remove below table'


def all_profiles(sk):
    """Every profile of the sketch except zero-area slivers (where an arc meets another curve
    within a micron, e.g. the cover's r3 fillets on its r29.3 circle; extruding one fails)."""
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        p = sk.profiles.item(i)
        if p.areaProperties().area * 100 >= 0.01:
            c.add(p)
    return c


def build_part(comp, recipe, outlines, log, rib=None, rib_opt=None):
    feats = comp.features
    bodies, sketches = [], {}
    for i, item in enumerate(recipe):
        name = item['name']
        if item.get('operation') == 'tilt':
            tilt_split(comp, bodies, item, log)
            bodies = [b for b in comp.bRepBodies if b.isValid]
            continue
        if item.get('operation') == 'side_holes':
            side_holes(comp, bodies, item, log)
            continue
        loops = outlines.get(name) or []
        if not loops:
            log.append('%s: outline %s is empty, skipped' % (comp.name, name)); continue
        sx, sy, sz = (list(item.get('shift') or []) + [0, 0, 0])[:3]
        # one sketch per nesting depth: loops of the same depth never nest, so every
        # profile of a sketch is the same kind (even depth = filled, odd = hole)
        key = (name, sx, sy)
        if key not in sketches:
            depths = sorted({l['depth'] for l in loops})
            sketches[key] = [(d, draw_outline(comp, name if d == 0 else '%s (depth %d)' % (name, d),
                                              [l for l in loops if l['depth'] == d], sx, sy)) for d in depths]
        dist = adsk.core.ValueInput.createByReal(item['extrude'] * MM)
        op = item.get('operation', 'add') if bodies else 'base'
        new = []
        for d, sk in sketches[key]:
            prof = all_profiles(sk)
            if prof.count == 0:
                log.append('%s / %s: no profile at depth %d' % (comp.name, name, d)); continue
            hole = d % 2 == 1
            if hole and not new: continue
            ei = feats.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation if hole
                                                   else adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ei.setDistanceExtent(False, dist)
            if sz:
                ei.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(sz * MM))
            if hole: ei.participantBodies = new
            ex = feats.extrudeFeatures.add(ei)
            ex.name = '%02d %s %s%s' % (i, op, name, ' holes' if hole else ('' if d == 0 else ' islands'))
            if not hole:
                new += [ex.bodies.item(k) for k in range(ex.bodies.count)]
        new = [b for b in new if b.isValid]
        if not new:
            log.append('%s / %s: nothing extruded, skipped' % (comp.name, name)); continue
        if op == 'base':
            bodies = new
            if rib and rib_opt and comp.name.startswith('lid'):
                add_ribs(comp, bodies, sketches, rib, rib_opt, log)
            continue
        kind = {'add': adsk.fusion.FeatureOperations.JoinFeatureOperation,
                'subtract': adsk.fusion.FeatureOperations.CutFeatureOperation,
                'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation}[op]
        if op == 'add':
            tools = adsk.core.ObjectCollection.create()
            for b in new: tools.add(b)
            ci = feats.combineFeatures.createInput(bodies[0], tools)
            ci.operation = kind; ci.isKeepToolBodies = False
            try:
                feats.combineFeatures.add(ci)
            except Exception:
                bodies += new                       # disjoint lump: keep it as its own body
        else:
            for t, target in enumerate(list(bodies)):
                tools = adsk.core.ObjectCollection.create()
                for b in new: tools.add(b)
                ci = feats.combineFeatures.createInput(target, tools)
                ci.operation = kind
                ci.isKeepToolBodies = t < len(bodies) - 1   # tools are used by every body, removed after the last
                try:
                    feats.combineFeatures.add(ci)
                except Exception as e:
                    log.append('%s: %s %s failed (%s)' % (comp.name, op, name, e))
    for k, b in enumerate([b for b in bodies if b.isValid]):
        b.name = comp.name if k == 0 else '%s %d' % (comp.name, k + 1)


def top_outer_edges(body, right):
    """The body's top outside edge: on its largest top face, the longest chain of the outer loop
    between two points on the joint plane (the body's inner x side). The joint line itself and
    the notches round the centre openings are the other chains."""
    planar = adsk.core.SurfaceTypes.PlaneSurfaceType
    tops = [f for f in body.faces if f.geometry.surfaceType == planar and abs(f.evaluator.getNormalAtPoint(f.pointOnFace)[1].z - 1) < 1e-6]
    zmax = max(f.pointOnFace.z for f in tops)
    top = max([f for f in tops if abs(f.pointOnFace.z - zmax) < 1e-6], key=lambda f: f.area)
    jx = body.boundingBox.minPoint.x if right else body.boundingBox.maxPoint.x
    on = lambda v: abs(v.geometry.x - jx) < 1e-5
    loop = [l for l in top.loops if l.isOuter][0]
    ces = [loop.coEdges.item(i) for i in range(loop.coEdges.count)]
    if len(ces) == 1:           # a round part (the trackpad ring): its whole outer circle
        return [ces[0].edge]
    ends = lambda c: (c.edge.endVertex, c.edge.startVertex) if c.isOpposedToEdge else (c.edge.startVertex, c.edge.endVertex)
    first = [i for i, c in enumerate(ces) if on(ends(c)[0]) and not on(ends(c)[1])]
    if not first: return []
    chains, cur = [], []
    for c in ces[first[0]:] + ces[:first[0]]:
        a, b = ends(c)
        if on(a) and on(b): continue
        cur.append(c.edge)
        if on(b):
            chains.append(cur); cur = []
    return max(chains, key=lambda ch: sum(e.length for e in ch)) if chains else []


def largest_top_loop(body):
    """The outer loop of the body's largest upward planar face (all of it: a closed outline) and that face's z."""
    planar = adsk.core.SurfaceTypes.PlaneSurfaceType
    tops = [f for f in body.faces if f.geometry.surfaceType == planar and abs(f.evaluator.getNormalAtPoint(f.pointOnFace)[1].z - 1) < 1e-6]
    if not tops:
        return [], 0
    top = max(tops, key=lambda f: f.area)
    loop = [l for l in top.loops if l.isOuter][0]
    return [loop.coEdges.item(i).edge for i in range(loop.coEdges.count)], top.pointOnFace.z


def edge_probes(body, edges, ztop):
    """Per edge: its mid point and the horizontal unit direction into the body (tested just under the top)."""
    out = []
    INS = adsk.fusion.PointContainment.PointInsidePointContainment
    for e in edges:
        ev = e.evaluator
        _, t0, t1 = ev.getParameterExtents()
        tm = (t0 + t1) / 2
        _, p = ev.getPointAtParameter(tm)
        _, d = ev.getFirstDerivative(tm)
        n = math.hypot(d.x, d.y)
        if n < 1e-9:
            continue
        nx, ny = -d.y / n, d.x / n
        if body.pointContainment(adsk.core.Point3D.create(p.x + nx * 0.02, p.y + ny * 0.02, ztop - 0.01)) != INS:
            nx, ny = -nx, -ny
        out.append((p.x, p.y, nx, ny))
    return out


def chamfer_ok(body, probes, ztop, h, v):
    """How many probes show the chamfer h (mm) across the top and v down the side, not the other way round:
    solid at 1/4 h in, 0.9 v down (under the slope), empty at 3/4 h in, 0.1 v down (above it)."""
    INS = adsk.fusion.PointContainment.PointInsidePointContainment
    good = 0
    for x, y, nx, ny in probes:
        a = body.pointContainment(adsk.core.Point3D.create(x + nx * 0.25 * h * MM, y + ny * 0.25 * h * MM, ztop - 0.9 * v * MM)) == INS
        b = body.pointContainment(adsk.core.Point3D.create(x + nx * 0.75 * h * MM, y + ny * 0.75 * h * MM, ztop - 0.1 * v * MM)) != INS
        good += a and b
    return good


def top_hole_loop(body, size):
    """The edges of the inner loop of the body's largest upward planar face whose box is size (w, h) mm, and its z."""
    planar = adsk.core.SurfaceTypes.PlaneSurfaceType
    tops = [f for f in body.faces if f.geometry.surfaceType == planar and abs(f.evaluator.getNormalAtPoint(f.pointOnFace)[1].z - 1) < 1e-6]
    if not tops:
        return [], 0
    top = max(tops, key=lambda f: f.area)
    for l in top.loops:
        if l.isOuter:
            continue
        bb = l.boundingBox
        if abs((bb.maxPoint.x - bb.minPoint.x) / MM - size[0]) < 0.05 and abs((bb.maxPoint.y - bb.minPoint.y) / MM - size[1]) < 0.05:
            return [l.coEdges.item(i).edge for i in range(l.coEdges.count)], top.pointOnFace.z
    return [], 0


def end_edges(body, z):
    """The straight edges along y at the east and west ends (body box x min / max) of the upward planar faces at z (mm)."""
    planar = adsk.core.SurfaceTypes.PlaneSurfaceType
    bb = body.boundingBox
    out = []
    for f in body.faces:
        if f.geometry.surfaceType != planar or abs(f.evaluator.getNormalAtPoint(f.pointOnFace)[1].z - 1) > 1e-6 or abs(f.pointOnFace.z / MM - z) > 1e-3:
            continue
        for e in f.edges:
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.x - b.x) < 1e-6 and min(abs(a.x - bb.minPoint.x), abs(a.x - bb.maxPoint.x)) < 1e-6:
                out.append(e)
    return out


def top_chamfer2(comp, body, param, log, edges=None, ztop=0, what='top outside chamfer'):
    """Two-distance chamfer round the outer loop of the largest top face (param = (horizontal, vertical) names),
    or round the given edges of a top face at ztop."""
    if edges is None:
        edges, ztop = largest_top_loop(body)
    if not edges:
        log.append('%s: no edges, no %s' % (comp.name, what))
        return
    probes = edge_probes(body, edges, ztop)
    up = comp.parentDesign.userParameters
    h, v = (up.itemByName(n).value / MM for n in param)
    try:
        for flip in (False, True):
            col = adsk.core.ObjectCollection.create()
            for e in edges:
                col.add(e)
            ci = comp.features.chamferFeatures.createInput2()
            ci.chamferEdgeSets.addTwoDistancesChamferEdgeSet(col, adsk.core.ValueInput.createByString(param[0]),
                                                             adsk.core.ValueInput.createByString(param[1]), flip, False)
            feature = comp.features.chamferFeatures.add(ci)
            good = chamfer_ok(max([b for b in comp.bRepBodies if b.isValid], key=lambda b: b.volume), probes, ztop, h, v)
            if good == len(probes) or flip:
                break
            feature.deleteMe()
        feature.name = what
        log.append('%s: %s %g x %g on %d edges (flipped %s), %d of %d probes the right way round'
                   % (comp.name, what, h, v, len(edges), flip, good, len(probes)))
    except Exception as e:
        log.append('%s: %s failed (%s)' % (comp.name, what, e))


def top_edge(comp, kind, param, log):
    """Fillet or chamfer the top outside edge of the part's body, size = the user parameter."""
    bodies = [b for b in comp.bRepBodies if b.isValid]
    if not bodies:
        log.append('%s: no body for the top %s' % (comp.name, kind)); return
    body = max(bodies, key=lambda b: b.volume)
    if kind == 'chamfer2':
        top_chamfer2(comp, body, param, log)
        return
    edges = top_outer_edges(body, comp.name.endswith('right'))
    if not edges:
        log.append('%s: top outside edge not found, no %s' % (comp.name, kind)); return
    col = adsk.core.ObjectCollection.create()
    for e in edges: col.add(e)
    size = adsk.core.ValueInput.createByString(param)
    try:
        if kind == 'chamfer':
            ci = comp.features.chamferFeatures.createInput2()
            ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, size, False)
            feature = comp.features.chamferFeatures.add(ci)
        else:
            fi = comp.features.filletFeatures.createInput()
            fi.edgeSetInputs.addConstantRadiusEdgeSet(col, size, False)
            feature = comp.features.filletFeatures.add(fi)
        feature.name = 'top outside ' + kind
        log.append('%s: top outside %s on %d edges' % (comp.name, kind, len(edges)))
    except Exception as e:
        log.append('%s: top outside %s failed (%s)' % (comp.name, kind, e))


def add_thread(comp, radius, internal, designation, cls, log):
    """Modeled ISO metric thread on the part's cylinder face of `radius` (mm), its faces then
    offset by -thread_play so the printed pair has play (Fusion's thread size doesn't follow
    the face: it is the designation's, the face only has to be near it)."""
    faces = [f for b in comp.bRepBodies for f in b.faces
             if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType
             and abs(f.geometry.radius / MM - radius) < 0.01]
    if len(faces) != 1:
        log.append('%s: %d cylinder faces of r %g, no thread' % (comp.name, len(faces), radius)); return
    tf = comp.features.threadFeatures
    try:
        col = adsk.core.ObjectCollection.create(); col.add(faces[0])
        ti = tf.createInput(col, tf.createThreadInfo(internal, 'ISO Metric profile', designation, cls))
        ti.isModeled = True
        ti.isFullLength = True
        thread = tf.add(ti)
        thread.name = '%s %s thread' % (designation, 'internal' if internal else 'external')
    except Exception as e:
        log.append('%s: %s thread failed (%s)' % (comp.name, designation, e)); return
    body = thread.bodies.item(0) if thread.bodies.count else faces[0].body
    # the thread's faces (helical flanks, crest, root): the non-planar faces that go round the
    # whole thread, i.e. whose outer size is between the thread's minor and major diameter
    keep = []
    for f in body.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        bb = f.boundingBox
        w, h = (bb.maxPoint.x - bb.minPoint.x) / MM, (bb.maxPoint.y - bb.minPoint.y) / MM
        if 2 * 23.9 < w < 2 * 25.2 and 2 * 23.9 < h < 2 * 25.2:
            keep.append(f)
    try:
        of = comp.features.offsetFacesFeatures
        off = of.add(of.createInput(keep, adsk.core.ValueInput.createByString('-thread_play')))
        off.name = 'thread play'
        log.append('%s: %s %s thread, %d faces offset by thread_play' % (comp.name, designation,
                   'internal' if internal else 'external', len(keep)))
    except Exception as e:
        log.append('%s: thread play offset failed (%s)' % (comp.name, e))


def build_design(data, ribs=None, tilt=None):
    """Build every part of the case data in a new design. ribs = (depth, gap, width) mm or
    None, tilt = wedge angle (deg) or None (no wedge parts). Returns the log lines.
    Called by run() after its dialogs, or directly (tools/fusion/Bridge)."""
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    root = design.rootComponent
    rib, rib_opt = data.get('rib'), None
    if rib and ribs:
        depth, gap, width = ribs
        rib_opt = {'gap': gap, 'width': width}
        design.userParameters.add('plate_rib', adsk.core.ValueInput.createByString('%g mm' % depth), 'mm',
                                  'plate rib depth below the switch plate (max %.2f)' % (rib['plate_z'] - rib['pcb_top']))
    cases = dict(data['cases'])
    wedge = data.get('wedge')
    if wedge and tilt:
        design.userParameters.add('tilt_angle', adsk.core.ValueInput.createByString('%g deg' % tilt), 'deg',
                                  'tilt wedge: key plane angle, south edge up (max %g)' % wedge['max_angle'])
    else:
        cases = {k: v for k, v in cases.items() if not k.startswith('wedge_')}
    top_edges = TOP_EDGES.get(data.get('design'), {})
    for prefix, (kind, param, size) in top_edges.items():
        if any(k.startswith(prefix) for k in cases):
            if kind == 'chamfer2':
                for pn, sz, d in zip(param, size, ('horizontal (across the top)', 'vertical (down the side)')):
                    design.userParameters.add(pn, adsk.core.ValueInput.createByString('%g mm' % sz), 'mm', 'top outside chamfer of the %s, %s' % (prefix, d))
            else:
                design.userParameters.add(param, adsk.core.ValueInput.createByString('%g mm' % size), 'mm', 'top outside edge %s of the %s' % (kind, prefix))
    top_holes = TOP_HOLES.get(data.get('design'), {})
    end_chamfers = END_CHAMFERS.get(data.get('design'), {})
    for part, items in end_chamfers.items():
        if part in cases:
            for what, param, size, z in items:
                for pn, sz, d in zip(param, size, ('horizontal (along the top)', 'vertical (down the end)')):
                    design.userParameters.add(pn, adsk.core.ValueInput.createByString('%g mm' % sz), 'mm', '%s chamfer of the %s, %s' % (what, part, d))
    for prefix, holes in top_holes.items():
        if any(k.startswith(prefix) for k in cases):
            for what, param, size, box in holes:
                for pn, sz, d in zip(param, size, ('horizontal (across the top)', 'vertical (down the opening)')):
                    design.userParameters.add(pn, adsk.core.ValueInput.createByString('%g mm' % sz), 'mm', '%s top edge chamfer, %s' % (what, d))
    threads = THREADS.get(data.get('design'), {})
    if any(k in cases for k in threads):
        design.userParameters.add('thread_play', adsk.core.ValueInput.createByString('%g mm' % THREAD_PLAY), 'mm',
                                  'play per side on the printed threads (faces offset normal to the flanks)')
    # (the root component can't be renamed; it takes the name the design is saved under)
    log, tl = [], design.timeline
    for part, recipe in cases.items():
        start = tl.markerPosition
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = part
        build_part(comp, recipe, data['outlines'], log, rib, rib_opt)
        for prefix, (kind, param, size) in top_edges.items():
            if part.startswith(prefix):
                top_edge(comp, kind, param, log)
        for prefix, holes in top_holes.items():
            if part.startswith(prefix):
                for what, param, size, box in holes:
                    body = max([b for b in comp.bRepBodies if b.isValid], key=lambda b: b.volume)
                    edges, ztop = top_hole_loop(body, box)
                    top_chamfer2(comp, body, param, log, edges, ztop, what + ' chamfer')
        for what, param, size, z in end_chamfers.get(part, []):
            body = max([b for b in comp.bRepBodies if b.isValid], key=lambda b: b.volume)
            top_chamfer2(comp, body, param, log, end_edges(body, z), z * MM, what + ' chamfer')
        if part in threads:
            add_thread(comp, *threads[part], log)
        adsk.doEvents()
        try:
            if tl.markerPosition - 1 > start:
                tl.timelineGroups.add(start, tl.markerPosition - 1).name = part
        except Exception:
            pass
    return ['Built %d parts of %s.' % (len(cases), data.get('design', ''))] + log


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        dlg = ui.createFileDialog()
        dlg.title = 'Keyboard case data (case/fusion/<design>_case.json)'
        dlg.filter = 'Case data (*_case.json);;All files (*.*)'
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        data = json.load(open(dlg.filename, encoding='utf-8'))
        rib, ribs, tilt = data.get('rib'), None, None
        if rib:
            room = rib['plate_z'] - rib['pcb_top']
            txt, cancelled = ui.inputBox(
                'Plate ribs under the switch plate (empty = none):\n'
                'depth below the plate, relief gap around each switch, rib width  [mm]\n'
                '(depth max %.2f = down to the PCB top; width > 1.45 merges neighbouring frames)' % room,
                'Plate ribs', '1.0, 1.0, 1.5')
            if cancelled: return
            if txt.strip() and txt.strip() != '0':
                ribs = [float(v) for v in txt.replace(';', ',').split(',')]
                if not 0 < ribs[0] <= room + 1e-6:
                    ui.messageBox('Rib depth must be > 0 and <= %.2f mm' % room); return
        wedge = data.get('wedge')
        if wedge:
            txt, cancelled = ui.inputBox(
                'Tilt wedge under the tub, south edge raised (empty or 0 = no wedge):\n'
                'key plane angle in degrees (up to %g); change it later as the user parameter tilt_angle' % wedge['max_angle'],
                'Tilt wedge', '%g' % wedge['angle'])
            if cancelled: return
            if txt.strip() and float(txt) != 0:
                tilt = float(txt)
                if not 0 < tilt <= wedge['max_angle']:
                    ui.messageBox('Tilt angle must be > 0 and <= %g degrees' % wedge['max_angle']); return
        log = build_design(data, ribs, tilt)
        ui.messageBox(log[0] + (('\n\n' + '\n'.join(log[1:])) if len(log) > 1 else ''))
    except Exception:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
