#!/usr/bin/env bash
# Deploys ONLY the fast research read endpoint (kalshiFastRead), from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-fastread.sh
#
# The function sends only GET requests for public market data through the account's own key (the two secrets the bot already holds), refuses to run in the bot's buying and exit-watch minutes,
# and stores nothing. It is protected by ONE secret token, KALSHI_FASTREAD_TOKEN, separate from the nightly report's. The first run makes a random token, stores it in Secret Manager and prints it
# ONCE here, in your own terminal, so you can put it in the Claude environment's secrets (never in a chat). A later run keeps the existing token.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=shwoopnet
ONLY=functions:kalshiFastRead

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

if [ "${DRY_RUN:-}" = "1" ]; then
  echo "[dry run] create KALSHI_FASTREAD_TOKEN if it does not exist"
elif "${FB[@]}" functions:secrets:get KALSHI_FASTREAD_TOKEN --project "$PROJECT" >/dev/null 2>&1; then
  echo "KALSHI_FASTREAD_TOKEN already exists: keeping it."
else
  TOKEN="$(openssl rand -hex 32)"
  printf '%s' "$TOKEN" | "${FB[@]}" functions:secrets:set KALSHI_FASTREAD_TOKEN --data-file - --project "$PROJECT"
  echo
  echo "NEW FAST READ TOKEN (shown once; copy it into the Claude environment's secrets, not into a chat):"
  echo "$TOKEN"
  echo
fi

echo "Deploying to $PROJECT: $ONLY"
# Deploy stamp, as the other deploy scripts: which commit this deploy comes from. Never read by any order code.
if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] write functions/deploy-stamp.json"; else printf '{"commit":"%s","at":"%s"}\n' "$(git rev-parse HEAD 2>/dev/null || echo unknown)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > functions/deploy-stamp.json; fi
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. The URL is printed above (kalshiFastRead). POST a JSON body {\"job\": {\"requests\": [...]}} with: Authorization: Bearer <token>. It answers 400 during the bot's busy minutes of each quarter hour."
