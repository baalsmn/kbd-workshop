# One key: the assembly STEP (cap + legend insert + legend body in place, coloured) and the
# parts as separate files: key_<name>.step (assembly), key_<name>_cap.step/.stl,
# key_<name>_insert.step/.stl (insert in its own frame, top up) and key_<name>_legend.stl.
# Usage: python keycaps/assembly.py [u] [legend] [--stab] [--thumb]   -> keycaps/build/
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Compound, Color, export_step, export_stl
import keycap as K

args = [a for a in sys.argv[1:] if not a.startswith('--')]
u = float(args[0]) if args else 1.0
legend = args[1] if len(args) > 1 else 'A'
stab, thumb = '--stab' in sys.argv, '--thumb' in sys.argv
P = K.P
z_top, z_pocket, z_ceil = K.insert_levels(P)
cap = K.build_cap(u, stab, thumb)
ins, leg = K.build_insert(legend)
place = K.top_frame(P) * Pos(0, 0, z_pocket)
tag = 'key_%gu%s%s_%s' % (u, '_stab' if stab else '', '_thumb' if thumb else '', K.file_name(legend))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
os.makedirs(out, exist_ok=True)
# the separate parts first (the assembly compound takes the shapes over)
export_step(cap, os.path.join(out, tag + '_cap.step')); export_stl(cap, os.path.join(out, tag + '_cap.stl'))
export_step(ins, os.path.join(out, tag + '_insert.step')); export_stl(ins, os.path.join(out, tag + '_insert.stl'))
if leg is not None:
    export_stl(leg, os.path.join(out, tag + '_legend.stl'))
parts = [cap, place * ins] + ([place * leg] if leg is not None else [])
for s_, (name, col) in zip(parts, [('cap', (0.93, 0.93, 0.90)), ('insert', (0.80, 0.80, 0.78)), ('legend', (0.12, 0.12, 0.14))]):
    s_.label, s_.color = name, Color(*col)
export_step(Compound(children=parts), os.path.join(out, tag + '.step'))
print(os.path.join(out, tag + '.step'), '+ _cap, _insert' + (', _legend' if leg is not None else ''))
