# EXITS3: hand case for the exit engine and the first two cards (OIREL, OICORE rule history), written before the code and before any extract is read (2026-11-15 ~16:10Z)

Spec: EXITS3_SPEC_NOV15.md (140aa224, accepted by the Head 14:42Z). Data: Forensics' OIREL extract (claude/forensics-desk, extracts/OIREL_extract.sqlite.xz; per its README it is also the OICORE rule extract): KXBTC15M, 2026-08-06 to before 2026-10-03 (XOI1's W3 cut), first source wins. Reader rule from the README: candles ending after the market's close are dropped.

**Entry rules, from the code that produced the printed figures:**
- **OICORE rule history (FALS4, research branch src/scalper/fals4.py, the "core C=10 next fill"):**
  - signal candle ends 180 s before the close; back candle ends 360 s before;
  - doi = oi(signal) - oi(back) > 86,299.56;
  - side = the first of YES, NO whose ask at the signal candle is 0.05 to 0.50 (NO ask = 1 - yes_bid);
  - fill = that side's ask on the candle ending 120 s before the close, kept only if 0 < fill < 1;
  - 10 contracts. A missing signal, back or fill candle, or a missing oi, means no trade.
- **OIREL (src/scalper/oirel.py):** the same, except the trigger is doi / oi(back) > 0.26764675317954373, and an oi of 0 or missing on either candle means no trade.
- Both enter at the candle ending 120 s before the close. So the only later mark is the candle ending 60 s before. M (at 180 s) is before entry: every entry is held under M (counted as "M n/a, held"). Entry and exit are in the last 2 minutes, so the **primary haircut is 2c** (C8). 1c and 0 are printed too.

**Exit engine (all cards):**
- e = the raw entry ask.
- Marks are candles ending after the entry candle and at or before close - 60 s.
- Side bid: YES = bid_c; NO = 1 - ask_c.
- Sellable: 0 < side bid < 1 (a NO needs ask_c < 1; a YES needs bid_c > 0).
- Triggers on the raw side bid:
  - T: bid >= min(2e, 0.90) - 1e-9.
  - S: bid <= e / 2 + 1e-9.
  - M: the mark ending exactly close - 180 s, if after the entry candle.
- After a trigger, the sale is at the first sellable mark at or after it. If none by the last mark, the position is held (counted as "triggered, not sold").
- Prices:
  - entry = min(0.99, e + h);
  - sale = max(0.01, bid - h);
  - hold pays 1 or 0;
  - fee per order = ceil(round(100 x 0.07 x c x p x (1 - p), 9)) / 100 at c = 10, divided by c per contract.
  - Net per contract = value - entry - fee_in/c - fee_out/c (no fee_out on hold).
- A void (result not yes or no) refunds the price and keeps the entry fee: net = -fee_in/c when held. A void after a sale changes nothing.
- Printed per card, variant (hold, T, S, M) and h (0, 1c, 2c):
  - n, cash PF, PF of each half by count floor(n/2) in close order, mean cents, day-clustered z (UTC day of the close, per-day sums);
  - exits by reason.

**Expected by hand (test_exits3.py; invented windows, YES side unless stated, c = 10):**
- **E1:** entry YES e 0.20 at -120. Mark -60 bid 0.45 (>= 0.40), so T sells at 0.45.
  - h 0: fees 0.12/10 and 0.18/10, net = 0.25 - 0.030 = 0.220.
  - h 1c: entry 0.21, sale 0.44, fees 0.12 and 0.18, net 0.200.
  - S: no trigger, held. Result yes: 1 - 0.20 - 0.012 = 0.788.
- **E2:** NO entry: yes_bid 0.70 at -120, so e 0.30. Mark -60 yes_ask 0.90, so the NO bid is 0.10 (<= 0.15) and S sells at 0.10.
  - h 0: fees 0.15 and 0.07, net = 0.10 - 0.30 - 0.022 = -0.222.
  - T: no trigger, held. Result yes (so NO loses): -0.30 - 0.015 = -0.315.
- **E3:** e 0.30, mark -60 bid 0.40: T, S and M all held. Result no: -0.315 in every variant.
- **E4:** e 0.40, mark -60 bid 0.00, so S triggers but there is no sellable mark: held, counted "triggered, not sold". Result yes: 1 - 0.40 - 0.017 = 0.583.
- **E5 (engine, an entry at -600):** e 0.50; marks -540 bid 0.52, -180 bid 0.61, -60 bid 0.95.
  - T (target 0.90) sells at 0.95 at -60.
  - M sells at 0.61 at -180.
  - S held.
  - h 0: T net = 0.45 - (0.18 + 0.04)/10 = 0.428 (fee(0.50) = ceil(17.5) = 18; fee(0.95) = ceil(3.325) = 4). M net = 0.11 - (0.18 + 0.17)/10 = 0.075 (fee(0.61) = ceil(16.653) = 17).
- **E6 (void):** e 0.30 held, result void: net = -0.015.
- **Entry rules** (level oi at -360, signal oi at -180, side ask 0.20 at -180, fill 0.22 at -120):
  - level 300,000, signal 400,000 (doi 100,000, ratio 0.333): both cards trade.
  - level 400,000, signal 490,000 (90,000, 0.225): OICORE only.
  - level 200,000, signal 280,000 (80,000, 0.40): OIREL only.
  - level 300,000, signal 400,000, but both sides' asks outside 0.05 to 0.50: neither trades.
  - the fill candle missing: neither trades.
- **Summary:** PF = gains / losses; halves floor(n/2). With 4 trades nets (+0.2, -0.1, +0.3, -0.3), PF 0.5 / 0.4 = 1.25; half 1 (first 2) PF 2.0, half 2 PF 1.0.
- **Test-data slip (disclosed, first test run):** my first 'both sides outside 0.05 to 0.50' window used bid 0.60 and ask 0.70, which leaves the NO ask at 0.40, inside the band, so the code rightly traded. The fixture is now bid 0.40, ask 0.55 (NO ask 0.60), both outside. The expected results are unchanged.
- **C1 added to the entry rules (before any extract was read; the haircut rule applies C1 to every recompute):** the signal candle (-180 s) and the fill candle (-120 s) must each be two-sided (0 < yes_bid < yes_ask < 1), or there is no trade, counted as "not two-sided". FALS4 and OIREL did not require this, so n can be a little below theirs. The test windows were made two-sided (signal bid 0.18 under ask 0.20, fill bid 0.20 under ask 0.22). Two new checks: a 0.00 signal bid, and a fill candle with bid equal to ask, each give "not two-sided".
