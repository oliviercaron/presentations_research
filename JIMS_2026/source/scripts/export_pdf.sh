#!/usr/bin/env bash
# Exporte le diaporama rendu (index.html) en PDF, une page par diapo, fragments dépliés.
# Usage, depuis slides_thesis/ :  bash scripts/export_pdf.sh [nom.pdf]   (par défaut jims2026_caron.pdf)
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
PORT=8766
PROFILE="$(mktemp -d)"
NAME="${1:-jims2026_caron.pdf}"
HTML="${2:-index.html}"
OUT="$(pwd -W 2>/dev/null || pwd)/$NAME"   # chemin absolu, Chrome sous Windows ignore le cwd
PROFILE_W="$(cygpath -w "$PROFILE" 2>/dev/null || echo "$PROFILE")"

python -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null; rm -rf "$PROFILE"' EXIT
sleep 1

"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw --virtual-time-budget=90000 \
  --user-data-dir="$PROFILE_W" --print-to-pdf="$OUT" \
  "http://127.0.0.1:$PORT/$HTML?print-pdf"
# Chrome n'échoue pas quand le PDF est ouvert (donc verrouillé) : vérifier qu'il a bien été réécrit
if [ "$NAME" -nt "$HTML" ]; then echo "$NAME écrit"; else echo "ÉCHEC : $NAME n'a pas été réécrit (fichier ouvert ailleurs ?)" >&2; exit 1; fi
