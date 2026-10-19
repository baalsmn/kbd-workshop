# Waypoints for the 5 V trunks, for route_grid.py --chains (KiCad python).
# One trunk per key row and half, on the back, in the free band just north of the row's
# LEDs (between the LEDs / caps and the next row's socket pads): the row line on the
# back runs just south of each LED, so each LED row gets its own trunk and its LEDs
# and caps a 2-3 mm branch. A waypoint per key at key-local (0, -NORTH), in the key's
# own frame, chained from the outer column inwards (turned thumb keys left out); the
# inner ends are joined to the 5 V feed in the centre routing step.
# Usage: python tools/lib/power_chains.py <board.kicad_pcb> <out.json> [width mm]
import sys, re, math, json, pcbnew
NORTH = 9.0            # mm north of the key centre (LED centre is 5.16 north)
b = pcbnew.LoadBoard(sys.argv[1])
width = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
keys = {}
for f in b.GetFootprints():
    if not f.GetReference().startswith('S'): continue
    nets = [p.GetNetname() for p in f.Pads() if p.GetNumber()]
    k = next((n for n in nets if re.search(r'_?c\d+_r\d+$', n)), None)
    if not k: continue
    m = re.search(r'(mirror_)?(?:hand-zone_)?c(\d+)_r(\d+)$', k)
    half = 'right' if m.group(1) else 'left'
    a = math.radians(f.GetOrientationDegrees()); o = f.GetPosition()
    # key-local (u, v) -> board: inverse of the footprint frame used by route_grid
    u, v = 0.0, -NORTH
    x = o.x / 1e6 + u * math.cos(a) + v * math.sin(a)
    y = o.y / 1e6 - u * math.sin(a) + v * math.cos(a)
    keys[(half, int(m.group(3)), int(m.group(2)))] = (x, y, f.GetOrientationDegrees())
chains = []
for half in ('left', 'right'):
    for r in sorted({k[1] for k in keys if k[0] == half}):
        angs = sorted(keys[k][2] for k in keys if k[0] == half); med = angs[len(angs) // 2]
        # turned keys (the thumb keys) stay out of the trunks: a trunk through the thumb
        # area boxes their LEDs in; they branch to the nearest 5 V copper instead
        cols = sorted(c for (h, rr, c) in keys if h == half and rr == r and abs(keys[(h, rr, c)][2] - med) < 1.0)
        pts = [keys[(half, r, c)][:2] for c in cols]
        chains.append({'width': width, 'half': half, 'row': r, 'points': [[round(x, 3), round(y, 3)] for x, y in pts]})
json.dump({'VCC': chains}, open(sys.argv[2], 'w'), indent=1)
print('%d trunks: ' % len(chains) + ', '.join('%s r%d (%d keys)' % (c['half'], c['row'], len(c['points'])) for c in chains))
