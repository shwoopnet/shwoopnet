#!/bin/sh
# Every file runs even if an earlier one fails, and the exit code says if any did.
status=0
for t in test_scalper test_opening test_ow2 test_ow3 test_ss1 test_ss2 test_bk1 test_e3 test_e4 test_wx1 test_dt1 test_growth test_xm1 test_sp1 test_e3f test_e3b test_arb1 test_pm1 test_flb1 test_l1b test_pm2 test_fwd1 test_e5 test_vol1 test_pm3 test_growth2 test_growth3 test_e5b_e3c test_buydip1 test_idx1 test_tp1 test_perp1 test_perp2; do
  python3 tests/$t.py || status=1
done
exit $status
