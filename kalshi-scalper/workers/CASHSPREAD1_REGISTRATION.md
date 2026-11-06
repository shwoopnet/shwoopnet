# CASHSPREAD1 registration: when is the cost of trading Kalshi's index, metal and energy perps lowest around the US cash session (written 2026-11-06, before any spread statistic was computed)

Discovery only. No live code, no promote verb. Part of the cash open and cash close mechanism family (sibling tests CASHOPEN1, CASHCLOSE1, CASHGAP1).

## Mechanism and counterparty
A perp's quoted spread is the price of the market maker's risk: it should be narrowest while the cash tape the maker hedges against is liquid (09:30 to 16:00 New York) and widest overnight, and widest again in the first minutes after the 09:30 open when the opening auction imbalance is being digested. Counterparty to a taker who crosses the spread: the market maker. Honest alternative: the maker quotes a fixed tick-sized spread all day, so there is no cycle and the cost is the same at any hour.

## Data and what was already read (disclosed)
Hourly recorder, branch origin/perp-data, one commit per sample (73 samples, 2026-10-21 to 2026-11-06, about 4 a day at irregular times). Schema: ts_utc, ticker, asset_class, status, bid, ask, bid_size, ask_size, price, reference_price, marks, open_interest, volume_24h. BEFORE registering I read only counts of rows by date, asset class and status (not any bid, ask or spread value): single-stock equity perps are `inactive` (bid 0) in every sample before 2026-11-03 and quote only inside US hours after that. So the Equities class has no dev-window book and is NOT tested here on hourly data.
**Held-out third: all hourly dates on or after 2026-11-01 are never read** (17 recorded dates, cut = last 6). Development dates 2026-10-21 to 2026-10-31. Halves: D1 2026-10-21 to 2026-10-26, D2 2026-10-27 to 2026-10-31.

## Part A (runnable now, hourly data)
Universe, on observability and not on any outcome: asset classes Indices, Metals and Energy; a perp is used if its status is `active` with bid and ask above 0 in at least 90% of the dev snapshots. Spread s = (ask - bid) / mid in basis points. Buckets by New York clock: MID = Monday to Friday 10:30 to 15:30; OFF = everything else (nights, weekends). Statistic: for each perp the median s in MID and in OFF, ratio R = MID/OFF, then the median of R over perps; also the same for the Indices class alone (SPY, QQQ, US Tech 100). Day clustering: a snapshot's cluster is its New York date; the readout is the median ratio with a bootstrap by date. Bar for a bucket: at least 15 snapshots per half.
**Prediction (before computing):** median R about 0.8 to 1.0 for Indices (spread already near a minimum tick, little cycle), metals about 1.0; LEAD 25%, FALSIFIED 50%, NOT_ENOUGH_DATA 25%.
**Verdict rules:** LEAD (a cost fact, not a trade) if the Indices R is at most 0.75 in both halves; FALSIFIED if the Indices R is above 0.90 in either half; NOT_ENOUGH_DATA if any bucket holds under 15 snapshots in a half; otherwise INCONCLUSIVE reported as such.

## Part B (needs the 30 second recorder, perps30/)
Universe: the Equities and Indices perps with a median spread of 25 bps or less in 09:30 to 10:30 across the dev files (a cost rule; chosen before any return), at most 15 cheapest. Per perp-day: median s in the first 5 minutes after 09:30 (EARLY) against the median s from 09:50 to 10:30 (SETTLED); also 15:40 to 15:55 against 16:05 to 16:30 on close files. LEAD if EARLY/SETTLED is at least 1.5 on at least 75% of dev perp-days in both halves; FALSIFIED if under 1.2 in either half. Bar: at least 12 dev trading days. Cut: **perps30 files dated on or after 2026-12-01 are never read** (last third of the 24 trading days that the stop date plus a reviewed extension would give; the cut is fixed now). NOT_ENOUGH_DATA today: no perps30 file exists on origin/perp-data as of 2026-11-06 16:00 UTC (the open window has already passed; first expected 2026-11-09 if the workflow starts).
**Read date for Part B: 2026-12-01** (dev days 2026-11-06 to 2026-11-30, 15 or 16 days, after the Nov 30 close file lands). The recorder's STOP_DATE is 2026-12-07 (21 trading days); 24 days would need the stop date moved by a reviewed edit and reaches the 24th open day on 2026-12-10.

## Count
N +1 (descriptive cost test; Parts A and B are one rule). Running count before: about 730,455; after: about 730,456 (z bar about 5.27; the coordinator keeps the total).
