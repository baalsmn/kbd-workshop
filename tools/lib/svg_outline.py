# Outline of a single-path SVG (M/m L/l H/h V/v C/c Z/z) as a polygon, normalised so
# the larger of width / height spans [-1, 1] (x right, y down). Used for the logo
# footprint: python tools/lib/svg_outline.py drafts/<logo>.svg [samples per curve]
import sys, re, json, math

def path_points(d, nc=12):
    tok = re.findall(r'[MmLlHhVvCcZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)
    i, cmd, x, y, sx, sy, out, loops = 0, None, 0.0, 0.0, 0.0, 0.0, [], []
    num = lambda: float(tok[i])
    while i < len(tok):
        if re.match(r'[A-Za-z]', tok[i]): cmd = tok[i]; i += 1
        if cmd in 'Zz':
            if out: loops.append(out); out = []
            x, y = sx, sy; continue
        rel = cmd.islower(); c = cmd.upper()
        if c == 'M':
            x, y = (x + float(tok[i]), y + float(tok[i + 1])) if rel else (float(tok[i]), float(tok[i + 1])); i += 2
            if out: loops.append(out)
            out = [(x, y)]; sx, sy = x, y; cmd = 'l' if rel else 'L'
        elif c == 'L':
            x, y = (x + float(tok[i]), y + float(tok[i + 1])) if rel else (float(tok[i]), float(tok[i + 1])); i += 2; out.append((x, y))
        elif c == 'H':
            x = x + float(tok[i]) if rel else float(tok[i]); i += 1; out.append((x, y))
        elif c == 'V':
            y = y + float(tok[i]) if rel else float(tok[i]); i += 1; out.append((x, y))
        elif c == 'C':
            v = [float(t) for t in tok[i:i + 6]]; i += 6
            p1, p2, p3 = ((x + v[0], y + v[1]), (x + v[2], y + v[3]), (x + v[4], y + v[5])) if rel else ((v[0], v[1]), (v[2], v[3]), (v[4], v[5]))
            p0 = (x, y)
            for k in range(1, nc + 1):
                t = k / nc; a, b, cc, dd = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                out.append((a * p0[0] + b * p1[0] + cc * p2[0] + dd * p3[0], a * p0[1] + b * p1[1] + cc * p2[1] + dd * p3[1]))
            x, y = p3
        else: raise ValueError('unsupported path command ' + cmd)
    if out: loops.append(out)
    return loops

def signed_area(P): return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(P, P[1:] + P[:1]))

def keyhole(loops):
    """One polygon from an outer loop plus holes (even-odd fill): each hole is joined
    to the outer outline by a zero-width slit straight up from its topmost vertex
    (y down), so a single filled polygon shows the holes as gaps."""
    loops = [l[:-1] if len(l) > 1 and math.dist(l[0], l[-1]) < 1e-9 else l for l in loops]
    outer = max(loops, key=lambda l: abs(signed_area(l)))
    holes = [l for l in loops if l is not outer]
    if signed_area(outer) < 0: outer = outer[::-1]
    for h in sorted(holes, key=lambda l: min(p[1] for p in l)):
        if signed_area(h) > 0: h = h[::-1]                      # holes run the other way
        k = min(range(len(h)), key=lambda i: (h[i][1], h[i][0])); hx, hy = h[k]
        best = None                                             # first outer edge straight above
        for j in range(len(outer)):
            a, b = outer[j], outer[(j + 1) % len(outer)]
            if (a[0] - hx) * (b[0] - hx) > 0 or a[0] == b[0]: continue
            t = (hx - a[0]) / (b[0] - a[0]); y = a[1] + t * (b[1] - a[1])
            if y < hy and (best is None or y > best[0]): best = (y, j)
        y, j = best
        ring = h[k:] + h[:k]
        outer = outer[:j + 1] + [(hx, y)] + ring + [ring[0], (hx, y)] + outer[j + 1:]
    return outer

if __name__ == '__main__':
    svg = open(sys.argv[1], encoding='utf-8').read()
    d = re.search(r'<path[^>]*\sd="([^"]+)"', svg, re.S).group(1)
    loops = path_points(d, int(sys.argv[2]) if len(sys.argv) > 2 else 12)
    pts = keyhole(loops) if len(loops) > 1 else loops[0]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9: pts = pts[:-1]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2; R = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
    print(json.dumps([[round((x - cx) / R, 5), round((y - cy) / R, 5)] for x, y in pts]))
    print('%d loop(s) -> one polygon, %d points, %.4f x %.4f units' % (len(loops), len(pts), max(xs) - min(xs), max(ys) - min(ys)), file=sys.stderr)
