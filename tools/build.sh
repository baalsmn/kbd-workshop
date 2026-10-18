#!/usr/bin/env bash
# Build a keyboard design with Ergogen and run KiCad DRC.
# Usage: tools/build.sh [name]   (default kugo82; also kugo80, hachigo74)
#   reads <keyboard>/<name>.yaml (kugo/kugo82.yaml, hachigo74/hachigo74.yaml, ...)
#   build/            Ergogen input (config.yaml = <name>.yaml, footprints/)
#   out/pcbs/         <name>.kicad_pcb (+ <name>.kicad_dru) -> open in KiCad
#   out/cases/        *.jscad (turn into STL with tools/case.sh)
#   out/outlines/     2D outlines (dxf/svg)
# Model paths in the board are ${KIPRJMOD}/../../3dmodels, i.e. relative to
# the project root, which is why the output goes to <project>/out.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
. "$P/tools/lib/design.sh"
KICAD_CLI="${KICAD_CLI:-/c/Users/balin/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe}"

rm -rf "$P/build" "$P/out"
mkdir -p "$P/build/footprints"
cp "$YAML" "$P/build/config.yaml"
cp "$P"/footprints/*.js "$P/build/footprints/"
# local footprints (gitignored, e.g. the logo artwork) replace the placeholders
[ -d "$P/footprints/local" ] && cp "$P"/footprints/local/*.js "$P/build/footprints/" 2>/dev/null || true

cd "$P"
ergogen build -o out --debug
cp "$P/keyboard.kicad_dru" "$P/out/pcbs/$NAME.kicad_dru"   # same rules for every design

"$KICAD_CLI" pcb drc out/pcbs/$NAME.kicad_pcb -o out/drc.rpt >/dev/null
grep -E "^\*\* Found" out/drc.rpt
# list anything that is not just an unrouted connection
awk '/^\[/{show = ($0 !~ /^\[unconnected_items\]/)} /^\*\*/{show = 0} show' out/drc.rpt | head -40
