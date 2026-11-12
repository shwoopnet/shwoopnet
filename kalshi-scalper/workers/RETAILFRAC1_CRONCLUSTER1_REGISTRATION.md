# RETAILFRAC1 stage A and CRONCLUSTER1 stage A: registration (Nov 12, 2026)

Written and committed BEFORE any tape, book or coverage file was loaded. Source protocol: `IDEA_DESK_A_PROTOCOLS.md` P3 and P4 (branch `claude/idea-desk-a`), followed as written. Zero Kalshi API calls; held data only (`origin/quote-data:book15r6/`, every date and HHMM folder present at run time, extracted into a scratch dir, never committed).

Frozen-window key (`DATA_INVENTORY.md`): F11 says windows closing after 2026-10-30 00:00Z are the GEN5 forward set, read automatically through the candidate file. Stage A loads NO outcome column, no price path to settlement and no P&L; it is a flow-composition and timing census, so it does not read the forward result. The `result` column of coverage is used only as a presence flag (non-empty or not) to apply the protocol's window filter, and is dropped immediately; its value is never tabulated.

## P3 stage A rules (verbatim in substance)
- Window filter: coverage row has a result (presence only), `tape_sum_count` within 1% of `volume_fp` (the sum of tape `count_fp` per ticker vs `volume_fp`), `max_gap_ms` under 10,000.
- `frac(trade)`: `count_fp` differs from its nearest integer by more than 0.001. Signed YES-direction size: +count_fp if `taker_outcome_side=='yes'` else -count_fp. T = `close_time`.
- Per series and overall: (1) share of trades and of contracts that are fractional; (2) median and p90 size of each class; (3) fractional share of contracts by minutes to close (15 one-minute buckets) and by UTC 4 hour block; (4) YES share of each class's contracts, and mean price paid for the side bought, by class (price paid = yes_price if taker side yes else 1 - yes_price); (5) per-window correlation between net fractional flow and net whole flow over (T-600 s, T-360 s], summarised per series (mean and median of the per-window Pearson... defined as the Pearson correlation ACROSS windows of the two nets; windows with no trade of either class count as 0).
- KILL (CLOSED, 1 try): fractional share of contracts under 2% or over 98% in EVERY series, or item 5 above +0.8 in EVERY series.
- Stage B thresholds (`f_min`, `w_min`, development median of |net flow| over (T-600,T-360], development = closing before 2026-11-08 00:00Z) would be fixed by stage A, but stage B is NOT run here. Stage B is justified only if stage A shows two clearly different crowds (my operational reading, fixed now: kill gate does not fire AND item-5 correlation is below +0.5 in at least 3 of 5 series AND the fractional share is between 5% and 95% in at least 3 series AND the two classes differ in size, p90 ratio of at least 3 or YES-share gap of at least 5 points). If met, I register stage B in a separate commit and report to the parent before running it.

## P4 stage A rules
1. Contracts taken by second of the minute (0 to 59 of `created_time`, UTC), per series and per minutes-to-close bucket. `peak = (contracts in seconds 0 to 9) / (total x 10/60)`. Interval: 1,000 bootstrap resamples of whole windows (fixed seed 20261112), 2.5th to 97.5th percentile.
2. From the book: for every minute boundary inside a window, size at each side's best ask and spread at the last snapshot in seconds 52 to 59, against the first snapshot in seconds 8 to 15. (YES ask = 1 - no_bid_px_1, size = no_bid_sz_1; NO ask = 1 - yes_bid_px_1, size = yes_bid_sz_1; spread = 1 - yes_bid_px_1 - no_bid_px_1.) Ratio = mean after / mean before, per series, with the window bootstrap interval.
3. Report `peak` and depth ratio for gold at 6 to 7 minutes to close and Bitcoin at 2 to 3 minutes, beside all-window figures.
- Reading: FINDING only if `peak` >= 1.3 with an interval clear of 1 AND touch depth lower after the boundary than before. Anything less: "no cluster", closed. No try is counted.

## Ledger count
Tests added to the shared ledger (about 1,100,000, z about 5.34; lenient N 8,795, z about 4.39): P4 stage A adds 0 (measurement). P3 stage A adds 1 only if its kill gate fires and closes the card; otherwise 0 until stage B. Stage B, if ever run, adds exactly 1 (the pooled five-series line); that moves neither bar at the shown precision (z 5.34 and 4.39 both unchanged to two decimals).

## One pass
The script writes a marker file; a second scored run refuses. Results are appended below.

---
# Results (one pass, run Nov 12, 2026)

Script `RETAILFRAC1_CRONCLUSTER1_stageA.py`, full output `RETAILFRAC1_CRONCLUSTER1_stageA.json`. Data: all 74 hour folders of `book15r6` (Oct 29 to Nov 11), 296 files. One crash before any output (a timestamp-format error in the parser, no result produced); fixed the parser and ran once. Windows kept by the protocol filter: BTC 956 of 956, ETH 955 of 956, XRP 959 of 961, DOGE 975 of 976, gold 627 of 629. Joined-late windows kept (stage A).

## P3 stage A
| Series | Trades whole / frac | Frac share of trades | Frac share of contracts | Median size whole / frac | p90 whole / frac | YES share whole / frac | Mean price paid whole / frac | corr(net frac, net whole), (T-600,T-360] |
|---|---|---|---|---|---|---|---|---|
| Bitcoin | 9.42M / 30.02M | 76.1% | 65.5% | 19 / 9.1 | 263 / 134 | .501 / .509 | .530 / .409 | +0.63 |
| Ethereum | 2.25M / 2.58M | 53.4% | 50.9% | 10 / 8.3 | 125 / 96 | .505 / .520 | .525 / .390 | +0.27 |
| XRP | 1.68M / 1.72M | 50.5% | 53.5% | 7 / 8.6 | 99 / 92 | .508 / .515 | .495 / .364 | +0.55 |
| Dogecoin | 1.38M / 1.05M | 43.1% | 51.0% | 7 / 8.6 | 50 / 62 | .505 / .513 | .503 / .376 | +0.26 |
| Gold | 1.23M / 3.09M | 71.5% | 64.0% | 17 / 11.9 | 250 / 126 | .500 / .520 | .556 / .410 | +0.38 |

Fractional share of contracts by minutes to close (bucket 14 down to 0, in the json) is flat at 45% to 65% with a higher share in the first and last minute (Bitcoin 75% in the last-minute bucket; the json lists all 15). By UTC 4 hour block the share moves by under 8 points (lowest 08:00 to 12:00 UTC in every series).

Kill gate (CLOSED if fractional share under 2% or over 98% in every series, or correlation above +0.8 in every series): did NOT fire (shares 43% to 76%; highest correlation +0.63).

Two-crowds reading (fixed above before the run): correlation below +0.5 in 3 of 5 series (ETH, DOGE, gold) PASSES; fractional share 5% to 95% in all 5 PASSES; classes differ by p90 size ratio of 3 or more OR YES-share gap of 5 points or more: best p90 ratio 1.96 (Bitcoin), largest YES gap 2.0 points (gold): FAILS. Under the rule as registered, the two classes are not "clearly different crowds" by size or direction. One difference does stand out and was not in the rule: fractional takers pay on average 12 to 14 cents less per contract for the side they buy (0.36 to 0.41 against 0.50 to 0.56), i.e. they buy the cheaper side more often. That is descriptive only; no outcome was read, so it says nothing about who wins.

## P4 stage A (CRONCLUSTER1)
| Series | peak, all windows (95% interval) | peak, 6 to 7 min to close | peak, 2 to 3 min to close | touch depth after / before, all (95%) | 6 to 7 min | 2 to 3 min |
|---|---|---|---|---|---|---|
| Bitcoin | 1.01 (0.995 to 1.02) | 1.04 (1.01 to 1.07) | 0.87 (0.84 to 0.90) | 1.13 (1.09 to 1.16) | 0.98 (0.95 to 1.01) | 1.16 (0.97 to 1.35) |
| Ethereum | 1.03 (1.01 to 1.05) | 1.10 (1.05 to 1.16) | 0.98 (0.94 to 1.03) | 1.08 (1.06 to 1.11) | 1.03 (0.99 to 1.07) | 1.21 (1.10 to 1.34) |
| XRP | 1.03 (1.01 to 1.05) | 1.21 (1.16 to 1.27) | 1.10 (1.04 to 1.16) | 1.09 (1.06 to 1.13) | 1.04 (0.96 to 1.12) | 1.20 (1.07 to 1.35) |
| Dogecoin | 1.05 (1.02 to 1.07) | 1.17 (1.11 to 1.24) | 1.13 (1.07 to 1.20) | 1.10 (1.06 to 1.13) | 1.04 (0.94 to 1.14) | 1.44 (1.25 to 1.67) |
| Gold | 0.97 (0.95 to 0.99) | 1.11 (1.06 to 1.17) | 0.80 (0.75 to 0.86) | 0.96 (0.93 to 0.99) | 1.03 (0.98 to 1.11) | 0.95 (0.87 to 1.07) |

Spread at the touch is the same before and after the boundary (for example Bitcoin 0.0077 against 0.0076). Boundary pairs: 8,394 (gold) to 12,690 (Dogecoin).

Gate (FINDING needs peak 1.3 or more with an interval clear of 1, AND touch depth lower after the boundary): did NOT fire. Gold at 6 to 7 minutes (where L1 buys) has peak 1.11 (interval clear of 1 but far under 1.3) and depth after slightly higher (1.03, interval includes 1). Bitcoin at 2 to 3 minutes (OICORE) has peak 0.87, below 1. Only the last-minute bucket and the first seconds of Ethereum, XRP and Dogecoin lean early (second 0 alone is 1.2 to 1.3 times flat) but the 0 to 9 second window does not reach 1.3. Verdict: NO CLUSTER, closed, no try counted. No send-time candidate for Refinement.

## Verdicts
- P3 stage A: kill gate did not fire; the registered two-crowds rule is not met (classes look alike in size and direction, they differ in price paid). Stage B is NOT justified under the rule as registered; no stage B was registered or run. Ledger count unchanged (0 tests added). The card stays open at Idea; whether the 12 to 14 cent price-paid gap is a reason to spend a family-budget try is a call for the parent, not made here.
- P4 stage A: NO CLUSTER (closed, 0 tries).

## Rulings (Nov 12, 2026, 00:15Z, from main): both cards CLOSED
RETAILFRAC1: closed as NO TWO CROWDS; stage B was not run (the registered two-crowds rule failed, and a stage B try would be +1 in the ledger; the flow family already has FLOW1 and TAPEFLOW1 falsified). CRONCLUSTER1: closed as NO CLUSTER. DESCRIPTION ONLY (not a signal): fractional takers pay less for the side they buy (CORRECTED Nov 12 by Desk A: the 12 to 14 cents is contract-weighted; per TRADE the difference is 4 to 7 cents); the most likely reading is composition (small dollar-typed orders buy cheaper contracts, the known longshot lean), not a second signal.

## RETIRED (Nov 12, 2026, POWER2 + main): RETAILFRAC1 stage B retired: not justified (no two crowds); CRONCLUSTER1 closed as NO CLUSTER.

## Correction (Nov 12, 2026, Desk A via main)
The "fractional takers pay 12 to 14 cents less" figure is CONTRACT-WEIGHTED; per trade it is 4 to 7 cents. Description only; composition, not a signal.
