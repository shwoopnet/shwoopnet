# SEARCH1 chosen-combination haircut recompute, BUILD 2: hand case (Testing Desk, Nov 15, 2026). Written BEFORE any code.
Sources, read for the rule only: research branch claude/epic-ptolemy-0amjd9 `src/scalper/search1.py` (settle, combos, the constants), `lstrats.favorite` and `net`, `analyze.valid_quote` and CANDLE_MAX_SPREAD, README:6030 (pre-registration) and the Oct 23 result line (chosen 420 s, band 0.97 to 0.995, SL50; confirmation n 361, PF 1.31); rnd-queue C1 to C10; Desk A's input list (extract claude/forensics-desk 31351c1b `SEARCH1_extract.sqlite.xz` sha256 979ac4dcd49cb29578cdd2e2af42386f41dabcce344ac973b57610f2c9e316a9, closes Aug 6 to Oct 2; cut day inferred 2026-09-27, ts 1790467200). Desk A's hand case was read as the statement of the haircut; my windows and figures are my own.
## What I build: `search1_second.py <extract.sqlite> <cut_ts>`
Reads only the extract (market(ticker, series, open_ts, close_ts, result, strike, src), candle(ticker, end_ts, bid_c, ask_c, volume, oi)); prints aggregates only; writes nothing. Series KXBTC15M and KXETH15M pooled (others ignored, counted). A market counts only with a result of yes or no AND every one of its candles (after dropping those ending after the close) having a bid and an ask; otherwise it is out whole (counted: excluded result, incomplete market). Entry candle = the candle ending exactly close - 420 (none: skip, no candle). `valid_quote(bid, ask)`: bid >= 0.001, ask <= 0.999, ask >= bid, ask - bid <= 0.10 (MY READING: with 1e-9 slack on the three inequalities that touch a boundary, because the card compares raw floats; to confirm with Desk A); invalid: skip (bad quote), before the band test. Band 0.97 to 0.995 inclusive (the card's favorite(): YES if lo <= ask <= hi, else NO at round(1 - bid, 4) if in band; otherwise skip band). Exit SL50: later candles = those ending strictly after the entry candle and at or before close - 30; the first whose bought-side bid is at or under 0.50 (YES bid = bid close; NO bid = round(1 - ask close, 4)) is sold at that bid; none: hold to settlement. Haircut (C1 to C10): entry price = min(round(ask + h, 6), 0.99) (so a raw ask of 0.995 is 0.99 even at h = 0), exit price = max(round(bid - h, 6), 0.01); fee_up_order = ceil(0.07 x 10 x price x (1 - price) x 100 - 1e-9) / 100 on EACH leg; cash = 10 x (exit - entry) - fee_in - fee_out, or 10 x (win - entry) - fee_in when held. Halves floor(n/2) by close time (ties by ticker). PF = positive over absolute negative (infinite with no loss, 0 with no win and a loss, n/a with neither). Printed for the whole surviving set, for DISCOVERY (closes before the cut: information only, the combination was chosen on that window) and for CONFIRMATION (closes at or after the cut), each at h = 0, 0.01, 0.02. 2c is the primary haircut (C8: the exit can fall in the last 2 minutes), 1c printed. The C7 count test is evaluated on the confirmation set only: 1c PF >= 1.3 with both halves >= 1.0 and 2c PF >= 1.0 (1e-9 slack). Every line: "upper bound, not fill-checked; fee mode per-order rounded".
## Invented windows (close = 3000000 + 900 k; S1 to S3 close before the cut, the rest after; b/a = YES bid / ask close; entry candle ends at close - 420)
| W | entry candle | later candles | result | expected |
|---|---|---|---|---|
| S1 | 0.97 / 0.98 | bids stay above 0.50 | yes | YES p 0.98, held, win |
| S2 | 0.01 / 0.02 (YES ask 0.02 out of band; NO price 0.99 in band) | C-360: 0.02 / 0.03 (NO bid 0.97); C-240: 0.56 / 0.59 (NO bid 0.41) | no | NO p 0.99, SL50 exit at NO bid 0.41 |
| S3 | 0.96 / 0.97 (ask on the edge) | stays high | no | YES p 0.97, held, loss |
| S4 | 0.50 / 0.52 | | yes | skip (band) |
| S5 | only a candle at C-360 | | yes | skip (no candle) |
| S6 | as S1 but one later candle has a null bid | | yes | out whole (incomplete market) |
| S7 | 0.97 / 0.98 | one candle ending at C-30 with 0.50 / 0.52 | yes | YES p 0.98; the C-30 candle is the exit (end at or before close - 30 inclusive; bid 0.50 at or under 0.50 inclusive): sold at 0.50 |
| S8 | 0.97 / 0.98 | one candle ending at C-20 with bid 0.30 | yes | held (a candle ending after close - 30 is not a later candle): win |
| S9 | 0.98 / 0.995 (ask on the top edge, inclusive) | | yes | YES, raw price min(0.995, 0.99) = 0.99, held, win |
| S10 | 0.95 / 1.00 (ask over 0.999) | | yes | skip (bad quote) |
| S11 | 0.86 / 0.98 (spread 0.12) | | yes | skip (bad quote) |
| S12 | 0.97 / 0.98 | | void | excluded (result) |
Plus one KXXRP15M market (ignored).
## Expected, by hand (fee = ceil(70 price (1 - price) - 1e-9) / 100 per leg)
| W | h 0 | 1c | 2c |
|---|---|---|---|
| S1 | price 0.98, fee 0.02: 10 x 0.02 - 0.02 = +0.18 | 0.99, fee 0.01: 0.10 - 0.01 = +0.09 | 0.99 (cap): +0.09 |
| S2 | entry 0.99 fee 0.01; exit 0.41 fee 0.17 (70 x 0.41 x 0.59 = 16.933 -> 17): 10 x (0.41 - 0.99) - 0.01 - 0.17 = -5.98 | entry 0.99; exit 0.40 fee 0.17 (16.8 -> 17): -5.90 - 0.18 = -6.08 | entry 0.99; exit 0.39 fee 0.17 (16.653 -> 17): -6.00 - 0.18 = -6.18 |
| S3 | 0.97 fee 0.03: -9.70 - 0.03 = -9.73 | 0.98 fee 0.02: -9.82 | 0.99 fee 0.01: -9.91 |
| S7 | entry 0.98 fee 0.02; exit 0.50 fee 0.18 (17.5 -> 18): 10 x (0.50 - 0.98) - 0.20 = -5.00 | entry 0.99 fee 0.01; exit 0.49 fee 0.18 (17.493 -> 18): -5.00 - 0.19 = -5.19 | exit 0.48 fee 0.18 (17.472 -> 18): -5.10 - 0.19 = -5.29 |
| S8 | as S1: +0.18 | +0.09 | +0.09 |
| S9 | 0.99 fee 0.01: 0.10 - 0.01 = +0.09 | +0.09 | +0.09 |
Trades 6 (S1, S2, S3, S7, S8, S9; wins 3, SL exits 2, held loss 1). Counts: markets considered 12 + 1 other series; other series 1; excluded result 1 (S12); incomplete market 1 (S6); of the 10 left: trades 6, skip band 1 (S4), no candle 1 (S5), bad quote 2 (S10, S11).
All six: h 0: positives 0.18 + 0.18 + 0.09 = 0.45, negatives 5.98 + 9.73 + 5.00 = 20.71, net -20.26, PF 0.021729; 1c: 0.27, 6.08 + 9.82 + 5.19 = 21.09, net -20.82, PF 0.012802; 2c: 0.27, 6.18 + 9.91 + 5.29 = 21.38, net -21.11, PF 0.012629. Halves floor(6/2) = 3 (S1, S2, S3 | S7, S8, S9): h 0: 0.18 / 15.71 = 0.011458, net -15.53 | 0.27 / 5.00 = 0.054, net -4.73; 1c: 0.09 / 15.90 = 0.005660, net -15.81 | 0.18 / 5.19 = 0.034682, net -5.01; 2c: 0.09 / 16.09 = 0.005594, net -16.00 | 0.18 / 5.29 = 0.034026, net -5.11.
Discovery (S1, S2, S3; n 3): h 0 PF 0.011458 net -15.53; 1c 0.005660, -15.81; 2c 0.005594, -16.00. Its halves floor(3/2) = 1: S1 | S2, S3: h 0 infinite | 0.0 (no win in S2, S3); 1c infinite | 0.0; 2c infinite | 0.0.
Confirmation (S7, S8, S9; n 3): h 0 PF 0.27 / 5.00 = 0.054, net -4.73; 1c 0.034682, -5.01; 2c 0.034026, -5.11. Its halves 1: S7 | S8, S9: h 0 PF 0.0 (S7 loss only), net -5.00 | infinite (net +0.27); 1c 0.0, -5.19 | infinite (+0.18); 2c 0.0, -5.29 | infinite (+0.18).
COUNTS toward the 20 to 30: no.
## Further hand cases
- valid_quote edges: bid 0.001 passes, 0.0009 fails; ask 0.999 passes, 0.9991 fails; ask below bid fails; spread exactly 0.10 passes (slack) and 0.1001 fails.
- The entry candle must end EXACTLY 420 s before the close (a candle at 421 or 419 is not the entry candle: skip, no candle).
- A candle ending after the close is dropped (and counted) before the incomplete-market test, so a null-bid candle ending after the close does not put a market out.
- Exit price floor 0.01: a NO exit with ask close 1.0 (NO bid 0.0) at h = 0.02 prices at 0.01 (unit test on the price function).
- The printout names the extract's raw sha256, the cut, every count and each set's n; no ticker.
