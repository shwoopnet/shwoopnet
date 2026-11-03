# BOOKS1 result (run once 2026-11-03; registered in baaf539, sha256 prefix c673b39a45af255f; W3 frozen third not fetched or joined)

Code `src/scalper/books1.py`, tests `tests/test_books1.py` (5 pass), raw `data/books1_result.txt`. N +2.

**Reachability:** ESPN core odds endpoint keyless; DraftKings open and close moneylines for 860 of 972 W1+W2 games (112 had no line). Closing pre-game line, not only latest. Earliest Kalshi quote median 6 to 7 minutes before start (never 30 or 60), so look = last valid candle at or before start minus 120 s (108 games had none).

**Universe:** 972 games (college football, MLB, NFL; NBA games pre-W3 absent) -> 258 cheap sides (lower ask in 3c to 30c; 494 games had no side that cheap).

**Gap, sportsbook de-vigged probability minus Kalshi ask, cheap sides:** median +0.76c, p90 +2.21c, |gap| median 1.04c (college football n 228 median +0.89c; MLB n 14 +0.07c; NFL n 16 +0.41c). The two prices are nearly one price; the small positive gap is about the spread.

**Treated (q >= 3 x ask): n 0.** The largest gap is far from tripling the ask. **Control (all cheap sides, W1+W2): n 258, win 0.112 vs mean ask 0.160 vs mean book probability 0.168, mean net -5.73c after fees.** Cheap sides won less than both prices (informational; 0.112 vs 0.160 is about 2 standard errors at n 258, one league dominates, not a claim).

**Verdict: NOT_ENOUGH_DATA (0 treated of 150); prediction held** (median gap +0.5c to +2c, p90 under 6c, 0 to 15 trades). The 3x idea is closed: no mispricing of that size exists against the book. A looser ratio would be a new registration and the gap evidence says it also yields nothing worth fees (gap 1c vs fee 0.4c to 1.5c).
**Forward plan:** none worth a recorder. If wanted, the only open lead is the control's win rate below the ask (cheap sides overpriced, i.e. selling YES), which is a favourite-side-adjacent claim the owner rule excludes here.
