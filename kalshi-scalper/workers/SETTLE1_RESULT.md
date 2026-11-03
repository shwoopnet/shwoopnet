# SETTLE1 result (2026-11-03, run once): NOT_ENOUGH_DATA by count, FALSIFIED on every PF line; W3 outcomes never read

Registration `workers/SETTLE1_REGISTRATION.md` (commit bddb529, before any OKX bar met any Kalshi quote); code `src/scalper/settle1.py` (commit 4cb6b67), tests `tests/test_settle1.py`; printout `studies/settle1_result_2026-11-03.txt`. Data: `data/alts3.sqlite` (Kalshi 1 minute candles, 2026-08-06 to 10-13, silver and WTI from 08-06, natural gas from 08-27, platinum and palladium from 09-17) and OKX `history-candles` 1 minute bars for XAG, XPT, XPD, CL and NG perps (cached outside git). Fee 7% x C x p x (1-p) rounded up, C = 10, taker at the next minute's ask, hard limit 0.30, held. N + 10 (5 families x 2 looks).

## Part 1: the rulebook (full table in the registration)
- Every non-crypto family settles on ONE print at the close against ONE print at the open: Pyth 1 minute candle close for FX, silver, copper, platinum, palladium, WTI, natural gas and the 10Y yield (hourly, "no averaging applies"); a single index value at the named minute (3 pm, 10 am, 4 pm) for the S&P and Nasdaq ladders; the exchange settlement price for the daily WTI and gold markets. **Only Bitcoin and Ethereum average (60 s BRTI/ERTI).** So there is no averaging-window mechanism outside crypto, and nothing is published after the close that Kalshi's quotes have not already seen (the Pyth feed is public and continuous). The only rulebook-implied edge left is a quote that lags a public real-time reference.
- Tie rule: the primary text says "at least" (a tie settles YES; 1.1% to 2.7% of FX windows per FXUSD); the FX secondary text says "strictly greater". Not used here.
- Reference availability: OKX perps exist for silver, platinum, palladium, WTI, natural gas (this test), the indices (IDXFUT1) and TLT. **None for copper or any of the five FX pairs** (no spot or perp; Yahoo and Dukascopy 429, Pyth Benchmarks 401 per LAG15): `NOT_RUNNABLE`. Hourly FX and metal ladders, the 10Y hourly yield and the daily range markets were not run (new data pulls, or owned by DAILY2, WTIW1, IDXFUT1).

## Part 2: how often is the implied winner still cheap (no outcome used)
The registered trigger (|z| >= 1 over the remaining 2 or 3 minutes) fired on 61% of market-looks (16,349 of 26,863), not the 15 to 25% I predicted: a typical 12 minute move from the open is many times the remaining-minutes sigma. Share of triggered looks whose implied side was priced at or below 0.30:

| Family | look 180 s | look 120 s | mean price vs mean Phi (180 s) |
|---|---|---|---|
| Silver (XAG) | 0.23% (6 of 2,609) | 1.04% (28 of 2,700) | 0.956 vs 0.955 |
| WTI (CL) | 0.59% (16 of 2,701) | 0.80% (22 of 2,764) | 0.948 vs 0.955 |
| Platinum (XPT) | 2.33% (18 of 771) | 5.61% (35 of 624) | 0.902 vs 0.952 |
| Palladium (XPD) | 3.67% (26 of 709) | 9.18% (57 of 621) | 0.876 vs 0.952 |
| Natural gas (NG) | 4.66% (73 of 1,566) | 7.32% (94 of 1,284) | 0.897 vs 0.953 |

## Part 3: the treated trades (implied side priced 0.05 to 0.30), outcomes on W1 and W2 only
Windows by the 68 dates with a triggered quotable look: W1 23, W2 23, W3 22 (frozen; counts only: 197 treated trades there, no outcome loaded).

| Cut | n | days | win | mean price | PF | mean | day-clustered z |
|---|---|---|---|---|---|---|---|
| W1 | 23 | 13 | 0.174 | 0.150 | 1.10 | +1.44c | +0.16 |
| W2 | 93 | 20 | 0.161 | 0.180 | 0.81 | -2.95c | -0.76 |
| **W1+W2** | **116** | 33 | 0.164 | 0.174 | **0.86** | **-2.08c** | **-0.57** |
| W1+W2 fees x1.2 | 116 | 33 | 0.164 | 0.174 | 0.85 | -2.27c | -0.63 |
| W1+W2 +1c slip | 116 | 33 | 0.164 | 0.174 | 0.80 | -3.12c | -0.86 |
| Control (|z| < 0.25, cheaper side in the band) | 468 | 41 | 0.197 | 0.175 | 1.08 | +1.17c | +0.64 |

Per cell (W1+W2; n is tiny, descriptive only): silver 180 s n 4 PF 1.32, 120 s n 14 PF 1.46; platinum n 2 and 3 (PF 5.04, 2.08); palladium n 3 and 8 (PF 0.00, 0.58); WTI 180 s n 7 PF 4.89, 120 s n 10 PF 1.84; natural gas 180 s n 33 PF 0.80, 120 s n 32 PF 0.14 (win 3.1%, mean -16.14c, z -4.15). Days with a treated trade: silver 13, platinum 3, palladium 2, WTI 14, natural gas 19 (platinum and palladium fail the 8 day rule). (The palladium 180 s z of about -1e16 is a one-day cluster dividing by zero; ignore it.)

## Part 4: is the reference a reference? (calibration of the implied side, all triggered looks on W1+W2 dates)
Silver 3,573 looks: wins 0.956 against Phi 0.959 and price 0.957. WTI 3,641: 0.958 against 0.957 and price 0.951. **The market and the OKX model agree to a tenth of a point.** Natural gas 1,588: 0.905 against Phi 0.957, price 0.902 (the market is right, the perp is off by 5 points). Platinum 204: 0.853 against Phi 0.961 and price 0.874; palladium 213: 0.845 against 0.958 and price 0.858 (the perp is 11 points over-confident and the market is correct). So for silver and WTI the quote already equals a real-time reference (it is the same information); for platinum, palladium and natural gas the cheap implied winners are mostly the reference being wrong (Pyth feed differs from a thin OKX perp), not the maker being slow.

## Verdict
- Pooled W1+W2 treated trades 116 < 150: **NOT_ENOUGH_DATA**. Independently **FALSIFIED** by the registered lines: PF 1.10 (W1) and 0.81 (W2) under 1.5; negative at fees x1.2 (-2.27c); the treated mean (-2.08c) is below the control (+1.17c); and the registered calibration line fires for platinum and palladium (more than 10 points under Phi). No cell has 8 days and a PF over 1.5 in both windows with n over 30.
- W3 never read. No forward registration. **Killed assumption: a real-time public reference for the 15 minute metal and energy markets finds quotes that lag it.** On silver and WTI the quote is the reference; on platinum, palladium and natural gas the cheap-looking prices are real information the OKX perp lacks.
- **Capped-probe spec: none.** Nothing is positive in both windows with a mechanism.
- Prediction check: wrong on the trigger share (61% against 15 to 25%), right on NOT_ENOUGH_DATA, PF below 1 and treated worse than control.

## What this adds to the ledger
Copper and the five FX pairs still have no keyless minute reference from this sandbox (the same gap LAG15 recorded); the only way to test them is a forward recorder of a spot feed (not built, and a prior of 2% does not justify it). The hourly FX and metal ladders (`KXEURUSDH`, `KXWTIH`, `KXSILVERH`, `KXPLATINUMH`) remain untried; silver and WTI quotes equal their reference at 2 to 3 minutes, so a ladder test would need a different mechanism than "the quote lags".
