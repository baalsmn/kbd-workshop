# Sourced by the tools: resolves a design name to its yaml and keyboard folder.
#   NAME  design name (default kugo82), e.g. hachigo74
#   YAML  ergogen/<NAME>.yaml (all Ergogen inputs live in ergogen/, with ergogen/footprints/)
#   KB    the keyboard folder for its outputs (kugo82/, hachigo74/), from the yaml's first-line
#         tag "# keyboard: <folder>" (default: a folder named <NAME>)
# Shared files (tools/, ergogen/, kicad-libraries/, keyboard.kicad_dru) stay in the
# root; build/ and out/ are root-level scratch folders holding the last build
# (the boards' model paths are ${KIPRJMOD}/../../kicad-libraries/3dmodels, i.e. out/pcbs -> root).
NAME="${1:-kugo82}"
YAML="$P/ergogen/$NAME.yaml"
[ -f "$YAML" ] || { echo "no ergogen/$NAME.yaml under $P" >&2; exit 1; }
KBN="$(head -1 "$YAML" | awk '$1 == "#" && $2 == "keyboard:" {print $3}')"
KB="$P/${KBN:-$NAME}"
[ -d "$KB" ] || { echo "keyboard folder $KB (for $NAME) not found" >&2; exit 1; }
