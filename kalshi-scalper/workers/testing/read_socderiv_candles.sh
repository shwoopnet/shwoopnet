#!/bin/bash
# SOCDERIV candle read (Testing Desk). Usage: read_socderiv_candles.sh <lists run> <candle run A> <candle run B> <out file>
# Run ONLY after Auditor B's structure check of both candle runs (rule 16). Prints the guard's list-hash line (stderr) into the same log; commit the log BEFORE comparing with the History Miner's print.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
[ $# -eq 4 ] || { echo "usage: $0 <lists run> <candle run A> <candle run B> <out>"; exit 2; }
want_reader=77ea2ba71def6e3e; want_scorekit=f219b43c755b4b87
[ "$(sha256sum socderiv.py | cut -c1-16)" = "$want_reader" ] || { echo "refused: socderiv.py is not the audited build"; exit 3; }
[ "$(sha256sum scorekit.py | cut -c1-16)" = "$want_scorekit" ] || { echo "refused: scorekit.py is not the audited build"; exit 3; }
python3 -I socderiv.py measure "$1" --candles "$2" "$3" > "$4" 2> "$4.stderr"
cat "$4.stderr" >> "$4.log"; echo "reader $want_reader scorekit $want_scorekit" >> "$4.log"
grep -q "HELDOUT_PULL_RUNS.md copy read by the guard" "$4.stderr" || { echo "run log has no guard list-hash line: not counted"; exit 4; }
