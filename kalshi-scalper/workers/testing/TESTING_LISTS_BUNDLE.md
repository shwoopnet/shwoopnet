# TESTING_LISTS_BUNDLE: one run for the Testing Desk's five small jobs (Testing Desk, Nov 12, 2026)

Built at the Head's request (17:42Z) because the runner allows 12 real runs a UTC day (all used for Nov 12) and fourteen jobs wait. `kalshi_pull_jobs/TESTING_LISTS_BUNDLE.json` (built by `bundle.py build`, 53 KB, passes `python3 -I scripts/kalshi_pull.py TESTING_LISTS_BUNDLE --dry-run`). Owner field MAIN. Public market data only, nothing closing on or after any held-out constant is requested (TIE3 and SOCDERIV 2026-11-13T00:00Z; POL-i2 2026-11-05T00:00Z), no rule scored, no try. **Main drops the five separate files from PR 826 when this arrives.**

## Contents (request ids carry the sub-job prefix, so each manifest row says where it belongs)

| Prefix | Sub-job | Requests | Pages at most | What |
|---|---|---|---|---|
| `t3_` | TIE3_LISTS | 32 | 88 | settled lists of the 20 period series (8 also on `/historical`), 4 fee-field reads |
| `wx_` | WXDAYEND_A | 22 | 22 | **18 one-market candle windows (the registered finishing count of card 74, already approved) and 4 settled lists**; these are the only candle requests in the bundle |
| `ur_` | UNRATE_LISTS | 4 | 8 | settled lists of KXU3 and KXUE, live and historical |
| `p2_` | POLI2_LISTS | 79 | 237 | one live settled list per Politics series with daily, weekly or monthly frequency |
| `sd_` | SOCDERIV_LISTS | 67 | 131 | 64 league series lists and 3 fee-field reads |
| | **Total** | **204** (the Head said about 208) | **486** | job cap 500 (486 pages plus 14 for 429 retries; the runner counts pages against the cap) |

Order is the Head's scoring order, so if the 200 MB stop ever bites it falls on the LAST sub-job (SOCDERIV), not on the others. **Time:** 204 requests to 486 pages at one a second is under 9 minutes (limit 40). **Limits:** 204 requests of the 1,200 a run; job file 53 KB of 2 MB.

## Size, said plainly (the page caps and the 200 MB run cap)

If every one of the 486 pages were a full 1,000-market page at about 2.1 MB (Desk B's census measured 2.0 to 2.2 MB per full page) that is about **1.0 GB, five times the run cap**; it cannot all be stored. My expectation is far lower because most series list well under 1,000 settled markets in this window: TIE3 about 12,000 markets (about 25 MB), POL-i2 about 10,000 to 25,000 (20 to 50 MB), SOCDERIV about 35,000 (about 75 MB), WXDAYEND under 1 MB, UNRATE under 2 MB: **about 120 to 150 MB in all, so the 200 MB stop is a real risk and my estimate is uncertain by a factor of two.** If it stops (status `stopped_size`) the runner keeps what it stored; the splitter reports exactly which request ids are missing, and only the last sub-jobs are cut. A rerun of the missing sub-job alone then needs one more run.

## After the bundle lands: `bundle.py split <landed run folder> <out dir>`

Writes `<out>/<SUB_JOB>/manifest.json` plus the answer files, with the ORIGINAL request ids and the sub-job's own job definition, so every existing reader works unchanged. It prints a report: per sub-job expected requests, answered, failed (with status) and missing ids, a state (COMPLETE, PARTIAL, NOT RUN), the bundle status and bytes, and any row whose id is not in the job (never merged into a sub-job). One sub-job's failure never blocks reading the others. Tested on a synthetic bundle: a 429 row, a missing row, a size stop that cuts the last 20 requests, and a foreign id (`test_bundle.py`).

**Scoring order, each within the hour the bundle lands** (commands from the repo root, `OUT` = the split folder):
1. TIE3 lists: `python3 -W ignore kalshi-scalper/workers/testing/tie3.py events $OUT/TIE3_LISTS`; confirm the ticker-suffix assumption (a game shares its suffix across series) and tell the Head at once if it fails.
2. WXDAYEND count: `python3 -W ignore kalshi-scalper/workers/testing/wxdayend.py score $OUT/WXDAYEND_A`, then build WXDAYEND_B (`build-b $OUT/WXDAYEND_A`, 4 requests).
3. UNRATE count: `python3 -W ignore kalshi-scalper/workers/testing/unrateround.py events $OUT/UNRATE_LISTS`.
4. POL-i2 stage 1: count the qualifying gaps needs candles, so stage 1 is the market lists only: `python3 -W ignore kalshi-scalper/workers/testing/poli2_count.py build-s2 $OUT/POLI2_LISTS` (builds the stage 2 job and reports markets dropped by the 400 cap); the kill (fewer than 40 qualifying gaps per half) is applied after the candles.
5. SOCDERIV lists: `python3 -W ignore kalshi-scalper/workers/testing/socderiv.py games $OUT/SOCDERIV_LISTS` (sampled games, guards, counts) and the candle estimate for the Head's 300 line.
Candle stages for TIE3, POL-i2, UNRATE and SOCDERIV still wait for the Head's go.

## Known limits

- The union of the five sub-jobs' allowed endpoints is wider than any one of them (`/markets` accepts the union of their parameters); each request still has to match its own path and values, and each sub-job's tickers and series are in the allowlists, so the bundle asks for nothing a sub-job did not. The file is security-relevant like every job file.
- The splitter can only report what the manifest says; a failed answer is reported, not retried.
