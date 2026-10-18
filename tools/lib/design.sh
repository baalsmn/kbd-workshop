# Sourced by the tools: resolves a design name to its keyboard folder.
#   NAME  design name (default kugo82), e.g. kugo80, hachigo74
#   YAML  <keyboard>/<NAME>.yaml      KB  the keyboard folder (kugo/, hachigo74/)
# Shared files (tools/, footprints/, kicad libraries/, keyboard.kicad_dru) stay in the
# root; build/ and out/ are root-level scratch folders holding the last build
# (the boards' model paths are ${KIPRJMOD}/../../kicad libraries/3dmodels, i.e. out/pcbs -> root).
NAME="${1:-kugo82}"
YAML="$(ls "$P"/*/"$NAME".yaml 2>/dev/null | head -1 || true)"
[ -n "$YAML" ] || { echo "no <keyboard>/$NAME.yaml found under $P" >&2; exit 1; }
KB="$(dirname "$YAML")"
