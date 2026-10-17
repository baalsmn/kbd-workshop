# Build the project symbol library (kicad project/Symbols/Keyboard.kicad_sym) from
# KiCad's built-in symbols, with this keyboard's pin names, reference prefixes
# and footprints (Keyboard:... in kicad project/Footprints/Keyboard.pretty), and
# fix the Helios symbol (Symbols/helios.kicad_sym) to the footprint's pad numbers.
# Also writes the project library tables (sym-lib-table, fp-lib-table).
#
# Usage: python tools/lib/kicad_symbols.py "kicad project" [kicad share/symbols dir]
import sys, os, re, copy

proj = sys.argv[1]
SYMDIR = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\balin\AppData\Local\Programs\KiCad\10.0\share\kicad\symbols'

# ---- minimal S-expression reader / writer (strings kept as Q) ----
class Q(str): pass
def parse(text):
    tok = re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack = [[]]
    for m in tok:
        t = m.group(0)
        if t == '(': stack.append([])
        elif t == ')': x = stack.pop(); stack[-1].append(x)
        elif t[0] == '"': stack[-1].append(Q(t[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else: stack[-1].append(t)
    return stack[0][0]
def dump(x, ind=0):
    if isinstance(x, list):
        simple = all(not isinstance(e, list) for e in x)
        if simple: return '(' + ' '.join(dump(e) for e in x) + ')'
        head = [dump(e) for e in x if not isinstance(e, list)]
        body = ['\n' + '\t' * (ind + 1) + dump(e, ind + 1) for e in x if isinstance(e, list)]
        return '(' + ' '.join(head) + ''.join(body) + '\n' + '\t' * ind + ')'
    if isinstance(x, Q): return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return str(x)
def find(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]

LIBS = {}
def builtin(lib, name):
    if lib not in LIBS: LIBS[lib] = parse(open(os.path.join(SYMDIR, lib + '.kicad_sym'), encoding='utf-8').read())
    sym = next(s for s in find(LIBS[lib], 'symbol') if s[1] == name)
    sym = copy.deepcopy(sym)
    ext = find(sym, 'extends')
    if ext:                                   # flatten a derived symbol onto its base
        base = builtin(lib, ext[0][1]); sym.remove(ext[0])
        props = {p[1] for p in find(sym, 'property')}
        for e in base[2:]:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props: continue
            if isinstance(e, list) and e[0] == 'symbol': continue
            if isinstance(e, list) and e[0] not in [x[0] for x in sym if isinstance(x, list)]: sym.insert(2, e)
        sym += [rename_unit(u, ext[0][1], name) for u in find(base, 'symbol')]
    return sym
def rename_unit(u, old, new):
    u = copy.deepcopy(u); u[1] = Q(new + u[1][len(old):]); return u
def rename(sym, new):
    old = sym[1]; sym[1] = Q(new)
    for i, u in enumerate(sym):
        if isinstance(u, list) and u and u[0] == 'symbol': sym[i] = rename_unit(u, old, new)
    return sym
def prop(sym, key, value, hide=None):
    for p in find(sym, 'property'):
        if p[1] == key:
            p[2] = Q(value)
            if hide is not None:
                for h in find(p, 'hide'): p.remove(h)
                eff = find(p, 'effects')
                for h in (find(eff[0], 'hide') if eff else []): eff[0].remove(h)
                if hide: p.append(['hide', 'yes'])
            return sym
    sym.append(['property', Q(key), Q(value), ['at', '0', '0', '0'], ['hide', 'yes'],
                ['effects', ['font', ['size', '1.27', '1.27']]]])
    return sym
def flag(sym, key, value):
    for f in find(sym, key): f[1] = value
    return sym
def pins(sym):
    return [p for u in find(sym, 'symbol') for p in find(u, 'pin')]
def pin_names(sym, names, offset='2.032'):
    for p in pins(sym):
        num = find(p, 'number')[0][1]
        if num in names: find(p, 'name')[0][1] = Q(names[num])
    for pn in find(sym, 'pin_names'): sym[sym.index(pn)] = ['pin_names', ['offset', offset]]
    return sym
def add_pin(sym, like, number, name, dy):
    p = copy.deepcopy(next(p for p in pins(sym) if find(p, 'number')[0][1] == like))
    at = find(p, 'at')[0]; at[2] = '%g' % (float(at[2]) + dy)
    find(p, 'number')[0][1] = Q(number); find(p, 'name')[0][1] = Q(name)
    unit = next(u for u in find(sym, 'symbol') if find(u, 'pin')); unit.append(p)
    return sym
def move_prop(sym, key, y):
    for p in find(sym, 'property'):
        if p[1] == key: find(p, 'at')[0][2] = '%g' % y

FP = 'Keyboard:'
TP_PINS = {'1': 'SCK', '2': 'SO', '3': 'SS', '4': 'DR', '5': 'SI', '6': 'B2', '7': 'B3', '8': 'B1',
           '9': 'SCL', '10': 'SDA', '11': 'GND', '12': 'VDD'}
out = []

s = rename(builtin('Switch', 'SW_Push_45deg'), 'SW_Push_45deg')
prop(s, 'Reference', 'S'); prop(s, 'Footprint', FP + 'Gateron_KS-33_Hotswap_1U')
prop(s, 'Description', 'Key switch (Gateron KS-33 on hot-swap socket); footprints Gateron_KS-33_Hotswap_1U / 1.25U / 2U_Stab_KS-57')
prop(s, 'ki_fp_filters', 'Gateron_KS-33_Hotswap*'); out.append(s)

s = builtin('Device', 'D'); prop(s, 'Reference', 'D'); prop(s, 'Value', '1N4148W')
prop(s, 'Footprint', FP + 'D_SOD-123'); prop(s, 'ki_fp_filters', 'D_SOD-123*'); out.append(s)
s = builtin('Device', 'C'); prop(s, 'Value', '100nF'); prop(s, 'Footprint', FP + 'C_0603'); prop(s, 'ki_fp_filters', 'C_0603* C_0805*'); out.append(s)
s = builtin('Device', 'R'); prop(s, 'Value', '330'); prop(s, 'Footprint', FP + 'R_0603'); prop(s, 'ki_fp_filters', 'R_0603*'); out.append(s)

def box_symbol(name, ref, value, fp, descr, left, right, half_w=6.35, extra=()):
    """Plain box symbol: left / right = [(number, name, type)] from the top, 2.54 pitch."""
    n = max(len(left), len(right)); top = (n - 1) * 1.27; half_h = top + 2.54
    def fl(v): return '%g' % v
    def pin(num, nm, typ, x, y, ang):
        return ['pin', typ, 'line', ['at', fl(x), fl(y), str(ang)], ['length', '2.54'],
                ['name', Q(nm), ['effects', ['font', ['size', '1.27', '1.27']]]],
                ['number', Q(num), ['effects', ['font', ['size', '1.27', '1.27']]]]]
    def prop_(k, v, y, hide=False):
        e = ['property', Q(k), Q(v), ['at', '0', fl(y), '0'], ['effects', ['font', ['size', '1.27', '1.27']]]]
        if hide: e.append(['hide', 'yes'])
        return e
    sym = ['symbol', Q(name), ['pin_names', ['offset', '1.016']], ['exclude_from_sim', 'no'],
           ['in_bom', 'yes'], ['on_board', 'yes'],
           prop_('Reference', ref, half_h + 1.27), prop_('Value', value, -half_h - 1.27),
           prop_('Footprint', fp, 0, True), prop_('Datasheet', '', 0, True), prop_('Description', descr, 0, True)]
    sym += [prop_(k, v, 0, True) for k, v in extra]
    sym.append(['symbol', Q(name + '_0_1'),
                ['rectangle', ['start', fl(-half_w), fl(half_h)], ['end', fl(half_w), fl(-half_h)],
                 ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['type', 'background']]]])
    pins_ = [pin(num, nm, t, -half_w - 2.54, top - 2.54 * k, 0) for k, (num, nm, t) in enumerate(left)]
    pins_ += [pin(num, nm, t, half_w + 2.54, top - 2.54 * k, 180) for k, (num, nm, t) in enumerate(right)]
    sym.append(['symbol', Q(name + '_1_1')] + pins_)
    return sym

# SK6812MINI-E as drawn on JLCPCB's part page (C5149201): GND / DIN left, DOUT / VDD
# right; pin numbers = the OPSCO datasheet = our footprint (1 GND 2 DIN 3 VDD 4 DOUT)
s = box_symbol('SK6812MINI-E', 'LED', 'SK6812MINI-E', FP + 'LED_SK6812MINI-E_Reverse',
               'OPSCO SK6812MINI-E-012 addressable RGB LED, reverse mount (LCSC C5149201)',
               [('1', 'GND', 'power_in'), ('2', 'DIN', 'input')], [('4', 'DOUT', 'output'), ('3', 'VDD', 'power_in')],
               extra=[('LCSC', 'C5149201'), ('ki_fp_filters', 'LED_SK6812MINI-E*')])
prop(s, 'Datasheet', 'https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK6812MINIE/C5149201')
out.append(s)

s = rename(builtin('Connector', 'Conn_01x12_Socket'), 'Molex_505278-1270')
pin_names(s, TP_PINS); add_pin(s, '12', '13', 'MP', -2.54); add_pin(s, '12', '14', 'MP', -5.08)
for p in pins(s):
    if find(p, 'number')[0][1] in ('13', '14'): p[1] = 'passive'
move_prop(s, 'Value', -22.86)
prop(s, 'Reference', 'J'); prop(s, 'Value', 'Molex_505278-1270'); prop(s, 'Footprint', FP + 'Molex_505278-1270_12p')
prop(s, 'Description', 'Molex 505278-1270 FFC connector, 12 pin 0.5 mm, to the Cirque TM040040 (pin n = trackpad pin n; Type D cable). MP = mounting tabs (GND)')
prop(s, 'ki_fp_filters', 'Molex_505278*'); prop(s, 'LCSC', 'C47149418')   # JLCPCB part (Extended)
out.append(s)

s = rename(builtin('Connector', 'Conn_01x12_Pin'), 'Cirque_TM040040')
pin_names(s, TP_PINS); prop(s, 'Reference', 'TP'); prop(s, 'Value', 'TM040040'); prop(s, 'Footprint', '')
prop(s, 'Description', 'Cirque GlidePoint TM040040 trackpad (I2C mode: R1 removed). Cabled module, not on the board: 3D model footprint Keyboard:Cirque_TM040040_3D is board only')
prop(s, 'ki_fp_filters', ''); flag(s, 'on_board', 'no'); out.append(s)

s = rename(builtin('Connector', 'Conn_01x04_Socket'), 'OLED_SSD1306_128x64_I2C')
pin_names(s, {'1': 'GND', '2': 'VCC', '3': 'SCL', '4': 'SDA'})
prop(s, 'Reference', 'DISP'); prop(s, 'Value', 'SSD1306 0.96in'); prop(s, 'Footprint', FP + 'OLED_0.96in_SSD1306_I2C')
prop(s, 'Description', '0.96in SSD1306 128x64 OLED module, I2C address 0x3C, VCC = 3V3'); prop(s, 'ki_fp_filters', 'OLED*'); out.append(s)

for n in ('GND', 'VCC', '+3V3', '+5V'):
    out.append(builtin('power', n))

lib = ['kicad_symbol_lib', ['version', '20251024'], ['generator', Q('keyboard-workshop')], ['generator_version', Q('10.0')]] + out
os.makedirs(os.path.join(proj, 'Symbols'), exist_ok=True)
open(os.path.join(proj, 'Symbols', 'Keyboard.kicad_sym'), 'w', encoding='utf-8', newline='\n').write(dump(lib) + '\n')

# ---- Helios: renumber the pins to the footprint's (0xCB) pad numbers ----
HELIOS_PADS = {'GP0': '1', 'GP1': '2', 'GP2': '5', 'GP3': '6', 'GP4': '7', 'GP5': '8', 'GP6': '9', 'GP7': '10',
               'GP8': '11', 'GP9': '12', '5V': '13', 'RST': '15', '3V3': '16', 'GP29': '17', 'GP28': '18',
               'GP27': '19', 'GP26': '20', 'GP22': '21', 'GP20': '22', 'GP23': '23', 'GP21': '24', 'GP12': '25',
               'GP13': '26', 'GP14': '27', 'GP15': '28', 'GP16': '29', 'GP11': '30', 'GP10': '31',
               'D+': '32', 'D-': '33', 'GP25': '34'}
hp = os.path.join(proj, 'Symbols', 'helios.kicad_sym')
h = parse(open(hp, encoding='utf-8').read()); hs = find(h, 'symbol')[0]
gl = [p for p in pins(hs) if find(p, 'name')[0][1] == 'GND' and float(find(p, 'at')[0][1]) < 0]
gl.sort(key=lambda p: -float(find(p, 'at')[0][2]))           # left edge, top first: pads 3, 4
for p in pins(hs):
    nm = find(p, 'name')[0][1]
    find(p, 'number')[0][1] = Q(('3', '4')[gl.index(p)] if p in gl else '14' if nm == 'GND' else HELIOS_PADS[nm])
move_prop(hs, 'Reference', 24.13); move_prop(hs, 'Value', -31.75)
for k in ('Reference', 'Value'):
    for pr in find(hs, 'property'):
        if pr[1] == k:
            find(pr, 'at')[0][1] = '0'
            for e in find(pr, 'effects'):
                for j in find(e, 'justify'): e.remove(j)
prop(hs, 'Reference', 'MCU'); prop(hs, 'Value', '0xCB Helios'); prop(hs, 'Footprint', FP + '0xCB_Helios')
prop(hs, 'Description', '0xCB Helios RP2040; pin numbers = footprint pads (0xCB numbering). GP25 = 5 V level-shifted RGB output')
open(hp, 'w', encoding='utf-8', newline='\n').write(dump(h) + '\n')

# ---- project library tables ----
open(os.path.join(proj, 'sym-lib-table'), 'w', newline='\n').write(
    '(sym_lib_table\n  (version 7)\n'
    '  (lib (name "Keyboard")(type "KiCad")(uri "${KIPRJMOD}/Symbols/Keyboard.kicad_sym")(options "")(descr "keyboard-workshop symbols"))\n'
    '  (lib (name "Helios")(type "KiCad")(uri "${KIPRJMOD}/Symbols/helios.kicad_sym")(options "")(descr "0xCB Helios"))\n)\n')
open(os.path.join(proj, 'fp-lib-table'), 'w', newline='\n').write(
    '(fp_lib_table\n  (version 7)\n'
    '  (lib (name "Keyboard")(type "KiCad")(uri "${KIPRJMOD}/Footprints/Keyboard.pretty")(options "")(descr "keyboard-workshop footprints"))\n)\n')
print('symbols:', ', '.join(s[1] for s in out), '+ Helios (renumbered)')
