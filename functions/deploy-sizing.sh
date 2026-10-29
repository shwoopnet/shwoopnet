#!/usr/bin/env bash
# Deploys ONLY kalshiLiveArmed (the function that runs the L1 tick and the sizing) and kalshiBooks (the read-only relay that feeds the market cards) to the shwoopnet project, from a fresh clone, typed on a phone in Cloud Shell:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-sizing.sh
#
# Why it exists: functions/.env is gitignored, so a fresh clone has none, and a deploy without KALSHI_LIVE_ENABLED=on turns the server's order switch OFF (no buys, and the
# exit watch only records what it would sell). This script writes that line first and refuses to deploy without it. It holds no secret and asks for none: Firebase asks you to sign in.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=functions/.env
PROJECT=shwoopnet
ONLY=functions:kalshiLiveArmed,functions:kalshiBooks

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

# Keep any lines already in the file (the optional watchdog and stop alert URLs); only make sure the order switch line is there.
touch "$ENV_FILE"
if ! grep -q '^KALSHI_LIVE_ENABLED=on$' "$ENV_FILE"; then
  sed -i '/^KALSHI_LIVE_ENABLED=/d' "$ENV_FILE"
  echo 'KALSHI_LIVE_ENABLED=on' >> "$ENV_FILE"
fi
grep -q '^KALSHI_LIVE_ENABLED=on$' "$ENV_FILE" || { echo "STOP: the order switch line is missing from $ENV_FILE, not deploying."; exit 1; }
echo "Order switch line is in place:"
grep '^KALSHI_LIVE_ENABLED=' "$ENV_FILE"
echo "(If your old .env also had KALSHI_WATCHDOG_URL or KALSHI_STOP_ALERT_URL, add those lines to $ENV_FILE now, or this deploy drops them.)"

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

# The bot buys about 6 minutes before each 15 minute close (minutes 8 to 10 of each quarter hour). A deploy restarts the function for a moment, so wait those out.
if [ "${DRY_RUN:-}" != "1" ]; then
  while m=$(( 10#$(date -u +%M) % 15 )); [ "$m" -ge 7 ] && [ "$m" -le 10 ]; do
    echo "Waiting out the buying minutes (minute $m of the quarter hour)..."
    sleep 20
  done
fi

echo "Deploying $ONLY to $PROJECT."
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. Open the Kalshi page: it should say Running. If it says 'Order switch: OFF', the .env line did not reach the deploy, so run this script again."

# After a deploy: do the words on the page still match what the bot now does? (the owner, Oct 29, 2026: stale lines like "XRP is entered 10 minutes out" after XRP was paused). Never blocks; it only warns.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if command -v node >/dev/null 2>&1 && [ -f "$REPO_ROOT/test/siteFreshnessGates.test.js" ]; then
  echo
  echo "Checking that the page's words still match the bot's code..."
  node "$REPO_ROOT/test/siteFreshnessGates.test.js" || echo "WARNING: some page text is out of date with the bot. Tell Claude, it will fix the lines."
fi
