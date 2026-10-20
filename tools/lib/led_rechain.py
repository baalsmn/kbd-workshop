# Re-order the SK6812 data chain on a (routed) KiCad board and renumber it
# (KiCad python). The new order is given as runs of the existing chain:
#   python tools/lib/led_rechain.py <board.kicad_pcb> "LED74>LED41,LED75,LED76,LED4>LED37" [--dry]
#   "A>B" = from LED A along the existing chain to LED B; "A" = that single LED.
#   The runs must cover every LED exactly once.
# Then:
#   - LEDs are renamed LED1..LEDn in the new order, each LED's cap (the 0603 next to
#     it, its old C<number>) is renamed to match (LEDk + Ck);
#   - data nets: R1 (the 330 R after the MCU) -> LED1 is LED_DATA, LEDk DOUT -> LEDk+1
#     DIN is LED_k, the last LED's DOUT has no net (no-connect);
#   - tracks / vias of connections that survive (same DOUT -> DIN pads) get the new net
#     name; those of dropped connections are deleted; new connections are left
#     unrouted (ratsnest).
# Run tools/lib/kicad_project.py on the result afterwards for a matching schematic.
import sys, re, pcbnew
board_f, spec = sys.argv[1], sys.argv[2]
dry = '--dry' in sys.argv
b = pcbnew.LoadBoard(board_f)
fp = {f.GetReference(): f for f in b.GetFootprints()}
leds = {r: f for r, f in fp.items() if re.fullmatch(r'LED\d+', r)}
pad = lambda f, n: next(p for p in f.Pads() if p.GetNumber() == n)
DIN, DOUT = '2', '4'
nxt = {}                                   # existing chain: LED -> next LED (via its DOUT net)
by_din = {pad(f, DIN).GetNetname(): r for r, f in leds.items()}
for r, f in leds.items():
    n = pad(f, DOUT).GetNetname()
    if n in by_din: nxt[r] = by_din[n]
order = []
for run in spec.split(','):
    a, _, z = run.strip().partition('>')
    if not z: order.append(a); continue
    cur = a
    while True:
        order.append(cur)
        if cur == z: break
        cur = nxt.get(cur)
        if cur is None: sys.exit('run %s: the chain ends before %s' % (run, z))
if sorted(order) != sorted(leds): sys.exit('the runs cover %d LEDs (%d distinct), the board has %d' % (len(order), len(set(order)), len(leds)))
r1 = fp['R1']
first_in = pad(r1, '2')
print('new chain: R1 -> ' + ' -> '.join(order[:3]) + ' ... ' + ' -> '.join(order[-2:]))

# caps: the 0603 cap whose VCC pad is nearest to the LED's VDD pad (pad 3)
caps = {r: f for r, f in fp.items() if re.fullmatch(r'C\d+', r) and 'C_0603' in f.GetFPIDAsString()}
capof = {}
for r, f in leds.items():
    vdd = pad(f, '3').GetPosition()
    c = min(caps, key=lambda q: min((p.GetPosition() - vdd).EuclideanNorm() for p in caps[q].Pads()))
    capof[r] = c
if len(set(capof.values())) != len(capof): sys.exit('cap pairing is not one to one')

# connections: (DOUT pad of a / R1 pin 2) -> (DIN pad of b)
old_conn = {}                             # old net name -> (from pad, to pad)
for r, f in leds.items():
    n = pad(f, DIN).GetNetname()
    src = [p for f2 in b.GetFootprints() for p in f2.Pads() if p.GetNetname() == n and not (f2.GetReference() == r and p.GetNumber() == DIN)]
    old_conn[n] = (src[0] if src else None, pad(f, DIN))
new_conn = [(first_in, pad(leds[order[0]], DIN), 'LED_DATA')] + \
           [(pad(leds[a], DOUT), pad(leds[bb], DIN), 'LED_%d' % (k + 1)) for k, (a, bb) in enumerate(zip(order, order[1:]))]
key = lambda p: (p.GetParentFootprint().GetReference(), p.GetNumber()) if p else None
old_by_pair = {(key(s), key(d)): n for n, (s, d) in old_conn.items()}
tracks = {}
for t in b.GetTracks(): tracks.setdefault(t.GetNetname(), []).append(t)
kept, new, dropped = [], [], []
used_old = set()
for s, d, name in new_conn:
    on = old_by_pair.get((key(s), key(d)))
    if on: kept.append((on, name)); used_old.add(on)
    else: new.append(name)
for n in old_conn:
    if n not in used_old: dropped.append(n)
last_out = pad(leds[order[-1]], DOUT)
print('connections kept (tracks renamed): %d, new (unrouted): %s, dropped (tracks deleted): %s' % (len(kept), new, dropped))
print('tracks deleted: %d' % sum(len(tracks.get(n, [])) for n in dropped))
if dry: sys.exit(0)

def net(name):
    ni = b.FindNet(name)
    if ni is None or ni.GetNetCode() <= 0:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni)
    return ni
# 1. drop the tracks of dropped connections
for n in dropped:
    for t in tracks.get(n, []): b.Remove(t)
# 2. every data pad / kept track to a temporary net, then to its final net
tmp = {}
for on, name in kept:
    tmp[name] = net('__tmp_' + name)
    for t in tracks.get(on, []): t.SetNet(tmp[name])
for s, d, name in new_conn:
    ni = tmp.get(name) or net('__tmp_' + name); tmp[name] = ni
    s.SetNet(ni); d.SetNet(ni)
for n in dropped:                          # pads of dropped connections not reused above
    for f2 in b.GetFootprints():
        for p in f2.Pads():
            if p.GetNetname() == n: p.SetNet(b.FindNet(''))
last_out.SetNet(b.FindNet('') or net(''))
for name, ni in tmp.items():
    final = net(name) if b.FindNet(name) is None else None
    tgt = final or b.FindNet(name)
    for f2 in b.GetFootprints():
        for p in f2.Pads():
            if p.GetNetCode() == ni.GetNetCode(): p.SetNet(tgt)
    for t in b.GetTracks():
        if t.GetNetCode() == ni.GetNetCode(): t.SetNet(tgt)
# 3. renumber LEDs and their caps (via temporary names)
ren = {}
for k, r in enumerate(order):
    ren[r] = 'LED%d' % (k + 1); ren[capof[r]] = 'C%d' % (k + 1)
for old in ren: fp[old].SetReference('__' + old)
for old, newr in ren.items(): fp[old].SetReference(newr)
# the free DOUT of the last LED: KiCad's no-connect net name, as the schematic generator uses
last_out.SetNet(net('unconnected-(%s-DOUT-Pad4)' % ren[order[-1]]))
b.BuildConnectivity()
pcbnew.SaveBoard(board_f, b)
print('saved %s: %d LEDs and caps renumbered; unconnected now %d' % (board_f, len(order), b.GetConnectivity().GetUnconnectedCount(True)))
