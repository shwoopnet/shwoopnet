#!/bin/bash
# Hourly temperature measure step (Testing Desk). Usage: read_hourlytemp_candles.sh <case folder holding lists/ and candles/> <out file>
# Run ONLY after Auditor B's structure check of the candle run; copy (do not link) the runs into <case folder>/lists and /candles. Commit the print BEFORE comparing with Desk B's reader.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
[ $# -eq 2 ] || { echo "usage: $0 <case folder> <out>"; exit 2; }
[ "$(sha256sum hourlytemp_second.py | cut -c1-16)" = "c3b6f048bad6082c" ] || { echo "refused: hourlytemp_second.py is not the audited build"; exit 3; }
python3 -I hourlytemp_second.py "$1" > "$2" 2>&1
