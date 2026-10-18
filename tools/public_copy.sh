#!/usr/bin/env bash
# Build a clean public copy of this (private) repository's history in
# ../keyboard-workshop-public: a fresh clone rewritten with git filter-repo so
# that no commit contains material that cannot be published:
#   - vendor datasheets (datasheets/*.pdf, drafts/*.pdf),
#   - vendor 3D models and vendor footprints of unknown licence (every location
#     they ever had), sea-picro,
#   - logo artwork (Claude / Claude Code logos and their footprint files).
# Files whose earlier versions held logo artwork (the KiCad board, the 1:1
# printout) lose their history and come back as their current, clean versions in
# a final commit. The copy has no remote; push it only on purpose.
# Needs git-filter-repo (pip install git-filter-repo, or GFR_DIR=<pip --target dir>).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$(dirname "$P")/keyboard-workshop-public}"
[ -e "$OUT" ] && { echo "$OUT exists - remove it first"; exit 1; }
[ -z "$(git -C "$P" status --porcelain)" ] || { echo "commit your changes first"; exit 1; }
git clone -q --no-local "$P" "$OUT"
cd "$OUT"
w() { cygpath -w "$1" 2>/dev/null || echo "$1"; }
GFR=(python -m git_filter_repo); [ -n "${GFR_DIR:-}" ] && export PYTHONPATH="$(w "$GFR_DIR")"
RESTORE=(hachigo74/kicad/hachigo74.kicad_pcb hachigo74/hachigo74_layout_1to1.pdf)
args=(--force --invert-paths
  --path-glob 'datasheets/*.pdf' --path-glob 'drafts/*.pdf' --path-glob 'drafts/claude*'
  --path footprints/claude_logo.js --path-glob '*Claude_Logo_8mm.kicad_mod' --path-glob 'footprints/local/*' --path-glob 'ergogen/footprints/local/*'
  --path-glob '*505278-1270.stp' --path-glob '*Gateron_KS-52B200T*' --path-glob '*Gateron_ks33_hotswap_socket.step'
  --path-glob '*Gateron_ks33_low_profile_swictch.step' --path-glob '*KS-33 Low Profile 2.0*' --path-glob '*LED_SK6812MINI-E.step'
  --path-glob '*TM040040-2024-303.stp' --path-glob '*low profile stabilizer..stp' --path-glob '*sea-picro.step'
  --path-glob '*Gateron_KS-33_switch.stp' --path-glob '*Gateron_KS-57_stabilizer.stp'
  --path-glob 'keyboard.pretty/Gateron-KS33-Hotswap-*' --path 'keyboard.pretty/MX_SK6812MINI-E.kicad_mod'
  --path 'keyboard.pretty/OLED Display_128x64_096_I2C.kicad_mod' --path 'keyboard.pretty/molex_5052781270_12p.kicad_mod')
for f in "${RESTORE[@]}"; do args+=(--path "$f"); done
"${GFR[@]}" "${args[@]}" >/dev/null
for f in "${RESTORE[@]}"; do mkdir -p "$(dirname "$f")"; cp "$P/$f" "$f"; done
python - <<'PY'
p = 'datasheets/LINKS.md'; s = open(p, encoding='utf-8').read()
i = s.find('The PDFs in this folder'); j = s.find('| Part |')
if i >= 0 and j > i:
    s = s[:i] + ("The manufacturers' datasheets are not included in this repository (they are not\n"
                 "covered by its licences). Download them from the sources below; the file names\n"
                 "are the ones the project used.\n\n") + s[j:]
    open(p, 'w', encoding='utf-8').write(s)
PY
git add -A
git commit -q -m "Restore the current KiCad board and 1:1 printout

Their earlier versions are left out of this public history (they contained logo
artwork); these are the clean current versions. Datasheet PDFs are not included:
datasheets/LINKS.md lists where to get them."
echo "public copy: $OUT ($(git rev-list --count HEAD) commits, $(git count-objects -vH | sed -n 's/size-pack: //p'), remotes: $(git remote | wc -l))"
