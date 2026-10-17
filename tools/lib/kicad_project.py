# Create a portable KiCad project for a design from its built Ergogen board:
#   <project dir>/<name>.kicad_pro / .kicad_pcb / .kicad_sch / .kicad_dru
#   <project dir>/libraries/   copy of "kicad libraries" (symbols, footprints, 3D models)
#   <project dir>/sym-lib-table, fp-lib-table -> ${KIPRJMOD}/libraries/...
# Every path is ${KIPRJMOD}-relative, so the folder can be moved or zipped whole.
#
# The PCB is the Ergogen board with every footprint linked to its library footprint
# (Keyboard:<name>), its 3D models in libraries/3dmodels and its schematic symbol.
# The schematic is generated from the board's netlist: one symbol per footprint
# (same reference, value, footprint), a net label on every pin, laid out in blocks.
#
# Usage (KiCad python, after tools/build.sh <name>):
#   python tools/lib/kicad_project.py out/pcbs/<name>.kicad_pcb "kicad libraries" <project dir> <name> [--force]
# It refuses to overwrite an existing project unless --force is given (the project
# becomes the master once it is routed / edited in KiCad).
import sys, os, re, uuid, shutil, json, collections, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_common import Q, parse, dump, find, RENAME, footprint_name

board_file, libsrc, proj, name = sys.argv[1:5]
# once the project is in use (routing, schematic edits) a re-run would overwrite it
if os.path.exists(os.path.join(proj, name + '.kicad_pcb')) and '--force' not in sys.argv:
    sys.exit('%s already has %s.kicad_pcb - it may hold routing / edits. Re-run with --force to overwrite.' % (proj, name))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIBNICK, FPNICK = 'keyboard-workshop', 'Keyboard'
U = lambda: str(uuid.uuid4())

# ---- 1. libraries copy + tables + rules + project file ----
os.makedirs(proj, exist_ok=True)
libs = os.path.join(proj, 'libraries')
def _writable(func, path, *_):                     # KiCad's own 3D models arrive read-only
    os.chmod(path, 0o666); func(path)
if os.path.exists(libs): shutil.rmtree(libs, onerror=_writable)
for sub in ('Symbols', 'Footprints', '3dmodels'):
    shutil.copytree(os.path.join(libsrc, sub), os.path.join(libs, sub))
shutil.copy2(os.path.join(libsrc, 'README.md'), os.path.join(libs, 'README.md'))
for d, _, fs in os.walk(libs):
    for f in fs: os.chmod(os.path.join(d, f), 0o666)
pretty = os.path.join(libs, 'Footprints', 'Keyboard.pretty')
for f in os.listdir(pretty):                     # 3D paths: ${KIPRJMOD}/3dmodels -> ${KIPRJMOD}/libraries/3dmodels
    p = os.path.join(pretty, f); s = open(p, encoding='utf-8').read()
    open(p, 'w', encoding='utf-8', newline='\n').write(s.replace('${KIPRJMOD}/3dmodels/', '${KIPRJMOD}/libraries/3dmodels/'))
open(os.path.join(proj, 'sym-lib-table'), 'w', newline='\n').write(
    '(sym_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/libraries/Symbols/keyboard-workshop.kicad_sym")(options "")(descr "project symbols"))\n)\n' % LIBNICK)
open(os.path.join(proj, 'fp-lib-table'), 'w', newline='\n').write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/libraries/Footprints/Keyboard.pretty")(options "")(descr "project footprints"))\n)\n' % FPNICK)
shutil.copy2(os.path.join(ROOT, 'keyboard.kicad_dru'), os.path.join(proj, name + '.kicad_dru'))
pro = os.path.join(proj, name + '.kicad_pro')
if not os.path.exists(pro):
    json.dump({'meta': {'filename': name + '.kicad_pro', 'version': 1},
               'sheets': [], 'boards': [], 'text_variables': {}}, open(pro, 'w'), indent=2)

# ---- 2. board: library links, 3D paths, symbol links ----
lib = parse(open(os.path.join(libs, 'Symbols', 'keyboard-workshop.kicad_sym'), encoding='utf-8').read())
LIBSYM = {s[1]: s for s in find(lib, 'symbol')}
def sym_fields(sym, extra):
    f = {pr[1]: pr[2] for pr in find(LIBSYM[sym], 'property')
         if pr[1] not in ('Reference', 'Value', 'Footprint') and not pr[1].startswith('ki_')}
    f.update(extra); return f
b = pcbnew.LoadBoard(board_file)
SHEETFILE = name + '.kicad_sch'
CAPVAL = {'C_0603': '100nF', 'C_0805': '10uF'}
parts = []                                       # one per schematic symbol
INBOM = {}
for fp in sorted(b.GetFootprints(), key=lambda f: (re.sub(r'\d', '', f.GetReference()), int(re.sub(r'\D', '', f.GetReference()) or 0))):
    lname, _ = footprint_name(fp)
    fp.SetFPID(pcbnew.LIB_ID(FPNICK, lname))
    ms = fp.Models()
    for i in range(len(ms)):                     # by index: iterating gives copies (edits would be lost)
        base = os.path.basename(ms[i].m_Filename.replace('\\', '/')); base = RENAME.get(base, base)
        ms[i].m_Filename = '${KIPRJMOD}/libraries/3dmodels/' + base
    ref = fp.GetReference(); kind = re.sub(r'\d', '', ref)
    if kind in ('MECH', 'LOGO'):                 # 3D model / silkscreen only: no symbol
        fp.SetBoardOnly(True); fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        continue
    sym, value, extra = {
        'S':    ('SW_Push_45deg', 'KS-33', {}),
        'D':    ('D', '1N4148W', {}),
        'LED':  ('SK6812MINI-E', 'SK6812MINI-E', {'LCSC': 'C5149201'}),
        'C':    ('C', CAPVAL.get(lname, fp.GetValue()), {}),
        'R':    ('R', fp.GetValue() or '330', {}),
        'MCU':  ('helios', '0xCB Helios', {}),
        'DISP': ('OLED_SSD1306_128x64_I2C', 'SSD1306 0.96in', {}),
        'J':    ('Molex_505278-1270', 'Molex_505278-1270', {'LCSC': 'C47149418'}),
    }[kind]
    if kind == 'S': value = 'KS-33 ' + re.search(r'Hotswap_(.*)$', lname).group(1).replace('_Stab_KS-57', ' + KS-57')
    fp.SetValue(value)
    nets = {}
    for p in fp.Pads():
        if p.GetNumber(): nets[p.GetNumber()] = p.GetNetname()
    u = U()
    fp.SetPath(pcbnew.KIID_PATH('/' + u)); fp.SetSheetname('/'); fp.SetSheetfile(SHEETFILE)
    for k, v in sym_fields(sym, extra).items():      # same fields as the symbol (schematic parity)
        new = not fp.HasField(k); fp.SetField(k, v)
        if new: fld = fp.GetField(k); fld.SetVisible(False); fld.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
    parts.append(dict(ref=ref, kind=kind, sym=sym, value=value, fp=FPNICK + ':' + lname, nets=nets, uuid=u, extra=extra, obj=fp))
    INBOM[ref] = not fp.IsExcludedFromBOM()      # e.g. the Helios module: soldered by hand, not in the BOM
# nets with a single pin in the schematic (the trackpad symbol counts: it shares the
# Molex nets through the cable) are unused pins: no net on the pad, a no-connect flag
# on the schematic pin
pins_per_net = collections.Counter(n for pt in parts for n in pt['nets'].values() if n)
for pt in parts:
    if pt['kind'] == 'J':
        for k, n in pt['nets'].items():
            if n and k not in ('13', '14'): pins_per_net[n] += 1      # the trackpad's pin n
SINGLE = {n for n, c in pins_per_net.items() if c == 1}
def pin_name(sym, num):
    for unit in find(LIBSYM[sym], 'symbol'):
        for pn in find(unit, 'pin'):
            if find(pn, 'number')[0][1] == num: return find(pn, 'name')[0][1]
    return ''
for pt in parts:                                 # KiCad's own name for a no-connect pin's net
    for p in pt['obj'].Pads():
        if p.GetNetname() in SINGLE:
            nn = 'unconnected-(%s-%s-Pad%s)' % (pt['ref'], pin_name(pt['sym'], p.GetNumber()), p.GetNumber())
            ni = b.FindNet(nn)
            if ni is None: ni = pcbnew.NETINFO_ITEM(b, nn); b.Add(ni)
            p.SetNet(ni)
    pt['nets'] = {k: ('' if n in SINGLE else n) for k, n in pt['nets'].items()}
pcbnew.SaveBoard(os.path.join(proj, name + '.kicad_pcb'), b)
print('unused pins (no net / no-connect):', ', '.join(sorted(SINGLE)))

# ---- 3. schematic ----
def sym_pins(s):
    out = []
    for unit in find(s, 'symbol'):
        for p in find(unit, 'pin'):
            at = find(p, 'at')[0]
            out.append((find(p, 'number')[0][1], float(at[1]), float(at[2]), int(float(at[3]))))
    return out
PINS = {k: sym_pins(v) for k, v in LIBSYM.items()}

items = []                                       # schematic body items
used = set()
G = 1.27
def snap(v): return round(v / G) * G
def label(net, x, y, pin_ang):
    ang = {0: 180, 180: 0, 90: 270, 270: 90}[pin_ang % 360]
    just = 'right' if ang in (180, 90) else 'left'
    items.append(['global_label', Q(net), ['shape', 'passive'], ['at', '%g' % x, '%g' % y, str(ang)], ['fields_autoplaced', 'yes'],
                  ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just]], ['uuid', Q(U())],
                  ['property', Q('Intersheetrefs'), Q('${INTERSHEET_REFS}'), ['at', '%g' % x, '%g' % y, '0'],
                   ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]]])
def no_connect(x, y):
    items.append(['no_connect', ['at', '%g' % x, '%g' % y], ['uuid', Q(U())]])
def text(t, x, y, size=2.54):
    items.append(['text', Q(t), ['exclude_from_sim', 'no'], ['at', '%g' % x, '%g' % y, '0'],
                  ['effects', ['font', ['size', '%g' % size, '%g' % size], ['bold', 'yes']], ['justify', 'left', 'bottom']], ['uuid', Q(U())]])

NETPADS = collections.Counter()
for pt in parts:
    for n in set(pt['nets'].values()):
        if n: NETPADS[n] += 1
def place(sym, x, y, ref, value, fp, nets, u=None, extra=None, on_board=True, in_bom=True, rot=0, show_value=True, ref_at=None, val_at=None):
    """Symbol at (x, y), rotated rot (0 / 90) degrees CCW; a net label on every pin
    (a no-connect flag where the pin has no net). ref_at / val_at: field offsets."""
    x, y = snap(x), snap(y); used.add(sym); s = LIBSYM[sym]; u = u or U()
    in_bom = INBOM.get(ref, in_bom)
    c, sn = (1, 0) if rot == 0 else (0, 1)
    def tr(px, py): return x + px * c - py * sn, y - (px * sn + py * c)      # symbol (y up) -> sheet (y down)
    node = ['symbol', ['lib_id', Q(LIBNICK + ':' + sym)], ['at', '%g' % x, '%g' % y, str(rot)], ['unit', '1'],
            ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'], ['on_board', 'yes' if on_board else 'no'],
            ['dnp', 'no'], ['uuid', Q(u)]]
    vals = {'Reference': ref, 'Value': value, 'Footprint': fp}
    vals.update(extra or {})
    for pr in find(s, 'property'):
        k = pr[1]
        if k.startswith('ki_'): continue
        at = find(pr, 'at')[0]; e = find(pr, 'effects'); hidden = bool(find(pr, 'hide')) or bool(e and find(e[0], 'hide'))
        px, py = tr(float(at[1]), float(at[2]))
        if k == 'Reference' and ref_at: px, py = x + ref_at[0], y + ref_at[1]
        if k == 'Value' and val_at: px, py = x + val_at[0], y + val_at[1]
        show = (k == 'Reference' or (k == 'Value' and show_value)) and not (hidden and k not in ('Reference', 'Value'))
        node.append(['property', Q(k), Q(vals.get(k, pr[2])), ['at', '%g' % px, '%g' % py, '0'],
                     ['effects', ['font', ['size', '1.27', '1.27']]]] + ([] if show else [['hide', 'yes']]))
    for k, v in (extra or {}).items():
        if k not in [p[1] for p in find(s, 'property')]:
            node.append(['property', Q(k), Q(v), ['at', '%g' % x, '%g' % y, '0'], ['effects', ['font', ['size', '1.27', '1.27']]], ['hide', 'yes']])
    for num, px, py, ang in PINS[sym]:
        node.append(['pin', Q(num), ['uuid', Q(U())]])
    node.append(['instances', ['project', Q(name), ['path', Q('/' + ROOT_UUID), ['reference', Q(ref)], ['unit', '1']]]])
    items.append(node)
    for num, px, py, ang in PINS[sym]:
        px_, py_ = tr(px, py)
        net = nets.get(num, '') if nets is not None else ''
        if net: label(net, px_, py_, ang + rot)
        elif nets is not None: no_connect(px_, py_)
def put(pt, x, y, **kw):
    place(pt['sym'], x, y, pt['ref'], pt['value'], pt['fp'], pt['nets'], pt['uuid'], pt['extra'], **kw)

ROOT_UUID = U()
by = collections.defaultdict(list)
for pt in parts: by[pt['kind']].append(pt)

# key matrix: switch + diode per key, at its matrix position (column net C*, row net R*)
diode_of = {pt['nets'].get('2'): pt for pt in by['D']}
cols = sorted({pt['nets']['1'] for pt in by['S']}, key=lambda n: int(n[1:]))
rows = sorted({diode_of[pt['nets']['2']]['nets']['1'] for pt in by['S']}, key=lambda n: int(n[1:]))
X0, Y0, DX, DY = 30.48, 45.72, 53.34, 15.24
text('Key matrix (COL2ROW): columns %s, rows %s (left half R1-R5, right half R6-R10); value = switch / keycap size' % (
     cols[0] + '-' + cols[-1], rows[0] + '-' + rows[-1]), X0 - 12.7, Y0 - 15.24)
for pt in by['S']:
    d = diode_of[pt['nets']['2']]
    ci, ri = cols.index(pt['nets']['1']), rows.index(d['nets']['1'])
    x, y = X0 + ci * DX, Y0 + ri * DY
    put(pt, x, y, show_value=False)
    put(d, x + 27.94, y, show_value=False)

# RGB chain: LEDs in chain order, decoupling caps below
X1 = X0 + len(cols) * DX + 20.32
text('RGB LEDs: SK6812MINI-E chain (GP25 -> R1 330R -> indicators -> keys)', X1 - 12.7, Y0 - 15.24)
for i, pt in enumerate(by['LED']):
    put(pt, X1 + (i % 6) * 50.8, Y0 + (i // 6) * 13.97, show_value=False)
caps = [pt for pt in by['C'] if pt['value'] == '100nF']; others = [pt for pt in by['C'] if pt['value'] != '100nF']
YC = Y0 + ((len(by['LED']) + 5) // 6) * 13.97 + 22.86
text('LED decoupling capacitors, 100 nF, one per LED (VCC - GND)', X1 - 12.7, YC - 12.7)
for i, pt in enumerate(caps):
    put(pt, X1 + (i % 12) * 25.4, YC + (i // 12) * 12.7, rot=90, show_value=False, ref_at=(0, -3.81))

# MCU, peripherals, power
YM = Y0 + len(rows) * DY + 40.64
text('MCU: 0xCB Helios (RP2040)', X0 - 12.7, YM - 33.02)
for pt in by['MCU']: put(pt, X0 + 40.64, YM + 10.16)
text('OLED 0.96in SSD1306 (I2C 0x3C)', X0 + 101.6, YM - 33.02)
for pt in by['DISP']: put(pt, X0 + 116.84, YM - 15.24)
text('Trackpad: Cirque TM040040 (I2C 0x2A, R1 removed),', X0 + 101.6, YM + 5.08)
text('12-pin 0.5 mm Type D FFC, pin n = pin n', X0 + 101.6, YM + 10.16)
for pt in by['J']: put(pt, X0 + 116.84, YM + 33.02)
jn = by['J'][0]['nets'] if by['J'] else {}   # trackpad pin n = Molex pin n
place('Cirque_TM040040', X0 + 165.1, YM + 33.02, 'TP1', 'TM040040', '', {k: v for k, v in jn.items() if k not in ('13', '14')},
      on_board=False)
text('LED data resistor, bulk capacitor', X0 + 215.9, YM - 33.02)
for i, pt in enumerate(by['R'] + others):
    put(pt, X0 + 228.6, YM - 17.78 + i * 12.7, rot=90, ref_at=(0, -3.81), val_at=(0, 3.81))
text('Power flags', X0 + 215.9, YM + 5.08)
for i, net in enumerate(('VCC', 'GND', '3V3')):
    x, y = snap(X0 + 228.6 + i * 20.32), snap(YM + 25.4)
    used.add('PWR_FLAG')
    pf = LIBSYM['PWR_FLAG']; u = U()
    node = ['symbol', ['lib_id', Q(LIBNICK + ':PWR_FLAG')], ['at', '%g' % x, '%g' % y, '0'], ['unit', '1'],
            ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['uuid', Q(u)],
            ['property', Q('Reference'), Q('#FLG0%d' % (i + 1)), ['at', '%g' % x, '%g' % (y - 5.08), '0'], ['effects', ['font', ['size', '1.27', '1.27']]], ['hide', 'yes']],
            ['property', Q('Value'), Q('PWR_FLAG'), ['at', '%g' % x, '%g' % (y - 3.81), '0'], ['effects', ['font', ['size', '1.27', '1.27']]]],
            ['property', Q('Footprint'), Q(''), ['at', '%g' % x, '%g' % y, '0'], ['effects', ['font', ['size', '1.27', '1.27']]], ['hide', 'yes']],
            ['property', Q('Datasheet'), Q(''), ['at', '%g' % x, '%g' % y, '0'], ['effects', ['font', ['size', '1.27', '1.27']]], ['hide', 'yes']]]
    node += [['pin', Q(num), ['uuid', Q(U())]] for num, *_ in PINS['PWR_FLAG']]
    node.append(['instances', ['project', Q(name), ['path', Q('/' + ROOT_UUID), ['reference', Q('#FLG0%d' % (i + 1))], ['unit', '1']]]])
    items.append(node)
    for num, px, py, ang in PINS['PWR_FLAG']: label(net, x + px, y - py, 270)

def libcopy(n):
    s = [e for e in LIBSYM[n]]; s = list(s); s[1] = Q(LIBNICK + ':' + n); return s
sch = ['kicad_sch', ['version', '20231120'], ['generator', Q('keyboard-workshop')], ['generator_version', Q('8.0')],
       ['uuid', Q(ROOT_UUID)], ['paper', Q('A1')],
       ['title_block', ['title', Q(name)], ['company', Q('keyboard-workshop')],
        ['comment', '1', Q('Generated from the Ergogen PCB by tools/lib/kicad_project.py (net labels on every pin)')]],
       ['lib_symbols'] + [libcopy(n) for n in sorted(used)]] + items + \
      [['sheet_instances', ['path', Q('/'), ['page', Q('1')]]]]
open(os.path.join(proj, SHEETFILE), 'w', encoding='utf-8', newline='\n').write(dump(sch) + '\n')
print('%s: %d symbols (%s), %d labels -> %s' % (name, sum(1 for i in items if i[0] == 'symbol'),
      ', '.join('%s x%d' % (k, len(v)) for k, v in by.items()), sum(1 for i in items if i[0] == 'global_label'), proj))
