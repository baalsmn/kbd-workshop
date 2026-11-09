# Bambu Studio 3MF writer (Bambu project layout) for the keycaps: write_3mf() puts objects (each one or
# more parts on their own filaments) on plates, with the print settings (bambu_settings.py: A1 0.2 nozzle,
# PolyTerra PLA x2, 0.06 process + our changes) as Metadata/project_settings.config when Bambu Studio's
# system presets are found on this PC: open the file as a project and they load with it. Plates are laid
# out for a 256 x 256 bed (Bambu A1), plate i at x = i * 1.2 * 256 like Bambu Studio does.
# Used by legend_cap.py and slope_test.py (the old insert project, plate 1 inserts / plate 2 caps, was
# dropped with the insert caps, user 2026-11-09).
import os, sys, math, json, zipfile, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bambu_settings

def mesh(shape, tol=0.01, ang=0.15):
    v, t = shape.tessellate(tol, ang)
    return [(p.X, p.Y, p.Z) for p in v], t


def read_stl(path):
    """Vertices + triangles of a binary or ASCII STL (shared vertices merged)."""
    import struct
    data = open(path, 'rb').read()
    n = struct.unpack('<I', data[80:84])[0] if len(data) >= 84 else 0
    if len(data) == 84 + 50 * n:                              # binary
        tri_pts = [struct.unpack('<9f', data[84 + 50 * i + 12:84 + 50 * i + 48]) for i in range(n)]
        tri_pts = [(t[0:3], t[3:6], t[6:9]) for t in tri_pts]
    else:                                                     # ASCII
        v = [tuple(float(x) for x in l.split()[1:4]) for l in data.decode('ascii', 'ignore').splitlines()
             if l.strip().startswith('vertex')]
        tri_pts = [tuple(v[i:i + 3]) for i in range(0, len(v), 3)]
    key, verts, tris = {}, [], []
    for t in tri_pts:
        ids = []
        for q in t:
            k = tuple(round(c, 5) for c in q)
            if k not in key: key[k] = len(verts); verts.append(k)
            ids.append(key[k])
        if len(set(ids)) == 3: tris.append(tuple(ids))
    return verts, tris


def read_3mf(path):
    """{object name: (vertices, triangles)} of a 3MF's mesh objects (Fusion's export: millimetres, one
    object per body, no transforms)."""
    import re
    m = zipfile.ZipFile(path).read('3D/3dmodel.model').decode('utf-8')
    unit = {'millimeter': 1.0, 'centimeter': 10.0, 'meter': 1000.0, 'inch': 25.4}[
        (re.search(r'<model[^>]*unit="([a-z]+)"', m) or [None, 'millimeter'])[1]]
    out = {}
    for name, body in re.findall(r'<object[^>]*name="([^"]*)"[^>]*>(.*?)</object>', m, re.S):
        v = [tuple(float(c) * unit for c in q) for q in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', body)]
        t = [tuple(int(c) for c in q) for q in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body)]
        if v and t:
            out[name] = (v, t)
    return out


def mesh_xml(oid, verts, tris):
    out = ['  <object id="%d" p:UUID="%s" type="model">\n   <mesh>\n    <vertices>\n' % (oid, uuid.uuid4())]
    out += ['     <vertex x="%.5f" y="%.5f" z="%.5f"/>\n' % v for v in verts]
    out.append('    </vertices>\n    <triangles>\n')
    out += ['     <triangle v1="%d" v2="%d" v3="%d"/>\n' % t for t in tris]
    out.append('    </triangles>\n   </mesh>\n  </object>\n')
    return ''.join(out)


NOT_IN_NAMES = set('<>:/' + chr(92) + '|?*"')          # Bambu Studio refuses these in any name


def safe_name(s):
    """A name Bambu Studio accepts (no <>:/\\|?*", e.g. from a symbol legend: '/' -> 'u002f'),
    XML-escaped for the attribute."""
    s = ''.join('u%04x' % ord(c) if c in NOT_IN_NAMES else c for c in s)
    return s.replace('&', '&amp;').replace("'", '&apos;')


def write_3mf(path, objects, bed, names, title='keycaps (keyboard-workshop)'):
    """Bambu Studio project 3MF: objects = (name, plate, (x, y), [(part name, filament, mesh or shape)],
    per-object settings); names = {plate: name}; the print settings (bambu_settings) when available.
    Every object / part / plate name and the title go through safe_name(). Returns {plate: [object ids]}."""
    names = {k: safe_name(v) for k, v in names.items()}
    title = safe_name(title)
    objects = [(safe_name(o[0]), o[1], o[2], [(safe_name(q[0]),) + tuple(q[1:]) for q in o[3]], o[4]) for o in objects]
    model_files, rels, res, build, settings, plates = {}, [], [], [], [], {k: [] for k in names}
    nid = 1
    for n, (name, plate, (x, y), parts, extra) in enumerate(objects):
        part_ids, comp_xml, part_meshes = [], [], []
        for pname, ext, shp in parts:
            verts, tris = shp if isinstance(shp, tuple) else mesh(shp)
            part_meshes.append((nid, verts, tris)); part_ids.append((nid, pname, ext, len(tris))); nid += 1
        oid = nid; nid += 1
        mpath = '3D/Objects/object_%d.model' % oid           # (not 'path': that is the output file)
        model_files[mpath] = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
                             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                             'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                             ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                             + ''.join(mesh_xml(i, v, t) for i, v, t in part_meshes) + ' </resources>\n <build/>\n</model>\n')
        rels.append(mpath)
        res.append('  <object id="%d" p:UUID="%s" type="model">\n   <components>\n%s   </components>\n  </object>\n' % (
            oid, uuid.uuid4(), ''.join('    <component p:path="/%s" objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                                      % (mpath, i, uuid.uuid4()) for i, _, _, _ in part_ids)))
        build.append('  <item objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 %.3f %.3f 0" printable="1"/>\n' % (
            oid, uuid.uuid4(), x + (plate - 1) * bed * 1.2, y))
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
                  ' <metadata name="Application">BambuStudio-%s</metadata>\n' % bambu_settings.studio_version() +
                  ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                  ' <metadata name="Title">%s</metadata>\n' % title +
                  ' <resources>\n' + ''.join(res) + ' </resources>\n <build p:UUID="%s">\n' % uuid.uuid4()
                  + ''.join(build) + ' </build>\n</model>\n')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
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
        if bambu_settings.available():
            z.writestr('Metadata/project_settings.config', json.dumps(bambu_settings.project_settings(2, len(names)), indent=4))
        z.writestr('Metadata/model_settings.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(settings) + plate_xml + '</config>\n')
    return plates

