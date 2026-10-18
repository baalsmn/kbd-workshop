# Export a built design as an exact KLE (keyboard-layout-editor.com) layout:
# every key at its Ergogen position and angle, with its original KLE labels,
# colours and alignment.
#
# Usage:
#   python tools/lib/kle_export.py <name> <keys map json> <out kle json>
#   python tools/lib/kle_export.py --make-map <kle json> <points.yaml of a build that
#          still matches the KLE file> <keys map json>
# The keys map (key name -> raw KLE label + properties) carries the labels over by
# key name, so it keeps working after keys have moved away from the KLE layout.
#
# KLE units: 1U = 19 mm (the design's key spacing), so positions are exact in mm / 19.
# Each key is its own row with r / rx / ry: rotated about its own centre, which KLE
# draws exactly. Angles: Ergogen r is counter-clockwise (y up), KLE r clockwise
# (y down) -> KLE r = -Ergogen r.
import sys, os, re, json, math

SP = 19.0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def points(path):
    K, cur = {}, None
    for l in open(path, encoding='utf-8'):
        m = re.match(r'^((?:mirror_)?[\w-]+_c\d+_r\d+):', l)
        if m: cur = m.group(1); K[cur] = {'u': 1.0}; continue
        if re.match(r'^\S', l): cur = None
        if not cur: continue
        m = re.match(r"^    (x|'y'|r): ([-\d.e]+)", l)
        if m: K[cur][m.group(1).strip("'")] = float(m.group(2))
        m = re.match(r'^        keycap_u: ([\d.]+)', l)
        if m: K[cur]['u'] = float(m.group(1))
    return K

def kle_keys(path):
    """Keys of an (unrotated) KLE file: centre, raw label and the properties in force."""
    data = json.load(open(path, encoding='utf-8'))
    keys, cur, y = [], {'a': 4, 'c': '#cccccc', 't': '#000000', 'f': 3}, 0.0
    meta = data[0] if isinstance(data[0], dict) else {}
    for row in data:
        if not isinstance(row, list): continue
        x, w, h = 0.0, 1.0, 1.0
        for it in row:
            if isinstance(it, dict):
                for k in ('a', 'c', 't', 'f', 'f2', 'fa', 'p'):
                    if k in it: cur[k] = it[k]
                x += it.get('x', 0); y += it.get('y', 0); w = it.get('w', w); h = it.get('h', h)
                continue
            keys.append({'x': x + w / 2, 'y': y + h / 2, 'w': w, 'label': it, 'props': dict(cur)})
            x += w; w, h = 1.0, 1.0
        y += 1
    return meta, keys

def make_map(kle_file, pts_file, out):
    meta, kk = kle_keys(kle_file); K = points(pts_file)
    left = [n for n in K if not n.startswith('mirror_')]
    a = math.radians(15); ref = left[0]
    def local(n, o):
        dx, dy = K[n]['x'] - K[o]['x'], K[n]['y'] - K[o]['y']
        return (dx * math.cos(a) - dy * math.sin(a)) / SP, (dx * math.sin(a) + dy * math.cos(a)) / SP
    o = min(left, key=lambda n: (round(local(n, ref)[1], 1), local(n, ref)[0]))
    mirror = min(k['x'] for k in kk) + max(k['x'] for k in kk)
    ko = max((k for k in kk if k['x'] < mirror / 2), key=lambda k: (round(k['y'], 1), -k['x']))
    res, miss = {}, []
    for n in sorted(K):
        lx, ly = local(n.replace('mirror_', ''), o)
        tx, ty = ko['x'] + lx, ko['y'] - ly
        if n.startswith('mirror_'): tx = mirror - tx
        q = min(kk, key=lambda k: math.hypot(k['x'] - tx, k['y'] - ty))
        if math.hypot(q['x'] - tx, q['y'] - ty) > 0.2: miss.append(n); continue
        res[n] = {'label': q['label'], 'props': q['props']}
    json.dump({'meta': meta, 'keys': res}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote %s: %d keys mapped, %d unmatched %s' % (out, len(res), len(miss), miss[:5]))

def export(name, map_file, out):
    K = points(os.path.join(ROOT, 'out', 'points', 'points.yaml'))
    M = json.load(open(map_file, encoding='utf-8')); keys = M['keys']
    xs = [k['x'] / SP for k in K.values()]; ys = [-k['y'] / SP for k in K.values()]
    x0, y0 = min(xs) - 1, min(ys) - 1                     # keep everything at positive KLE coordinates
    meta = dict(M.get('meta', {})); meta['name'] = name + ' (exact: Ergogen positions and angles, 1U = 19 mm)'
    rows = [meta]
    order = sorted(K, key=lambda n: (n.startswith('mirror_'), n))
    for n in order:
        k = K[n]; e = keys.get(n, {'label': '', 'props': {}})
        cx, cy = k['x'] / SP - x0, -k['y'] / SP - y0
        r = round(-k['r'], 4) + 0.0
        props = {'r': r, 'rx': round(cx, 5), 'ry': round(cy, 5), 'x': round(-k['u'] / 2, 5), 'y': -0.5}
        if k['u'] != 1: props['w'] = k['u']
        for p in ('c', 't', 'a', 'f', 'f2', 'fa', 'p'):
            if p in e['props']: props[p] = e['props'][p]
        rows.append([props, e['label']])
    json.dump(rows, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote %s: %d keys, %d with labels' % (out, len(order), sum(1 for n in order if n in keys)))

if __name__ == '__main__':
    if sys.argv[1] == '--make-map': make_map(*sys.argv[2:5])
    else: export(*sys.argv[1:4])
