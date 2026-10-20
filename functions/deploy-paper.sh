#!/usr/bin/env bash
# Deploys ONLY the paper tracker (kalshiPaperTick) and the Firestore rules (the admin-only read rule for its records), from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-paper.sh
#
# The tracker is keyless: it holds no secret, signs nothing and places no order, so unlike deploy-sizing.sh and deploy-push.sh this needs no order switch line and touches no live function.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=shwoopnet
ONLY=functions:kalshiPaperTick,firestore:rules

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

echo "Deploying to $PROJECT: $ONLY"
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. The tracker starts recording at the next entry minute (8 or 9 of a quarter hour). Open the Kalshi page: the Paper candidates card fills as markets settle."
