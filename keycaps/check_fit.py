# Fit checks for keycaps/keycap.py (build123d; run from the repo root after building a design,
# so out/points and out/outlines are there):
#   1. each cap seated on the KS-33 (stem on the cup floor) and moved down over the 3.0 travel
#      against the switch's fixed parts, and the 2U cap against the KS-57 housings too;
#   2. the legend insert in its pocket: no overlap, pins flush with the ceiling;
#   3. the cap footprints on the Ergogen key points: gaps between neighbours and to the
#      centre cover / trackpad ring (which stand higher than a pressed cap's skirt).
# Usage: python keycaps/check_fit.py [<design>]   (default hachigo74)
import os, sys, math, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos, Rot, Box, Align, import_step, RectangleRounded, Compound
import ezdxf
import keycap as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, 'kicad-libraries', '3dmodels')
P = K.P
SEAT = 5.55 + P['stem_drop']                     # skirt bottom above the PCB top at rest
TRAVEL = 3.0

sw = import_step(os.path.join(M, 'vendor_Gateron_KS-33_switch.step'))
sw_fixed = [s for s in sw.solids() if s.bounding_box().max.Z <= 8.5]        # housing + cover (actuator moves)
st = import_step(os.path.join(M, 'vendor_Gateron_KS-57B210T_stabilizer.step'))
# stabilizer model: key centre at x 60, PCB top at z 3.25; housings = the two big solids under 9.9
st_fixed = [Pos(-60, 0, -3.25) * s for s in st.solids() if s.volume > 200]


def overlap(a, parts):
    v = 0
    for s in parts:
        i = a & s
        if i is not None and i.solids(): v += i.volume
    return v


def sweep(cap, parts):
    worst = None
    for k in range(int(TRAVEL * 10) + 1):
        d = k / 10
        v = overlap(Pos(0, 0, SEAT - d) * cap, parts)
        if v > 1e-3:
            return d, v
    return None, 0


print('1. travel sweep (skirt bottom %.2f above the PCB top at rest, %.2f bottomed out)' % (SEAT, SEAT - TRAVEL))
caps = {}
for u, stab, thumb in ((1, False, False), (1.25, False, False), (1.25, False, True), (2, True, False), (2, True, True)):
    cap, src = K.get_cap(u, stab, thumb)
    caps[(u, stab, thumb)] = cap
    parts = sw_fixed + (st_fixed if stab else [])
    d, v = sweep(cap, parts)
    print('   %gU%s%s (%s): %s' % (u, ' + stab' if stab else '', ' thumb' if thumb else '', src, 'clear over the full %.1f mm' % TRAVEL if d is None
                            else 'HITS at %.1f mm travel (%.3f mm3)' % (d, v)))
    # the stems / crosses at rest: switch cross top 8.55, stab cross top 9.8 above the PCB top
    if stab:
        print('      stab stem bottom %.2f above the PCB top (KS-57 slider top 6.80)' % (SEAT - P['stem_drop'] + P['stab_rise']))

print('2. legend insert in the pocket')
cap = caps[(1, False, False)]
W, D = 19 - P['gap'], P['depth']
t = math.tan(math.radians(P['draft']))
z_top, z_pocket, z_ceil = K.insert_levels(P, W - 2 * P['h_centre'] * t, D - 2 * P['h_centre'] * t)
ins, _, _ = K.get_insert('A')
placed = K.top_frame(P) * Pos(0, 0, z_pocket) * ins
print('   overlap cap / insert %.4f mm3; insert top %.2f below the top plane; floor %.2f, pins %.1f long (flush with the ceiling)'
      % (overlap(placed, [cap]), -z_top, P['floor'], P['floor']))
cz = P['h_centre'] + z_ceil
print('   ceiling at the centre: cap z %.2f (switch cross top at cap z %.2f when seated)' % (cz, 8.55 - SEAT))

print('3. layout (%s)' % (sys.argv[1] if len(sys.argv) > 1 else 'hachigo74'))
y = subprocess.run(['node', '-e', '''
const y=require(require('child_process').execSync('npm root -g').toString().trim()+'/ergogen/node_modules/js-yaml');
const p=y.load(require('fs').readFileSync(process.argv[1],'utf8'));
console.log(JSON.stringify(Object.entries(p).map(([k,v])=>[k,v.x,v.y,v.r,v.meta.keycap_u||1])))''',
                    os.path.join(ROOT, 'out', 'points', 'points.yaml')], capture_output=True, text=True, shell=False)
pts = json.loads(y.stdout)
foot = {}
for name, x, yy, r, u in pts:
    foot[name] = Pos(x, yy) * Rot(0, 0, r) * RectangleRounded(u * P['pitch'] - P['gap'], P['depth'], P['r_bottom'])
names = list(foot)
gaps = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        da = math.hypot(pts[i][1] - pts[names.index(b)][1], pts[i][2] - pts[names.index(b)][2])
        if da > 45: continue
        gaps.append((foot[a].distance_to(foot[b]), a, b))
gaps.sort()
print('   smallest cap-to-cap gaps (mm):')
for g, a, b in gaps[:6]: print('     %.2f  %s / %s' % (g, a, b))
from step_case import outline_face
for n in ('center_cover_top', 'center_cover_low', 'tp_ring_wall', 'tp_ring_lip'):
    f = os.path.join(ROOT, 'out', 'outlines', n + '.dxf')
    if not os.path.exists(f): continue
    o = outline_face(f)
    near = sorted((o.distance_to(foot[k]), k) for k in names)[:2]
    print('   %-17s nearest caps: %s' % (n, ', '.join('%s %.2f' % (k, d) for d, k in near)))
