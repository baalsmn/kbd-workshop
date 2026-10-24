# OrcaSlicer / Bambu Studio project (3MF, Bambu project layout) with two plates:
#   plate 1 "inserts": the Hungarian alphabet as legend inserts, face down (smooth face on the
#     bed), each object = insert (filament 1) + legend (filament 2, the first 0.4 mm);
#   plate 2 "keycaps": one of each cap (1U, 1.25U, 1.25U thumb, 2U, 2U thumb) lying on the north
#     skirt face (layer lines run across the top, nothing on the top needs support), the cavity
#     opening to the back (+y) so the seam (position back) lands on the skirt rim. Per object:
#     tree supports for the inside only (stem underside, the cavity roof), 4 mm brim (17.5 mm
#     tall on its north face), 8 wall loops (walls all perimeters).
# Print settings (orca_settings.py: A1 0.2 nozzle, PolyTerra PLA x2, 0.06 process + our changes) are
# stored as Metadata/project_settings.config when Orca's system presets are found on this PC:
# open the file as a project and they load with it. Plates are laid out for a 256 x 256 bed (Bambu A1), plate i at
# x = i * 1.2 * 256 like Orca does.
# Usage: python keycaps/orca_project.py [--out keycaps/build/keycaps_hu.3mf] [--bed 256]
import os, sys, math, json, zipfile, uuid, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Rot
import keycap as K
import orca_settings

HU = 'A Á B C D E É F G H I Í J K L M N O Ó Ö Ő P Q R S T U Ú Ü Ű V W X Y Z'.split()
CAPS = [((1, False, False), '1U'), ((1.25, False, False), '1.25U'), ((1.25, False, True), '1.25U thumb'),
        ((2, True, False), '2U stab'), ((2, True, True), '2U stab thumb')]


def mesh(shape, tol=0.01, ang=0.15):
    v, t = shape.tessellate(tol, ang)
    return [(p.X, p.Y, p.Z) for p in v], t


def mesh_xml(oid, verts, tris):
    out = ['  <object id="%d" p:UUID="%s" type="model">\n   <mesh>\n    <vertices>\n' % (oid, uuid.uuid4())]
    out += ['     <vertex x="%.5f" y="%.5f" z="%.5f"/>\n' % v for v in verts]
    out.append('    </vertices>\n    <triangles>\n')
    out += ['     <triangle v1="%d" v2="%d" v3="%d"/>\n' % t for t in tris]
    out.append('    </triangles>\n   </mesh>\n  </object>\n')
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'keycaps_hu.3mf'))
    ap.add_argument('--bed', type=float, default=256.0)
    A = ap.parse_args()
    P = K.P
    objects = []        # (name, plate, (x, y), [(part name, extruder, shape)], extra metadata)
    # plate 1: inserts, flipped face down (top face on the bed)
    flip = Pos(0, 0, P['insert_t']) * Rot(180, 0, 0)
    cols, pitch = 7, 14.0
    rows = math.ceil(len(HU) / cols)
    for i, ch in enumerate(HU):
        ins, leg = K.build_insert(ch)
        x = A.bed / 2 + (i % cols - (cols - 1) / 2) * pitch
        y = A.bed / 2 - (i // cols - (rows - 1) / 2) * pitch
        objects.append(('insert %s' % ch, 1, (x, y), [('insert', 1, flip * ins), ('legend %s' % ch, 2, flip * leg)], {}))
    # plate 2: caps on the north skirt face, cavity opening to +y
    place = [(-28, 22), (28, 22), (-32, -8), (0, -8), (32, -8)]          # 2U, 2U thumb / 1U, 1.25U, 1.25U thumb
    order = [3, 4, 0, 1, 2]
    per_object = {'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '0',
                  'support_threshold_angle': '40', 'brim_type': 'outer_only', 'brim_width': '4',
                  'brim_object_gap': '0.1', 'seam_position': 'back', 'wall_loops': '8'}
    for (dx, dy), k in zip(place, order):
        (u, stab, thumb), label = CAPS[k]
        cap = Rot(0, 0, 180) * Rot(-(90 + P['draft']), 0, 0) * K.build_cap(u, stab, thumb)
        vs = [v for v in cap.tessellate(0.01, 0.15)[0]]           # (bounding boxes of the valley surface are loose)
        x0, x1, y0, y1 = min(v.X for v in vs), max(v.X for v in vs), min(v.Y for v in vs), max(v.Y for v in vs)
        cap = Pos(-(x0 + x1) / 2, -(y0 + y1) / 2, -min(v.Z for v in vs)) * cap
        objects.append(('cap %s' % label, 2, (A.bed / 2 + dx, A.bed / 2 + dy), [('cap', 1, cap)], dict(per_object)))

    model_files, rels, res, build, settings, plates = {}, [], [], [], [], {1: [], 2: []}
    nid = 1
    for n, (name, plate, (x, y), parts, extra) in enumerate(objects):
        part_ids, comp_xml, part_meshes = [], [], []
        for pname, ext, shp in parts:
            verts, tris = mesh(shp)
            part_meshes.append((nid, verts, tris)); part_ids.append((nid, pname, ext, len(tris))); nid += 1
        oid = nid; nid += 1
        path = '3D/Objects/object_%d.model' % oid
        model_files[path] = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
                             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                             'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                             ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                             + ''.join(mesh_xml(i, v, t) for i, v, t in part_meshes) + ' </resources>\n <build/>\n</model>\n')
        rels.append(path)
        res.append('  <object id="%d" p:UUID="%s" type="model">\n   <components>\n%s   </components>\n  </object>\n' % (
            oid, uuid.uuid4(), ''.join('    <component p:path="/%s" objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                                      % (path, i, uuid.uuid4()) for i, _, _, _ in part_ids)))
        build.append('  <item objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 %.3f %.3f 0" printable="1"/>\n' % (
            oid, uuid.uuid4(), x + (plate - 1) * A.bed * 1.2, y))
        s = ['  <object id="%d">\n    <metadata key="name" value="%s"/>\n    <metadata key="extruder" value="1"/>\n' % (oid, name)]
        s += ['    <metadata key="%s" value="%s"/>\n' % kv for kv in extra.items()]
        for i, pname, ext, nf in part_ids:
            s.append('    <part id="%d" subtype="normal_part">\n      <metadata key="name" value="%s"/>\n'
                     '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                     '      <metadata key="extruder" value="%d"/>\n'
                     '      <mesh_stat face_count="%d" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                     '    </part>\n' % (i, pname, ext, nf))
        s.append('  </object>\n')
        settings.append(''.join(s))
        plates[plate].append(oid)
    names = {1: 'inserts (Hungarian alphabet, face down)', 2: 'keycaps'}
    plate_xml = ''.join('  <plate>\n    <metadata key="plater_id" value="%d"/>\n    <metadata key="plater_name" value="%s"/>\n'
                        '    <metadata key="locked" value="false"/>\n%s  </plate>\n' % (
                            k, names[k], ''.join('    <model_instance>\n      <metadata key="object_id" value="%d"/>\n'
                                                 '      <metadata key="instance_id" value="0"/>\n'
                                                 '      <metadata key="identify_id" value="%d"/>\n    </model_instance>\n'
                                                 % (o, 1000 + o) for o in v)) for k, v in plates.items())
    main_model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                  'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
                  'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                  'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                  ' <metadata name="Application">BambuStudio-01.10.02.67</metadata>\n'
                  ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                  ' <metadata name="Title">keycaps (keyboard-workshop)</metadata>\n'
                  ' <resources>\n' + ''.join(res) + ' </resources>\n <build p:UUID="%s">\n' % uuid.uuid4()
                  + ''.join(build) + ' </build>\n</model>\n')
    os.makedirs(os.path.dirname(A.out), exist_ok=True)
    with zipfile.ZipFile(A.out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                   ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                   ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                   ' <Default Extension="png" ContentType="image/png"/>\n'
                   ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
        z.writestr('3D/3dmodel.model', main_model)
        z.writestr('3D/_rels/3dmodel.model.rels', '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   + ''.join(' <Relationship Target="/%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                             % (p, i + 1) for i, p in enumerate(rels)) + '</Relationships>\n')
        for p, txt in model_files.items():
            z.writestr(p, txt)
        if orca_settings.available():
            z.writestr('Metadata/project_settings.config', json.dumps(orca_settings.project_settings(2), indent=4))
        z.writestr('Metadata/model_settings.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(settings) + plate_xml + '</config>\n')
    print('%s: %d objects, plate 1 %d inserts, plate 2 %d caps, print settings %s' % (
        A.out, len(objects), len(plates[1]), len(plates[2]), 'included' if orca_settings.available() else 'NOT included (no Orca presets)'))


if __name__ == '__main__':
    main()
