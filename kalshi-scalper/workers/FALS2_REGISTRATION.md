# FALS2 registration: falsifier for RISK1 (the account risk estimate under the current live rules)

Worker FALS2, Strategy Research V2, 2026-10-29. Research only. Written and pushed **before** any of my own simulation or tally was run. `src/scalper/risk1.py` is NOT read until my own version below has produced its numbers; after that it is read only for the look-ahead audit (e) and to explain differences. Nothing here changes a live rule.

**Under attack.** `workers/RISK1_REGISTRATION.md` and `workers/RISK1_RESULT.md`: per-market history at 1 contract (gold PF 1.22, +0.98 / +1.48 / +0.20 / +1.22 c a contract ALL / T1 / T2 / T3; Dogecoin PF 0.91; Ethereum smooth 62 entries, PF 2.33), and the bootstrap ($528: 30 d median +$99, p5 -$16, 7.9% below start, stop at least once 1.8%; 90 d median +$330, p5 +$103, 0.5% below start, 5.5% stop; $1,028: 30 d +$200 / -$9 / 5.9% / 1.0%; 90 d +$670 / +$246 / 0.3% / 2.6%). This is a risk estimate for a real-money deposit, so the job is to find where it is too kind.

## Live rules, read by me from `origin/main` `functions/kalshiLiveLib.js` (2026-10-29), not from RISK1

- Tradable: `L1_SERIES` minus `PAUSED_SERIES` = gold, Dogecoin, Ethereum, tried in that order. All at the 6 minute look (`entryLead`, 330 to 400 s left); history: the candle with `end_ts == close_ts - 360` exactly, missing means no entry.
- `l1Pick`: `validQuote` (bid >= 0.001, ask <= 0.999, ask >= bid, spread <= 0.10) on the YES bid and ask; YES if round4(ask) in [0.88, 0.97] (1e-9 tolerance), else NO if round4(1 - bid) in band. Limit: YES ceil to the cent, NO 1 - floor(bid) to the cent.
- Gold quiet hours: Central hour of the decision time in 20..23 (`inQuietHours` on `now`).
- Ethereum `smoothGate` / `pathShape` / `sideMids`: mids (b + a)/2 (1 minus that for NO) of every candle of that market with finite closing bid and ask, ending at or before the decision candle (I use the decision candle as the last one; live includes the in-progress candle, which a few seconds into the minute is close to the decision candle's close, and using the next full candle would be look-ahead), at least 4 earlier candles, min step >= -0.005 in plain float arithmetic, last minus first >= 0.10.
- One crypto order per window, first in list order (Dogecoin before Ethereum); every order assumed filled. If Dogecoin is skipped by the window cap, Ethereum may still take the window (as in the code).
- Sizes: Dogecoin 5 (`FIXED_CONTRACTS`, 5 since Oct 29), Ethereum 1, gold `l1Count(cashLeft, cost1, cap, addon)` with addon = min(floor(pool / 0.93), addonCap(cap)), add-on clamped again inside to floor(base_count x 0.25), ceiling 50; cost1 = worst + fee(worst, 1). `maxContractsFor`: gold 50, Dogecoin 5, Ethereum 1.
- Ladder `reviewSizing(state, cash - saved, now)` at every window: reseed at start (cap = max(cap, target), base = cash - saved); target = clamp(floor(x / 43), 1, 40); target < cap held 2 hours then cap = target, base = x; else every 3 days base = x and cap + 1 toward the target.
- `foldSkim` everyWin, in order time (gold before crypto in a window), on `settledPnl` = payout + exit proceeds - maxCost (maxCost = worst x C + fee(worst, C), worst = the limit, as live books it); a loss stop sets pool 0.
- Window cap 5.5% of `base` on account money (maxCost minus addonCost), first order never cut to 0; cash check: cash left >= cost + $0.50.
- Loss stop: worst = net of orders sent in the last 24 h since session start (settled pnl as above) minus maxCost of open orders, against -(0.12 x base + addonAtRisk); checked before a window's orders and right after them (this window's orders open, counted as lost).
- Exit watch: first later candle ending before the close with `validQuote` and bought-side bid (YES bid, or 1 - YES ask) in (0, 0.25]: sold at that bid, fee at C; else settled by Kalshi's result.
- Fills (main): the decision candle's ask of the side plus RISK1's per-market slippage (gold +0.60c, Dogecoin +0.86c, Ethereum +0.87c, `workers/DRIFT.md` 30 d); fee 7% x C x p x (1 - p) rounded up to the cent per order on the price paid; cash moves by the price paid. The loss stop and pool use the live bookkeeping (maxCost at the rounded-up limit).

## Data

1 minute candles and results from `data/l1b.sqlite`, `data/book.sqlite`, `data/fresh.sqlite`. **Dogecoin is not in those three files** (it is in `e3b.sqlite` and `alts2.sqlite`, plus `fresh.sqlite`), so Dogecoin also reads `e3b` and `alts2`; stated here before scoring. A ticker in more than one file is taken from the file with more candles for it (ties to the earlier file in the order l1b, book, e3b, alts2, fresh). Only markets with result yes or no. Days: US Central dates of the decision time; a full day is one inside the span where all three series have data, from 2026-08-06 to the last full day (expected 2026-10-28). Thirds by date, equal day counts.

## Check 1: per-market reproduction (1 try)

1 contract, fee at C = 1, slippage as above, live filters, one crypto per window. Per market: entries, settled losses, 25c exits, PF, mean net c a contract ALL and per third. Every difference from RISK1's table reported with a reason. Material difference: any market's entry count off by more than 3%, or a gold mean per third off by more than 0.15c.

## Check 2: my own bootstrap (1 try)

Vectorised day-block bootstrap: whole Central days with replacement, 10,000 paths of 90 days, 30 days read off the same paths, seed 29102026, starts $528 and $1,028, the rules above; after a stop the bot stays off for the rest of that Central day and restarts (reseeded, a new session) at the next day's first window (RISK1's STOP_DAY). Net = final cash (savings included) - start. Report median, p5, share below start, share with at least one stop. Material difference from RISK1: median off by more than 10% or $10 (whichever is bigger), p5 off by more than $25, share below start off by more than 3 points.

## Check 3: stress, each fixed now, each one try (same paths, STOP_DAY, both starts, 30 and 90 days)

- **(a) one candle later:** the decision (band, side, smooth, quiet hour) on the close - 360 candle, but the fill at the NEXT candle's (close - 300) ask of the same side, plus the same per-market slippage (conservative: the live send still lags whatever quote it sees); no entry if that candle is missing or its quote is not valid; the exit watch looks only after that candle.
- **(b1) gold slippage +1.0c on top of the live 0.60c (1.60c total); (b2) +1.5c on top (2.10c total).** (RISK1's own sensitivity row was 1.5c total.)
- **(c) 3-day blocks:** resample blocks of 3 consecutive history days (start uniform over every valid start), 30 blocks for 90 days, so runs of bad days are kept.
- **(d) best 5 days dropped:** the 5 history days with the highest 1 contract net across the three markets under the live rules (Check 1 records) are removed from the pool before resampling.
- **(e) look-ahead audit:** list every candle my code reads to decide an entry and assert none ends after close - 360; then read `risk1.py` and do the same, and check its smooth gate, band and exit use only candles at or before the decision (exit: only after).

## Verdict rule (fixed now)

CONFIRMED if Checks 1 and 2 are within the material-difference limits and no stress check turns the $528 90 day median negative or the $528 30 day share below start above 25%. CHANGED otherwise, naming the check and giving the corrected numbers. Either way all stress rows are reported. These are verdicts on RISK1's arithmetic, not on any strategy; the strategy verdict words do not apply.

**Prediction (stated now):** Checks 1 and 2 reproduce within the limits (gold entries within a few percent); (a) and (b2) move the $528 30 day median down by at least a third; (c) widens p5 noticeably; (d) lowers the median by roughly a third. At least one stress check likely crosses the CHANGED line (my guess: b2).

**Tries:** Check 1, Check 2, a, b1, b2, c, d, e = 8 (running count about 439,013 + 8 = about 439,021).
