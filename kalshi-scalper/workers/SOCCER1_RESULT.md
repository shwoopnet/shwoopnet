# Result: SOCCER1 (Kalshi soccer cheap side vs de-vigged DraftKings three-way price), 2026-11-04

Registration `workers/SOCCER1_REGISTRATION.md` (sha256 prefix 067a55065976e4413c824e150670484ab63a8d061174220332aa6d6c4628e865, pushed before any candle, price or result was read). Code `src/scalper/soccer1.py`, tests `tests/test_soccer1.py`. **N: +2.** Cheap side only; no favourite-side result computed. Frozen W3 never fetched or joined.

**Leagues:** EPL, La Liga, Serie A, Bundesliga, Ligue 1, Champions League, Europa League, MLS, English Championship, Eredivisie, Primeira Liga, Liga MX. Kalshi match events before the cut: 526; ESPN events with odds: 519 of 522 fetched (99%); **joined 445 matches** (81 Kalshi events unmatched by team name, dropped as registered; ESPN list stops at Oct 2 by date).
**Gap (q minus ask, cheap outcomes G):** median +0.12c, p90 +1.45c, n 801 outcomes in 433 matches. One price again (prediction held: median +0.5 to +2c was slightly high).
**Win vs price:** ask 3-10c n 52 win 0.019 vs ask 0.066 vs q 0.078; 10-20c n 180 win 0.194 vs 0.156 vs 0.165; 20-30c n 569 win 0.267 vs 0.255 vs 0.255. Draws and most outcomes sit at 20-30c.
**Control (all cheap outcomes):** win 0.235 vs ask 0.221, mean net +0.18c after fees, PF 1.01, z(match) 0.13. Flat, not the -1 to -3c predicted; indistinguishable from zero.
**Treated (q >= 3 x ask): n 0.** The goals-total rule T (strike equal to the book line) had no cheap outcome at all (line strikes trade near 50c).
**Verdict: NOT_ENOUGH_DATA (0 of 150).** Not FALSIFIED by the rule. The gap evidence says Kalshi soccer cheap prices equal the de-vigged book to about 0.1c at the median, so a 3x gap does not occur.
**Forward plan:** none worth building. The only live lead is the 10-20c bucket (win 0.194 vs ask 0.156, n 180), which is an ordinary calibration wobble at that size and would need a new registration; a recorder of the DK close would not change the treated count of 0.
