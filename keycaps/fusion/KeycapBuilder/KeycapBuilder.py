# Fusion script: rebuilds the keycaps of keycaps/build/keycaps_fusion.json (written by
# `python keycaps/keycap.py --fusion`) as parametric designs, one document per cap, every step of
# keycap.py's build_cap as a named timeline feature (in one timeline group per stage):
#   skirt (sketch + extrude tapered by the user parameter `draft`), sloped top (plane at `slope`,
#   split + remove), north roll-off (side sketch, cut), valley (revolved profile, scaled, moved,
#   combined), thumb (loft through closed east-west sections above the surface, cut), insert pocket and
#   pin holes, inside cavity (tapered cut up to the ceiling plane), stabilizer recesses, stems
#   and cross holes, top-edge fillet (user parameter `top_fillet`), and the legend insert as its
#   own component (insert body with pins + the legend as a sketch text body). The inserts of the
#   letter set (recipe 'legends') are built as designs of their own and saved too.
# Numbers come from the recipe (mm, cap frame: z 0 = skirt bottom, +y = north). Each design ends
# with the build123d volume next to Fusion's in the log, as a check.
# Run: add the folder in Scripts and Add-Ins, run, pick keycaps_fusion.json, give the cap names
# (empty = all) and a legend, and say whether to save them (build/fusion/<cap>.f3d / .step / .stl:
# **Fusion is the source of the caps**). Or build_keycap(rec, legend) + export_keycap() (bridge).
import adsk.core, adsk.fusion, traceback, json, math

MM = 0.1                                       # Fusion's internal unit is cm


def P(x, y, z):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def VR(mm):
    return adsk.core.ValueInput.createByReal(mm * MM)


def VS(expr):
    return adsk.core.ValueInput.createByString(expr)


def coll(items):
    c = adsk.core.ObjectCollection.create()
    for i in items: c.add(i)
    return c


class Builder:
    def __init__(self, comp, rec, log):
        self.c, self.r, self.log = comp, rec, log
        self.f = comp.features
        sl = math.radians(rec['top']['slope'])
        self.cs, self.sn, self.h = math.cos(sl), math.sin(sl), rec['top']['h_centre']

    # -- helpers ------------------------------------------------------------------------------
    def tf(self, x, y, z):                     # top frame -> cap frame (mm)
        return x, y * self.cs - z * self.sn, self.h + y * self.sn + z * self.cs

    def plane_z(self, z, name):
        pi = self.c.constructionPlanes.createInput()
        pi.setByOffset(self.c.xYConstructionPlane, VR(z))
        pl = self.c.constructionPlanes.add(pi); pl.name = name; pl.isLightBulbOn = False
        return pl

    def plane_off(self, base, d, name):
        pi = self.c.constructionPlanes.createInput()
        pi.setByOffset(base, VR(d))
        pl = self.c.constructionPlanes.add(pi); pl.name = name; pl.isLightBulbOn = False
        return pl

    def sketch(self, plane, name):
        sk = self.c.sketches.add(plane); sk.name = name
        return sk

    def sp(self, sk, x, y, z):                 # model point (mm) -> sketch space
        return sk.modelToSketchSpace(P(x, y, z))

    def poly(self, sk, pts, closed=True):      # pts: model points (mm)
        q = [self.sp(sk, *p) for p in pts]
        lines = sk.sketchCurves.sketchLines
        n = len(q) if closed else len(q) - 1
        for i in range(n):
            lines.addByTwoPoints(q[i], q[(i + 1) % len(q)])

    def rrect(self, sk, cx, cy, w, d, r, z, square_south=False):   # rounded rectangle, horizontal plane
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
        L, A = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        q = 1 - math.sqrt(0.5)
        rs = 0 if square_south else r            # (thumb caps: square south corners)
        for a, b in (((x0 + rs, y0), (x1 - rs, y0)), ((x1, y0 + rs), (x1, y1 - r)),
                     ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + rs))):
            L.addByTwoPoints(self.sp(sk, a[0], a[1], z), self.sp(sk, b[0], b[1], z))
        arcs = [((x1, y1 - r), (x1 - r * q, y1 - r * q), (x1 - r, y1)),
                ((x0 + r, y1), (x0 + r * q, y1 - r * q), (x0, y1 - r))]
        if not square_south:
            arcs += [((x1 - r, y0), (x1 - r * q, y0 + r * q), (x1, y0 + r)),
                     ((x0, y0 + r), (x0 + r * q, y0 + r * q), (x0 + r, y0))]
        for (ax, ay), (mx, my), (bx, by) in arcs:
            A.addByThreePoints(self.sp(sk, ax, ay, z), self.sp(sk, mx, my, z), self.sp(sk, bx, by, z))

    def profiles(self, sk):
        return coll([sk.profiles.item(i) for i in range(sk.profiles.count)])

    def biggest_profile(self, sk):
        return max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda p: p.areaProperties().area)

    def group(self, start, name):
        tl = self.c.parentDesign.timeline
        try:
            if tl.markerPosition - 1 > start:
                tl.timelineGroups.add(start, tl.markerPosition - 1).name = name
        except Exception:
            pass

    def marker(self):
        return self.c.parentDesign.timeline.markerPosition

    # -- steps --------------------------------------------------------------------------------
    def skirt(self):
        r = self.r; m = self.marker()
        sk = self.sketch(self.c.xYConstructionPlane, 'skirt outline')
        self.rrect(sk, 0, 0, r['W'], r['D'], r['skirt']['r'], 0, r['skirt'].get('square_south', False))
        ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VR(r['H'])),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection, VS('-draft'))
        ex = self.f.extrudeFeatures.add(ei); ex.name = 'skirt (taper = draft)'
        self.body = ex.bodies.item(0); self.body.name = 'cap'
        self.group(m, 'skirt')

    def top(self):
        m = self.marker()
        base = self.plane_z(self.h, 'top centre height')
        sk = self.sketch(base, 'top tilt axis')
        ax = sk.sketchCurves.sketchLines.addByTwoPoints(self.sp(sk, -40, 0, self.h), self.sp(sk, 40, 0, self.h))
        sk.isLightBulbOn = False
        self.top_plane = None
        for expr in ('slope', '-slope'):
            pi = self.c.constructionPlanes.createInput()
            pi.setByAngle(ax, VS(expr), base)
            pl = self.c.constructionPlanes.add(pi)
            n = pl.geometry.normal
            if n.z < 0: n = adsk.core.Vector3D.create(-n.x, -n.y, -n.z)
            if n.y * self.sn <= 0:                # the top rises to the north: normal leans south
                self.top_plane = pl; break
            pl.deleteMe()
        self.top_plane.name = 'top plane (slope)'; self.top_plane.isLightBulbOn = False
        if not self.r.get('top_surface'):        # (dish tops: the top surface holds the plane; cutting at
            self.split_remove(self.top_plane, lambda bs: max(bs, key=lambda b: b.boundingBox.maxPoint.z), 'top cut')
        self.group(m, 'sloped top')            # it too leaves coincident faces)

    def split_remove(self, tool, pick, name, extend=True):
        si = self.f.splitBodyFeatures.createInput(self.body, tool, extend)
        sf = self.f.splitBodyFeatures.add(si); sf.name = name + ' (split)'
        bs = [sf.bodies.item(i) for i in range(sf.bodies.count)]
        if len(bs) < 2:
            self.log.append('%s: nothing split off' % name); self.body = bs[0] if bs else self.body; return
        gone = pick(bs)
        self.body = max((b for b in bs if b != gone), key=lambda b: b.volume)
        self.f.removeFeatures.add(gone).name = name + ' (remove)'

    def roll(self):
        if self.r['roll'] is None: return      # (dish tops: part of the one top surface)
        m = self.marker()
        q = [(0, y, z) for y, z in self.r['roll']]           # T, A, B, C, E, arc midpoint
        sk = self.sketch(self.c.yZConstructionPlane, 'north roll-off profile')
        self.poly(sk, q[:5], closed=False)
        sk.sketchCurves.sketchArcs.addByThreePoints(self.sp(sk, *q[4]), self.sp(sk, *q[5]), self.sp(sk, *q[0]))
        ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setSymmetricExtent(VR(self.r['W'] + 10), True)
        ei.participantBodies = [self.body]
        self.f.extrudeFeatures.add(ei).name = 'north roll-off (cut)'
        self.group(m, 'north roll-off')

    def valley(self):
        v = self.r['valley']
        if v is None: return                   # (dish tops: part of the one top surface)
        m = self.marker()
        x0, z0, r0 = v['flat']
        sk = self.sketch(self.c.xZConstructionPlane, 'valley profile (radius / height)')
        L = sk.sketchCurves.sketchLines
        if r0 > 1e-6:                            # (legend caps: a dish from the centre, no flat floor)
            L.addByTwoPoints(self.sp(sk, 0, 0, z0), self.sp(sk, r0, 0, z0))
        sk.sketchCurves.sketchFittedSplines.add(coll([self.sp(sk, rr, 0, zz) for rr, zz in v['profile']]))
        r1, R = v['profile'][-1][0], v['R']
        self.poly(sk, [(r1, 0, 0), (R, 0, 0), (R, 0, 10), (0, 0, 10), (0, 0, z0)], closed=False)
        axis = [l for l in [sk.sketchCurves.sketchLines.item(i) for i in range(sk.sketchCurves.sketchLines.count)]
                if abs(l.startSketchPoint.worldGeometry.x) < 1e-6 and abs(l.endSketchPoint.worldGeometry.x) < 1e-6][0]
        ri = self.f.revolveFeatures.createInput(sk.profiles.item(0), axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ri.setAngleExtent(False, VS('360 deg'))
        rv = self.f.revolveFeatures.add(ri); rv.name = 'valley tool (revolve)'
        tool = rv.bodies.item(0); tool.name = 'valley tool'
        if abs(v['sx'] - 1) > 1e-6:
            si = self.f.scaleFeatures.createInput(coll([tool]), self.c.originConstructionPoint, VR(10))
            si.setToNonUniform(adsk.core.ValueInput.createByReal(v['sx']), adsk.core.ValueInput.createByReal(1),
                               adsk.core.ValueInput.createByReal(1))
            self.f.scaleFeatures.add(si).name = 'valley tool (stretch east-west)'
        mt = adsk.core.Matrix3D.create()
        mt.setToRotation(math.radians(self.r['top']['slope']), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
        mt.translation = adsk.core.Vector3D.create(0, 0, self.h * MM)
        mi = self.f.moveFeatures.createInput2(coll([tool]))
        mi.defineAsFreeMove(mt)
        self.f.moveFeatures.add(mi).name = 'valley tool (onto the sloped top)'
        ci = self.f.combineFeatures.createInput(self.body, coll([tool]))
        ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation; ci.isKeepToolBodies = False
        self.f.combineFeatures.add(ci).name = 'valley (cut)'
        self.group(m, 'valley')

    def surface(self):
        """Dish tops (legend caps): the whole top as one surface (plane - dish - north roll-off, no edge
        between the dish and the roll-off), cut like the thumb surface: a loft through closed sections."""
        rows = self.r.get('top_surface')
        if not rows: return
        self.loft_cut(rows, 'top surface', 'top surface (plane - dish - roll-off)')

    def thumb(self):
        rows = self.r.get('thumb')
        if not rows: return
        self.loft_cut(rows, 'thumb', 'thumb roll-off')

    def loft_cut(self, rows, what, group):
        m = self.marker()
        paths = []
        for k, row in enumerate(rows):
            y = row[0][1]
            pi = self.c.constructionPlanes.createInput()
            pi.setByOffset(self.c.xZConstructionPlane, VR(y))
            pl = self.c.constructionPlanes.add(pi)
            if abs(pl.geometry.origin.y - y * MM) > 1e-6:      # (the XZ plane's normal may point -y)
                pl.deleteMe()
                pi = self.c.constructionPlanes.createInput(); pi.setByOffset(self.c.xZConstructionPlane, VR(-y))
                pl = self.c.constructionPlanes.add(pi)
            pl.name = '%s section %d' % (what, k); pl.isLightBulbOn = False
            sk = self.sketch(pl, '%s section %d' % (what, k))
            sk.sketchCurves.sketchFittedSplines.add(coll([self.sp(sk, *q) for q in row]))
            (x0, _, z0), (x1, _, z1) = row[0], row[-1]           # closed above the surface (as the
            self.poly(sk, [(x1, y, z1), (x1, y, 15), (x0, y, 15), (x0, y, z0)], closed=False)   # build123d prism)
            sk.isLightBulbOn = False
            paths.append(sk.profiles.item(0))
        li = self.f.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        for prof in paths: li.loftSections.add(prof)
        li.isSolid = True
        lf = self.f.loftFeatures.add(li); lf.name = '%s tool (loft above the %s)' % (what, what)
        tool = lf.bodies.item(0); tool.name = what + ' tool'
        ci = self.f.combineFeatures.createInput(self.body, coll([tool]))
        ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation; ci.isKeepToolBodies = False
        self.f.combineFeatures.add(ci).name = group + ' (cut)'
        self.group(m, group)

    def pocket(self):
        r, m = self.r, self.marker()
        pk = r['pocket']
        if pk is None: return                  # (legend caps: no pocket, one continuous top)
        pl = self.plane_off(self.top_plane, pk['z'], 'insert pocket floor')
        sk = self.sketch(pl, 'insert pocket')
        cx, cy, cz = self.tf(0, 0, pk['z'])
        if pk['square']:
            self.log.append('square insert: drawn as a circle in Fusion')
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.sp(sk, cx, cy, cz), pk['r'] * MM)
        ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setDistanceExtent(False, VR(10)); ei.participantBodies = [self.body]
        self.f.extrudeFeatures.add(ei).name = 'insert pocket (cut)'
        sk2 = self.sketch(pl, 'pin holes')
        for x, y, rr in r['pins']:
            sk2.sketchCurves.sketchCircles.addByCenterRadius(self.sp(sk2, *self.tf(x, y, pk['z'])), rr * MM)
        ei = self.f.extrudeFeatures.createInput(self.profiles(sk2), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VR(r['floor'] + 3)),
                            adsk.fusion.ExtentDirections.NegativeExtentDirection)
        ei.participantBodies = [self.body]
        self.f.extrudeFeatures.add(ei).name = 'pin holes (cut)'
        self.group(m, 'insert pocket')

    def cavity(self):
        r, m = self.r, self.marker()
        cv = r['cavity']
        ceil = self.plane_off(self.top_plane, r['z_ceil'], 'ceiling (parallel to the top)')
        pl = self.plane_z(-1, 'below the skirt')
        sk = self.sketch(pl, 'cavity outline')
        self.rrect(sk, 0, 0, cv['w'], cv['d'], cv['r'], -1)
        ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.ToEntityExtentDefinition.create(ceil, False),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection, VS('-draft'))
        ei.participantBodies = [self.body]
        self.f.extrudeFeatures.add(ei).name = 'cavity (cut, taper = draft)'
        if r['recess']:
            sk = self.sketch(self.c.xYConstructionPlane, 'stabilizer recesses')
            for x, y, w, d, zr in r['recess']:
                self.poly(sk, [(x - w / 2, y - d / 2, 0), (x + w / 2, y - d / 2, 0), (x + w / 2, y + d / 2, 0), (x - w / 2, y + d / 2, 0)])
            ei = self.f.extrudeFeatures.createInput(self.profiles(sk), adsk.fusion.FeatureOperations.CutFeatureOperation)
            ei.setDistanceExtent(False, VR(r['recess'][0][4])); ei.participantBodies = [self.body]
            self.f.extrudeFeatures.add(ei).name = 'stabilizer recesses (cut)'
        self.group(m, 'cavity')

    def stems(self):
        r, m = self.r, self.marker()
        for k, st in enumerate(r['stems']):
            name = 'stem' if k == 0 else 'stabilizer stem %d' % k
            pl = self.plane_z(st['bottom'], name + ' bottom')
            sk = self.sketch(pl, name)
            sk.sketchCurves.sketchCircles.addByCenterRadius(self.sp(sk, st['x'], 0, st['bottom']), r['stem_r'] * MM)
            ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            ei.setDistanceExtent(False, VR(st['top'] - st['bottom'])); ei.participantBodies = [self.body]
            self.f.extrudeFeatures.add(ei).name = name + ' (join)'
            pl2 = self.plane_z(st['bottom'] - 1, name + ' cross start')
            sk2 = self.sketch(pl2, name + ' cross')
            a, b = st['cross'][0] / 2, st['cross'][1] / 2
            x0, z = st['x'], st['bottom'] - 1
            pts = [(a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b), (-b, -a), (b, -a), (b, -b), (a, -b)]
            self.poly(sk2, [(x0 + px, py, z) for px, py in pts])
            ei = self.f.extrudeFeatures.createInput(sk2.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            ei.setDistanceExtent(False, VR(st['cross_top'] - st['bottom'] + 1)); ei.participantBodies = [self.body]
            self.f.extrudeFeatures.add(ei).name = name + ' cross hole (cut)'
        self.group(m, 'stems')

    def fillet(self):
        r = self.r
        if not r['fillet']: return
        m = self.marker()
        W, D, sd = r['W'], r['D'], math.sin(math.radians(r['skirt']['draft']))
        side, top = set(), set()
        for i in range(self.body.faces.count):
            fc = self.body.faces.item(i)
            ok, n = fc.evaluator.getNormalAtPoint(fc.pointOnFace)
            c = fc.centroid
            cx, cy, cz = c.x / MM, c.y / MM, c.z / MM
            outer = abs(cx) > W / 2 - 1.2 or abs(cy) > D / 2 - 1.2
            if outer and abs(abs(n.z) - sd) < 0.03 and cz > 0: side.add(fc.tempId)
            elif n.z > 0.15 and cz > 0.3: top.add(fc.tempId)
        edges = []
        for i in range(self.body.edges.count):
            e = self.body.edges.item(i)
            fs = {e.faces.item(k).tempId for k in range(e.faces.count)}
            if fs & side and fs & top: edges.append(e)
        fi = self.f.filletFeatures.createInput()
        try:
            fi.edgeSetInputs.addConstantRadiusEdgeSet(coll(edges), VS('top_fillet'), True)
        except Exception:
            fi.addConstantRadiusEdgeSet(coll(edges), VS('top_fillet'), True)
        try:
            self.f.filletFeatures.add(fi).name = 'top edge fillet (top_fillet)'
        except Exception as ex:
            self.log.append('%s: top fillet failed (%d edges): %s' % (r['name'], len(edges), ex))
        self.group(m, 'top edge fillet')

    def insert(self, root, legend):
        r = self.r; ins = r['insert']
        mt = adsk.core.Matrix3D.create()
        mt.setToRotation(math.radians(r['top']['slope']), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
        x, y, z = self.tf(0, 0, ins['z'])
        mt.translation = adsk.core.Vector3D.create(x * MM, y * MM, z * MM)
        occ = root.occurrences.addNewComponent(mt)
        occ.component.name = 'legend insert'
        make_insert(occ.component, ins, legend)
        return occ


    def double_shot(self):
        """Legend caps (legend_cap.py): split the cap like a double-shot moulding into the core
        (translucent: stems, a layer over the cavity ceiling, the legend up through the top) and the
        shell (the rest: top + skirt). A 'core region' body is built (cavity outline up to the core
        plane + the stem ends + the legend text), intersected with the cap (cap kept) = core, then
        cut from the cap = shell."""
        r, m = self.r, self.marker()
        lg, co, cv = r['legend'], r['core'], r['cavity']
        F = adsk.fusion.FeatureOperations
        core_pl = self.plane_off(self.top_plane, co['z'], 'core top (parallel to the top)')
        sk = self.sketch(self.plane_z(-1, 'core region start'), 'core region outline')
        self.rrect(sk, 0, 0, cv['w'], cv['d'], cv['r'], -1)
        ei = self.f.extrudeFeatures.createInput(sk.profiles.item(0), F.NewBodyFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.ToEntityExtentDefinition.create(core_pl, False),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection, VS('-draft'))
        region = self.f.extrudeFeatures.add(ei); region.name = 'core region (taper = draft)'
        rb = region.bodies.item(0); rb.name = 'core'
        sk = self.sketch(self.plane_z(co['stem_below'], 'stem ends start'), 'stem ends')
        for st in r['stems']:
            sk.sketchCurves.sketchCircles.addByCenterRadius(self.sp(sk, st['x'], 0, co['stem_below']), (r['stem_r'] + 0.5) * MM)
        ei = self.f.extrudeFeatures.createInput(self.profiles(sk), F.JoinFeatureOperation)
        ei.setDistanceExtent(False, VR(-1 - co['stem_below'] + 0.5)); ei.participantBodies = [rb]
        self.f.extrudeFeatures.add(ei).name = 'stem ends (join)'
        # legend: sketch text on a plane parallel to the top, its glyph box's south-east corner at lg['at']
        sk = self.sketch(self.plane_off(self.top_plane, lg['z0'], 'legend start (below the ceiling)'), 'legend')
        cx, cy = lg['at'][0] - lg['w'] / 2, lg['at'][1] + lg['h'] / 2
        c = self.sp(sk, *self.tf(cx, cy, lg['z0']))
        ti = sk.sketchTexts.createInput2(lg['text'], lg['h'] * MM)    # (Fusion's text height = the glyph height
        ti.setAsMultiLine(adsk.core.Point3D.create(c.x - 1, c.y - 1, 0), adsk.core.Point3D.create(c.x + 1, c.y + 1, 0),
                          adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                          adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)   # of a capital; centred on its glyph box)
        try: ti.fontName = lg['font']
        except Exception: pass
        if lg.get('bold'): ti.textStyle = adsk.fusion.TextStyles.TextStyleBold
        txt = sk.sketchTexts.add(ti)
        xd, yd = sk.xDirection, sk.yDirection      # read from above: east = +x, north = +y
        txt.isHorizontalFlip = xd.x < 0
        txt.isVerticalFlip = (yd.y * self.cs + yd.z * self.sn) < 0
        nz = xd.crossProduct(yd).z
        ei = self.f.extrudeFeatures.createInput(txt, F.NewBodyFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VR(lg['len'])),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection if nz > 0
                            else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        lex = self.f.extrudeFeatures.add(ei); lex.name = 'legend (extrude)'
        lbs = [lex.bodies.item(i) for i in range(lex.bodies.count)]
        bb = txt.boundingBox                       # the glyph box, back in the top frame (logged as a check)
        pts = [sk.sketchToModelSpace(adsk.core.Point3D.create(x, y, 0)) for x in (bb.minPoint.x, bb.maxPoint.x)
               for y in (bb.minPoint.y, bb.maxPoint.y)]
        loc = [(q.x / MM, (q.y / MM) * self.cs + (q.z / MM - self.h) * self.sn) for q in pts]
        self.log.append('legend glyph box (top frame): x %.2f..%.2f y %.2f..%.2f' % (
            min(q[0] for q in loc), max(q[0] for q in loc), min(q[1] for q in loc), max(q[1] for q in loc)))
        ci = self.f.combineFeatures.createInput(rb, coll(lbs)); ci.operation = F.JoinFeatureOperation
        self.f.combineFeatures.add(ci).name = 'legend into the core region (join)'
        ci = self.f.combineFeatures.createInput(rb, coll([self.body])); ci.operation = F.IntersectFeatureOperation
        ci.isKeepToolBodies = True
        self.f.combineFeatures.add(ci).name = 'core = cap & core region (intersect)'
        ci = self.f.combineFeatures.createInput(self.body, coll([rb])); ci.operation = F.CutFeatureOperation
        ci.isKeepToolBodies = True
        cut = self.f.combineFeatures.add(ci); cut.name = 'shell = cap - core (cut)'
        # closed counters (the A's triangle) come out as bodies of their own: Fusion doesn't join bodies
        # that don't touch, so they stay separate shell bodies (the shell STL holds them all)
        rest = sorted((b for b in self.c.bRepBodies if b != rb), key=lambda b: -b.volume)
        self.body, self.islands = rest[0], rest[1:]     # (the cut may hand back an island as its body)
        for k, b in enumerate(self.islands):
            b.name = 'shell island %d' % (k + 1)
        self.body.name = 'shell'
        self.core = rb
        self.group(m, 'double shot: core / shell')


def make_insert(c, ins, legend):
    """The legend insert in component c (its own frame: top face at z = t, pins down): insert body
    with the pins, and the legend as a sketch text extruded in a sub-component 'legend' (every
    piece of the letter) and cut from the insert. Returns (insert body, legend occurrence or None)."""
    lb = None
    f = c.features
    sk = c.sketches.add(c.xYConstructionPlane); sk.name = 'insert outline'
    sk.sketchCurves.sketchCircles.addByCenterRadius(P(0, 0, 0), ins['d'] / 2 * MM)
    ei = f.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, VR(ins['t']))
    ex = f.extrudeFeatures.add(ei); ex.name = 'insert (extrude)'
    body = ex.bodies.item(0); body.name = 'insert'
    sk2 = c.sketches.add(c.xYConstructionPlane); sk2.name = 'pins'
    for px, py, d in ins['pins']:
        sk2.sketchCurves.sketchCircles.addByCenterRadius(P(px, py, 0), d / 2 * MM)
    ei = f.extrudeFeatures.createInput(coll([sk2.profiles.item(i) for i in range(sk2.profiles.count)]),
                                       adsk.fusion.FeatureOperations.JoinFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VR(ins['pin_len'])),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ei.participantBodies = [body]
    f.extrudeFeatures.add(ei).name = 'pins (join)'
    if legend:
        def text(comp, name):                  # the legend text on the insert top, in comp
            pi = comp.constructionPlanes.createInput(); pi.setByOffset(comp.xYConstructionPlane, VR(ins['t']))
            top = comp.constructionPlanes.add(pi); top.name = 'insert top'; top.isLightBulbOn = False
            sk3 = comp.sketches.add(top); sk3.name = name
            ti = sk3.sketchTexts.createInput2(legend, ins.get('legend_height', ins['legend_size']) * MM)  # capital height
            h = ins['d'] / 2
            ti.setAsMultiLine(P(-h, -h, 0), P(h, h, 0), adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                              adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            try: ti.fontName = ins['font']
            except Exception: pass
            return sk3.sketchTexts.add(ti)
        depth = adsk.fusion.DistanceExtentDefinition.create(VR(ins['legend_depth']))
        # the recess: the text cut into the insert body
        ei = f.extrudeFeatures.createInput(text(c, 'legend recess text'), adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setOneSideExtent(depth, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        ei.participantBodies = [body]
        f.extrudeFeatures.add(ei).name = 'legend recess (cut)'
        # the legend itself in its own sub-component: every piece of the letter (e.g. an accent)
        lo = c.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        lc = lo.component; lc.name = 'legend'
        ei = lc.features.extrudeFeatures.createInput(text(lc, 'legend text'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setOneSideExtent(depth, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        lex = lc.features.extrudeFeatures.add(ei); lex.name = 'legend (extrude)'
        for k in range(lex.bodies.count):
            lex.bodies.item(k).name = 'legend' if k == 0 else 'legend %d' % (k + 1)
        lb = lo
    return body, lb


def build_insert_design(ins, legend, name):
    """New parametric design with one legend insert (component <name> at the origin)."""
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    occ = design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    body, leg = make_insert(occ.component, ins, legend)
    return design, occ, body, leg


def export_insert(design, occ, body, leg, folder, name, f3d=False):
    """<name>.step (insert + legend bodies), <name>.stl (insert), <name>_legend.stl; .f3d if asked."""
    import os
    os.makedirs(folder, exist_ok=True)
    em = design.exportManager
    base = os.path.join(folder, name)
    if f3d:
        em.execute(em.createFusionArchiveExportOptions(base + '.f3d'))
    em.execute(em.createSTEPExportOptions(base + '.step', occ.component))
    for b, suffix in ((body, '.stl'), (leg, '_legend.stl')):
        if b is None: continue
        so = em.createSTLExportOptions(b, base + suffix)
        so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(so)
    return [base + e for e in ('.f3d', '.step', '.stl', '_legend.stl') if os.path.exists(base + e)]


def build_keycap(rec, legend='A', params=None):
    """New parametric design for one cap recipe; returns (design, log lines)."""
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    up = design.userParameters
    up.add('draft', VS('%g deg' % rec['skirt']['draft']), 'deg', 'skirt angle from vertical')
    up.add('slope', VS('%g deg' % rec['top']['slope']), 'deg', 'top slope (north up)')
    up.add('top_fillet', VS('%g mm' % (rec['fillet'] or 0.6)), 'mm', 'top edge fillet')
    root = design.rootComponent
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component; comp.name = rec['name']
    log = []
    b = Builder(comp, rec, log)
    b.skirt(); b.top(); b.roll(); b.valley(); b.thumb(); b.pocket(); b.cavity(); b.stems(); b.fillet()
    b.insert(root, legend)
    vol = b.body.volume * 1000
    log.insert(0, '%s: Fusion %.1f mm3, build123d %.1f mm3 (%+.2f %%)' % (rec['name'], vol, rec['volume'],
                                                                         100 * (vol - rec['volume']) / rec['volume']))
    build_keycap.last = (occ, b.body)
    return design, log


def build_legend_cap(rec):
    """New parametric design for a legend cap recipe (legend_cap.py --fusion): the cap steps without
    the pocket, then the double-shot split. Returns (design, log); build_keycap.last = (occ, [shell
    bodies], core)."""
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    up = design.userParameters
    up.add('draft', VS('%g deg' % rec['skirt']['draft']), 'deg', 'skirt angle from vertical')
    up.add('slope', VS('%g deg' % rec['top']['slope']), 'deg', 'top slope (north up)')
    up.add('top_fillet', VS('%g mm' % (rec['fillet'] or 0.6)), 'mm', 'top edge fillet')
    occ = design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component; comp.name = rec['name']
    log = []
    b = Builder(comp, rec, log)
    b.skirt(); b.top(); b.roll(); b.valley(); b.surface(); b.thumb(); b.pocket(); b.cavity(); b.stems(); b.fillet()
    co = rec['core']
    if co is None:                                 # blank cap: same shape, one body, no split
        b.body.name = 'cap'
        v = b.body.volume * 1000
        log.append('%s: Fusion %.1f mm3, build123d %.1f mm3 (%+.2f %%), 1 body' % (
            rec['name'], v, rec['volume'], 100 * (v - rec['volume']) / rec['volume']))
        build_keycap.last = (occ, [b.body], None)
        return design, log
    b.double_shot()
    for name, bodies, ref in (('shell', [b.body] + b.islands, co['shell_volume']), ('core', [b.core], co['core_volume'])):
        v = sum(x.volume for x in bodies) * 1000
        log.append('%s %s: Fusion %.1f mm3, build123d %.1f mm3 (%+.2f %%), %d body(s)' % (
            rec['name'], name, v, ref, 100 * (v - ref) / ref, len(bodies)))
    build_keycap.last = (occ, [b.body] + b.islands, b.core)
    return design, log


def export_legend_cap(design, rec, folder):
    """<name>.f3d, <name>.step (shell + core), <name>_shell.stl (every shell body, merged),
    <name>_core.stl; blank caps: <name>.f3d, <name>.step, <name>.stl."""
    import os, struct
    os.makedirs(folder, exist_ok=True)
    occ, shells, core = build_keycap.last
    em = design.exportManager
    base = os.path.join(folder, rec['name'])
    em.execute(em.createFusionArchiveExportOptions(base + '.f3d'))
    em.execute(em.createSTEPExportOptions(base + '.step', occ.component))
    def stl(body, path):
        so = em.createSTLExportOptions(body, path)
        so.isBinaryFormat = True
        so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(so)
    if core is None:                               # blank cap: <name>.stl
        stl(shells[0], base + '.stl')
        return [base + e for e in ('.f3d', '.step', '.stl') if os.path.exists(base + e)]
    stl(core, base + '_core.stl')
    tris = b''
    for k, body in enumerate(shells):             # binary STLs: 80 byte header, count, 50 bytes a triangle
        p = base + '_shell_%d.stl' % k
        stl(body, p)
        data = open(p, 'rb').read(); os.remove(p)
        tris += data[84:84 + 50 * struct.unpack('<I', data[80:84])[0]]
    open(base + '_shell.stl', 'wb').write(b'shell (%d bodies)' % len(shells) + b' ' * (80 - len(b'shell (%d bodies)' % len(shells)))
                                         + struct.pack('<I', len(tris) // 50) + tris)
    return [base + e for e in ('.f3d', '.step', '_shell.stl', '_core.stl') if os.path.exists(base + e)]


def export_keycap(design, rec, folder):
    """Save the design (<name>.f3d) and the cap alone (<name>.step, <name>.stl): Fusion is the source
    of the caps (keycap.py get_cap() loads these STEP files for the files, fit checks and the Bambu project)."""
    import os
    os.makedirs(folder, exist_ok=True)
    occ, body = build_keycap.last
    em = design.exportManager
    base = os.path.join(folder, rec['name'])
    em.execute(em.createFusionArchiveExportOptions(base + '.f3d'))
    em.execute(em.createSTEPExportOptions(base + '.step', occ.component))
    so = em.createSTLExportOptions(body, base + '.stl')
    so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    em.execute(so)
    return [base + e for e in ('.f3d', '.step', '.stl') if os.path.exists(base + e)]


def run(context):
    app = adsk.core.Application.get(); ui = app.userInterface
    try:
        dlg = ui.createFileDialog()
        dlg.title = 'Keycap recipe (keycaps/build/keycaps_fusion.json)'
        dlg.filter = 'Keycap recipe (*.json);;All files (*.*)'
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK: return
        data = json.load(open(dlg.filename, encoding='utf-8'))
        names = [c['name'] for c in data['caps']]
        txt, cancelled = ui.inputBox('Caps to build (empty = all):\n' + ', '.join(names), 'Keycaps', '')
        if cancelled: return
        pick = [t.strip() for t in txt.split(',') if t.strip()] or names
        leg, cancelled = ui.inputBox('Legend on the insert (empty = none):', 'Keycaps', 'A')
        if cancelled: return
        save = ui.messageBox('Also save each cap (.f3d, .step, .stl) to build/fusion next to the recipe?\n'
                             '(Fusion is the source of the cap files, fit checks and the Bambu project)', 'Keycaps',
                             adsk.core.MessageBoxButtonTypes.YesNoButtonType) == adsk.core.DialogResults.DialogYes
        import os
        folder = os.path.join(os.path.dirname(dlg.filename), 'fusion')
        log = []
        for rec in data['caps']:
            if rec['name'] in pick:
                design, lg = build_keycap(rec, leg.strip())
                log += lg
                if save:
                    log.append('  saved: ' + ', '.join(os.path.basename(f) for f in export_keycap(design, rec, folder)))
        if data.get('legends') and ui.messageBox('Also build the legend inserts (%d letters, each a design, saved to\n'
                'build/fusion/inserts: insert_<letter>.step / .stl / _legend.stl, and insert_A.f3d)?' % len(data['legends']),
                'Keycaps', adsk.core.MessageBoxButtonTypes.YesNoButtonType) == adsk.core.DialogResults.DialogYes:
            for ch, fn in data['legends']:
                d, o, b, lgb = build_insert_design(data['insert'], ch, 'insert_' + fn)
                export_insert(d, o, b, lgb, os.path.join(folder, 'inserts'), 'insert_' + fn, f3d=(ch == 'A'))
                adsk.core.Application.get().activeDocument.close(False)
            log.append('inserts: %d saved to %s' % (len(data['legends']), os.path.join(folder, 'inserts')))
        ui.messageBox('\n'.join(log) or 'nothing built')
    except Exception:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
