# HOURLY1 result (2026-11-02; registered in acdb9e5 before any candle; `src/scalper/hourly1.py`, `tests/test_hourly1.py`, run once)

**SOL (KXSOLD): FALSIFIED. XRP (KXXRPD): FALSIFIED (and NOT_ENOUGH_DATA by count). DOGE+HYPE (KXDOGED + KXHYPED): FALSIFIED (and NOT_ENOUGH_DATA by count).** OVERLAPS_L1 did not fire for any asset (share of qualifying entries priced 0.88 to 0.97: SOL 1%, XRP 3%, DOGE 0%, HYPE 1%; bar 50%). Holdout W3 unread for every group. Not a pass, no promote verb.

Data: 1,012,662 settled "above" markets (SOL 460,775; XRP 116,865; DOGE 83,202; HYPE 351,820), 68 UTC dates (2026-08-27 to 2026-11-02), 1,587 hourly closes; OKX 1 minute klines (97,700 per pair); Kalshi 1 minute candles for the 45,438 markets with strike within 2% of spot that had any candle. Look 10 minutes before the close, C = 10, taker at the ask, fee 7% x C x p x (1-p) rounded up (x1.2 stress), edge 0.08 after fee (Try A verdict, 0.12 Try B), N = 728,720, z bar 5.27.

Headline numbers (Try A, window, n, cost, N as above):
- SOL: Brier model 0.1197 vs market mid 0.1045 (4,928 eligible strikes); W1 n 63 PF 0.96 mean -0.92c; W2 n 108 PF 0.87 mean -3.07c; pooled n 171 PF 0.90 mean -2.27c z -0.66; fees x1.2 W1 -1.18c, W2 -3.35c.
- XRP: Brier 0.0903 vs 0.0799 (1,208 eligible); W1 n 9 PF 1.53, W2 n 8 PF 0.63; pooled n 17 (under 150).
- DOGE+HYPE: Brier 0.1224 vs 0.1136 (2,662 eligible: DOGE 345, HYPE 2,317); W1 n 18 PF 2.88 mean +20.6c z +2.66; W2 n 53 PF 1.05 mean +1.05c; pooled n 71 PF 1.32 mean +6.0c z +0.93 (under 150, not a finding: W1 is 18 trades).
Try B (information only): SOL pooled n 81 PF 0.84; XRP n 3; DOGE+HYPE n 22 PF 1.92 mean +15.3c.

Printed result (verbatim from the one run):
```
HOURLY1 run 2026-11-02T19:01:04.063838+00:00 N=728720 z bar 5.27 cost: fee 7% x C x p x (1-p) rounded up, C=10, taker at the ask
markets 1012662, with candles 45438
--- GROUP SOL (KXSOLD)
KXSOLD: events with a model 1559, eligible strikes 4928, qualifying trades 551, banned under 0.2 408, share priced 0.88 to 0.97 1% -> scored
Try A edge 0.08 (verdict): eligible strikes 4928 on 68 dates; Brier model 0.1197 market mid 0.1045
W1: n 63 days 15 PF 0.96 mean -0.92c z -0.21 | fees x1.2 mean -1.18c
W2: n 108 days 19 PF 0.87 mean -3.07c z -0.66 | fees x1.2 mean -3.35c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 171 days 34 PF 0.90 mean -2.27c z -0.66
SOL Try A edge 0.08 (verdict): FALSIFIED | Brier model no better than the market mid; W1 PF 0.96 under 1.5; W1 not positive at fees x1.2; W2 PF 0.87 under 1.5; W2 not positive at fees x1.2; pooled mean -2.27c under 2.0; pooled z -0.66 under 5.27
Try B edge 0.12: eligible strikes 4928 on 68 dates; Brier model 0.1197 market mid 0.1045
W1: n 26 days 8 PF 1.31 mean +5.72c z +0.65 | fees x1.2 mean +5.45c
W2: n 55 days 11 PF 0.68 mean -8.39c z -1.13 | fees x1.2 mean -8.68c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 81 days 19 PF 0.84 mean -3.86c z -0.60
SOL Try B edge 0.12: FALSIFIED | Brier model no better than the market mid; trades 81 under 150
--- GROUP XRP (KXXRPD)
KXXRPD: events with a model 1043, eligible strikes 1208, qualifying trades 75, banned under 0.2 80, share priced 0.88 to 0.97 3% -> scored
Try A edge 0.08 (verdict): eligible strikes 1208 on 68 dates; Brier model 0.0903 market mid 0.0799
W1: n 9 days 9 PF 1.53 mean +5.71c z +0.55 | fees x1.2 mean +5.49c
W2: n 8 days 6 PF 0.63 mean -8.69c z -0.82 | fees x1.2 mean -8.98c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 17 days 15 PF 0.94 mean -1.06c z -0.14
XRP Try A edge 0.08 (verdict): FALSIFIED | Brier model no better than the market mid; trades 17 under 150
Try B edge 0.12: eligible strikes 1208 on 68 dates; Brier model 0.0903 market mid 0.0799
W1: n 1 days 1 PF inf mean +0.00c z +0.00 | fees x1.2 mean +0.00c
W2: n 2 days 2 PF 1.09 mean +2.20c z +0.06 | fees x1.2 mean +1.90c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 3 days 3 PF 2.31 mean +22.23c z +0.74
XRP Try B edge 0.12: FALSIFIED | Brier model no better than the market mid; trades 3 under 150
--- GROUP DOGE+HYPE (KXDOGED, KXHYPED)
KXDOGED: events with a model 345, eligible strikes 345, qualifying trades 16, banned under 0.2 13, share priced 0.88 to 0.97 0% -> scored
KXHYPED: events with a model 1139, eligible strikes 2317, qualifying trades 250, banned under 0.2 131, share priced 0.88 to 0.97 1% -> scored
Try A edge 0.08 (verdict): eligible strikes 2662 on 68 dates; Brier model 0.1224 market mid 0.1136
W1: n 18 days 10 PF 2.88 mean +20.61c z +2.66 | fees x1.2 mean +20.34c
W2: n 53 days 19 PF 1.05 mean +1.05c z +0.13 | fees x1.2 mean +0.78c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 71 days 29 PF 1.32 mean +6.01c z +0.93
DOGE+HYPE Try A edge 0.08 (verdict): FALSIFIED | Brier model no better than the market mid; trades 71 under 150
Try B edge 0.12: eligible strikes 2662 on 68 dates; Brier model 0.1224 market mid 0.1136
W1: n 7 days 3 PF 3.86 mean +28.44c z +3.06 | fees x1.2 mean +28.17c
W2: n 15 days 7 PF 1.46 mean +9.12c z +0.61 | fees x1.2 mean +8.84c
W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)
pooled (windows read): n 22 days 10 PF 1.92 mean +15.27c z +1.45
DOGE+HYPE Try B edge 0.12: FALSIFIED | Brier model no better than the market mid; trades 22 under 150
```

Reading: the numeric prediction (model Brier worse than the quote mid in every group, SOL PF 0.5 to 1.2, pooled mean -6c to +1c) held for SOL; XRP and DOGE+HYPE fell far below the predicted 200 trades because their ladders are barely quoted (XRP 1,208 and DOGED 345 eligible strikes in 68 days, most strikes within 2% of spot had no candle or failed the 10 contract volume rule). Even where the 10 minute quote is two sided, it is closer to the outcome than a 60 minute realised-vol lognormal: the hourly horizon did not turn the LAG15 result around. The only positive cell (HYPE, W1) is 18 trades inside a group that failed Brier and count.

Limits and disclosures (none changes the verdict):
- Code changed after registration (acdb9e5), before any outcome was scored and without reading any outcome: (1) KXDOGED stores its strike in `custom_strike.floor_strike` (strike type "custom" at top level, rules text says "above"), so `strike_of` was added; (2) Kalshi's batch candle endpoint caps 10,000 candlesticks per request, so candle requests were regrouped to one event window (8 minutes) and at most 100 tickers per request instead of several events per request. First market listing (all four series in one process) ran past the 30 minute background limit and was discarded; listing was redone per series. The first candle fetch attempt failed every group on the 10,000 cap and cached nothing.
- Metadata read before registration was SOL only (see the registration); the other three series' counts were first seen after it. The market listing carries `result`, but nothing was scored before the run.
- Rules text was read for KXSOLD and KXDOGED (both: 60 second average of CF Benchmarks RTI, strictly above); KXXRPD and KXHYPED assumed the same (their rules text was not read). One venue (OKX USDT) is not the CF index; the basis is unmeasured.
- Candle coverage is the limit: only 45,438 of the 1,012,662 markets had any candle, so the traded sample is the liquid middle of the ladder. A quote is not a fill; the taker-at-the-ask assumption is generous.
- Only the 10 minute look and the 2% strike filter were run; no variant.

Forward read: one is possible from public history (Kalshi candles and OKX klines are retrievable later, no recorder needed), earliest **2026-12-02** (30 fresh days), but SOL is FALSIFIED with n above 150 and the others cannot reach 150 trades in 68 days (XRP 75 qualifying, DOGED 16), so none is planned. A recorder of the order book (the Oct 29 book recorder style) would be needed only to ask whether thin ladders can be quoted passively.
