# RV2 registration: US Tech 100 perp versus US 500 perp spread mean reversion (written 2026-11-06, before any spread, signal or return was computed)

Discovery only. No live code, no promote verb.

## Mechanism and counterparty
The two index perps are the only equity pair with 17 days of quotes. Tech 100 and the S&P 500 share most of their factor; the log spread should be stationary at a few hours if arbitrageurs link the two books. Counterparty: the less liquid index book (Tech 100 has the larger open interest, US 500 is thinner) quoting a lagged price. Honest alternative: the spread is a random walk over 4 hours (tech beta is a real, trending factor), mean reversion is a chart shape, and cost of four legs eats it.

## Rule (one definition, no tuning)
s = ln(mid Tech100) - ln(mid US500), snapshots with both quotes (bid > 0, ask > 0, status active). z = (s - mean) / sd over the trailing 20 snapshots (at least 12). TRIGGER |z| at least 1.0. z above +1: sell Tech 100, buy US 500; z below -1: the reverse. 1 unit (per $1) each leg, entry at that snapshot at ask/bid, exit at the first snapshot at least 4 and at most 8 hours later, no overlap. Control: the same trade with the sign reversed (trend, not reversion), reported beside it.

## Universe (cost only)
Both legs median spread about 1 bp on the development rows, well under the 5 bp limit; US 2000 not added (no hypothesis).

## Numeric prediction (written before)
Development has about 53 snapshots, minus 12 warm-up; about 40 usable, at most about 30 with the 4 hour hold and no overlap, about 30% trigger: **8 to 14 trades**. Gross reversion about +2 bp per trade (between -10 and +15), cost about 50 bp (fees 48 bp + spreads about 4 bp), net about -48 bp, PF near 0. Verdict **NOT_ENOUGH_DATA** (about 99%); if a count were reached, FALSIFIED. Months to 100: about 30 development days of this pair at the present rate means about **2027-01-15** (one rerun, with a new frozen cut).

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
N +2. Running about 730,459.
