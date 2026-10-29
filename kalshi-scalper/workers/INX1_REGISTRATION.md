# INX1 registration: Kalshi's S&P 500 and Nasdaq 100 4 pm "above K" markets against a fair value from the index and its implied volatility

Worker INX1, Strategy Research V2, 2026-10-29. Research only. Written and pushed before any Kalshi quote was compared with any index price, model probability or outcome.

## Ledger check (done first)

- **INDEX1** (README, "Strategy card INDEX1", 2026-10-28) is the same family and nearly the same idea: KXINX at 12:30 ET against a VIX-implied Normal probability, 6c edge. It was **parked and never run** (the owner limited scope to gold and Bitcoin on 2026-10-28; the lead has assigned this family to V2 workers in the owner's widened brief). INX1 replaces INDEX1's single 12:30 ET look with three looks inside the last hour, uses the intraday implied volatility index at the decision minute instead of the previous close, and uses the hourly-ladder "above K" series at its 4 pm close. INDEX1 is not run separately; if the lead counts INX1 as INDEX1's run, the 1 try INDEX1 already carries in the count stays and INX1 adds 6.
- **E4** ran L1's favourite-band rule (88c to 97c, 6 minutes before each hourly close) on KXINXU, 40 days: -2.78c, FALSIFIED. INX1 is not L1's rule (no price band, a model fair value, both sides, 60/30/10 minutes). Not repeated.
- The 15 minute S&P and Nasdaq series (KXINX15M, KXNDQ15M) have no settled markets; the 2026-10-28 scoreboard lists the daily index levels as never tested. Nothing else in `kalshi-scalper/README.md` (grep INX, NDX, NASDAQ, S&P, SPX) tests a fair value on these markets.
- **GOLDFV1** (2026-10-29, FALSIFIED) is the nearest analogue in another market: Kalshi gold priced the latest minute of COMEX. That is this test's honest alternative.

## What was looked at before registering (disclosed)

Counts and volumes only. Kalshi `KXINXU` settled listing reaches back to 2026-08-24: 334 events, 47 of them at H1600 (the 4 pm ET close), median contracts traded per 4 pm event about 370,000; strikes are 5 index points apart, about 60 per event. `KXNASDAQ100U` is listed the same way (counts printed by the same census). The daily range series `KXINX` and `KXNASDAQ100` exist (25 point buckets plus tails) and are not used. Yahoo 1 minute bars are limited to 8 days per request; Yahoo **5 minute** bars for ^GSPC, ^NDX, ^VIX, ^VXN reach 2026-08-06 in one request, so they are the index data (only bar counts and date ranges were read). No quote, model value, signal or outcome has been computed.

## The rule (exact)

- **Markets:** KXINXU (S&P 500) and KXNASDAQ100U (Nasdaq 100), events whose close is the 4 pm ET cash close (event suffix H1600; close time from the market record, so a half day would follow its own close). "Above K" markets (`strike_type` greater_or_equal, K = `floor_strike`). Settlement as Kalshi recorded it (`result`).
- **Days:** every 4 pm event closing from 2026-08-24 (Kalshi's reach) to 2026-10-28, with Yahoo bars on the day.
- **Looks:** L = 60, 30 and 10 minutes before the close. D = close - L.
- **Information at D:** S = close of the Yahoo 5 minute index bar that starts at D - 300 s (^GSPC for S&P, ^NDX for Nasdaq), V = close of the volatility index bar that starts at D - 300 s (^VIX for S&P, ^VXN for Nasdaq); if either bar is missing, the last bar that started within 15 minutes before D; else no entry that look.
- **Fair value:** p = Phi( ln(S/K) / (V/100 x sqrt((L/390)/252)) ), zero drift.
- **Universe (before the first look, from quotes and time only):** among the event's strikes within 4% of the Yahoo index level at close - 75 min (download screen), keep those whose Kalshi quote mid ((yes_bid + yes_ask)/2) at the last two-sided candle ending at or before close - 75 min (15 minutes before the 60 minute look, at most 15 minutes stale) is between 0.05 and 0.95. The universe is fixed for the day and all three looks.
- **Quote and fill:** the Kalshi 1 minute candle ending at D + 60 (the first minute after the signal; its closing bid and ask, a quote one could hit after the signal is known). It must have yes_bid > 0 and yes_ask < 1. Buy YES at yes_ask if p - yes_ask >= 0.05; buy NO at 1 - yes_bid if yes_bid - p >= 0.05. At most the 2 strikes with the largest edge per event per look. Information only: the same with the candle ending at D.
- **Exit:** hold to settlement. No stop.
- **Size:** C = 1 and C = 10 contracts per order (10 assumes the touch had at least 10; candles carry no size, so the 10 contract result is an upper bound).
- **Fees:** 7% x C x price x (1 - price), rounded up to the cent per order; check at fees x1.2.
- **Zero volume:** primary keeps a fill candle with zero traded volume if it is two-sided; reported again treating zero-volume fill candles as unfillable.

## Variants (N tried = 6)

{S&P, Nasdaq} x {60, 30, 10 minutes}. Each is scored on its own. The 0.05 margin, the 2 strike cap, the 4% screen, the 0.05 to 0.95 universe, 75 minutes and zero drift are fixed here and not tuned. Running count before INX1 about 438,904 (V2_STATUS); after INX1 about 438,910 (other workers may add in parallel).

## Windows

Trading days with at least one 4 pm event in scope, sorted by date, split into thirds by date (A discovery, B validation, C holdout). Same split for both indices (by the S&P day list). Verdicts on A and B are written into `workers/INX1_RESULT.md` before C is computed; C is read once.

## Counterparty

Kalshi index takers and quoters who price a level by the last print, a round number or a stale or wrong volatility, so that a strike's ask sits 5c or more under the probability implied by the index level and its own implied volatility in the last hour. **Honest alternative (expected):** Kalshi's quoters price off S&P and Nasdaq futures and options in real time (as Kalshi gold priced COMEX within a minute, GOLDFV1), so a 5c gap is mostly the model being wrong. The known model error in advance: VIX scaled linearly in time understates last-hour variance (the closing auction and the intraday U shape), so the model is too confident near the close and its "edges" will lean toward buying the favourite and selling the tails; a loss pattern of favourites losing more often than the model says is that bias, not a counterparty.

## Numeric prediction

About 45 trading days (about 15 per window), 1 to 2 trades per day per variant where a signal fires; PF after fees 0.6 to 1.1 per window for most variants; no variant at PF >= 1.5 in both A and B.

## Kill criteria and verdicts (per variant, at C = 1, fees x1)

- Fewer than 8 trading days with a trade in A or in B: `NOT_ENOUGH_DATA`.
- PF under 1.5 in A or in B: `FALSIFIED` (C not needed for that variant, but C is still computed once for the record if any variant survives).
- PF at least 1.5 in A, B and C, positive at fees x1.2 in all three: still `NOT_ENOUGH_DATA` unless the day-clustered z of net per trade over all three windows reaches the deflated bar (about 5.17 at N about 438,910), which 45 days cannot reach unless the edge is enormous; only then `NOT_YET_FALSIFIED`, which earns a forward read registration only.
- Family verdict: FALSIFIED if every variant is FALSIFIED; otherwise the strongest variant verdict, stated with its numbers.

Reported per variant and window: PF at C = 1 and C = 10, net, trades, independent days and markets, loss rate, fees x1.2 PF, zero-volume share and the result with zero-volume fills dropped, the D-candle (information) PF.

## Data and code

Public, keyless: Kalshi `/markets` (settled) and `/markets/candlesticks` (1 minute, from close - 90 min to close - 8 min), Yahoo chart 5 minute bars. Stored under `kalshi-scalper/data/` or the session scratchpad (not committed). Code `kalshi-scalper/src/scalper/inx1.py`.
