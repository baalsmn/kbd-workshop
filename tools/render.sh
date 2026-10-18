#!/usr/bin/env bash
# Render the assembled keyboard (PCB + parts + keycaps + case) with kicad-cli.
# Usage: tools/render.sh [name] [case_rgb] [keycap_rgb]   (name default kugo82)
#   defaults: dark grey case "0.13 0.13 0.14", light grey keycaps "0.58"
#   (the raytracer brightens colours a lot, so pick darker values than you'd think)
# Writes <keyboard>/renders/<name>_case_{top,iso,centre}.png. Run tools/build.sh and
# tools/case.sh first. Works on render-only copies; design files are untouched.
#
# Two workarounds live in here:
#  - KiCad's 3D settings may hide "virtual" footprints (no smd/through_hole
#    attribute, or no attr line at all: switches, case holder, trackpad). The render copy marks every such
#    footprint "smd" instead of changing the user's KiCad settings.
#  - kicad-cli renders run one at a time (parallel runs were unreliable).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
T="$P/tools"
KICAD_CLI="${KICAD_CLI:-/c/Users/balin/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe}"
JSCAD="$T/jscad/node_modules/.bin/openjscad"
. "$T/lib/design.sh"
CASE_RGB="${2:-0.13 0.13 0.14}"
CAP="${3:-0.58}"
PCB_TOP_Z=10.1   # PCB top in case coordinates (see the cases: stack-up in the design yaml)

R="$P/build/render"; rm -rf "$R"; mkdir -p "$R/wrl" "$R/caps"
m() { cygpath -m "$1" 2>/dev/null || echo "$1"; }

# case parts: fixed jscad (from tools/case.sh) -> ASCII STL -> coloured VRML
for p in tub_left tub_right lid_left lid_right center_cover trackpad_ring oled_spacers; do
  (cd "$P/build/case" && "$JSCAD" "$p.jscad" -of stla -o "$R/$p.stl" >/dev/null 2>&1
   node "$T/lib/stl2wrl.js" "$R/$p.stl" "$R/wrl/$p.wrl" $CASE_RGB >/dev/null) &
done
wait

# keycap copies in the chosen colour
for f in "$P/kicad-libraries/3dmodels/"keycap_lowprofile_*u.wrl; do
  sed -E "s/diffuseColor 0\.8[0-9]* 0\.8[0-9]* 0\.[0-9]+/diffuseColor $CAP $CAP $CAP/g" "$f" > "$R/caps/$(basename "$f")"
done

# render board: absolute model paths, keycap copies, case models, no virtual footprints
sed -e "s|\${KIPRJMOD}/../../kicad-libraries/3dmodels/keycap_lowprofile_|$(m "$R/caps")/keycap_lowprofile_|g" \
    -e "s|\${KIPRJMOD}/../../|$(m "$P")/|g" "$P/out/pcbs/$NAME.kicad_pcb" > "$R/base.kicad_pcb"
node -e '
const fs=require("fs");const [src,dst,w,z]=process.argv.slice(1);let c=fs.readFileSync(src,"utf8");
c=c.replace(/\(attr((?:\s+(?!smd|through_hole)[a-z_]+)*)\)/g,(m,rest)=>"(attr smd"+rest+")");
// footprints with no attr line at all (e.g. ks33_hotswap) count as virtual too
c=c.replace(/(\(footprint "[^"]+"\s*\(layer "[^"]+"\)\s*\(at [^)]*\))(?![\s\S]{0,60}\(attr)/g,m=>m+" (attr smd)");
const mdl=n=>`(model "${w}/${n}.wrl" (offset (xyz 0 0 -${z})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))`;
const fp=`  (footprint "case_render" (layer "F.Cu") (at 0 0) (attr smd exclude_from_pos_files exclude_from_bom)
    (property "Reference" "CASE1" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
    ${["tub_left","tub_right","lid_left","lid_right","center_cover"].map(mdl).join("\n    ")})
`;const i=c.lastIndexOf(")");fs.writeFileSync(dst,c.slice(0,i)+fp+")\n");' \
  "$R/base.kicad_pcb" "$R/render.kicad_pcb" "$(m "$R/wrl")" "$PCB_TOP_Z"

RD="$KB/renders"; mkdir -p "$RD"; cd "$R"
"$KICAD_CLI" pcb render render.kicad_pcb -o "$RD/${NAME}_case_top.png" --side top --zoom 1.05 -w 1800 -h 1000 --quality high --background opaque >/dev/null 2>&1
"$KICAD_CLI" pcb render render.kicad_pcb -o "$RD/${NAME}_case_iso.png" --rotate "-48,0,0" --zoom 1.05 -w 1800 -h 1000 --quality high --background opaque >/dev/null 2>&1
"$KICAD_CLI" pcb render render.kicad_pcb -o "$RD/${NAME}_case_centre.png" --rotate "-50,0,0" --zoom 2.8 -w 1600 -h 1000 --quality high --background opaque --pan "0,0.3,0" >/dev/null 2>&1
ls -la "$RD"/${NAME}_case_*.png
