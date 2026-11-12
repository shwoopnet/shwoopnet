# S6, S8, S9: one page for the Head (Nov 12, 2026). Effect sizes and market structure recalled from memory and UNVERIFIED; arithmetic mine; costs ASSUMED. No data pulled, spend $0.

Bar arithmetic: PF 1.5 needs net mean/sd about 0.162 per event (n = 1,141 at z 5.46; 255 at z 2.58). Net d of 0.05 is PF about 1.06 to 1.13.

## Free estimates recorded today (get_cost, historical-streaming)
| Item | Estimate |
|---|---|
| ARCX.PILLAR ohlcv-1m SPY, 2018-05-01 to 2026-11-12 | $1.152 |
| ARCX statistics SPY, 2026-08-27 (the 771.10 assertion) | $0.000003 |
| ARCX trades SPY, 2026-08-27 19:59-20:02Z (fallback for the print) | $0.0027 |
| ARCX trades SPY, full day 2026-08-27 | $0.0230 |
| XNAS.ITCH imbalance, 20 names, 1 year | $4.427 |
| XNAS.ITCH imbalance, 20 names, one day full / 15:45-16:05 ET slice | $0.0176 / $0.0130 |
| XNAS.ITCH imbalance, 20 names, one day, 9:25-9:31 ET (opening cross) | $0.0046 |
Slicing to the closing window saves only about a quarter (most imbalance messages are in the last minutes anyway); the one-year closing figure stays about $3.3 to $4.4 for 20 Nasdaq names. NYSE imbalance for 20 names, 1 year, was $9.86 (predecessor's estimate, not re-run today).

## S6 Leveraged-ETF rebalance, last 30 minutes (SPY)
(1) Arithmetic. Forced flow = sum over leveraged and inverse funds of AUM x L(L-1) x the day's return (3x: 6, 2x: 2, -1x: 2, -2x: 6, -3x: 12). If the S&P-linked and Nasdaq-linked funds together hold a few tens of billions of dollars of AUM, a 1% day forces roughly $0.3 to $0.6 billion of buying or selling at the close (guess; the order of magnitude is from the Cheng and Madhavan 2009 style estimate and is not measured). The last 30 minutes of S&P cash equities trades tens of billions, so the flow is about 1 to 2% of that volume. A square-root impact rule (impact about daily sd x sqrt(flow/volume) x 0.5) gives about 5 to 12 bp, but the flow is predictable from 15:00 and arbitrageurs front-run it, so the observed afternoon continuation is probably 1 to 5 bp on 1%-move days. Last-30-minute SPY sd on such days is about 25 to 35 bp. Gross d about 0.03 to 0.15; after 1.2 bp cost net d about 0.0 to 0.12, PF about 1.0 to 1.15. Chance of PF 1.5 in three windows: about 1 to 2 percent, and only if the rebalance effect is at the top of my guess.
(2) Events: about 40 qualifying days a year at a 1% threshold (estimate), about 300 in 7.5 years; at a 2% threshold fewer than 100. With n about 300 a verdict can only be "no evidence at n = 300", or a LEAD (z 2.58 needs d 0.15 at n 300). It cannot be a pass.
(3) Pulls: ARCX 1-minute SPY $1.152 (SPY alone); official close from the pilot assertion ($0.000003 for the SPY day; whole pilot $0.30).
(4) Recommendation: cannot clear 1.5 by arithmetic. If the Head wants one measurement of the forced-flow story for $1.15 it is cheap, but it is a measurement, not a candidate for the bar. My call: efficient, move on, unless the Head wants the $1.15 curiosity read.

## S8 Closing auction imbalance, provide liquidity
(1) Arithmetic. Published imbalance data exists (Nasdaq and NYSE close imbalance feeds from 15:50 ET). Per-event effect for a large imbalance (more than 5% of average daily volume) could be 10 to 30 bp on the close print for that name with partial reversal at the next open (Bogousslavsky and Muravyev 2023 style findings, recalled, not verified). Overnight sd of a single large name about 60 to 100 bp, so d about 0.1 to 0.3 per event gross at the upper end, minus about 3 to 6 bp costs. That arithmetic is the best of the three, but two structural problems are known from memory and need verification before any money: (a) at NYSE, market-on-close and limit-on-close entries stop at about 15:50 except orders that offset the published imbalance, and at Nasdaq entry stops about 15:55, so a participant who first sees the 15:50 message may be unable to place the registered limit-on-close trade at the official close at all (if true, S8 as registered is blocked by mechanics); (b) the side that is paid for absorbing the imbalance is exactly what exchange liquidity providers and designated market makers compete on, so edge per event is likely already arbitraged to the cost of a retail-size order. Chance of clearing 1.5: about 3 to 5 percent, mostly the part I cannot rule out (a mid-size effect on thin names).
(2) Events: imbalance above 5% of ADV is rare, my guess 1 to 2% of name-days: about 50 to 100 events a year for 20 names. $25 buys about 3 years of 20 Nasdaq names only if NYSE is skipped ($4.43 a year), so about 150 to 300 events. A verdict can support "no evidence at n = x" or a LEAD at best; a pass needs 1,141 events, about 4 times more data than the cap can buy.
(3) Pulls: XNAS.ITCH imbalance for 20 names, 1 year, $4.427 (3 years about $13); plus daily statistics for the same names ($0.08); NYSE doubles it. Needs the pilot assertion first (price definition).
(4) Recommendation: test only if the Head accepts a LEAD-only outcome; first verify the order-entry cutoffs on the exchange rule pages (free). If a cutoff makes the registered trade impossible, S8 is "blocked by mechanics" and we move on. I would do the free cutoff check before spending anything.

## S9 Opening cross imbalance
(1) Arithmetic. Nasdaq publishes opening-cross imbalance information from 9:25 ET and opening-only orders can be entered until about 9:28, so the registered trade is mechanically possible on Nasdaq names (NYSE less clear). Opening auction prices partly revert in the first half hour; observed per-event reversal for the largest imbalances might be 3 to 10 bp against a 30-minute sd of about 30 to 50 bp, so gross d about 0.1 to 0.2 at the top end, net of 3 to 6 bp costs about 0.0 to 0.1. PF about 1.0 to 1.2. Chance of 1.5 in three windows: about 1 to 3 percent.
(2) Events: a large opening imbalance is also a few percent of name-days; about 100 a year for 20 names; the opening window for 20 names, one year, costs about $1.2 (0.0046 x 252) plus 1-minute bars. Verdict: "no evidence at n = x" or a LEAD at best.
(3) Pulls: XNAS imbalance 9:25 to 9:31 ET for 20 names, about $1.2 a year; 1-minute bars for the 30-minute exit about $2 for 20 names (estimate first).
(4) Recommendation: efficient, move on. It is mechanically feasible but the effect per event is small against assumed costs and it rides the same pilot.

## Overall
None of S6, S8, S9 clears PF 1.5 by arithmetic at the effect sizes I recall; S8 has the largest per-event effect and the most to lose from the structural facts above. Honest answer for the owner: the stocks search found no card that could pass the bar at a price within the $25 cap. The cheapest worthwhile thing left is the free order-entry cutoff check for S8 and the $0.30 pilot only if S8 or S6 is kept. Recommended spend now: $0.
