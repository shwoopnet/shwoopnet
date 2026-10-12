#!/bin/sh
# Every file runs even if an earlier one fails, and the exit code says if any did.
status=0
for t in test_scalper test_opening test_ow2 test_ow3 test_ss1; do
  python3 tests/$t.py || status=1
done
exit $status
