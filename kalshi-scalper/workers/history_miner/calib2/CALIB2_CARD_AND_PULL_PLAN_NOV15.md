# CALIB2: the CALIB1 calibration census for the rest of Kalshi, card and pull plan (History Miner, 2026-11-15 ~16:40Z; the Head's brief of 16:08Z). NO PULL: Main runs pulls only on the Head's go.

**Sources read for this card (counts and labels only, no price or result):**
- Desk C's all-Kalshi census (claude/idea-desk-c 441feae6, CENSUS_NOV15.md);
- Desk B's census tables (claude/idea-desk-b, workers/census/families.csv and first_cut_series.csv: 60 day settled counts per series, many capped at 300 or 1,000);
- Forensics' DATA_INVENTORY_TABLE_NOV14.md.

**What it is:** CALIB1's table and candidate rule on other families. It is descriptive: no try is counted until a rule card is registered from it.

## 1. Window, thirds, cuts (constants)
- **Window:** markets CLOSING from 2026-09-14T00:00Z (the first day the batched live candle endpoint covers; older closes need one historical request per market, too dear) to before 2026-11-09T00:00Z.
- **Thirds:** third 1 = 09-14 to 10-03; third 2 = 10-03 to 10-22; third 3 (held-out, read once) = 10-22 to 11-09. The same constants for every family.
- **Third 3 is never listed:** the listing jobs use max_close_ts = 2026-10-21T23:59:59Z, so no result after third 2 is even fetched until a rule card is registered.
- **Held-out exclusions, before any listing:**
  - FEDIMPL1: every Fed series (KXFED, KXFEDDECISION and kin) is OUT entirely (its held-out runs from 2025-09-17).
  - **Unreleased holds** (RND_QUEUE releases of Nov 13): CAL1 finance and indices, ECON1, POLENT1, POLI2, COUNT1 hold windows in finance, indices, economics, politics, entertainment and counts. Until Auditor B gives each one's dates from Desk A's registry, every series those cards name is OUT.
  - POLGAPH (politics, held-out from 2026-11-05) is after the window, so no change.
  - Released, so usable: W-CAT-SPORTS1 (27 sports series), W-CAT-CAL1 weather.
  - **Rule:** for each series, the window ends at the EARLIER of 2026-11-09 and the start of any OPEN card's held-out on it. Auditor B confirms the per-series list (a dated line here) BEFORE any listing job is written.
- **Hosts:** only Kalshi's public API (api.elections.kalshi.com, GET only, no key), through the existing kalshi-pull runner. No score site, no banned host.
- **Closed families:** weather daily temperature is CLOSED (three falsified). It is measured for information only; a candidate there would need the owner to lift the closure before any rule card.

## 2. Families, looks and priority (counts are Desk B's 60 day settled, lower bounds where capped)

| Tier | Family (series) | 60 day markets | Looks before the close | Why this tier |
|---|---|---|---|---|
| A | Gas and diesel daily and weekly (55) | about 41,000 | 24 h, 1 h, 10 min | largest pool; many series share one close each day, so candles batch well |
| A | Commodity, FX and index ladders (27: KXGOLDD, KXSILVERD, KXCOPPERD, KXNATGASD, ..., KXINX, KXNASDAQ100, KXDJI, the FX AD ladders) | about 17,700 | 24 h, 1 h, 10 min | many strikes share one close |
| A | Soccer, smaller leagues (52) | 19,600 or more | 24 h, 1 h, 10 min | large; markets of a game share a close. **Excluded if Auditor B finds an OPEN SOCDERIV or SOCCER-family hold** |
| B | Tennis (8), NFL props (20), NFL periods (17), NHL and NBA/MLS periods (15), international basketball (10), soccer extras (11), soccer major (12), US game winners (5) | about 44,000 or more in all | 24 h, 1 h, 10 min (game markets list about 1 to 3 days before) | large pooled; per-game grouping |
| B | Weather daily temperature (48, CLOSED family: information only) | 17,200 | 24 h, 1 h, 10 min | |
| C | Music and video charts (6), streaming (7), mentions (3), approval and ballot (2), post counts (2), rates (7), power demand, Truflation, quake, AI share, cricket, NASCAR, MLB and NHL props, volleyball, minor hockey | a few hundred to 2,000 each | 24 h, 1 h, 10 min (for charts and streaming, also 3 days) | too small to reach 300 a bucket a third except pooled; listed so the table is complete |
| OUT | Esports and virtual sports (about 950 events a day) | thousands | none | one close per map, so no batching: 3 looks x about 35,000 events is over 100,000 requests. VIRT1 and ESPORT1 already FALSIFIED. Proposed out of CALIB2 |
| OUT | Fed series (FEDIMPL1), and any series of an unreleased hold (above) | | | held-out |

- **Looks, fixed:** the candle ending exactly 24 h, 1 h and 10 min before the market's close. 1 minute candles, both sides, two-sided only, 5c buckets, exactly as CALIB1.
- **A market that opened less than 24 h before its close has no 24 h row**, counted "not open". Charts and streaming also get a 3 day look (a fourth look, stated now).

## 3. Candidate rule, statistics and print (identical to CALIB1, with its Amendments 1 and 2)
- n >= 300 in third 1 AND third 2, gap >= mean fee + 2c in each, the same sign. Neighbours are printed. buckets_inspected and expected_chance_candidates_null are printed.
- **Pools:** each series, each family (the table's family label), and each tier.
- **Fee:** the taker fee 0.07 x p(1 - p) per contract, rounded per order at 1 contract. Series whose fee schedule differs (Kalshi lists maker fees on some, and the S&P ladders a lower rate) are FLAGGED in the print, from the listing's own fee fields if present, else "fee schedule not checked". A candidate on a flagged series is re-read at its own fee before any rule card.

## 4. Pull plan (sized for Main; 12 requests a minute shared; every job file under 470 requests)

**Stage 1, listings (results of thirds 1 and 2 only):**
- One GET /markets?series_ticker=S&status=settled&min_close_ts=1789344000&max_close_ts=1792627199&limit=1000 per series, following the cursor.
- Pages: about 1 per 1,000 markets, at least 1 per series.
- Tier A: about 82 series and 59,000 markets over thirds 1 and 2 (2/3 of 56/60 of the 60 day counts), so about 82 + 59 = **about 141 requests: 1 file**.
- Tier B: about 145 series and 41,000 or more markets, so **about 190 requests: 1 file**.
- Tier C: about 50 series, **about 60 requests: 1 file**.
- **About 390 requests, 3 files, about 33 minutes at 12 a minute.**
- The listing answer carries the result field. It is fetched only for closes before 2026-10-22 (thirds 1 and 2) and read only by the CALIB2 reader after Auditor B's CLEAN.

**Stage 2, candles (written OFFLINE from the stage 1 listings, never by hand):**
- For each distinct close time and each look: one batched GET /markets/candlesticks?market_tickers=...&start_ts=L-120&end_ts=L&period_interval=1, at most 100 tickers per request (2 window minutes x 100 = 200, far under the 10,000 limit).
- Estimate: requests = 3 looks x the sum over distinct close times of ceil(markets sharing it / 100).
  - Tier A: daily ladders and gas close once a day per group; about 37 days x about 70 groups x 3, so **about 7,800 requests (17 files)**.
  - Tier B: about 300 games a day x 37 days x 3, so **about 33,000 requests (71 files)**. Tier B is therefore proposed as a SECOND pull, decided after Tier A's table.
  - Tier C: about 2,000 (5 files).
- **Proposed first go: stage 1 for all tiers (3 files) and stage 2 for Tier A only (about 17 files, about 11 hours at 12 a minute).**
- **These are estimates from lower-bound counts.** The stage 2 builder prints the exact request and file counts from the listings before anything is dispatched, for the Head's go.

## 5. Gates
- Auditor B: the per-series held-out list (dated line in section 1) before stage 1 is written; then the job files; then the reader's code and hand case before the read.
- The Head's go before each stage. Main dispatches.
- The table is committed blind; figures by message. No try is counted by the table itself.
