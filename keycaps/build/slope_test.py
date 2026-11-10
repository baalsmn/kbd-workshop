# Three blank 1U test caps for the top slope (user 2026-11-08: try which way the top should lean, per row):
#   +3  north up (the usual caps: top-row style), north roll-off
#    0  level top, north roll-off (home-row style)
#   -3  south up, roll-off on the south edge (bottom-row style): the +3 cap turned 180 deg about z
# Monolithic (blank) caps, build123d. Writes keycaps/results/cap_1u_slope_<s>.3mf (print-ready, the south
# skirt face on top and horizontal, as every cap) and build/work/slope_test/<same>.step, and checks each over the
# full travel against the KS-33 STEP.
# Usage (build123d PYTHONPATH, from the repo root): python keycaps/build/slope_test.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Rot, import_step, export_step
import keycap as K
import legend_cap as LC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(K.WORK, 'slope_test')
sw = import_step(os.path.join(ROOT, 'kicad-libraries', '3dmodels', 'vendor_Gateron_KS-33_switch.step'))
fixed = [s for s in sw.solids() if s.bounding_box().max.Z <= 8.5]
SEAT = 5.55 + K.P['stem_drop']


def sweep(cap):
    for k in range(31):
        d = k / 10
        v = sum((i.volume if i is not None and i.solids() else 0) for i in ((Pos(0, 0, SEAT - d) * cap) & s for s in fixed))
        if v > 1e-3:
            return 'HITS at %.1f travel (%.3f mm3)' % (d, v)
    return 'clear over the full 3.0 travel'


for s in (3, 0, -3):
    cap = K.build_cap(1, p=dict(K.P, slope=float(abs(s))))
    name = 'cap_1u_slope_%+d' % s if s else 'cap_1u_slope_0'
    if s < 0:                                    # south up: the north-up cap turned round (the stem cross
        cap = Rot(0, 0, 180) * cap               # is symmetric, so it still fits the switch)
    LC.write_cap(name, '1u slope %+d' % s, cap, None, step_dir=OUT)
    b = cap.bounding_box()
    print('%-18s valid %s volume %6.1f  height %.2f  %s' % (name, cap.is_valid, cap.volume, b.size.Z, sweep(cap)))
