# CHART1 result (2026-11-02)

Verdict: NOT_RUNNABLE for the backtest. No outcome or PnL was computed. Window: none. n: 0 trades. Cost: fee 7% x p x (1-p) rounded up, taker (not applied, nothing scored). N: +2, running about 728,700 (z bar about 5.27).

Why: the signal is the daily top 10 rank. Netflix Tudum publishes weekly files (all-weeks-global.tsv, reachable, settlement truth only) and shows only the current day for daily ranks; FlixPatrol returns HTTP 403 from the sandbox and the Wayback Machine did not answer; kworb Spotify keeps only the current day (dated URLs 404). Billboard/Spotify leg: same obstacle, so not run. Registration (workers/CHART1_REGISTRATION.md, commit d9f8ff9) predates this check.

Built: src/scalper/chart1.py (rule and fee only), tests/test_chart1.py (synthetic, passes).

FORWARD registration stands: recorder of 5 lines in the registration (daily 23:30 UTC rank CSV for Netflix and Spotify lists plus Kalshi weekly rank quotes to the quote-data branch). Not built. Earliest information look 2026-12-14 (6 weeks); earliest honest verdict about 2027-05-03 (150 trades).
