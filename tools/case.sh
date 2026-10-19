#!/usr/bin/env bash
# Convert Ergogen's case .jscad files (out/cases, from tools/build.sh) into
# binary STL files in <keyboard>/case/ (build that design first):
#   tools/case.sh            -> kugo82/case/*.stl
#   tools/case.sh hachigo74  -> hachigo74/case/*.stl
#   (a design whose name differs from its folder goes to <keyboard>/case/<name>/)
# OpenJSCAD v1 mis-draws some arcs, so each file is fixed first:
#   - arcs with a chord < 1 mm are straightened (lib/fixarcs.js)
#   - the r12 / r11.99 corner arcs flagged "large":true are set to false
# Needs node; installs the OpenJSCAD v1 CLI into tools/jscad on first use.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
T="$P/tools"
. "$T/lib/design.sh"
JSCAD="$T/jscad/node_modules/.bin/openjscad"
[ -x "$JSCAD" ] || npm install --prefix "$T/jscad" >/dev/null

OUT="$KB/case"; [ "$NAME" = "$(basename "$KB")" ] || OUT="$KB/case/$NAME"
[ -f "$P/out/pcbs/$NAME.kicad_pcb" ] || { echo "out/ is not a build of $NAME - run tools/build.sh $NAME first"; exit 1; }
W="$P/build/case"; rm -rf "$W"; mkdir -p "$W" "$OUT"
for p in tub_left tub_right lid_left lid_right center_cover trackpad_ring oled_spacers; do
  node "$T/lib/fixarcs.js" "$P/out/cases/$p.jscad" "$W/$p.jscad"
  sed -i 's/\("radius":1[12][.0-9]*,[^}]*"large":\)true/\1false/g' "$W/$p.jscad"
done
cd "$W"
for p in tub_left tub_right lid_left lid_right center_cover trackpad_ring oled_spacers; do
  "$JSCAD" "$p.jscad" -o "$OUT/$p.stl" >/dev/null 2>&1 &
done
wait
ls -la "$OUT"/*.stl
