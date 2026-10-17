# Export the footprints of a built board into the project footprint library
# (kicad project/Footprints/Keyboard.pretty), exactly as placed on the board
# (unrotated, moved to the front side), and copy their 3D models into
# kicad project/3dmodels/ with ${KIPRJMOD}-relative paths.
#
# Usage (KiCad python, after tools/build.sh <name>):
#   python tools/lib/kicad_footprints.py out/pcbs/<name>.kicad_pcb "kicad project" [--force]
# Run it for every design: variants already in the library are kept (unless
# --force), new ones (e.g. a 1.5U switch only kugo82 has) are added.
import sys, os, re, shutil, collections, pcbnew

board_file, proj = sys.argv[1], sys.argv[2]
force = '--force' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KICAD_3D = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'share', 'kicad', '3dmodels')
LIB = os.path.abspath(os.path.join(proj, "Footprints", "Keyboard.pretty"))
MODELS = os.path.join(proj, '3dmodels')
os.makedirs(LIB, exist_ok=True); os.makedirs(MODELS, exist_ok=True)
IO = pcbnew.PCB_IO_KICAD_SEXPR()

# clean names for model files with awkward ones
RENAME = {'KS-33 Low Profile 2.0  KS33-20230109（KS-33-Y31  3D图）.stp': 'Gateron_KS-33_switch.stp',
          'low profile stabilizer..stp': 'Gateron_KS-57_stabilizer.stp'}

def name_of(fp):
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
        'claude_logo': ('Claude_Logo_8mm', '8 mm Claude logo, front silkscreen (board only)'),
    }.get(kind, (kind, kind))

def model_src(path):
    p = path.replace('${KIPRJMOD}/../../', ROOT + '/')
    p = re.sub(r'\$\{KICAD\d*_3DMODEL_DIR\}', KICAD_3D.replace('\\', '/'), p)
    return p

b = pcbnew.LoadBoard(board_file)
done, counts = {}, collections.Counter()
existing = {f[:-10] for f in os.listdir(LIB) if f.endswith('.kicad_mod')}
for fp in b.GetFootprints():
    name, descr = name_of(fp); counts[name] += 1
    if name in done: continue
    done[name] = fp.GetReference()
    if name in existing and not force: continue
    f = pcbnew.FOOTPRINT(fp)
    f.SetPosition(pcbnew.VECTOR2I(0, 0)); f.SetOrientationDegrees(0)
    if f.IsFlipped(): f.Flip(pcbnew.VECTOR2I(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(0)
    f.SetFPID(pcbnew.LIB_ID('Keyboard', name))
    f.SetLibDescription(descr)
    f.Reference().SetText('REF**'); f.Value().SetText(name)
    for p in f.Pads(): p.SetNetCode(0, True)
    if name in ('Cirque_TM040040_3D', 'Claude_Logo_8mm'):
        f.SetBoardOnly(True); f.SetExcludedFromBOM(True); f.SetExcludedFromPosFiles(True)
    for m in f.Models():
        src = model_src(m.m_Filename); base = RENAME.get(os.path.basename(src), os.path.basename(src))
        if not os.path.exists(src): print('  missing model', src); continue
        dst = os.path.join(MODELS, base)
        if not os.path.exists(dst): shutil.copy2(src, dst)
        m.m_Filename = '${KIPRJMOD}/3dmodels/' + base
    IO.FootprintSave(LIB, f)
    print('saved %-36s (from %s)' % (name, fp.GetReference()))
print('board %s: %s' % (os.path.basename(board_file), ', '.join('%s x%d' % kv for kv in counts.items())))
