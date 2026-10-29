# CAL result: event calendar and power check (Strategy Research V2, 2026-10-29, research only)

No profit or loss was read or computed. Counts only.

## The calendar

`studies/EVENT_CALENDAR_2026.csv`, 262 rows, 2026-08-01 to 2026-12-31. Columns: event, detail, release_utc, release_ct (US Central), release_et, status, source_url, retrieved (2026-10-29), note. Built by `workers/CAL_build.py` from pages and downloads fetched on 2026-10-29; nothing was written from memory.

**status** means: `verified` = date and time read from an official dated listing; `rule` = date official or from an official recurring rule, but the exact row could not be read on a page (see note); `unverified` = left out of every count.

| Event | Rows | Status | Source |
|---|---|---|---|
| CPI, 8:30 ET | 5 (Aug 12, Sep 11, Oct 14, Nov 10, Dec 10) | verified | bls.gov/schedule/2026/home.htm; past dates cross-checked on the BLS release archive |
| PPI, 8:30 ET | 5 (Aug 13, Sep 10, Oct 15, Nov 13, Dec 15) | verified | same |
| Employment Situation, 8:30 ET | 5 (Aug 7, Sep 4, Oct 2, Nov 6, Dec 4) | verified | same |
| GDP, 8:30 ET | 5 (Aug 26, Sep 30, Oct 29, Nov 25, Dec 23) | verified | bea.gov/news/schedule/full |
| PCE (Personal Income and Outlays), 8:30 ET | 5, same days as GDP | verified | same |
| Advance retail sales, 8:30 ET | 5 (Aug 14, Sep 16, Oct 15, Nov 17, Dec 16) | verified | Census release PDFs (Jul, Aug data) and census.gov/retail/release_schedule.html |
| FOMC statement, 2:00 pm ET | Sep 16, Oct 28 verified; Dec 9 `rule` | | federalreserve.gov statement pages ("For release at 2:00 p.m. EDT"); Dec 9 date from the FOMC calendar, time not stated there |
| Weekly jobless claims, Thu 8:30 ET | 19 `rule`, 3 `unverified` (Nov 26, Dec 24, Dec 31) | | dol.gov answered HTTP 403 to this session, so no row could be read on a DOL page |
| EIA Weekly Petroleum Status Report | 22 | verified | eia.gov schedule page: Wednesday 10:30 ET, holiday weeks Thursday 12:00 ET (Sep 10, Oct 15, Nov 12) |
| Treasury bill auctions (close 11:30 ET) | 72 verified, 7 `rule` | | fiscaldata.treasury.gov auctions_query (closing time given); upcoming_auctions (Oct 26 to 29, no time field) |
| Treasury coupon auctions (close 1:00 pm ET; FRNs 11:30) | 23 verified, 4 `rule` | | same |
| Coinbase, Kraken, Bitstamp scheduled maintenance | 16, 50, 13 | verified | each status page's Statuspage JSON; note says trading/API scope or not |

## Gaps and what could not be verified

- **Jobless claims**: every row is a rule (Thursday 8:30 ET), not a per-date confirmation; dol.gov blocked this session (HTTP 403), and I did not try to get around the block. The three holiday-week Thursdays are `unverified` and excluded. A human can confirm on dol.gov/ui/data.pdf archives.
- **Treasury**: only auctions held through 2026-10-22 (with times) and announced through 2026-10-29 (no time field) exist; November and December auctions are not announced yet. The upcoming feed lists a 2-Year Note on both Oct 26 and Oct 28 and a 5-Year on both Oct 22 and Oct 27; copied as given, not resolved. The completed-auctions feed has no CMB rows in the window.
- **FOMC Dec 9 time** is a rule (2:00 pm ET), not on the calendar page. Press conference times (2:30 pm) are not included.
- **Exchange maintenance**: the status pages return only the last 50 scheduled maintenances, so Kraken is covered only from mid-September (its 50 fill Sep 17 to Nov 10); Coinbase and Bitstamp reach August. Past maintenance that was never posted there is not covered. Most rows are funding, banking or one-asset notices; only rows whose name says system, order entry, website and API, infrastructure, trading halt or database are counted below.
- Not included: ISM, housing, JOLTS, consumer sentiment, Fed speeches, the Treasury refunding announcement, CME holiday hours.
- BEA's GDP and PCE are released together, so their windows are the same windows; claims share 8:30 ET with most monthly releases. `ANY_0830ET` pools every distinct 8:30 ET timestamp.

## Power check (counts only)

Entries: `scalper.tstop1.load()` (6 minute look, side price 0.88 to 0.97), all 26 series in the 15 minute history on file, closes 2026-08-06 to 2026-10-29 20:45Z. A window counts when its close is after the event and at most 30 minutes after it (event < close <= event + 1800 s). Because events fall on :00 or :30 and closes on the 15 minute grid, that is the two windows closing 15 and 30 minutes after the release, and every such entry (close minus 6 minutes) is placed after the release. Live 5 = gold, Bitcoin, Ethereum, Dogecoin, XRP. Rows with status `unverified` and non-trading maintenance are excluded.

| event type | events in data span | events with >=1 entry (days) | entries, all series | entries, live 5 | entry at or after release (all) | per series (all, top) |
|---|---|---|---|---|---|---|
| ANY_0830ET | 23 | 23 | 210 | 66 | 210 | ZEC 18, BNB 18, XRP 17, WTI 15, GOLD 14, BTC 13 |
| CLAIMS | 13 | 13 | 129 | 40 | 129 | XRP 12, ZEC 11, GOLD 10, BNB 10, WTI 10, BTC 9 |
| CPI | 3 | 3 | 20 | 6 | 20 | ZEC 3, WTI 2, DOGE 2, XRP 2, COPPER 2, ETH 1 |
| EIA_WPSR | 12 | 12 | 135 | 43 | 135 | NEAR 11, HYPE 10, GOLD 10, XRP 10, DOGE 9, BNB 8 |
| FOMC | 2 | 2 | 14 | 3 | 14 | COPPER 2, GOLD 2, HYPE 2, XRP 1, NEAR 1, SOL 1 |
| GDP | 3 | 3 | 28 | 9 | 28 | GOLD 4, ZEC 3, USDJPY 3, BNB 2, XRP 2, SOL 2 |
| JOBS | 3 | 3 | 26 | 8 | 26 | BNB 3, NEAR 2, SILVER 2, WTI 2, ETH 2, DOGE 2 |
| MAINT_BITSTAMP | 4 | 4 | 39 | 9 | 39 | COPPER 4, NEAR 4, HYPE 3, PALLADIUM 3, BTC 3, WTI 2 |
| MAINT_COINBASE | 1 | 1 | 2 | 0 | 2 | HYPE 2 |
| MAINT_KRAKEN | 9 | 5 | 67 | 21 | 67 | BTC 5, XRP 5, ZEC 4, DOGE 4, ETH 4, AUDUSD 4 |
| PCE | 3 | 3 | 28 | 9 | 28 | GOLD 4, ZEC 3, USDJPY 3, BNB 2, XRP 2, SOL 2 |
| PPI | 3 | 3 | 22 | 8 | 22 | BTC 3, XRP 3, WTI 2, HYPE 2, ZEC 2, BNB 2 |
| RETAIL | 3 | 3 | 26 | 9 | 26 | DOGE 4, BNB 3, WTI 2, HYPE 2, BTC 2, ETH 2 |
| TSY_BILL | 47 | 45 | 438 | 150 | 438 | BTC 34, XRP 33, BNB 32, DOGE 29, WTI 28, NEAR 28 |
| TSY_COUPON | 27 | 25 | 247 | 85 | 247 | BTC 24, ZEC 20, BNB 19, XRP 18, NEAR 16, GOLD 15 |

powered (>=300 entries on >=30 distinct event days): ['TSY_BILL']

**Reading.** Every macro release type is **underpowered**: CPI 20 entries on 3 days, jobs 26 on 3, PPI 22 on 3, retail 26 on 3, GDP and PCE 28 on 3 (the same windows), FOMC 14 on 2, claims 129 on 13, EIA 135 on 12, all 8:30 ET releases pooled 210 on 23 days, coupon auctions 247 on 25 days. On the live 5 alone none passes 150. At the pooled 8:30 ET rate (about 9 entries per release day, all series) 300 entries on 30 days needs about 33 release days, roughly mid December 2026 on a forward record; on the live 5 alone about 105 days, about a year.

**Only Treasury bill auctions clear the bar** (438 entries on 45 days, live 5: 150). That is close to a time-of-day filter: bill auctions close at 11:30 ET on four or five weekdays a week, so the counted windows are the 11:45 and 12:00 ET closes on most weekdays, inside the 08:00 to 12:00 Central block that MKTTIME1 and HOURS2 already scored. A draft is in `workers/CAL_REL1_DRAFT.md` as the brief required; it is NOT registered, NOT run, and its disclosure says why it is weak.

Files: `studies/EVENT_CALENDAR_2026.csv`, `workers/CAL_build.py`, `workers/CAL_power.py`, this file, `workers/CAL_REL1_DRAFT.md`. Tries: 0 (counts only; nothing scored).
