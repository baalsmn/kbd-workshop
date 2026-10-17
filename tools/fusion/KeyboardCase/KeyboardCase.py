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
BBOX_TOL = 0.05     # mm, profile box vs. loop box


def P(x, y):
    return adsk.core.Point3D.create(x * MM, y * MM, 0)


def draw_outline(comp, name, loops, sx, sy):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name if not (sx or sy) else '%s @%g,%g' % (name, sx, sy)
    sk.isComputeDeferred = True
    lines, arcs, circles = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchCircles
    for loop in loops:
        pts = {}                                    # shared end points -> connected loops

        def sp(p):
            k = (round(p[0], 4), round(p[1], 4))
            return pts.get(k)

        def keep(p, s):
            pts[(round(p[0], 4), round(p[1], 4))] = s

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
                for p, e in ((a, arc.startSketchPoint), (b, arc.endSketchPoint)):
                    o = sp(p)
                    if o is None: keep(p, e)
                    else:
                        try: o.merge(e)
                        except Exception: pass
    sk.isComputeDeferred = False
    return sk


def filled_profiles(sk, loops, sx, sy):
    """Profiles of the even-odd fill: the profile's box is its outer loop's box;
    the loop with that box has an even nesting depth for filled regions."""
    boxes = [([l['bbox'][0] + sx, l['bbox'][1] + sy, l['bbox'][2] + sx, l['bbox'][3] + sy], l['depth']) for l in loops]
    sel, missed = adsk.core.ObjectCollection.create(), 0
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        bb = pr.boundingBox
        b = [bb.minPoint.x / MM, bb.minPoint.y / MM, bb.maxPoint.x / MM, bb.maxPoint.y / MM]
        best = min(boxes, key=lambda t: max(abs(u - v) for u, v in zip(t[0], b)))
        if max(abs(u - v) for u, v in zip(best[0], b)) > BBOX_TOL:
            missed += 1
            continue
        if best[1] % 2 == 0:
            sel.add(pr)
    return sel, missed


def build_part(comp, recipe, outlines, log):
    feats = comp.features
    bodies, sketches = [], {}
    for i, item in enumerate(recipe):
        name = item['name']
        loops = outlines.get(name) or []
        if not loops:
            log.append('%s: outline %s is empty, skipped' % (comp.name, name)); continue
        sx, sy, sz = (list(item.get('shift') or []) + [0, 0, 0])[:3]
        key = (name, sx, sy)
        if key not in sketches:
            sketches[key] = draw_outline(comp, name, loops, sx, sy)
        sk = sketches[key]
        prof, missed = filled_profiles(sk, loops, sx, sy)
        if missed: log.append('%s / %s: %d profile(s) not matched' % (comp.name, name, missed))
        if prof.count == 0:
            log.append('%s / %s: no profile, skipped' % (comp.name, name)); continue
        ei = feats.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal(item['extrude'] * MM))
        if sz:
            ei.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(sz * MM))
        ex = feats.extrudeFeatures.add(ei)
        op = item.get('operation', 'add') if bodies else 'base'
        ex.name = '%02d %s %s' % (i, op, name)
        new = [ex.bodies.item(k) for k in range(ex.bodies.count)]
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
        root.name = data.get('design', 'keyboard') + ' case'
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
