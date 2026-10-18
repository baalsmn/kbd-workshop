# Refresh an existing KiCad project's library copy and 3D model links without
# touching its design (placement, routing, schematic):
#   - <project>/libraries/ is replaced by a fresh copy of kicad-libraries
#     (3D paths rewritten to ${KIPRJMOD}/libraries/3dmodels/; local-only parts such
#     as the logo are left out),
#   - the board's footprints get their 3D model files renamed via MODEL_MAP,
#   - footprints listed in --remove (references) are deleted from the board.
# Usage (KiCad python, KiCad closed):
#   python tools/lib/kicad_project_libs.py kicad-libraries <project dir> <name> [--remove REF ...]
import sys, os, shutil, pcbnew

libsrc, proj, name = sys.argv[1:4]
remove = sys.argv[sys.argv.index('--remove') + 1:] if '--remove' in sys.argv else []
LOCAL_ONLY = set()   # library files that must not be copied into projects
MODEL_MAP = {   # vendor model files -> models recreated from datasheets (same frames)
    '505278-1270.stp': 'Molex_505278-1270.step',
    'Gateron_KS-33_switch.stp': 'Gateron_KS-33_switch.step',
    'Gateron_KS-57_stabilizer.stp': 'Gateron_KS-57_stabilizer.step',
    'Gateron_ks33_hotswap_socket.step': 'Gateron_KS-2P02B01-02_socket.step',
    'LED_SK6812MINI-E.step': 'SK6812MINI-E.step',
    'TM040040-2024-303.stp': 'Cirque_TM040040.step',
}

libs = os.path.join(proj, 'libraries')
def _writable(func, path, *_): os.chmod(path, 0o666); func(path)
if os.path.exists(libs): shutil.rmtree(libs, onerror=_writable)
for sub in ('Symbols', 'Footprints', '3dmodels'):
    shutil.copytree(os.path.join(libsrc, sub), os.path.join(libs, sub), ignore=lambda d, fs: [f for f in fs if f in LOCAL_ONLY])
shutil.copy2(os.path.join(libsrc, 'README.md'), os.path.join(libs, 'README.md'))
pretty = os.path.join(libs, 'Footprints', 'Keyboard.pretty')
for f in os.listdir(pretty):
    p = os.path.join(pretty, f); s = open(p, encoding='utf-8').read()
    open(p, 'w', encoding='utf-8', newline='\n').write(s.replace('${KIPRJMOD}/3dmodels/', '${KIPRJMOD}/libraries/3dmodels/'))

pcb = os.path.join(proj, name + '.kicad_pcb')
b = pcbnew.LoadBoard(pcb)
renamed, gone = 0, []
for fp in list(b.GetFootprints()):
    if fp.GetReference() in remove:
        gone.append(fp.GetReference()); b.Remove(fp); continue
    ms = fp.Models()
    for i in range(len(ms)):                      # by index: iterating gives copies
        d, base = os.path.split(ms[i].m_Filename.replace(chr(92), '/'))
        if base in MODEL_MAP: ms[i].m_Filename = d + '/' + MODEL_MAP[base]; renamed += 1
pcbnew.SaveBoard(pcb, b)
b = pcbnew.LoadBoard(pcb)                       # check the saved file
missing = sorted({m.m_Filename for fp in b.GetFootprints() for m in fp.Models()
                  if not os.path.exists(m.m_Filename.replace('${KIPRJMOD}', proj))})
print('libraries refreshed; %d model links renamed; removed %s; unresolved models: %s' % (renamed, gone or 'none', missing or 'none'))
