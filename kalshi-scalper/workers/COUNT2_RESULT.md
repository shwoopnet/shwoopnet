# COUNT2 result (run once, 2026-11-03, development only; frozen third untouched)

Registration `workers/COUNT2_REGISTRATION.md` sha256 `b1e19193294ed890893e65dc0beb7ce97c8598a89acd0c2cd8fe25baebf48692` (commit 1ca8abc, pushed before any SPC file or candle was read; code commit 148897b). No amendments. One implementation detail added after the code commit and before the run: six KXTORNADO-25JAN markets have no `floor_strike`, so the strike is the number after "above" in `rules_primary` (`strike_of`, tested). Code `src/scalper/count2.py`, tests `tests/test_count2.py` (7 pass). Cache outside the repo (`/tmp/count2_cache`).

## Candidate table (summary)
Series list searched by settlement-source domain and by title: of about 30 count or threshold series checked, **only KXTORNADO** (39 monthly events, rules name SPC's Preliminary Report Summary, daily CSV archive keyless) met both bars (a) source identical to a keyless dated archive and (b) at least 20 settled events. Nominations (15 events), judges (11), pardons (11), bills (1 to 3), press briefings (3), CBP (9), BLS Chapter 11 (1), CDC H5N1 (2) fail on events, a key or publication lag; endorsements (30 events) and Truflation TSA (38) fail (a) (judged Truth Social posts; Truflation index, not the TSA table); Federal Register EO series have the 3 to 7 day publication lag (COUNT1); no Steam, GitHub, Hugging Face, PyPI, npm, SEC or Wikipedia count series exists. Full table in the registration. Families run: **1**.

## Pace model calibration (before any Kalshi data)
Negative binomial dispersion on 96 year-months of 2015 to 2022 (leave-one-year-out climatology): **r = 1.70** (very clustered: outbreaks). 3,743 SPC daily files fetched, none missing.

## KXTORNADO (rule COUNT2-T): 26 development events, 13 frozen events unread
- Events scored 19 of 26 (7 had markets that opened after the mid-month look). Quotes: about a third of the sides had no valid ask both before and after the look (about 234 of roughly 350 per pass skipped), so the book is thin at mid-month.
- **Trades n = 1** (KXTORNADO-25AUG-100, YES at 5c, model p 22%, lost: net -5.4c). Halves: 0 and 1. PF 0.0 on one trade. No claim.
- Control (every cheap side with ask 3c to 30c): n 6, win 17%, mean -1.7c, PF 0.88.
- Sensitivity r/2 and 2r: still 1 trade each.
- **Source check: the SPC daily-file month total is consistent with every settled market of the event in only 38% (10 of 26) of development months, under the registered 90%: SOURCE_MISMATCH.** All 16 mismatches go the same way: the daily-file sum is HIGHER than the bracket Kalshi paid (for example 2024-12: 167 against a winning bracket of 75 to 100; 2024-05: 648 against 500 to 550; 2025-05: 378 against 325 to 350; ratio 1.1 to 1.9). So Kalshi's "Storm Reports Legend" count is a smaller preliminary tally than the sum of the filtered daily CSVs (probably de-duplicated or cut at an earlier time); the two are not the same number, so the running count at the look is biased high. This is the same failure as COUNT1 with a government archive instead of a tracker.
- Verdict **NOT_ENOUGH_DATA** (1 trade, under 150) plus **SOURCE_MISMATCH**. Nothing to promote; no claim of an edge or of its absence.

## Forward plan
At 12 events a year, a measured take-up of 1 trade in 19 scored events (0.05 per event) is about 0.6 trades a year: 40 trades would take about 60 years. The registered forward freeze is therefore **not worth running**; the cell should be retired rather than carried. If someone wants it again, the work is to find Kalshi's actual tally (the "Preliminary Report Summary" page counts, which are not in the daily CSVs: try the SPC monthly or yearly "torngraph" or the `*_rpts_raw.csv` / preliminary summary at the time of resolution) and re-register, and the book must be thicker than it is mid-month (many markets have no quote).

## Probe spec
Not triggered (n = 1).

## Prediction check
Scored events 14 to 24: 19 (yes). Trades 3 to 25: 1 (no, fewer). Source check passes: predicted 55%, it failed. Verdict NOT_ENOUGH_DATA (97%): yes. N +2.
