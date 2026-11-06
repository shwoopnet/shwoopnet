# CMD1 result (2026-11-06): NOT_ENOUGH_DATA (development only; held-out sessions 2026-11-04 and 11-05 never loaded)

Registration `workers/CMD1_REGISTRATION.md`, shared rules `workers/CMD_COMMON.md` (commit 7bc9f8c). Code `workers/cmd/cmd.py`, full print `workers/cmd/cmd_output.txt`. Six pairs, development sessions Fri 2026-10-30, Mon 11-02, Tue 11-03 (three clusters; D1 = 10-30, D2 = 11-02 and 11-03). Times in the output are ET (CT is one hour earlier).

**Verdict word: NOT_ENOUGH_DATA.** Minimums are 60 trades on 15 session clusters; there are 3 clusters. R1 primary has 48 trades, R2 primary 146. Enough on a development cut at about **2026-12-04** (15 sessions, then the then-last third held out).

**Alignment (CMD0).** Convention (futures at T = Yahoo bar starting T-60) confirmed: 15 of 18 (pair x event) argmax minutes coincide at shift 0 (shift -1: 0, shift +1: 1). The three scheduled events were PCE Fri 10-30 08:30 ET and two 10:00 ET releases (11-02, 11-03). No shift applied.

**Lag profile.** Lag 0 return correlation perp versus futures: gold 0.968, silver 0.961, copper 0.866, WTI 0.967, US 500 0.990, Tech 100 0.990 (cash ^GSPC 0.979, ^NDX 0.963 in cash hours). Lead statistic corr(futures T-1, perp T) minus corr(perp T-1, futures T): gold +0.008, silver -0.008, copper +0.045, WTI +0.019 (D1 +0.162, D2 -0.010), US 500 +0.006, Tech 100 +0.005. Pairs at or above 0.03: 1 of 6 pooled (D1 2, D2 1). **Prediction missed: the perp does not visibly lag the futures at one minute** (copper only, D1 +0.052, D2 +0.043, thin spread-wide pair); cash indices show no lead either way (+-0.03).

**Trades (pooled, net of the recorded bid/ask, fee 12 bp a side unless stated).**
| rule | trades | gross after spread | break-even fee/side | net 5 bp | net 12 bp | net 24 bp | D1 n / net12 | D2 n / net12 |
|---|---|---|---|---|---|---|---|---|
| R1 H=5 | 91 | -1.99 bp | -0.99 | -12.0 | -26.0 | -50.0 | 29 / -24.1 | 62 / -26.9 |
| **R1 H=15 (primary)** | 48 | +1.05 | 0.53 | -8.9 | -22.9 | -46.9 | 14 / -24.5 | 34 / -22.3 |
| R1 H=30 | 30 | +0.71 | 0.35 | -9.3 | -23.3 | -47.3 | 8 / -20.5 | 22 / -24.3 |
| R2 H=1 | 175 | -1.28 | -0.64 | -11.3 | -25.3 | -49.3 | 53 / -25.9 | 122 / -25.0 |
| **R2 H=5 (primary)** | 146 | -1.28 | -0.64 | -11.3 | -25.3 | -49.3 | 40 / -22.1 | 106 / -26.5 |
| R2 H=15 | 112 | +4.64 | 2.32 | -5.4 | -19.4 | -43.4 | 31 / -19.7 | 81 / -19.2 |
Predictions: R1 gross +0 to +4 (hit, +1.05), R1 break-even 0 to 2 (hit), net at 12 about -22 to -26 (hit, -22.9); R2 gross +0 to +3 (missed: -1.28), net -22 to -25 (-25.3, edge of range). Per-session net at 12 bp is negative in every session and every cell; a day z over three clusters is not meaningful and is not claimed. No trade cell reaches even the 5 bp fee. Roll or bad-tick exclusions: 3 flagged minutes, all at the Friday 17:00 ET close bar (CMD3); R1 skipped 3 to 7 for no exit quote or flags and 1 pair above 100 bp.

**Disclosure.** The Kalshi fetch ended at 2026-11-04T00:00Z, which includes the first hour (23:00Z to 24:00Z on 11-03) of the held-out CME session 11-04; those rows are excluded by session date in the loader and were never used. No other held-out data was fetched.

N +6 as registered. No lead. Research only.
