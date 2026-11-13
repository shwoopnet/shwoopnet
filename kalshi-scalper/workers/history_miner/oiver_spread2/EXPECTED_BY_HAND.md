# OIVER-SPREAD build 2: rules as read and expected figures by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from Desk A's card 1 only: `kalshi-scalper/workers/DESK_A_OICORE_VERSIONS_NOV13.md` at 741092a7 (sha256 e7b918b0), with the parent rule as the card states it. Desk A's build was not read. No real row read; no real run (queued behind V1).

## Rules as built (the parent is OICORE as the card states it)
1. Inputs, one row a KXBTC15M window: ticker, close_ts, oi_180 (OI of the candle ending close - 180), oi_360 (OI of the candle ending close - 360), yes_bid, yes_ask (the decision candle), result (yes, no or void). A row builder is separate and is audited on its own.
2. Signal: oi_180 - oi_360 >= 86,300. A missing OI value drops the window, counted.
3. Quote: a bid of 0 or an ask of 1 is no quote. A crossed or locked quote (yes bid >= yes ask - 1e-9) is no quote (rule 18). Either way the window is counted and is not traded, by both parent and version.
4. Side: the cheaper ask of YES (yes_ask) and NO (1 - yes_bid); a tie goes to YES.
5. Band: the side's ask in [0.08, 0.50] (1e-9 tolerance). Under 0.08 is cheap_skipped; over 0.50 is out_of_band.
6. Price paid: min(ask + 0.01, 0.50), the limit 1c above the touch and never past the ceiling, booked as the fill.
7. Fee per order of C = 10 contracts: ceil(round(100 x 0.07 x 10 x p x (1 - p), 6)) / 100 dollars, divided by 10 for the per-contract figure.
8. Net per contract: a win is 1 - price - fee; a loss is -price - fee; a void is -fee.
9. VERSION: the parent's trade, kept only if yes_ask - yes_bid <= 0.03 + 1e-9 at the decision candle. Otherwise it is counted as spread_wide.
10. Blocks: development is close < 2026-12-01T00:00:00Z. Held-out rows are ignored and counted in development mode. A held-out read is refused in this build.
11. Printed: the removed share first, then for parent and version: n, PF (sum of wins over the absolute sum of losses), net sum and mean per contract, the halves (signals in close order; the first half is the first floor(n/2)), and net per contract-week (net sum / (span / 604,800 s), where the span is from the first to the last development window in the FILE, the same denominator for both). The 7g takeover check and the card's kills are informational; under 60 version signals the label is "no evidence at n = x".

## Open readings for the Head
- (a) The decision candle is the one ending at close - 120 (the end of OICORE's 180 to 120 s entry span).
- (b) C = 10 for the fee (OICORE's bottom step when the card was written; the ladder now starts at 20).
- (c) The price is booked at the limit (ask + 1c), not the touch.
- (d) The tie goes to YES.
- (e) The halves split by signal count.
- (f) The contract-week denominator is the file's development span.
- (g) The 86,300 threshold is inclusive.

## Made-up windows (inv/windows.csv), close = 1794000000 + 900 k for window k (W10 closes 2026-12-02)
| W | rise | bid | ask | side, ask | spread | parent | version | result | net |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 90,000 | 0.20 | 0.22 | YES 0.22 | 0.02 | trade, price 0.23, fee 12.397c -> 13c/10 = 0.013 | keep | yes | +0.757 |
| 2 | 100,000 | 0.70 | 0.75 | NO 0.30 | 0.05 | trade, price 0.31, fee 14.973c -> 0.015 | spread_wide | yes | -0.325 |
| 3 | 86,300 | 0.88 | 0.90 | NO 0.12 | 0.02 | trade, price 0.13, fee 7.917c -> 0.008 | keep | no | +0.862 |
| 4 | 86,299 | 0.30 | 0.32 | | | oi_below | | no | |
| 5 | 120,000 | 0.03 | 0.06 | YES 0.06 | | cheap_skipped | | no | |
| 6 | 95,000 | 0.40 | 0.40 | | | no_quote (locked) | | yes | |
| 7 | 95,000 | 0 | 0.30 | | | no_quote (no bid) | | no | |
| 8 | 90,000 | 0.45 | 0.49 | YES 0.49 | 0.04 | trade, price 0.50, fee 17.5c -> 0.018 | spread_wide | no | -0.518 |
| 9 | 90,000 | 0.69 | 0.72 | NO 0.31 | 0.03 | trade, price 0.32, fee 15.232c -> 0.016 | keep | yes | -0.336 |
| 10 | 90,000 | 0.20 | 0.22 | | | held_out_ignored | | yes | |

**Parent:** n 5, wins 1.619, losses 1.179, PF 1.373198, net 0.440, mean 0.088.
- Halves: W1 and W2 give PF 2.329231 (0.757 / 0.325). W3, W8 and W9 give PF 1.009368 (0.862 / 0.854).

**Version:** n 3, wins 1.619, losses 0.336, PF 4.818452, net 1.283, mean 0.427667.
- Halves: W1 gives PF inf. W3 and W9 give PF 2.565476.

**Removed share:** 2 / 5 = 0.4.

**Per contract-week:** the span is W1 to W9 = 7,200 s, so the factor is 84. Parent 36.96, version 107.772.

**Counts:** signal 7 (W1, 2, 3, 5, 6, 7, 8, 9 less W5 cheap... see list); exactly: oi_below 1, cheap_skipped 1, no_quote 2, held_out_ignored 1, parent traded 5, version spread_wide 2, version traded 3.

**Takeover check (info):** PF +3.445 >= 0.10 yes; net per week not lower, yes; second half not worse, yes; 60 signals, no. Label: "no evidence at n = 3".

**Kills (info):** removed more than half, no; PF below the parent's, no.

## Refusals expected
- a held mode run
- a HELDOUT_ path
- a result other than yes, no or void on a development row

## Dated line, 2026-11-13 19:53Z: the Head's convention for both builds (matching live OICORE on main), reworked by hand before the code
- (a) The decision quote is the candle ending close - 180 s (yes_bid and yes_ask in the input are that candle's; the row builder must take them from there). oi_rise = OI(close - 180) - OI(close - 360), unchanged.
- (b) C = 20, OICORE's current bottom step (PR 901), with the fee rounded up per order at C = 20.
- (c) The price is the ASK SEEN, with no +1c (PR 895), assumed filled at that ask as a taker at the touch, with no next-candle fill check. This is an UPPER BOUND on fills.
- (d) A tie goes to YES. (e) Halves split by signal count, the first floor(n/2). (f) As read. (g) The threshold is inclusive (>= 86,300), the floor is ask >= 0.08 and the ceiling ask <= 0.50.

Reworked figures (same windows; spreads, sides and skips unchanged). Fee = ceil(round(100 x 0.07 x 20 x p x (1 - p), 6)) / 100 / 20:
| W | side, price | order fee | per contract | result | net |
|---|---|---|---|---|---|
| 1 | YES 0.22 | 24.024c -> 25c | 0.0125 | yes, win | +0.7675 |
| 2 | NO 0.30 | 29.4c -> 30c | 0.015 | yes, loss | -0.315 |
| 3 | NO 0.12 | 14.784c -> 15c | 0.0075 | no, win | +0.8725 |
| 8 | YES 0.49 | 34.986c -> 35c | 0.0175 | no, loss | -0.5075 |
| 9 | NO 0.31 | 29.946c -> 30c | 0.015 | yes, loss | -0.325 |
**Parent:** n 5, wins 1.64, losses 1.1475, PF 1.429194, net 0.4925, mean 0.0985.
- Halves: W1 and W2 give PF 2.436508 (0.7675 / 0.315). W3, W8 and W9 give PF 1.048048 (0.8725 / 0.8325).
- Per contract-week: 0.4925 x 84 = 41.37.

**Version:** n 3, PF 5.046154 (1.64 / 0.325), net 1.315, mean 0.438333.
- Halves: W1 gives PF inf. W3 and W9 give PF 2.684615.
- Per contract-week: 110.46.

**Unchanged:** the removed share 0.4, the counts, the takeover and kill information, and the label "no evidence at n = 3".

## Dated line, 2026-11-13 21:17Z: the governing card is Desk A's 23b5bd9b (DESK_A_OICORE_VERSIONS_NOV13.md, sha256 ae1f1ee6...); reworked by hand before the code
- Rule 18 is named "not two-sided" as on the card (0 < bid, ask < 1, bid < ask with 1e-9): the counter no_quote is renamed not_two_sided; the logic is unchanged.
- **Weeks** = (last close - first close) / 7 days over the PARENT's trades, at least one week, and the same divisor for both. Here the parent runs W1 to W9 = 7,200 s, under a week, so the divisor is 1 week: per contract-week parent 0.4925, version 1.315 (was 41.37 and 110.46 on the file span).
- **Range:** a development row (close before 2026-12-01) outside [2026-09-12T00:00Z, 2026-11-09T00:00Z) STOPS the run. Held-out rows (on or after Dec 1) are still ignored and counted. Every made-up development row is inside.
- Every other figure is unchanged: parent PF 1.429194, version PF 5.046154, the halves, removed 0.4, the takeover and kill information (net per week still not lower), and the label.

## Dated line, 2026-11-13 21:30Z: voids (Auditor B's 16b finding of 21:28Z; Desk A's sheet v2 G5; the Head's ruling of 21:29Z), reworked by hand before the code
- Results "yes" and "no" are scored.
- "void" or blank on a development row is DROPPED: it is not a bet, not in n, not in the PF. It is counted as void_dropped, at the point where the parent would have traded. This means after every signal test (and, for DEPTH, after the replay-set test), before the trade is booked.
- Any other text still STOPS.
- Before this line a void was booked as a fee-only loss and a blank stopped the run; both are withdrawn.
- **Base figures:** unchanged, since the made-up development rows carry no void or blank.
- **New variant test:** the base windows plus two rows, W11 and W12, closing 1794009000 and 1794009900, both inside the range. The variant must give every base figure unchanged, plus counts void_dropped 2.
  - W11: a copy of W1 (a signal that passes the spread), result "void".
  - W12: a copy of W3 (passes), result blank.

## Dated line, 2026-11-13 21:32Z: void drop at LOAD (Auditor B, 21:31Z: Desk A's load_windows drops a result that is not yes or no before any signal test)
- A development row whose result is "void" or blank is dropped when the file is read, counted as void_dropped, and never reaches any other count (no_oi, oi_below, not_two_sided, band, and so on).
- Held-out rows are still ignored first and counted as held_out_ignored; any other text still STOPS.
- The variant adds W13, a copy of W4 (OI rise 86,299, so oi_below if it were read) with result "void".
- Expected variant counts: the base counts with void_dropped 3. oi_below stays 1, the base W4 alone. Every figure is unchanged.
