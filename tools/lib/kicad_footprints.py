# Export the footprints of a built board into the project footprint library
# (kicad-libraries/Footprints/Keyboard.pretty), exactly as placed on the board
# (unrotated, moved to the front side), and copy their 3D models into
# kicad-libraries/3dmodels/ with ${KIPRJMOD}-relative paths.
#
# Usage (KiCad python, after tools/build.sh <name>):
#   python tools/lib/kicad_footprints.py out/pcbs/<name>.kicad_pcb kicad-libraries [--force]
# Run it for every design: variants already in the library are kept (unless
# --force), new ones (e.g. a 1.5U switch only kugo82 has) are added.
import sys, os, re, shutil, collections, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_common import RENAME, footprint_name as name_of

board_file, proj = sys.argv[1], sys.argv[2]
force = '--force' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KICAD_3D = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'share', 'kicad', '3dmodels')
LIB = os.path.abspath(os.path.join(proj, "Footprints", "Keyboard.pretty"))
MODELS = os.path.join(proj, '3dmodels')
os.makedirs(LIB, exist_ok=True); os.makedirs(MODELS, exist_ok=True)
IO = pcbnew.PCB_IO_KICAD_SEXPR()

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
    if name in ('Cirque_TM040040_3D',):
        f.SetBoardOnly(True); f.SetExcludedFromBOM(True); f.SetExcludedFromPosFiles(True)
    ms = f.Models()
    for i in range(len(ms)):                     # by index: iterating gives copies (edits would be lost)
        m = ms[i]
        src = model_src(m.m_Filename); base = RENAME.get(os.path.basename(src), os.path.basename(src))
        if not os.path.exists(src): print('  missing model', src); continue
        dst = os.path.join(MODELS, base)
        if not os.path.exists(dst) and os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst); os.chmod(dst, 0o666)   # KiCad's own models (read-only in its install)
        m.m_Filename = '${KIPRJMOD}/3dmodels/' + base
    IO.FootprintSave(LIB, f)
    print('saved %-36s (from %s)' % (name, fp.GetReference()))
print('board %s: %s' % (os.path.basename(board_file), ', '.join('%s x%d' % kv for kv in counts.items())))
