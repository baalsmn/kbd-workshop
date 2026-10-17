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
import adsk.core, adsk.fusion, traceback, json, os

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


def all_profiles(sk):
    c = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count): c.add(sk.profiles.item(i))
    return c


def build_part(comp, recipe, outlines, log):
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
            bodies = new; continue
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
        # (the root component can't be renamed; it takes the name the design is saved under)
        log, tl = [], design.timeline
        for part, recipe in data['cases'].items():
            start = tl.markerPosition
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = part
            build_part(comp, recipe, data['outlines'], log)
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
