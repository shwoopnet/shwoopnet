# RV3 registration: perp versus its own reference price, fade the premium (metals, oil, index perps) (written 2026-11-06, before any premium, signal or return was computed)

Discovery only. No live code, no promote verb.

## Mechanism and counterparty
Each perp carries a reference_price (Kalshi's own index of the underlying). When the perp trades well above or below it, funding and any arbitrageur should pull it back. This is the "versus the front-month reference" test (d) of the brief: the recorded reference is the closest public thing to a front-month, no other front-month feed is used. Counterparty: the thin-book trader who pushed the perp away from the reference (gold and WTI are deep; copper and silver thinner). Honest alternative: a premium is a lag or a stale reference (the index perps keep a stale reference when the underlying market is closed), the perp is the market, and the reference follows it; fading it only pays the spread and 0.12% a side.

## Rule (one definition, no tuning)
For each qualified perp (below) with active status, bid > 0, ask > 0 and reference_price > 0: premium q = ln(mid / reference). z = (q - mean) / sd over the trailing 20 snapshots of that perp (at least 12). TRIGGER |z| at least 1.0. z above +1: sell the perp; z below -1: buy it (1 leg only, per $1), entry at that snapshot (bid to sell, ask to buy), exit at the first snapshot at least 4 and at most 8 hours later, no overlap in the same perp. The reference is not tradable, so the trade is a one-leg directional bet on the premium closing; the return is the perp's own move. Control: the same trade with the sign reversed.

## Universe (cost only, recorded spread on development rows, no return used)
Median spread at most 5 basis points: **GOLD (0.26 bp), SILVER (1.86), US 500 (1.0), US TECH 100 (1.12), WTI (3.0), COPPER (4.8)**. Excluded for cost: aluminum 7.8, palladium 7.9, platinum 7.3 (all above 5).

## Numeric prediction (written before)
About 53 development snapshots, about 20 usable per perp after warm-up, about 30% trigger: about 5 trades per perp, **about 25 to 40 in all six**; under the 100 bar. Gross premium reversion over 4 hours about +3 bp or noise; cost 24 bp fees (2 sides x 0.12%) + the spread (0.3 to 5 bp) + funding about 0.3 bp, net about -22 bp. Verdict **NOT_ENOUGH_DATA** (about 95%); if a count were reached, FALSIFIED (about 90%). The most likely nearby surprise is that the index perps' premium is a stale-reference effect that reverts mechanically at the open: that would show as a gross gain on US 500 and Tech 100 that does not survive the fee. Months to 100 trades: about 3 times the present development length, i.e. about **2026-12-20** for a rerun with a new cut.

## Data, split and cut (fixed now)
Source: branch `origin/perp-data`, hourly recorder `perps/perps-<date>.csv` (read per commit with `git show <commit>:perps/<file>`, de-duplicated on (ts, ticker): the files repeat). 73 snapshots from 2026-10-21T16:56Z to 2026-11-06T14:56Z, irregular (2 to 7 hours apart, about 4 a day, not hourly). Fields used: bid, ask, price, reference_price, status. The 30 second open/close recorder (`perps30/`) has NO data anywhere on main, `claude/perps-fast-recorder` or any recorder branch as of 2026-11-06 (`git ls-tree` checked): not used.
**Dates 2026-10-21 to 2026-11-06 are 17 dates. CUT DATE: everything from 2026-11-01T00:00Z on (6 dates, the last third) is HOLDOUT, never read, and the code drops those rows on load.** Development = 2026-10-21 to 2026-10-31 (11 dates, 53 snapshots). D1 = 2026-10-21 to 10-26, D2 = 2026-10-27 to 10-31.
Single-stock and ETF perps (AAPL, NVDA, GOOGL, SPY, QQQ, ...) were `inactive` with bid 0 until 2026-11-05T18:39Z: all their quotes lie in the holdout (counted by metadata only, no price or return read).

## Cost (stated)
Per trade, per leg, per side: cross the recorded spread (buy at ask, sell at bid, both from the recorded rows at entry and exit) plus a **0.12% fee per side** (the PERP1 placeholder; Kalshi perp fees are not recorded and not verified, so this is an assumption stated here) plus funding 0.02% of notional per calendar day held (PERP1 placeholder). Reported also at fees x1.2 and, as information only, the break-even fee per side. Returns are per $1 of each leg.

## Counting and bars (fixed)
Running N before this program about 730,455; deflated z bar about 5.27 (day-clustered z: daily sums of trade returns by entry date, z = mean / (sd / sqrt(days))).
- **NOT_ENOUGH_DATA**: fewer than 100 development trades. Below 100, mean, PF and the gross edge are reported as information and no FALSIFIED is declared.
- **FALSIFIED**: at least 100 development trades and any of: mean net per trade not positive in the whole of development or in either half; PF under 1.5 in either half or the whole; PF under 1.2 at fees x1.2.
- **LEAD**: all of the above pass and day-clustered z at least 5.27. Only then is the holdout read once; PF under 1.5 there is FALSIFIED. A lead gets a capped-probe spec; nothing trades, nothing is deployed.
Duplicate check done: PERP1 to 3 (daily trend, gold/silver ratio on daily Yahoo bars), FUND1 (crypto carry), PERPFLOW1, PERPOI1 (Bitcoin perp open interest), SNAPBACK1, STOCKLAD1 (not runnable). Nobody tested cross-perp relative value or the perp-versus-reference premium on Kalshi perps. Not a duplicate.

## Count
N +12 (six perp rules at +2). Running about 730,471.
