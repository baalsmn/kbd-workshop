#!/usr/bin/env bash
# Export the case parts as STEP (editable solids for Autodesk Fusion) next to
# the STLs, <keyboard>/case/step/*.step, plus the data file for the Fusion script
# (tools/fusion/KeyboardCase): <keyboard>/case/fusion/<name>_case.json.
#   tools/step.sh                  -> kugo82   (build it first: tools/build.sh)
#   tools/step.sh hachigo74        -> hachigo74 (tools/build.sh hachigo74 first)
# Uses build123d (OpenCascade); installed on first use into
# $LOCALAPPDATA/kugo-build123d (about 700 MB, kept out of OneDrive), or set
# B3D_DIR to an existing install.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
. "$P/tools/lib/design.sh"
C="$KB/case"; [ "$NAME" = "$(basename "$KB")" ] || C="$KB/case/$NAME"
OUT="$C/step"
B3D="${B3D_DIR:-$(cygpath -u "${LOCALAPPDATA:-$HOME/AppData/Local}" 2>/dev/null || echo "$HOME/AppData/Local")/kugo-build123d}"
if [ ! -d "$B3D/build123d" ]; then
  echo "installing build123d into $B3D ..."
  python -m pip install --target "$(cygpath -w "$B3D" 2>/dev/null || echo "$B3D")" build123d >/dev/null
fi
[ -f "$P/out/pcbs/$NAME.kicad_pcb" ] || { echo "out/ is not a build of $NAME - run tools/build.sh $NAME first"; exit 1; }

# the yaml's cases section as JSON (js-yaml from the global ergogen install)
JSY="$(npm root -g)/ergogen/node_modules/js-yaml"
node -e '
const yaml=require(process.argv[1]);const fs=require("fs");
const d=yaml.load(fs.readFileSync(process.argv[2],"utf8"));fs.writeFileSync(process.argv[3],JSON.stringify(d.cases||{},null,1));' \
  "$JSY" "$YAML" "$P/build/cases.json"

mkdir -p "$OUT"
w() { cygpath -w "$1" 2>/dev/null || echo "$1"; }
PYTHONPATH="$(w "$B3D")" python -I -c "import sys; sys.path.insert(0, r'$(w "$B3D")'); sys.argv = ['step_case.py'] + sys.argv[1:]; exec(open(r'$(w "$P/tools/lib/step_case.py")').read())" \
  "$(w "$P/build/cases.json")" "$(w "$P/out/outlines")" "$(w "$OUT")" tub_left tub_right lid_left lid_right center_cover trackpad_ring oled_spacers center_bridge cover_clip

# data file for the Fusion script tools/fusion/KeyboardCase (parametric timeline rebuild)
FOUT="$C/fusion"; mkdir -p "$FOUT"
PYTHONPATH="$(w "$B3D")" python -I -c "import sys; sys.path[:0] = [r'$(w "$B3D")', r'$(w "$P/tools/lib")']; sys.argv = ['fusion_data.py'] + sys.argv[1:]; exec(open(r'$(w "$P/tools/lib/fusion_data.py")').read())" \
  "$(w "$P/build/cases.json")" "$(w "$P/out/outlines")" "$(w "$FOUT/${NAME}_case.json")" "$NAME" tub_left tub_right lid_left lid_right center_cover trackpad_ring oled_spacers center_bridge cover_clip

# tilt wedge under the tub (south edge raised): STEP + STL at WEDGE_ANGLE (default 6 deg),
# and the parametric wedge parts in the Fusion data file (user parameter tilt_angle)
PYTHONPATH="$(w "$B3D")" python -I -c "import sys; sys.path[:0] = [r'$(w "$B3D")', r'$(w "$P/tools/lib")']; sys.argv = ['wedge_case.py'] + sys.argv[1:]; exec(open(r'$(w "$P/tools/lib/wedge_case.py")').read())"   "$(w "$P/out/outlines")" "$(w "$OUT")" --angle "${WEDGE_ANGLE:-6}" --stl-dir "$(w "$C")" --json "$(w "$FOUT/${NAME}_case.json")"
