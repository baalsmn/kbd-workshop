# 1:1 printable layout of a built design (keycaps with legends + case outline) as a
# vector PDF: one A4 landscape page per half, each running OVERLAP mm past the centre
# line with alignment marks, so the two sheets can be taped together. A 100 mm ruler
# on each page checks the print scale (print at 100 % / "actual size").
#
# Usage (after tools/build.sh <name>; needs PyMuPDF and node):
#   python tools/lib/printview.py <name> <kle json> <out.pdf>
# Reads out/points/points.yaml and out/outlines/*.dxf. Legend: centre-left (Hungarian
# character), else front-centre (QMK keycode), as in topview.js.
import sys, os, re, math, json, subprocess
import pymupdf

name, kle_file, out_pdf = sys.argv[1:4]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'out')
SP, CAP, OVERLAP = 19.0, 18.2, 10.0               # key spacing, 1U keycap size, past the centre line
MM = 72 / 25.4
A4W, A4H = 297.0, 210.0
FONT = r'C:\Windows\Fonts\arial.ttf'
FONTB = r'C:\Windows\Fonts\arialbd.ttf'

# ---- key points: x, y, r, keycap width
K, cur = {}, None
for l in open(os.path.join(OUT, 'points', 'points.yaml'), encoding='utf-8'):
    m = re.match(r'^((?:mirror_)?[\w-]+_c\d+_r\d+):', l)
    if m: cur = m.group(1); K[cur] = {'u': 1.0}; continue
    if re.match(r'^\S', l): cur = None
    if not cur: continue
    m = re.match(r"^    (x|'y'|r): ([-\d.e]+)", l)
    if m: K[cur][m.group(1).strip("'")] = float(m.group(2))
    m = re.match(r'^        keycap_u: ([\d.]+)', l)
    if m: K[cur]['u'] = float(m.group(1))
left = [n for n in K if not n.startswith('mirror_')]

# ---- legends from the KLE file (kle_parse.js), matched by position within a half
kle = json.loads(subprocess.run(['node', '-e', 'console.log(JSON.stringify(require(process.argv[1])))',
                                 os.path.join(ROOT, 'tools', 'lib', 'kle_parse.js')],
                                env=dict(os.environ, KLE_FILE=kle_file), capture_output=True, encoding='utf-8', check=True).stdout)
MIRROR = min(k['x'] for k in kle) + max(k['x'] for k in kle)     # right half = mirrored left (x -> MIRROR - x)
a = math.radians(15)
def local(n, o):                                   # key position in the left half's own frame, in U
    dx, dy = K[n]['x'] - K[o]['x'], K[n]['y'] - K[o]['y']
    return (dx * math.cos(a) - dy * math.sin(a)) / SP, (dx * math.sin(a) + dy * math.cos(a)) / SP
ref = left[0]
o = min(left, key=lambda n: (round(local(n, ref)[1], 1), local(n, ref)[0]))   # bottom-left key
kleft = [k for k in kle if k['x'] < MIRROR / 2]
ko = max(kleft, key=lambda k: (round(k['y'], 1), -k['x']))                    # its KLE key
def legend(n):
    src = n.replace('mirror_', '')
    lx, ly = local(src, o)
    tx, ty = ko['x'] + lx, ko['y'] - ly
    if n.startswith('mirror_'): tx = MIRROR - tx
    q = min(kle, key=lambda k: math.hypot(k['x'] - tx, k['y'] - ty))
    if math.hypot(q['x'] - tx, q['y'] - ty) > 0.2: return '?'
    p = q['pos'] + [''] * 12
    return (p[3] or p[10] or p[4] or p[0] or '').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

# ---- outlines (DXF LINE / ARC / CIRCLE / LWPOLYLINE) as polylines, y up
def dxf(f):
    path = os.path.join(OUT, 'outlines', f + '.dxf')
    if not os.path.exists(path): return []
    t = [s.strip() for s in open(path, encoding='utf-8').read().splitlines()]
    out = []
    for i in range(len(t) - 1):
        if t[i] != '0': continue
        typ, o_, pts = t[i + 1], {}, []
        j = i + 2
        while j < len(t) - 1 and t[j] != '0':
            if typ == 'LWPOLYLINE' and t[j] == '10': pts.append([float(t[j + 1]), 0.0])
            elif typ == 'LWPOLYLINE' and t[j] == '20': pts[-1][1] = float(t[j + 1])
            else: o_[t[j]] = float(t[j + 1]) if re.match(r'^-?[\d.e+-]+$', t[j + 1]) else t[j + 1]
            j += 2
        if typ == 'LINE': out.append([(o_['10'], o_['20']), (o_['11'], o_['21'])])
        elif typ in ('ARC', 'CIRCLE'):
            r = o_['40']; s0 = math.radians(o_.get('50', 0)); s1 = math.radians(o_.get('51', 360))
            if s1 <= s0: s1 += 2 * math.pi
            n_ = max(8, int((s1 - s0) * r / 0.5))
            out.append([(o_['10'] + r * math.cos(s0 + (s1 - s0) * k / n_), o_['20'] + r * math.sin(s0 + (s1 - s0) * k / n_)) for k in range(n_ + 1)])
        elif typ == 'LWPOLYLINE' and pts:
            out.append([tuple(p) for p in pts] + ([tuple(pts[0])] if int(o_.get('70', 0)) & 1 else []))
    return out

case = dxf('case')
xs = [p[0] for s in case for p in s]; ys = [p[1] for s in case for p in s]
CX = (K['hand-zone_c9_r2']['x'] + K['mirror_hand-zone_c9_r2']['x']) / 2      # centre line
YTOP, YBOT = max(ys), min(ys)
layers = [('case', (0.15, 0.15, 0.17), 0.5, None), ('pcb', (0.25, 0.6, 0.25), 0.25, [2, 1.2]),
          ('cirque_cover', (0.45, 0.45, 0.45), 0.35, None), ('cirque_flush', (0.1, 0.1, 0.1), 0.35, None),
          ('oled_window', (0.2, 0.3, 0.6), 0.35, None), ('indicator_holes', (0.7, 0.5, 0.0), 0.3, None)]

BOLD = pymupdf.Font(fontfile=FONTB)
doc = pymupdf.open()
for side in ('left', 'right'):
    page = doc.new_page(width=A4W * MM, height=A4H * MM)
    page.insert_font(fontname='ar', fontfile=FONT); page.insert_font(fontname='arb', fontfile=FONTB)
    if side == 'left': x0, x1 = min(xs) - 1, CX + OVERLAP
    else: x0, x1 = CX - OVERLAP, max(xs) + 1
    ox = (A4W - (x1 - x0)) / 2 - x0                 # page x = model x + ox (centred)
    oy = (A4H - (YTOP - YBOT)) / 2 + YTOP + 6       # page y = oy - model y (a bit low: title above)
    P = lambda x, y: pymupdf.Point((x + ox) * MM, (oy - y) * MM)
    clip = pymupdf.Rect((x0 + ox) * MM, 0, (x1 + ox) * MM, A4H * MM)
    sh = page.new_shape()
    def poly(pts, color, width, dashes=None, fill=None, close=False):
        sh.draw_polyline([P(*p) for p in pts])
        sh.finish(color=color, fill=fill, width=width * MM, dashes=('[%s] 0' % ' '.join('%g' % (d * MM) for d in dashes)) if dashes else None,
                  closePath=close)
    for f, col, w, dash in layers:
        for seg in dxf(f):
            if any(x0 - 2 <= x <= x1 + 2 for x, _ in seg): poly(seg, col, w, dash)
    # keycaps
    for n, k in K.items():
        if not (x0 - 12 < k['x'] < x1 + 12): continue
        w, h = (k['u'] - 1) * SP + CAP, CAP
        r = math.radians(k['r']); c, s = math.cos(r), math.sin(r)
        corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        poly([(k['x'] + u * c - v * s, k['y'] + u * s + v * c) for u, v in corners], (0.45, 0.45, 0.47), 0.3, fill=(0.88, 0.88, 0.9), close=True)
    # centre line and alignment marks (tape the sheets together along it)
    poly([(CX, YTOP + 9), (CX, YBOT - 9)], (0.8, 0.1, 0.1), 0.3, [3, 2])
    for y in (YTOP + 6, YBOT - 6):
        poly([(CX - 4, y), (CX + 4, y)], (0.8, 0.1, 0.1), 0.3); poly([(CX, y - 4), (CX, y + 4)], (0.8, 0.1, 0.1), 0.3)
    sh.commit()
    # legends (rotated with the key)
    for n, k in K.items():
        if not (x0 - 12 < k['x'] < x1 + 12): continue
        t = legend(n)
        size = 9 if len(t) <= 2 else 7 if len(t) <= 4 else 5.5
        tw = BOLD.text_length(t, fontsize=size)
        pt = P(k['x'], k['y'])
        page.insert_text(pymupdf.Point(pt.x - tw / 2, pt.y + size * 0.35), t, fontname='arb', fontsize=size, color=(0.15, 0.15, 0.15),
                         morph=(pt, pymupdf.Matrix(k['r'])))
    # trim everything outside this sheet's area (the sheets then tile cleanly at the centre line)
    ms = page.new_shape()
    for r_ in (pymupdf.Rect(0, 0, (x0 + ox) * MM, A4H * MM), pymupdf.Rect((x1 + ox) * MM, 0, A4W * MM, A4H * MM)):
        if r_.width > 0: ms.draw_rect(r_)
    ms.finish(color=None, fill=(1, 1, 1), width=0); ms.commit()
    # page furniture: title, ruler, notes
    page.insert_text(pymupdf.Point(12 * MM, 12 * MM), '%s - %s half - 1:1 scale' % (name, side), fontname='arb', fontsize=13)
    page.insert_text(pymupdf.Point(12 * MM, 17 * MM), 'Print at 100 %% ("actual size", no fit-to-page). Check the 100 mm ruler. '
                     'Keycaps %.1f mm per 1U at %g mm spacing. Red dashed line = keyboard centre: overlap the sheets there.' % (CAP, SP),
                     fontname='ar', fontsize=7.5, color=(0.3, 0.3, 0.3))
    rs = page.new_shape(); rx, ry = (12 if side == 'left' else A4W - 130), A4H - 12   # ruler away from the centre line
    rs.draw_line(pymupdf.Point(rx * MM, ry * MM), pymupdf.Point((rx + 100) * MM, ry * MM))
    for i in range(0, 101, 10):
        rs.draw_line(pymupdf.Point((rx + i) * MM, ry * MM), pymupdf.Point((rx + i) * MM, (ry - (3 if i % 50 else 5)) * MM))
    rs.finish(color=(0, 0, 0), width=0.3 * MM); rs.commit()
    for i in (0, 50, 100):
        page.insert_text(pymupdf.Point((rx + i - 1.5) * MM, (ry - 6) * MM), '%d' % i, fontname='ar', fontsize=7)
    page.insert_text(pymupdf.Point((rx + 103) * MM, ry * MM), '100 mm', fontname='ar', fontsize=8)
doc.subset_fonts()                               # embed only the glyphs used
doc.save(out_pdf, garbage=3, deflate=True)
print('wrote %s (%d pages, centre line x %.2f, %d keys)' % (out_pdf, len(doc), CX, len(K)))
