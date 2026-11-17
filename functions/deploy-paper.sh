#!/usr/bin/env bash
# Deploys ONLY the Firestore rules (the paper tracker it was named for was deleted on Nov 17, 2026; the file name stays so the one rules deploy has one known command), from a fresh clone:
#
#   git clone https://github.com/shwoopnet/shwoopnet && bash shwoopnet/functions/deploy-paper.sh
#
# Rules only: it holds no secret, signs nothing and touches no function, so unlike deploy-sizing.sh and deploy-push.sh this needs no order switch line.
# DRY_RUN=1 prints the commands instead of running the network ones (the test uses it).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=shwoopnet
ONLY=firestore:rules

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }

if command -v firebase >/dev/null 2>&1; then FB=(firebase); else FB=(npx --yes firebase-tools); fi

run npm --prefix functions install --no-audit --no-fund

if [ "${DRY_RUN:-}" != "1" ] && "${FB[@]}" login:list 2>&1 | grep -qi "no authorized accounts"; then
  "${FB[@]}" login --no-localhost
fi

echo "Deploying to $PROJECT: $ONLY"
run "${FB[@]}" deploy --only "$ONLY" --project "$PROJECT"
echo
echo "Done. The Firestore rules are published."
