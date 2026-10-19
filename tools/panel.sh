#!/usr/bin/env bash
# Make a JLCPCB assembly panel of a design's KiCad project board with KiKit:
# a frame (9 mm rails top and bottom per JLC's edge rail / fiducial guideline, 5 mm
# side rails), joined by mouse-bite tabs at the spots listed in <keyboard>/panel.json, with fiducials,
# tooling holes and the JLCJLCJLCJLC order number placeholder on the rails. The design board itself is not changed.
# Usage: tools/panel.sh [name]   (default kugo82; needs <keyboard>/panel.json)
#   reads  <keyboard>/kicad/<name>.kicad_pcb
#   writes <keyboard>/kicad/<name>_panel.kicad_pcb (same folder, so the
#          ${KIPRJMOD}/libraries 3D model paths keep working), then runs DRC on it
# KiKit installs on first use into %LOCALAPPDATA%/kugo-kikit: a venv on KiCad's own
# Python (--system-site-packages, for pcbnew). KiCad's install is not touched.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
. "$P/tools/lib/design.sh"
KBIN="${KICAD_BIN:-/c/Users/balin/AppData/Local/Programs/KiCad/10.0/bin}"
V="${KIKIT_DIR:-$LOCALAPPDATA/kugo-kikit}"

SRC="$KB/kicad/$NAME.kicad_pcb"; OUT="$KB/kicad/${NAME}_panel.kicad_pcb"; PRESET="$KB/panel.json"
[ -f "$SRC" ] || { echo "no $SRC (make the KiCad project first)" >&2; exit 1; }
[ -f "$PRESET" ] || { echo "no $PRESET" >&2; exit 1; }
if [ ! -x "$V/Scripts/kikit.exe" ]; then
  "$KBIN/python.exe" -m venv --system-site-packages "$V"
  "$V/Scripts/python.exe" -m pip install -q kikit
fi

cd "$P"   # the preset's plugin path (tools/lib/panel_tabs.py) is relative to the root
# KiKit needs a closed outline: snap Ergogen's sub-micron gaps in a temporary copy
# (kept in the project folder so the ${KIPRJMOD} model paths stay the same)
TMP="$KB/kicad/_${NAME}_panel_src.kicad_pcb"
"$KBIN/python.exe" "$P/tools/lib/snap_outline.py" "$SRC" "$TMP"
"$V/Scripts/kikit.exe" panelize -p "$PRESET" "$TMP" "$OUT" || { rm -f "$TMP"; exit 1; }
rm -f "$TMP" "${TMP%.kicad_pcb}.kicad_pro" "$KB/kicad/~${NAME}_panel.kicad_pro.lck"
# KiKit leaves the panel's .kicad_dru empty, and it moves footprint Edge.Cuts (the LED
# light cutouts, stabilizer cutouts) into the board outline, so the design's
# memberOfFootprint('LED*') rule no longer matches. Same 0.2 mm limit, matched by
# the LED courtyard instead.
cat > "${OUT%.kicad_pcb}.kicad_dru" <<'EOF'
(version 1)
# Panel copy of the design rule: 0.2 mm (JLCPCB routed-edge minimum) between the
# SK6812MINI-E pads and their light cutout. KiKit moves footprint cutouts into the
# board outline, so the cutout is matched as an Edge.Cuts item inside the LED courtyard.
(rule "LED cutout clearance (panel)"
  (constraint edge_clearance (min 0.2mm))
  (condition "A.memberOfFootprint('LED*') && B.Layer == 'Edge.Cuts' && B.intersectsCourtyard('LED*')"))
EOF
# plus the design's track width rules (they match net names by their end, so the
# panel's "Board_0-<name>" nets are covered)
sed -n '/^# Track widths/,$p' "$KB/kicad/$NAME.kicad_dru" | sed '1s/^/\n/' >> "${OUT%.kicad_pcb}.kicad_dru"
"$KBIN/kicad-cli.exe" pcb drc "$OUT" -o "$P/out/panel_drc.rpt" >/dev/null || true
grep -E "^\*\* Found" "$P/out/panel_drc.rpt"
echo "wrote ${OUT#$P/}"
