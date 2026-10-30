#!/usr/bin/env bash
# One laptop deploy for the phone alerts AND the Flatten / exit claim fix (#401), from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-push.sh
#
# Deploys ONLY: kalshiLiveExit and kalshiFlattenAll (the shared closing claim), and the five phone alert functions (kalshiPushKey, kalshiPushSubscribe, kalshiPushUnsubscribe, kalshiPushOrder,
# kalshiPushSession). kalshiLiveExit reads KALSHI_LIVE_ENABLED, and functions/.env is gitignored, so a fresh clone has none: a deploy without KALSHI_LIVE_ENABLED=on would turn the exit watch's
# selling OFF. This script writes that line first and refuses to deploy without it, like deploy-sizing.sh.
# It also makes the phone alerts' one secret, the VAPID private key, ONLY if it does not exist yet (replacing it would orphan every subscribed phone). The key is generated here, written to a
# private temporary file, handed to Firebase and deleted; it is never printed and never leaves this computer except into Firebase's secret store.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=functions/.env
PROJECT=shwoopnet
ONLY=functions:kalshiLiveExit,functions:kalshiFlattenAll,functions:kalshiPushKey,functions:kalshiPushSubscribe,functions:kalshiPushUnsubscribe,functions:kalshiPushOrder,functions:kalshiPushSlotOrder,functions:kalshiPushSession

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

# Keep any lines already in the file; only make sure the order switch line is there (macOS and Linux safe: no sed -i).
touch "$ENV_FILE"
if ! grep -q '^KALSHI_LIVE_ENABLED=on$' "$ENV_FILE"; then
  grep -v '^KALSHI_LIVE_ENABLED=' "$ENV_FILE" > "$ENV_FILE.tmp" || true
  echo 'KALSHI_LIVE_ENABLED=on' >> "$ENV_FILE.tmp"
  mv "$ENV_FILE.tmp" "$ENV_FILE"
fi
grep -q '^KALSHI_LIVE_ENABLED=on$' "$ENV_FILE" || { echo "STOP: the order switch line is missing from $ENV_FILE, not deploying."; exit 1; }
echo "Order switch line is in place:"
grep '^KALSHI_LIVE_ENABLED=' "$ENV_FILE"

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

# The phone alert key: made once.
if [ "${DRY_RUN:-}" = "1" ]; then
  echo "[dry run] create KALSHI_PUSH_VAPID_PRIVATE if it does not exist"
elif "${FB[@]}" functions:secrets:access KALSHI_PUSH_VAPID_PRIVATE --project "$PROJECT" >/dev/null 2>&1; then
  echo "The phone alert key already exists, keeping it."
else
  KEYFILE="$(mktemp)"
  chmod 600 "$KEYFILE"
  node -e "process.stdout.write(require('./functions/node_modules/web-push').generateVAPIDKeys().privateKey)" > "$KEYFILE"
  "${FB[@]}" functions:secrets:set KALSHI_PUSH_VAPID_PRIVATE --data-file "$KEYFILE" --project "$PROJECT" --force
  rm -f "$KEYFILE"
  echo "The phone alert key was created and stored in Firebase."
fi

# The bot buys about 6 minutes before each 15 minute close (minutes 8 to 10 of each quarter hour). A deploy restarts the exit watch for a moment, so wait those out.
if [ "${DRY_RUN:-}" != "1" ]; then
  while m=$(( 10#$(date -u +%M) % 15 )); [ "$m" -ge 7 ] && [ "$m" -le 10 ]; do
    echo "Waiting out the buying minutes (minute $m of the quarter hour)..."
    sleep 20
  done
fi

echo "Deploying to $PROJECT: $ONLY"
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. Open the Kalshi page: it should say Running. Then Tools, Phone alerts, tap it and allow notifications."

# After a deploy: do the words on the page still match what the bot now does? (the owner, Oct 29, 2026: stale lines like "XRP is entered 10 minutes out" after XRP was paused). Never blocks; it only warns.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if command -v node >/dev/null 2>&1 && [ -f "$REPO_ROOT/test/siteFreshnessGates.test.js" ]; then
  echo
  echo "Checking that the page's words still match the bot's code..."
  node "$REPO_ROOT/test/siteFreshnessGates.test.js" || echo "WARNING: some page text is out of date with the bot. Tell Claude, it will fix the lines."
fi
