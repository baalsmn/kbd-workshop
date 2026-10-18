# Shared helpers for the KiCad library / project scripts (no pcbnew import, so the
# plain-Python and KiCad-Python scripts can both use it).
import os, re

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

# clean names for model files with awkward ones
RENAME = {}   # model files are named as they should appear in the library (tools/lib/make_models.py)

def footprint_name(fp):
    """Library name and description for a board footprint (Ergogen footprint + its 3D models)."""
    kind = str(fp.GetFPID().GetLibItemName())
    models = [os.path.basename(m.m_Filename) for m in fp.Models()]
    if kind == 'ks33_hotswap':
        u = next((re.search(r'keycap_lowprofile_([\d.]+)u', m).group(1) for m in models if 'keycap_lowprofile_' in m), '1')
        stab = any('stabilizer' in m for m in models)
        return 'Gateron_KS-33_Hotswap_%sU%s' % (u, '_Stab_KS-57' if stab else ''), \
               'Gateron KS-33 low profile switch, KS-2P02B01-02 hot-swap socket (back), LED window%s, %sU keycap model' % (
                   ', KS-57 2U stabilizer cutouts' if stab else '', u)
    return {
        'sod123': ('D_SOD-123', 'SOD-123 diode'),
        'sk6812mini_e': ('LED_SK6812MINI-E_Reverse', 'SK6812MINI-E, reverse mounted through a PCB cutout (0.2 mm pad-to-cutout)'),
        'c_0603': ('C_0603', '0603 capacitor'),
        'c_0805': ('C_0805', '0805 capacitor'),
        'r_0603': ('R_0603', '0603 resistor'),
        'helios': ('0xCB_Helios', '0xCB Helios RP2040, castellated + through-hole pads, 0xCB pad numbering'),
        'molex_505278': ('Molex_505278-1270_12p', 'Molex 505278-1270 Easy-On FFC, 12 pin 0.5 mm, right angle'),
        'oled_i2c': ('OLED_0.96in_SSD1306_I2C', '0.96in SSD1306 128x64 I2C module, 4 pin header (GND VCC SCL SDA)'),
        'mech_model': ('Cirque_TM040040_3D', 'Cirque TM040040 trackpad, 3D model only (cabled, board only)'),
    }.get(kind, (kind, kind))
