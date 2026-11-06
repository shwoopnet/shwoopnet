# EVM4 registration (2026-11-06): the other underlyings (S&P 500, Nasdaq 100, gold, oil) perp versus RECDAILY ladders, and cost comparison (N +0)

Written before any pairing or price comparison was computed. Discovery only. This is a registration of what the recorded data can and cannot answer, with a census of availability only (counts and times, no price, no outcome).

**Mechanism.** Same as EVM1 to EVM3 for KXUS500PERP / KXUSTECH100PERP / KXGOLDPERP / KXWTIFUTURE against the RECDAILY ladders KXINX, KXNASDAQ100, KXGOLDD, KXWTI (listed in `workers/RECDAILY_WATCHLIST.json`, STRESSDAY1 entries added Nov 4). Tests: (a) lead-lag, (b) implied level minus perp as a 1 hour predictor after cost, (c) cheap side after the perp moved through the strike, (d) event spread versus perp spread (a cost table, no verdict).
**Universe on cost:** only a perp with a recorded spread of at most 10 bp of mid at the pairing time; no return used.

**Data census at registration.** Perp sampled hourly on `origin/perp-data` (3 to 5 samples a day, 2026-10-21 to 2026-11-06; 88 markets each), 30 second `perps30/<date>/<open|close>.csv.gz`: **absent on origin/main and every recorder branch at 2026-11-06**. RECDAILY quotes on `origin/quote-data`: 11 snapshot files from 2026-11-04 01:37 to 2026-11-06 11:27 UTC (hours apart, not every 30 minutes); index ladders (KXINX, KXNASDAQ100) appear only from the 2026-11-05 09:48 UTC snapshot; the nearest perp sample is 8 minutes from the 2026-11-05 02:20 snapshot (no index ladder in it) and 31 to 210 minutes from all others. Also the perp price unit is not dollars (US500 reads 13.47) and the conversion to the index level is not recorded. So no pair, no lead-lag and no next-hour move exists.

**Held out third.** Overlap dates 2026-11-04, 11-05, 11-06: the last third (2026-11-06 onward) is not read; cut 2026-11-05.

**Numeric prediction.** Verdict NOT_ENOUGH_DATA for (a), (b), (c); (d) deferred. After the 30 second recorder runs (first file expected 2026-11-06 close window, 15:40 to 17:00 New York) about 40 pairs a day per underlying inside the two windows, so 100 pairs per underlying by about 2026-11-10; but a lead-lag or next-hour test needs at least 20 trading days to have day-level clusters.

**Kill criteria / read date.**
- NOT_ENOUGH_DATA until at least 100 paired snapshots (a perp sample within 5 minutes of a ladder poll with at least 5 quoted strikes) per underlying AND at least 20 distinct dates, expected on or after **2026-12-07** if the 30 second recorder and RECDAILY run on schedule.
- Then: same bars as EVM2 (PF at least 1.5 each half, x1.2, trigger minus control, z at least 5.27 or the then running deflated bar) and EVM3. Unregistered tests are not read.
N +0.
