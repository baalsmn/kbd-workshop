# Keycap with the legend printed in (second approach; the insert caps of keycap.py stay as they are),
# split like a double-shot moulding: no insert pocket and no flat floor (the valley is one dish down to
# the centre), a translucent core (filament 2: stems, a thin layer over the cavity ceiling, the legend
# reaching up through the shell) and an opaque shell over it (filament 1: the rest of the top and the
# skirt), so the switch LED lights the core and shows through the legend only. The legend sits
# north-west of the top's centre point, its box's south-east corner on it.
#
# Usage (build123d PYTHONPATH): python keycaps/legend_cap.py [--units 1] [--legend A] [--out keycaps/build/legend]
#   writes cap_<u>u_<legend>.step (shell + core, coloured), _shell.stl, _core.stl and a Bambu Studio
#   3MF (one object, shell on filament 1, core on filament 2, lying on the north skirt face).
#   --legend '': the blank version (same shape, no legend, one material): cap_<u>u_blank.step/.stl/.3mf.
#   --fusion: also writes legend_cap_<u>u_<legend>_fusion.json (the cap recipe without the pocket plus
#   the legend / core numbers) for the Fusion builder (KeycapBuilder: build_legend_cap() +
#   export_legend_cap() -> build/fusion/legend/); the 3MF uses those Fusion STLs when they exist.
import os, sys, math, argparse, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Text, Align, FontStyle, Box, Compound, Color, extrude, export_step, export_stl
import keycap as K

L = dict(
    legend_size=5.85, legend_style='bold', # font size (cap height ~0.72 x; user: 30 % up from 4.5), bold
                                           # strokes: more light through
    legend_at=(0.0, 0.0),                  # the legend box's south-east corner, in the top frame: on the
                                           # top's centre point (user), so the legend fills the north-west
    valley=0.6,                            # dish depth at the centre (user: the valley continues to the centre,
                                           # a bit deeper than the insert caps' 0.5 flat)
    ceiling=-2.1,                          # cavity ceiling (top frame) = the insert caps': 0.2 lower (dish 0.7
                                           # with the ceiling following) touched the switch at 3.0 mm travel
    stem_d=5.0,                            # stem diameter (user: 5.22 was too wide; the insert caps keep 5.22);
                                           # 0.45 wall left at the cross hole's arm ends (4.10 x 1.20)
    core_t=0.5,                            # core layer over the cavity ceiling, parallel to it (user: thin core,
                                           # thick shell, so the slicer gets whole lines in both; ~2 x 0.22);
                                           # the shell above it is 1.0 at the centre, more where the top rises
)


def tag(legend):
    """File / design name part: the legend's file name, 'blank' for none."""
    return K.file_name(legend) if legend else 'blank'


def legend_cap(u, legend, p=None, l=L):
    """Double-shot split, in the cap frame: (shell, core). The core (translucent, filament 2) is the
    stems, a core_t layer over the cavity ceiling (inside the skirt walls) and the legend, reaching up
    through the shell; the shell (filament 1) is the rest of the top and the skirt. No legend (''):
    the blank cap of the same shape, one body: (cap, None)."""
    p = dict(K.P if p is None else p, pocket=False, valley_style='dish', valley=l['valley'], ceiling=l['ceiling'],
             stem_d=l['stem_d'])
    cap = K.build_cap(u, False, False, p)
    if not legend:
        return cap.clean(), None
    tf = K.top_frame(p)
    z_ceil = K.insert_levels(p)[2]
    under = tf * Pos(0, 0, z_ceil + l['core_t']) * Box(200, 200, 40, align=(Align.CENTER, Align.CENTER, Align.MAX))
    column = K.wall_inside(u, p) + Box(200, 200, 10, align=(Align.CENTER, Align.CENTER, Align.MAX))   # (+ the stem ends below the skirt)
    core = cap & column & under
    txt = Text(legend, l['legend_size'], font=p['legend_font'],
               font_style=FontStyle.BOLD if l['legend_style'] == 'bold' else FontStyle.REGULAR,
               align=(Align.MAX, Align.MIN))
    core = core + (cap & tf * Pos(*l['legend_at'], z_ceil - 0.05) * extrude(txt, amount=6))
    shell = cap - core
    return shell.clean(), core.clean()


def fusion_recipe(u, legend, shell, core, p=None, l=L):
    """keycap.recipe() without the pocket, plus what the double-shot split needs (KeycapBuilder);
    blank caps: legend / core None (one body)."""
    p = dict(K.P if p is None else p, pocket=False, valley_style='dish', valley=l['valley'], ceiling=l['ceiling'],
             stem_d=l['stem_d'])
    r = K.recipe(u, False, False, p)
    r.update({'name': 'legend_cap_%gu_%s' % (u, tag(legend)), 'pocket': None, 'insert': None, 'legend': None,
              'core': None, 'volume': shell.volume + (core.volume if core else 0)})
    if legend:
        t = Text(legend, l['legend_size'], font=p['legend_font'],
                 font_style=FontStyle.BOLD if l['legend_style'] == 'bold' else FontStyle.REGULAR)
        bb = t.bounding_box()
        r.update({'legend': {'text': legend, 'font': p['legend_font'], 'bold': l['legend_style'] == 'bold',
                             'w': bb.size.X, 'h': bb.size.Y,       # glyph box (Fusion text height = this height)
                             'at': list(l['legend_at']),           # glyph box's south-east corner (top frame)
                             'z0': r['z_ceil'] - 0.05, 'len': 6.0},
                  'core': {'z': r['z_ceil'] + l['core_t'], 'shell_volume': shell.volume, 'core_volume': core.volume,
                           'stem_below': -p['stem_drop'] - 0.5}})
    return r


def mesh_volume(m):
    v, t = m
    return sum(v[a][0] * (v[b][1] * v[c][2] - v[b][2] * v[c][1]) - v[a][1] * (v[b][0] * v[c][2] - v[b][2] * v[c][0])
               + v[a][2] * (v[b][0] * v[c][1] - v[b][1] * v[c][0]) for a, b, c in t) / 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--units', type=float, default=1)
    ap.add_argument('--legend', default='A', help='legend (empty = the blank cap, one material)')
    ap.add_argument('--fusion', action='store_true', help='also write the Fusion recipe')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'legend'))
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    shell, core = legend_cap(A.units, A.legend)
    name = 'cap_%gu_%s' % (A.units, tag(A.legend))
    base = os.path.join(A.out, name)
    if core is None:                                       # blank: one body, filament 1
        parts = [('cap', 1, shell)]
        shell.color, shell.label = Color(0.15, 0.15, 0.16), 'cap'
        export_step(shell, base + '.step'); export_stl(shell, base + '.stl')
    else:
        parts = [('shell', 1, shell), ('core %s' % A.legend, 2, core)]
        shell.color, core.color = Color(0.15, 0.15, 0.16), Color(0.95, 0.95, 0.92)
        shell.label, core.label = 'shell', 'core'
        export_step(Compound(children=[shell, core]), base + '.step')
        export_stl(shell, base + '_shell.stl'); export_stl(core, base + '_core.stl')
    import bambu_project as B                               # same orientation as the project's caps
    a = math.radians(-(90 + K.P['draft']))
    r = lambda x, y, z: (-x, -(y * math.cos(a) - z * math.sin(a)), y * math.sin(a) + z * math.cos(a))
    fb = os.path.join(K.FUSION_DIR, 'legend', 'legend_' + name)
    stls = [fb + '.stl'] if core is None else [fb + '_shell.stl', fb + '_core.stl']
    meshes = None
    if K.P['cap_source'] == 'fusion' and all(os.path.exists(x) for x in stls):
        meshes = [B.read_stl(x) for x in stls]              # Fusion is the source, when it is up to date:
        vols = [mesh_volume(m) for m in meshes]             # (its volumes match build123d's)
        if all(abs(v - sp.volume) <= 0.002 * sp.volume for v, (_, _, sp) in zip(vols, parts)):
            print('3MF meshes: Fusion (%s)' % ', '.join(os.path.basename(x) for x in stls))
        else:
            print('3MF meshes: build123d (the Fusion export is out of date: %s mm3 vs %s; rebuild it in Fusion)'
                  % (', '.join('%.1f' % v for v in vols), ', '.join('%.1f' % sp.volume for _, _, sp in parts)))
            meshes = None
    if meshes is None:
        meshes = [B.mesh(sp) for _, _, sp in parts]
    meshes = [([r(*v) for v in m[0]], m[1]) for m in meshes]
    allv = [v for m in meshes for v in m[0]]
    cx = (min(v[0] for v in allv) + max(v[0] for v in allv)) / 2
    cy = (min(v[1] for v in allv) + max(v[1] for v in allv)) / 2
    z0 = min(v[2] for v in allv)
    sh = lambda vv: [(x - cx, y - cy, z - z0) for x, y, z in vv]
    per_object = {'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '0',
                  'support_threshold_angle': '40', 'brim_type': 'outer_only', 'brim_width': '4',
                  'brim_object_gap': '0.1', 'seam_position': 'back', 'wall_loops': '8'}
    bed, label = 256.0, A.legend or 'blank'
    B.write_3mf(base + '.3mf', [('cap %gU %s' % (A.units, label), 1, (bed / 2, bed / 2),
                                 [(pn, fil, (sh(m[0]), m[1])) for (pn, fil, _), m in zip(parts, meshes)], per_object)],
                bed, {1: 'legend cap %gU %s' % (A.units, label)}, title='keycap %gU %s (keyboard-workshop)' % (A.units, label))
    if A.fusion:
        json.dump(fusion_recipe(A.units, A.legend, shell, core), open(os.path.join(A.out, 'legend_' + name + '_fusion.json'), 'w',
                  encoding='utf-8'), indent=1, ensure_ascii=False)
    for pn, _, s in parts:
        bb = s.bounding_box()
        print('%s %s: %.1f mm3, %d solid(s), box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
            name, pn, s.volume, len(s.solids()), bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z))


if __name__ == '__main__':
    main()
