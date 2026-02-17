#!/usr/bin/env bash
set -euo pipefail

CHROME="/mnt/c/Users/Olivier/Documents/GitHub/python_experiments/browser_use/.pw-browsers/chromium-1200/chrome-linux64/chrome"
PY="/mnt/c/Users/Olivier/Documents/GitHub/python_experiments/browser_use/.venv_wsl/bin/python"
SCRIPT="/mnt/c/Users/Olivier/Documents/GitHub/python_experiments/browser_use/scripts/amazon_best_seller_demo.py"

LOG="/tmp/chrome-linux.log"
PORT=9224

"$CHROME" --headless --no-sandbox --disable-dev-shm-usage --disable-gpu \
  --remote-debugging-port="$PORT" about:blank >"$LOG" 2>&1 &
PID=$!

sleep 2
export BROWSER_USE_CDP_URL="http://127.0.0.1:$PORT"

"$PY" "$SCRIPT"
STATUS=$?

kill "$PID" >/dev/null 2>&1 || true
exit "$STATUS"
