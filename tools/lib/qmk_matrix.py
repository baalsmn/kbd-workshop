# Matrix (row / column via each switch's diode), LED chain index and position of every key
# on a routed project board, named by the Ergogen points, for tools/lib/qmk_gen.py.
# KiCad python, after tools/build.sh <name> (for out/points/points.yaml):
#   python tools/lib/qmk_matrix.py <keyboard>/kicad/<name>.kicad_pcb out/points/points.yaml <keyboard>/firmware/matrix.json
# The LEDs are matched to the key whose LED window (0.69 W, 5.16 N of the switch) they sit
# in; LEDs with no key are the indicators. LED index = LED reference - 1 (the chain order).
import sys, json, math, re, pcbnew
board, points_yaml, out = sys.argv[1:4]
b = pcbnew.LoadBoard(board)
# --- points (name -> x, y in Ergogen frame, y up) ---
pts, cur = {}, None
for line in open(points_yaml, encoding='utf-8'):
    m = re.match(r'^(\S+):\s*$', line)
    if m: cur = m.group(1); pts[cur] = {}; continue
    m = re.match(r"^    (x|'y'|r):\s*(-?[\d.]+)", line) or re.match(r"^        (keycap_u):\s*(-?[\d.]+)", line)
    if m and cur: pts[cur][m.group(1).strip("'")] = float(m.group(2))
pts = {k: v for k, v in pts.items() if 'x' in v and 'y' in v}
fps = {f.GetReference(): f for f in b.Footprints()}
sw = [f for f in fps.values() if 'Hotswap' in f.GetFPID().GetLibItemName().wx_str()]
P = lambda f: (f.GetPosition().x / 1e6, f.GetPosition().y / 1e6)
# fit: board = (x + dx, -y + dy); translation from the centroids
cx = sum(P(f)[0] for f in sw) / len(sw); cy = sum(P(f)[1] for f in sw) / len(sw)
px = sum(v['x'] for v in pts.values()) / len(pts); py = sum(-v['y'] for v in pts.values()) / len(pts)
dx, dy = cx - px, cy - py
# net -> pads
pads_by_net = {}
for f in fps.values():
    for p in f.Pads():
        pads_by_net.setdefault(p.GetNetname(), []).append((f.GetReference(), p.GetNumber()))
keys, worst = [], 0
for f in sw:
    x, y = P(f)
    name = min(pts, key=lambda k: math.hypot(pts[k]['x'] + dx - x, -pts[k]['y'] + dy - y))
    d = math.hypot(pts[name]['x'] + dx - x, -pts[name]['y'] + dy - y); worst = max(worst, d)
    nets = [p.GetNetname() for p in f.Pads() if p.GetNumber() in ('1', '2')]
    col = [n for n in nets if re.fullmatch(r'C\d+', n)]
    other = [n for n in nets if not re.fullmatch(r'C\d+', n)]
    assert len(col) == 1 and len(other) == 1, (f.GetReference(), nets)
    diode = [r for r, n in pads_by_net[other[0]] if r.startswith('D')]
    assert len(diode) == 1, (f.GetReference(), other, diode)
    dnets = [p.GetNetname() for p in fps[diode[0]].Pads()]
    row = [n for n in dnets if re.fullmatch(r'R\d+', n)]
    assert len(row) == 1, (diode[0], dnets)
    # LED of this key: the LED nearest the switch's LED window (5.16 mm north)
    a = math.radians(f.GetOrientationDegrees())
    wx, wy = x + (-0.69) * math.cos(a) + (-5.16) * math.sin(a), y - (-0.69) * math.sin(a) + (-5.16) * math.cos(a)
    leds = [g for g in fps.values() if re.fullmatch(r'LED\d+', g.GetReference())]
    led = min(leds, key=lambda g: math.hypot(P(g)[0] - wx, P(g)[1] - wy))
    q = pts[name]
    keys.append({'name': name, 'ref': f.GetReference(), 'px': q['x'], 'py': q['y'], 'pr': q.get('r', 0), 'u': q.get('keycap_u', 1), 'col': col[0], 'row': row[0], 'x': x, 'y': y, 'r': f.GetOrientationDegrees(),
                 'led': int(led.GetReference()[3:]) - 1, 'led_dist': round(math.hypot(P(led)[0] - wx, P(led)[1] - wy), 2)})
used = {k['led'] for k in keys}
leds = sorted((int(g.GetReference()[3:]) - 1, P(g)) for g in fps.values() if re.fullmatch(r'LED\d+', g.GetReference()))
ind = [(i, p) for i, p in leds if i not in used]
keys.sort(key=lambda k: k['name'])
json.dump({'keys': keys, 'leds': [{'index': i, 'x': p[0], 'y': p[1]} for i, p in leds], 'indicators': [i for i, p in ind]}, open(out, 'w'), indent=1)
print('%d keys, worst name match %.2f mm, worst LED match %.2f mm, LEDs %d, indicators %s' % (len(keys), worst, max(k['led_dist'] for k in keys), len(leds), [i for i, p in ind]))
print('rows', sorted({k['row'] for k in keys}, key=lambda s: int(s[1:])), 'cols', sorted({k['col'] for k in keys}, key=lambda s: int(s[1:])))
print('duplicate matrix spots:', [rc for rc in {(k['row'], k['col']) for k in keys} if sum(1 for q in keys if (q['row'], q['col']) == rc) > 1])
print('duplicate LEDs:', [i for i in used if sum(1 for q in keys if q['led'] == i) > 1])
