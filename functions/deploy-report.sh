#!/usr/bin/env bash
# Deploys ONLY the nightly order report (kalshiNightlyReport), from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-report.sh
#
# The function is read only: it holds no Kalshi key, signs nothing, places no order and writes nothing. It is protected by ONE secret token, KALSHI_REPORT_TOKEN.
# The first run makes a random token, stores it in Secret Manager and prints it ONCE here, in your own terminal, so you can put it in the Claude environment's
# secrets (never in a chat). A later run keeps the existing token (replacing it would break the scheduled report until the environment is updated).
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=shwoopnet
ONLY=functions:kalshiNightlyReport

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

if [ "${DRY_RUN:-}" = "1" ]; then
  echo "[dry run] create KALSHI_REPORT_TOKEN if it does not exist"
elif "${FB[@]}" functions:secrets:get KALSHI_REPORT_TOKEN --project "$PROJECT" >/dev/null 2>&1; then
  echo "KALSHI_REPORT_TOKEN already exists: keeping it."
else
  TOKEN="$(openssl rand -hex 32)"
  printf '%s' "$TOKEN" | "${FB[@]}" functions:secrets:set KALSHI_REPORT_TOKEN --data-file - --project "$PROJECT"
  echo
  echo "NEW REPORT TOKEN (shown once; copy it into the Claude environment's secrets, not into a chat):"
  echo "$TOKEN"
  echo
fi

echo "Deploying to $PROJECT: $ONLY"
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. The URL is printed above (kalshiNightlyReport). Call it with: Authorization: Bearer <token>, optional ?hours=24 and ?orders=1."
