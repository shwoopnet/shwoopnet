#!/bin/bash
# usage: fieldscan.sh token ; prints per ref: py-file count and md-file count (excluding recorder scripts/workflows)
tok="$1"; out=""
for ref in origin/main origin/claude/epic-ptolemy-0amjd9 origin/claude/idea-desk-a origin/claude/idea-desk-b origin/claude/idea-desk-c origin/claude/testing-desk origin/claude/history-miner origin/claude/refine-live origin/claude/stocks-desk origin/claude/probe-desk origin/rnd-queue origin/claude/forensics-desk; do
  py=$(git grep -l -w -e "$tok" $ref -- 'kalshi-scalper/*.py' 'kalshi-scalper/**/*.py' ':!scripts' 2>/dev/null | grep -v "forensics/spxfv1\|listed_runs" | wc -l)
  md=$(git grep -l -w -e "$tok" $ref -- '*.md' ':!docs' ':!CLAUDE.md' 2>/dev/null | wc -l)
  [ "$py" != "0" -o "$md" != "0" ] && out="$out ${ref#origin/}:py$py/md$md"
done
echo "$tok |${out:- NONE}"
