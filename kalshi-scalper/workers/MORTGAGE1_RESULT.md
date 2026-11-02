# MORTGAGE1 result (single run 2026-11-02, after registration commit 1c0afbe; `src/scalper/mortgage1.py`, tests `tests/test_mortgage1.py`)

Data: FRED MORTGAGE30US and DGS10 (curl; Python urllib to FRED timed out in this sandbox), Kalshi `KX30YMORTW` 190 settled markets on 10 weekly events (2026-08-27 to 2026-10-29), hourly candles. Model fitted expanding on weeks before each event (from 2010-01-07). Look Thursday 12:00 UTC, edge 8c, spread at most 10c, C = 10, fee 7% x C x p x (1-p) rounded up per order, N about 728,700 (z bar 5.27).

- Brier at the look over 78 quoted strikes: nowcast 0.2803, persistence 0.4190, market mid 0.0461. The market is far better; the prediction (nowcast beats the market) failed.
- Try A (both sides): 65 trades on 10 events. Window 1 (3 events) n 7 PF 1.15 mean +2.21c; window 2 (3 events) n 36 PF 0.34 mean -5.03c z -2.01; window 3 (4 events, holdout) n 22 PF 0.14 mean -9.51c z -2.52. Pooled PF 0.39, mean -5.77c, z -2.71; fees x1.2 PF 0.39.
- Try B (long-shot side only): 58 trades, pooled PF 0.23, mean -6.76c, z -5.85; windows 1.15 / 0.00 / 0.00.

**Verdict: NOT_ENOUGH_DATA by the registered count rule (65 trades against 150; 10 events is all the history there is).** The registered FALSIFIED lines are also hit descriptively (PF under 1.5 in windows 2 and 3, nowcast Brier no better than the market, pooled PF 0.39), so the prior of a pass is now below 1%; the forward read (events from `KX30YMORTW-26NOV05`) is kept as registered but is not recommended as a priority. The mean loss of about 6c to 10c with 89% to 97% losing trades says the market already prices the yield move; 10 events are too few to separate that from a model mismatch (for example a weekly window that does not match the survey week). No variant was run.

Forward read: events from 2026-11-05 onward, 150 trades at about 6 to 7 per event is about 22 to 25 weekly events, so about 2027-04-15 (or the registered 2027-09-30 cap). No new recorder needed: Kalshi's hourly candles for settled markets are still served.
