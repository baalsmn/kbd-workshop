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
# Top fillets (TOP_FILLETS, per design, Fusion only: the STL / STEP files don't have them): the
# top outside edge of the lid plate and of the wedge rim, as the last step of each part, radius =
# user parameter `lid_fillet` / `wedge_fillet`. Not along the joint between the halves or round
# the centre openings.
import adsk.core, adsk.fusion, traceback, json, os, math

MM = 0.1            # Fusion's internal unit is cm
# design -> part name prefix -> (user parameter, radius in mm)
TOP_FILLETS = {'hachigo74': {'lid': ('lid_fillet', 1.0), 'wedge': ('wedge_fillet', 1.5)}}


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
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count): c.add(sk.profiles.item(i))
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


def top_fillet(comp, param, log):
    """Fillet the top outside edge of the part's body, radius = the user parameter."""
    bodies = [b for b in comp.bRepBodies if b.isValid]
    if not bodies:
        log.append('%s: no body to fillet' % comp.name); return
    body = max(bodies, key=lambda b: b.volume)
    edges = top_outer_edges(body, comp.name.endswith('right'))
    if not edges:
        log.append('%s: top outside edge not found, no fillet' % comp.name); return
    col = adsk.core.ObjectCollection.create()
    for e in edges: col.add(e)
    fi = comp.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(col, adsk.core.ValueInput.createByString(param), False)
    try:
        comp.features.filletFeatures.add(fi).name = 'top outside fillet'
        log.append('%s: top outside fillet on %d edges' % (comp.name, len(edges)))
    except Exception as e:
        log.append('%s: top outside fillet failed (%s)' % (comp.name, e))


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
    fillets = TOP_FILLETS.get(data.get('design'), {})
    for prefix, (param, r) in fillets.items():
        if any(k.startswith(prefix) for k in cases):
            design.userParameters.add(param, adsk.core.ValueInput.createByString('%g mm' % r), 'mm', 'top outside edge fillet of the %s' % prefix)
    # (the root component can't be renamed; it takes the name the design is saved under)
    log, tl = [], design.timeline
    for part, recipe in cases.items():
        start = tl.markerPosition
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = part
        build_part(comp, recipe, data['outlines'], log, rib, rib_opt)
        for prefix, (param, r) in fillets.items():
            if part.startswith(prefix):
                top_fillet(comp, param, log)
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
