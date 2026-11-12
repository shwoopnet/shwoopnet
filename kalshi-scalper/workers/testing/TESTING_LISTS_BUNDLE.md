# TESTING_LISTS_BUNDLE: one run for four of the Testing Desk's small jobs (Testing Desk, Nov 12, 2026; revised 17:50Z at the Head's change)

Built at the Head's request because the runner allows 12 real runs a UTC day (all used for Nov 12) and fourteen jobs wait. **Revised: SOCDERIV_LISTS is OUT of the bundle and is its own job again** (the Head, 17:44Z: a size stop cost a second run this morning). `kalshi_pull_jobs/TESTING_LISTS_BUNDLE.json` (built by `bundle.py build`) passes `python3 -I scripts/kalshi_pull.py TESTING_LISTS_BUNDLE --dry-run`. Owner MAIN. Public market data only; nothing closing on or after any held-out constant is requested (TIE3 2026-11-13T00:00Z; POL-i2 2026-11-05T00:00Z); no rule scored, no try.

## Contents (request ids carry the sub-job prefix, so each manifest row says where it belongs)

| Prefix | Sub-job | Requests | Pages at most | What |
|---|---|---|---|---|
| `t3_` | TIE3_LISTS | 32 | 88 | settled lists of the 20 period series (8 also on `/historical`), 4 fee-field reads |
| `wx_` | WXDAYEND_A | 22 | 22 | **18 one-market candle windows (the registered finishing count of card 74, already approved) and 4 settled lists**; the only candle requests in the bundle |
| `ur_` | UNRATE_LISTS | 4 | 8 | settled lists of KXU3 and KXUE, live and historical |
| `p2_` | POLI2_LISTS | 79 | 237 | one live settled list per Politics series with daily, weekly or monthly frequency |
| | **Total** | **137** | **355** | job cap 369 (355 pages plus 14 for 429 retries; the runner counts pages against the cap) |

**SOCDERIV_LISTS stays separate:** 67 requests, 131 pages at most, cap 140, as originally built.

Order is the Head's scoring order, so a size stop would fall on the last sub-job (POL-i2).

## Size, restated

- **Theoretical worst case** (every one of the 355 pages a full 1,000-market page at about 2.1 MB, the census measure): about 745 MB, which the 200 MB cap would cut. It cannot happen in practice: a second page is requested only when the first is full, and the markets simply are not there.
- **Expected, from the census listing's own counts** (I replaced my first guess for POL-i2, which was too high): the 79 Politics series are mostly weekly series with about 8 to 9 markets an event and daily series with 1 to 9; only 9 of the 79 settled anything on Nov 10. Roughly 4,000 to 8,000 markets over the window: **POL-i2 about 10 to 20 MB**. TIE3: NHL about 3,000 markets, NFL about 1,400, twelve soccer first-half series about 3,000: **about 15 to 25 MB**. UNRATE under 2 MB, WXDAYEND under 2 MB. **Bundle total about 30 to 50 MB, so under 100 MB.** The two heavier sub-jobs are TIE3 and POL-i2, about equal; neither is above 25 MB on my estimate. These are estimates from counts, not measured, and could be off by a factor of two (still under the 200 MB cap).
- Time: 137 requests to 355 pages at one a second is under 6 minutes.

## After the bundle lands: `bundle.py split <landed run folder> <out dir>`

Writes `<out>/<SUB_JOB>/manifest.json` plus the answer files, with the ORIGINAL request ids and the sub-job's own job definition, so every existing reader works unchanged. It prints a report: per sub-job expected requests, answered, failed (with status), missing ids and a state (COMPLETE, PARTIAL, NOT RUN), the bundle status and bytes, and any row whose id is not in the job (never merged). One sub-job's failure never blocks reading the others. Tested on a synthetic bundle (`test_bundle.py`): a 429 row, a missing row, a size stop cutting the last 20 requests, a foreign id.

**Scoring order, each within the hour the bundle lands** (`OUT` = the split folder):
1. TIE3 lists: `python3 -W ignore kalshi-scalper/workers/testing/tie3.py events $OUT/TIE3_LISTS`; confirm that a game shares its ticker suffix across series and tell the Head at once if it fails.
2. WXDAYEND count: `wxdayend.py score $OUT/WXDAYEND_A`, then `build-b $OUT/WXDAYEND_A` (4 requests).
3. UNRATE count: `unrateround.py events $OUT/UNRATE_LISTS`.
4. POL-i2 stage 1: `poli2_count.py build-s2 $OUT/POLI2_LISTS` builds the stage 2 job and reports the markets dropped by the 400 cap; the kill (fewer than 40 qualifying gaps per half) is applied after the candles.
SOCDERIV's own lists run: `socderiv.py games <its folder>`.
Candle stages for TIE3, POL-i2, UNRATE and SOCDERIV wait for the Head's go.

## Known limits

- The union of the four sub-jobs' allowed endpoints is wider than any one of them (`/markets` accepts the union of their parameters); each request still has to match its own path, and each sub-job's tickers and series are in the allowlists. Security-relevant like every job file.
- The splitter reports what the manifest says; a failed answer is reported, not retried.
