# BASERATES1: descriptive base-rate tables (Nov 11, 2026)

Offline. No Kalshi call, no outside host except GovInfo bulk files (FR daily XML, public laws XML). Nothing is scored: no PF, no entry rule, no use of settled EOWEEK prices. Tables are in `workers/baserates1/`; code `extract_gov.py`, `build_a.py`, `build_b.py` (re-run offline from `eo_list.csv`, `plaw_list.csv`, `data/ment1.sqlite`). Weeks are Sunday to Saturday; only complete weeks and months are used.

## A. Politics activity counts
Data: Federal Register EXECORDR, 512 orders, complete (no number gaps): Trump I 13765 to 13984 (220 orders, Jan 2017 to Jan 2021), Trump II 14147 to 14438 (292 orders, Jan 2025 to Oct 22, 2026). Extra pull for this job: FR bulk zips for 2017 to 2020, Jan 2021 and Jan to Apr 2025. Public laws by approved date: 115th and 116th (Trump I, held to Jan 3, 2021), 119th (Trump II, 138 laws to Nov 3, 2026).

| Table | File | Headline (n = weeks or months) |
|---|---|---|
| A1 weekly EO distribution, by period and quarter | A1_eo_weekly_distribution.csv, A1b histogram | Trump II n=90 weeks: mean 2.82, var 8.24 (dispersion 2.9). Since Sep 2025 (the Kalshi era) n=59: mean 1.56, var 1.91 (1.22, near Poisson). 2025 H1 n=31: mean 5.23. Trump I n=208: mean 1.01, var 1.67 (1.64). Quarterly means for Trump II fall 7.6, 4.3, 3.2, 1.2, then 2.2, 1.1, 1.5. The regime moved down, so any pooled Trump II figure overstates today. |
| A2 count so far this week, final weekly count | A2_eo_conditional_final_count.csv | Rows by period, weekday through which k orders were signed, with P(final > N), N=0..12. Since Sep 2025 through Wed: k=0 n=34, mean final 0.94; k=1 n=16, 2.31; k=2 n=6; k=3 n=3. Cells with n<5 are flagged and must not be used. |
| A3 bills per week and month | A3_bills_distribution.csv, A3b by month | Trump II: weekly mean 1.48 (n=92, dispersion 3.25); monthly mean 6.43 (n=21, var 44, dispersion 6.8, median 5, max 26). 2026 months: mean 6.8, median 5.5 (n=10). Trump I monthly mean 15.3, dispersion 33, driven by end-of-Congress bursts (Dec 2018: 129). |
| A4 bills, count so far this month | A4_bills_conditional_final_count.csv | Trump II, by day 1, 8, 15, 22 and k bucket; at most 21 months, most cells n<10. E.g. through day 15: 0 laws (n=4) mean final 0.5; 3 to 5 (n=6) mean 6.3; 6+ (n=4) mean 17.3. |

Reconciliation (A5, from EXECSUM, not re-derived): EO counts reproduce 96 of 96 Kalshi "above N" markets. Public laws by approved date reproduce 90 of 94 bills markets; the 4 misses are KXBILLSCOUNT Mar 2026 (Kalshi 4, public laws 2) and Jul 2026 (Kalshi 0, public laws 2). So the bills tables are public-law counts, not Kalshi's definition, and carry that error in about 2 of 10 months.

Limits: one administration pair, regimes not stationary (empirical tails from Trump I and 2025 H1 do not describe 2026); A2/A4 cells are small beyond k=0 and 1; the last week's EOs may not yet be published, so the final partial week is excluded; bursts (tariff, end-of-Congress) are the overdispersion, which makes P(above N) for high N sensitive to a handful of weeks.

## B. Mention base rates (data/ment1.sqlite, Kalshi settled history already held)
22,188 settled word markets, 1,124 calls (events), 114 series, Feb 2025 to Nov 2026. Word = ticker suffix (a short code, so two different words could share a code). Call = ticker minus the word. 90% intervals are Wilson.

| Table | File | Headline |
|---|---|---|
| B1 YES rate by series, sector | B1_yes_rate_by_series.csv, B1b | All 42.5% (90% CI 42.0 to 43.1, n=22,188). Trump speeches 42.5% (n=10,521, 390 calls); Earnings tech 54.2% (n=950), earnings finance 59.2% (n=228), restaurants 43.5%, other sectors 38 to 44%. Sectors are my hand mapping from ticker names (earnings sector for 54 companies, non-earnings by name). |
| B2 per series and word, n>=8 calls | B2_yes_rate_by_series_word_n8plus.csv | 522 word rows; use with the interval, not the point. |
| B3 call-level share of words YES | B3_call_level_share_yes.csv | 29 series with 5+ calls of 3+ words: the spread of a call's YES share against a binomial with independent words (the gap is the shared call effect). |
| B4 persistence, previous call YES vs NO | B4_word_persistence.csv, B4b streaks, B4c prior-rate bins | Pooled 16,491 consecutive pairs: next call YES 55.9% after YES (n=7,257) vs 32.4% after NO (n=9,234), difference +23.5 pts. Streaks: after 4+ NOs 18.7% (n=2,363), after 4+ YES 70.5% (n=1,222). Words with prior rate 0.9+ say YES next 73.9% (n=491), not 99%: persistence is strong but shrunk. Largest in earnings tech (71.3% vs 23.4%). Mostly word propensity (a fixed topical word), not proof of an exploitable signal. |
| B5 price vs base rate (description only) | B5a markets, B5b by quote bin, B5c by sector | Last two-sided quote at least 1h before close (spread <=0.05) against the word's prior YES rate (earlier calls, 3+ priors, else series rate). Only 235 markets have candles. Gap mean quote minus prior is large and meaningless at the extremes (quotes near 0.01 or 0.99 one hour out are mostly already resolved), small in the middle (n 8 to 14 per bin). No realized outcome column, no scoring. |

Limits: persistence and prior bins use all history in sample (no held-out), words overlap within a call, the 114 series are a hash-chosen subset of listed mention series, B5 candles exist only for the 500 MENT1-chosen markets and 235 qualify.

## Ready to compare against live prices after 22:15Z
- A1/A1b, A2 (Trump II since Sep 2025 rows, k=0 and 1 only) against KXEOWEEK "above N" ladders.
- A3/A3b and A4 against KXBILLSCOUNT, remembering the definition mismatch above.
- B1, B2 (word), B4 and B4c as a prior for a live word market (word persistence plus the word's own rate); B3 for call-level correlation across a call's words.
Not ready: B5 (only a description of old quotes).

## Corrections (Nov 12, 2026, from Desk A's re-check, branch claude/idea-desk-a DESK_A_VERIFY_NOV12.md section 4, c2165e0): counts MATCH, three labels fixed
Desk A reproduced the executive order counts: MATCH on 59 weeks (mean 1.559, variance 1.906), Trump II 2.822, Trump I 1.014, 292 orders without gaps, and the 17 orders Sep to Nov 2026 equal GovInfo's Federal Register bulk files. Fixes:
1. The row labelled "2025 H1" (31 weeks, mean 5.23) is really Jan 26 to Aug 30, 2025. A true first half is 22 weeks, mean 5.82.
2. The inauguration week (Jan 19 to 25, 2025, 38 orders) was EXCLUDED as partial. With it, Trump II is mean 3.21, variance 21.7, not 2.82 and 8.24. Wherever 2.82 / 8.24 appears, read it as "excluding the inauguration week".
3. IMPORTANT for any live use of the "count so far this week" table: GovInfo publication runs 3 to 6 days BEHIND signing, so the latest weeks (Oct 25, Nov 1) show zero orders only because they are unpublished (no order after 14438, signed Oct 22, in any issue through Nov 12). A conditional "count so far this week" table built from GovInfo is BLIND TO THE CURRENT WEEK; it cannot be used live without another count source. Extended to today the mean is 1.52 over 62 weeks.
