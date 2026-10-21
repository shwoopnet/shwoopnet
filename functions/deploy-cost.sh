#!/usr/bin/env bash
# Deploys ONLY the two keyless housekeeping functions changed in the Oct 21, 2026 cost review, from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-cost.sh
#
#   kalshiPaperTick     now returns at once (the paper tracker is switched off; its card is gone and live one-contract probes replaced it)
#   kalshiBookRecorder  while switched off it now deletes old order-book snapshots (200 a minute) instead of doing nothing, so stored data stops billing
#
# Neither holds a secret, signs anything or places an order, so unlike deploy-sizing.sh and deploy-push.sh this needs no order-switch line and touches no live function.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=shwoopnet
ONLY=functions:kalshiPaperTick,functions:kalshiBookRecorder

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

echo "Deploying to $PROJECT: $ONLY"
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. The paper tracker stops writing at once, and the old snapshots are deleted over the next hours (check Firestore usage tomorrow)."
