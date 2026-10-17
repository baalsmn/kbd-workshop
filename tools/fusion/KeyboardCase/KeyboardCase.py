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
import adsk.core, adsk.fusion, traceback, json, os, math

MM = 0.1            # Fusion's internal unit is cm


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
            if s['t'] == 'L':
                ln = lines.addByTwoPoints(sp(a) or P(*a), sp(b) or P(*b))
                keep(a, ln.startSketchPoint); keep(b, ln.endSketchPoint)
            else:
                arc = arcs.addByThreePoints(P(*a), P(*q[1]), P(*b))
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


def all_profiles(sk):
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count): c.add(sk.profiles.item(i))
    return c


def build_part(comp, recipe, outlines, log, rib=None, rib_opt=None):
    feats = comp.features
    bodies, sketches = [], {}
    for i, item in enumerate(recipe):
        name = item['name']
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
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent
        rib, rib_opt = data.get('rib'), None
        if rib:
            room = rib['plate_z'] - rib['pcb_top']
            txt, cancelled = ui.inputBox(
                'Plate ribs under the switch plate (empty = none):\n'
                'depth below the plate, relief gap around each switch, rib width  [mm]\n'
                '(depth max %.2f = down to the PCB top; width > 1.45 merges neighbouring frames)' % room,
                'Plate ribs', '1.0, 1.0, 1.5')
            if cancelled: return
            if txt.strip() and txt.strip() != '0':
                depth, gap, width = [float(v) for v in txt.replace(';', ',').split(',')]
                if not 0 < depth <= room + 1e-6:
                    ui.messageBox('Rib depth must be > 0 and <= %.2f mm' % room); return
                rib_opt = {'gap': gap, 'width': width}
                design.userParameters.add('plate_rib', adsk.core.ValueInput.createByString('%g mm' % depth), 'mm',
                                          'plate rib depth below the switch plate (max %.2f)' % room)
        # (the root component can't be renamed; it takes the name the design is saved under)
        log, tl = [], design.timeline
        for part, recipe in data['cases'].items():
            start = tl.markerPosition
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = part
            build_part(comp, recipe, data['outlines'], log, rib, rib_opt)
            adsk.doEvents()
            try:
                if tl.markerPosition - 1 > start:
                    tl.timelineGroups.add(start, tl.markerPosition - 1).name = part
            except Exception:
                pass
        ui.messageBox('Built %d parts of %s.%s' % (len(data['cases']), data.get('design', ''),
                      ('\n\n' + '\n'.join(log)) if log else ''))
    except Exception:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
