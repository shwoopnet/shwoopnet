#!/bin/sh
# Both files run even if the first fails, and the exit code says if either did.
status=0
python3 tests/test_scalper.py || status=1
python3 tests/test_opening.py || status=1
exit $status
