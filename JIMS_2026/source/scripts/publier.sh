#!/usr/bin/env bash
# Compile le diaporama, exporte le PDF et le publie au même endroit dans presentations_research
# (GitHub Pages) : https://oliviercaron.github.io/presentations_research/JIMS_2026/jims2026_caron_benavent.pdf
# Usage, depuis slides_jims2026/ :  bash scripts/publier.sh ["message de commit"]
# Ne committe que JIMS_2026/ et README.md : les autres modifications du dépôt ne sont pas touchées.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="C:/Users/Olivier/Documents/GitHub/presentations_research"
NOM="jims2026_caron_benavent.pdf"
quarto render index.qmd
bash scripts/export_pdf.sh "$NOM"
mkdir -p "$REPO/JIMS_2026"
cp "$NOM" "$REPO/JIMS_2026/$NOM"
# sources pour modifier ailleurs : qmd, styles, images utilisées, scripts des figures
SRC="$REPO/JIMS_2026/source"
rm -rf "$SRC"; mkdir -p "$SRC/assets/fig" "$SRC/scripts"
cp index.qmd _quarto.yml "$SRC/"
cp assets/*.scss assets/navbar.html "$SRC/assets/"; cp -r assets/img "$SRC/assets/"
for f in $(grep -o 'assets/fig/[A-Za-z0-9_.-]*' index.qmd | sort -u); do cp "$f" "$SRC/$f"; done
cp -r scripts/figures_diapo scripts/export_pdf.sh scripts/publier.sh "$SRC/scripts/"
rm -f "$SRC/scripts/figures_diapo/carte_sens_pfizer_candidats.csv"   # comptes non retenus : pas en public
cd "$REPO"
git add -A JIMS_2026 README.md
if git diff --cached --quiet -- JIMS_2026 README.md; then
  echo "rien de nouveau à publier"
else
  git commit -m "${1:-JIMS 2026 : mise à jour du diaporama}" -- JIMS_2026 README.md
  git push origin main
fi
echo "publié : https://oliviercaron.github.io/presentations_research/JIMS_2026/$NOM"
