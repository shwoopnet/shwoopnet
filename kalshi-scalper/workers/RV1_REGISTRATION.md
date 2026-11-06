# RV1 registration: stock-perp relative value (index vs member basket, ETF vs index, same-sector pairs) (written 2026-11-06, before any spread, signal or return was computed)

Discovery only. No live code, no functions/, no index.html, no promote verb.

## Mechanism and counterparty
Thinly traded single-stock perps drift from the index perp and from each other while arbitrageurs are scarce; the spread mean-reverts as funding and the few arbitrageurs pull it back. Counterparty: the thin-book trader on the leg that moved. Honest alternative: the legs are fairly priced to each other, any gap is noise or stale quotes, and 0.12% a side on two or more legs is the loss.

## Registered tries (all one rule form, nothing tuned)
(a) US Tech 100 perp versus an EQUAL-weight basket of recorded member perps (AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, COST, NFLX, AMD, ADBE, CSCO, QCOM, AMGN, TXN, INTC, MU, AMAT, PLTR, PEP, BKNG, PANW; free public index weights were not used); (b) SPY perp vs US 500 perp and QQQ perp vs US Tech 100 perp (ETF vs index basis); (c) six fixed same-sector pairs: GOOGL/META, NVDA/AMD, AAPL/MSFT, XOM/CVX, JPM/BAC, KO/PEP.
Signal for each spread s = ln(mid A) - ln(mid B) (basket: ln of the equal-weight average of member mids, scaled by a constant fitted on the first 12 development snapshots only): z = (s - mean) / sd over the trailing 20 snapshots (at least 12). Trigger |z| at least 1.0. Trade: sell the rich leg, buy the cheap leg, 1 unit each, enter at that snapshot, exit at the first snapshot at least 4 hours and at most 8 hours later, no overlapping trade in the same spread.

## Universe (cost only)
A leg qualifies only if its recorded median spread over development snapshots is at most 5 basis points; no return is used. 

## Numeric prediction (written before)
Stock perp quotes exist only from 2026-11-05T18:39Z, all inside the holdout. Development trades: **0**. Verdict **NOT_ENOUGH_DATA** (about 99%). If the history were long enough: gross reversion per 4 hours of 1 to 4 bp against a round-trip cost of about 50 bp (four legs fee 0.48% plus spread), FALSIFIED.
Enough data: needs 100 development trades. At about 4 snapshots a day and about 30% of snapshots triggering per spread, about 100 trades across the nine spreads needs roughly 30 to 40 development days of stock quotes, i.e. about **2026-12-20** at the present irregular recorder rate (about 2027-01-15 if the cut also moves so a third stays held out); rerun then with a new frozen cut. If the 30 second recorder starts writing, 4 hour holds still need the hourly file.

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
N +2 (registered, nothing scored; STOCKLAD1 precedent). Running about 730,457.
