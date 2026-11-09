# The keycaps (user 2026-11-09: monolithic caps only, the insert caps were dropped), built from keycap.py:
#   - blank (--legend ''): one body, one material; the legend goes on later by solvent transfer;
#   - legend (--legend A): split like a double-shot moulding into a translucent core (filament 2: stems,
#     a thin layer over the cavity ceiling, the legend reaching up through the shell) and an opaque
#     shell over it (filament 1: the rest of the top and the skirt), so the switch LED lights the core
#     and shows through the legend only. The legend sits north-west of the top's centre point, its
#     box's south-east corner on it.
#
# Usage (build123d PYTHONPATH): python keycaps/build/legend_cap.py [--units 1,1.25,1.25t,2s,2st,1v] [--legend A] [--fusion]
#   units: see keycap.py (s = stabilizer stems, t = thumb, v = tall). Writes per cap (name
#   cap_<size>_<legend|blank>) the print file keycaps/results/<name>.3mf (Bambu Studio: one object lying
#   on the north skirt face, shell on filament 1, core on filament 2, with the print settings) and
#   build/work/caps/<name>.step (shell + core, coloured). No STL (user: not needed). --fusion: also
#   build/work/caps/<name>_fusion.json for the Fusion builder (KeycapBuilder: build_legend_cap() +
#   export_legend_cap() -> results/<name>.f3d, build/work/fusion/<name>.step / .3mf); the print 3MF then
#   takes its meshes from Fusion's 3MF (shell and core in one file).
import os, sys, math, argparse, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Text, Align, FontStyle, Box, Compound, Color, extrude, export_step
import keycap as K

L = dict(
    legend_size=5.85, legend_style='bold', # font size (cap height ~0.72 x; user: 30 % up from 4.5), bold
                                           # strokes: more light through
    legend_font='Arial',
    legend_at=(0.0, 0.0),                  # the legend box's south-east corner, in the top frame: on the
                                           # top's centre point (user), so the legend fills the north-west
    core_t=0.5,                            # core layer over the cavity ceiling, parallel to it (user: thin core,
                                           # thick shell, so the slicer gets whole lines in both; ~2 x 0.22);
                                           # the shell above it is 1.0 at the centre, more where the top rises
)
PER_OBJECT = {'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '0',
              'support_threshold_angle': '40', 'brim_type': 'outer_only', 'brim_width': '4',
              'brim_object_gap': '0.1', 'seam_position': 'back', 'wall_loops': '8'}
BED = 256.0


def tag(legend):
    """File / design name part: the legend's file name, 'blank' for none."""
    return K.file_name(legend) if legend else 'blank'


def legend_cap(u, legend, stab=False, thumb=False, tall=False, p=None, l=L):
    """(shell, core) in the cap frame. The core (translucent, filament 2) is the stems, a core_t layer
    over the cavity ceiling (inside the skirt walls) and the legend, reaching up through the shell; the
    shell (filament 1) is the rest of the top and the skirt. No legend (''): the blank cap, one body:
    (cap, None)."""
    p = K.cap_params(thumb, tall, K.P if p is None else p)
    cap = K.build_cap(u, stab, thumb, p)
    if not legend:
        return cap.clean(), None
    tf = K.top_frame(p)
    z_ceil = K.z_ceiling(p)
    level = Pos(0, 0, p['h_centre'] + z_ceil + l['core_t']) if p.get('ceiling_level') else tf * Pos(0, 0, z_ceil + l['core_t'])
    under = level * Box(200, 200, 40, align=(Align.CENTER, Align.CENTER, Align.MAX))
    column = K.wall_inside(u, p) + Box(200, 200, 10, align=(Align.CENTER, Align.CENTER, Align.MAX))   # (+ the stem ends below the skirt)
    core = cap & column & under
    txt = Text(legend, l['legend_size'], font=l['legend_font'],
               font_style=FontStyle.BOLD if l['legend_style'] == 'bold' else FontStyle.REGULAR,
               align=(Align.MAX, Align.MIN))
    core = core + (cap & tf * Pos(*l['legend_at'], z_ceil - 0.05) * extrude(txt, amount=6))
    shell = cap - core
    return shell.clean(), core.clean()


def fusion_recipe(u, legend, shell, core, stab=False, thumb=False, tall=False, p=None, l=L):
    """keycap.recipe() plus what the double-shot split needs (KeycapBuilder); blank caps: legend / core
    None (one body)."""
    p = K.cap_params(thumb, tall, K.P if p is None else p)
    r = K.recipe(u, stab, thumb, p)
    r.update({'name': '%s_%s' % (K.cap_name(u, stab, thumb, tall), tag(legend)), 'legend': None,
              'core': None, 'volume': shell.volume + (core.volume if core else 0)})
    if legend:
        t = Text(legend, l['legend_size'], font=l['legend_font'],
                 font_style=FontStyle.BOLD if l['legend_style'] == 'bold' else FontStyle.REGULAR)
        bb = t.bounding_box()
        r.update({'legend': {'text': legend, 'font': l['legend_font'], 'bold': l['legend_style'] == 'bold',
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


def fusion_meshes(path, n_parts):
    """The parts' meshes from Fusion's 3MF (all bodies in one file): [cap] for a blank cap, [shell (with
    its islands), core] for a legend cap."""
    import bambu_project as B
    objs = B.read_3mf(path)
    if n_parts == 1:
        groups = [list(objs.values())]
    else:
        groups = [[m for k, m in objs.items() if k != 'core'], [objs['core']] if 'core' in objs else []]
    out = []
    for g in groups:
        if not g: return None
        v, t = [], []
        for vv, tt in g:
            t += [(a + len(v), b + len(v), c + len(v)) for a, b, c in tt]; v += vv
        out.append((v, t))
    return out


def print_meshes(parts, fusion_base=None):
    """The parts' meshes in print orientation: lying on the north skirt face, cavity opening to +y,
    centred, on z = 0. From Fusion's <fusion_base>.3mf (shell and core in one file) when it is there and
    up to date, else tessellated."""
    import bambu_project as B
    a = math.radians(-(90 + K.P['draft']))
    r = lambda x, y, z: (-x, -(y * math.cos(a) - z * math.sin(a)), y * math.sin(a) + z * math.cos(a))
    meshes = None
    src = (fusion_base or '') + '.3mf'
    if fusion_base and K.P['cap_source'] == 'fusion' and os.path.exists(src):
        meshes = fusion_meshes(src, len(parts))
        if meshes is not None:
            vols = [mesh_volume(m) for m in meshes]
            # current = within 0.2 % of build123d, or within 1 % when Fusion built it from the recipe of
            # today's shape (export newer than the recipe, whose build123d volume still matches): Fusion
            # makes fillets build123d can't (the 2U thumb caps, -0.5 %)
            rj = os.path.join(K.CAPS_DIR, os.path.basename(fusion_base) + '_fusion.json')
            total = sum(sp.volume for _, _, sp in parts)
            same_recipe = (os.path.exists(rj) and abs(json.load(open(rj, encoding='utf-8'))['volume'] - total) <= 1e-4 * total
                           and os.path.getmtime(src) >= os.path.getmtime(rj))
            tol = 0.01 if same_recipe else 0.002
            exact = all(abs(v - sp.volume) <= 0.002 * sp.volume for v, (_, _, sp) in zip(vols, parts))
            if all(abs(v - sp.volume) <= tol * sp.volume for v, (_, _, sp) in zip(vols, parts)):
                print('  3MF meshes: Fusion (%s)%s' % (os.path.basename(src), '' if exact else
                      ', %+.2f %% (its fillet)' % (100 * (sum(vols) - total) / total)))
            else:
                print('  3MF meshes: build123d (the Fusion export is out of date: %s mm3 vs %s; rebuild it in Fusion)'
                      % (', '.join('%.1f' % v for v in vols), ', '.join('%.1f' % sp.volume for _, _, sp in parts)))
                meshes = None
    if meshes is None:
        meshes = [B.mesh(sp) for _, _, sp in parts]
    meshes = [([r(*v) for v in m[0]], m[1]) for m in meshes]
    allv = [v for m in meshes for v in m[0]]
    cx = (min(v[0] for v in allv) + max(v[0] for v in allv)) / 2
    cy = (min(v[1] for v in allv) + max(v[1] for v in allv)) / 2
    z0 = min(v[2] for v in allv)
    return [([(x - cx, y - cy, z - z0) for x, y, z in m[0]], m[1]) for m in meshes]


def write_cap(name, label, shell, core, fusion_base=None, step_dir=K.CAPS_DIR, out_dir=K.RESULTS):
    """<step_dir>/<name>.step (coloured bodies) and <out_dir>/<name>.3mf (print-ready, one object)."""
    os.makedirs(step_dir, exist_ok=True); os.makedirs(out_dir, exist_ok=True)
    step, base = os.path.join(step_dir, name), os.path.join(out_dir, name)
    import bambu_project as B
    if core is None:                                       # blank: one body, filament 1
        parts = [('cap', 1, shell)]
        shell.color, shell.label = Color(0.15, 0.15, 0.16), 'cap'
        export_step(shell, step + '.step')
    else:
        parts = [('shell', 1, shell), ('core', 2, core)]
        shell.color, core.color = Color(0.15, 0.15, 0.16), Color(0.95, 0.95, 0.92)
        shell.label, core.label = 'shell', 'core'
        export_step(Compound(children=[shell, core]), step + '.step')
    meshes = print_meshes(parts, fusion_base)
    B.write_3mf(base + '.3mf', [('cap %s' % label, 1, (BED / 2, BED / 2),
                                 [(pn, fil, m) for (pn, fil, _), m in zip(parts, meshes)], dict(PER_OBJECT))],
                BED, {1: 'cap %s' % label}, title='keycap %s (keyboard-workshop)' % label)
    return parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--units', default='1', help='comma-separated sizes: 1, 1.25, 1.25t, 2s, 2st, 1v')
    ap.add_argument('--legend', default='A', help="legend ('' = the blank cap, one material)")
    ap.add_argument('--fusion', action='store_true', help='also write the Fusion recipe')
    A = ap.parse_args()
    os.makedirs(K.CAPS_DIR, exist_ok=True)
    for spec in A.units.split(','):
        u, stab, thumb, tall = K.parse_units(spec)
        shell, core = legend_cap(u, A.legend, stab, thumb, tall)
        size = K.cap_name(u, stab, thumb, tall)
        name = '%s_%s' % (size, tag(A.legend))
        print(name)
        parts = write_cap(name, '%s %s' % (size[4:], A.legend or 'blank'), shell, core, os.path.join(K.FUSION_DIR, name))
        if A.fusion:
            json.dump(fusion_recipe(u, A.legend, shell, core, stab, thumb, tall),
                      open(os.path.join(K.CAPS_DIR, name + '_fusion.json'), 'w', encoding='utf-8'),
                      indent=1, ensure_ascii=False)
        for pn, _, s in parts:
            bb = s.bounding_box()
            print('  %s: %.1f mm3, %d solid(s), valid %s, box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
                pn, s.volume, len(s.solids()), s.is_valid, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z))


if __name__ == '__main__':
    main()
