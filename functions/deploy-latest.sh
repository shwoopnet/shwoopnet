#!/usr/bin/env bash
# One command to deploy whatever has merged since the last deploy (the owner, Oct 30, 2026: "build the wrapper"):
#
#   bash functions/deploy-latest.sh
#
# It updates this folder to origin/main, runs the whole test suite, works out from the files that changed which of the three existing deploy scripts are needed,
# SHOWS that plan and asks before it runs anything. It only ever calls deploy-push.sh, deploy-sizing.sh and deploy-report.sh (in that order, the order CLAUDE.md requires),
# it never touches a secret, never pushes to git and never forces anything. A deploy that fails stops the run and the marker is NOT moved, so the next run offers it again.
#
# The marker is functions/.last-deployed (gitignored): the commit you last finished deploying. The first run has no marker, so it asks whether everything up to the
# current main is already deployed and, if you say yes, records that as the starting point.
# DRY_RUN=1 prints the plan and the commands without running the network ones, and ASSUME_YES=1 answers every question yes (the test uses both).
set -euo pipefail

cd "$(dirname "$0")/.."
MARKER=functions/.last-deployed

run() { if [ "${DRY_RUN:-}" = "1" ]; then echo "[dry run] $*"; else "$@"; fi; }
ask() {
  if [ "${ASSUME_YES:-}" = "1" ]; then echo "$1 [y/N] y (ASSUME_YES)"; return 0; fi
  local a; read -r -p "$1 [y/N] " a; [ "$a" = "y" ] || [ "$a" = "Y" ]
}

# Local edits to tracked files would be thrown away by the update below, so stop and say so.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "This folder has local changes to tracked files. Not updating (the update would discard them):"
  git status --short --untracked-files=no
  exit 1
fi

git fetch origin main
NEW="$(git rev-parse origin/main)"
git checkout main >/dev/null 2>&1 || git checkout -B main origin/main >/dev/null 2>&1
git reset --hard origin/main >/dev/null
echo "Now at: $(git log --oneline -1)"

if [ ! -f "$MARKER" ]; then
  echo "No record of a previous deploy from this folder."
  if ask "Is everything up to this commit already deployed? (yes records it as the starting point and stops)"; then
    [ "${DRY_RUN:-}" = "1" ] || echo "$NEW" > "$MARKER"
    echo "Recorded. Next time this deploys only what merged after $(git log --oneline -1 "$NEW" | cut -c1-60)."
    exit 0
  fi
  echo "Not recorded. Run the individual deploy scripts by hand once, then run this again."
  exit 1
fi

OLD="$(tr -d '[:space:]' < "$MARKER")"
if ! git cat-file -e "$OLD^{commit}" 2>/dev/null; then echo "The recorded commit $OLD is not in this repository. Delete $MARKER and run again."; exit 1; fi
if [ "$OLD" = "$NEW" ]; then echo "Nothing new since the last deploy ($(git log --oneline -1 "$OLD" | cut -c1-70))."; exit 0; fi

echo
echo "Merged since the last deploy:"
git log --oneline "$OLD..$NEW"
CHANGED="$(git diff --name-only "$OLD" "$NEW")"

# What each deploy covers (CLAUDE.md): the bot's minute function and size lock (sizing), the exit watch, Flatten and phone alerts (push), the nightly report (report).
# kalshiLiveLib.js and index.js are shared by more than one function, so a change there is offered to the matching deploys.
want() { echo "$CHANGED" | grep -Eq "$1"; }
DO_PUSH=0; DO_SIZING=0; DO_REPORT=0
want '^functions/(kalshiPushLib|kalshiExitAlarmLib|deploy-push)\.' && DO_PUSH=1
want '^functions/(kalshiLiveLib|kalshiSlot[A-Za-z]*Lib|deploy-sizing)\.' && DO_SIZING=1
want '^functions/(kalshiReportLib|deploy-report)\.' && DO_REPORT=1
want '^functions/index\.js$' && { DO_SIZING=1; DO_REPORT=1; }
want '^functions/(kalshiLiveLib)\.' && DO_PUSH=1   # the exit watch lives in kalshiLiveLib, so its changes also need the exit watch deployed
PAGE_ONLY=0
if [ $((DO_PUSH + DO_SIZING + DO_REPORT)) -eq 0 ]; then PAGE_ONLY=1; fi

echo
echo "Plan (in this order):"
[ $DO_PUSH -eq 1 ]   && echo "  1. deploy-push.sh    (exit watch, Flatten, phone alerts)"
[ $DO_SIZING -eq 1 ] && echo "  2. deploy-sizing.sh  (the bot's minute function, size lock, slot)"
[ $DO_REPORT -eq 1 ] && echo "  3. deploy-report.sh  (nightly report)"
if [ $PAGE_ONLY -eq 1 ]; then
  echo "  nothing to deploy: only page, docs or tests changed (the page is live once merged)."
  [ "${DRY_RUN:-}" = "1" ] || echo "$NEW" > "$MARKER"
  exit 0
fi
echo

echo "Running the whole test suite first (a failure stops here, nothing is deployed)."
for f in test/*.test.js; do node "$f" >/dev/null 2>&1 || { echo "FAILED: $f. Nothing deployed."; exit 1; }; done
echo "All tests pass."
echo

ask "Run the plan above?" || { echo "Stopped. Nothing deployed."; exit 0; }

if [ $DO_PUSH -eq 1 ];   then run bash functions/deploy-push.sh;   fi
if [ $DO_SIZING -eq 1 ]; then run bash functions/deploy-sizing.sh; fi
if [ $DO_REPORT -eq 1 ]; then run bash functions/deploy-report.sh; fi

[ "${DRY_RUN:-}" = "1" ] || echo "$NEW" > "$MARKER"
echo
echo "Done. Recorded $(git log --oneline -1 "$NEW" | cut -c1-70) as deployed."
