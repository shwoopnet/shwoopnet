#!/bin/bash
# WHEEL0 run wrapper (Testing Desk). Usage: read_wheel0.sh count <lists...> --candles <runs...> --drop <file>
# Logs the interpreter first (Forensics check 8c: built-in sum() on floats is compensated on Python 3.12+ and not before, so
# every WHEEL0 build must run on the version its run log records). Does not change wheel0_second.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
[ "$(sha256sum wheel0_second.py | cut -c1-16)" = "eeb35dc1490c4c6e" ] || { echo "refused: wheel0_second.py is not the recorded build"; exit 3; }
echo "interpreter: $(command -v python3)"
echo "version: $(python3 --version 2>&1)"
echo "sum check: sum([0.1]*10) = $(python3 -c 'print(repr(sum([0.1]*10)))')"
python3 -I wheel0_second.py "$@"
