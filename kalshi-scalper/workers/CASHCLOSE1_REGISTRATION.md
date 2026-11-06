# CASHCLOSE1 registration: the last 20 minutes drift into the 16:00 New York close (written 2026-11-06, before any perps30 file or Yahoo bar of this study was read)

Discovery only. No live code, no promote verb.

## Mechanism and counterparty
Index and ETF rebalancing, leveraged-ETF rebalancing and market-on-close orders are placed with a known direction late in the day and cluster in the last 20 minutes; the day's direction so far (intraday momentum, the first-to-last-half-hour result in the literature) should continue into the close. Counterparty: liquidity providers and discretionary traders who fade the day's move into the close. Honest alternative: the effect is a few basis points, smaller than the perp's 12 bps a side fee plus its spread, so it exists and cannot be bought.

## Data (not yet existing)
perps30/<date>/close.csv.gz, 15:40 to 17:00 New York, 30 second samples. None exists on origin/perp-data as of 2026-11-06 16:00 UTC. Cash reference: Yahoo 5 minute bars (60 day retention, so one fetch at the read date is enough): last 5 minute close at or before 15:39 and the previous session's close. Half days (2026-11-27) have no valid close file and are excluded.

## Rule (fixed)
Universe on cost: Equities and Indices perps whose median relative spread across dev close files in 15:40 to 15:59 is at most 25 bps; 15 cheapest; mapped as in CASHOPEN1. Signal: day return so far d = cash(15:39) / previous close - 1, direction = sign(d), no threshold. Trade the perp: entry at the first active sample at or after 15:40:00 (ask for a long, bid for a short), exit at the first active sample at or after 15:59:30 (bid for a long, ask for a short). One trade per perp-day. Cost = the recorded crossing plus 12 bps a side fee (x1.0 and x1.2). Control: always long, same entry and exit. A day where the perp is inactive is skipped and counted.

## Windows and cut
Dev close files 2026-11-06 to 2026-11-30 (15 files with Nov 27 excluded); **files on or after 2026-12-01 are held out and never read**. Halves: first 8 and last 7 dev files. z day clustered.

## Numeric prediction
About 120 to 200 trades; gross +1 to +3 bps (the effect is small and on the order of the noise of one 20 minute move), net -25 to -35 bps, PF 0.05 to 0.4. FALSIFIED 80%, NOT_ENOUGH_DATA 19%, LEAD 1%.

## Verdict rules
NOT_ENOUGH_DATA: under 150 dev trades or under 12 dev trading days (the date it reaches 150 at the observed rate is reported). FALSIFIED: with 150 or more trades, PF under 1.5 in either half, net per trade not above 0 in both halves, PF under 1.2 at fees x1.2, momentum minus the always-long control not positive in both halves, or day clustered z under 5.27. LEAD only if all pass, then the held-out files are read once.
**Read date: 2026-12-01.** With 10 to 12 qualifying perps the 150 trade bar is reached around 2026-12-01 to 2026-12-08 depending on the universe size; reported at read time.

## Count
N +1 (running about 730,455 before; about 730,458 after the three tests so far; the coordinator keeps the total).
