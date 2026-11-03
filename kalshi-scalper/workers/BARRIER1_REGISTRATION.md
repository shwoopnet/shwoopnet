# BARRIER1 registration (Strategy Research V2 worker, 2026-11-03, research only)

Written and pushed BEFORE any barrier-market price or outcome was read. Code `src/scalper/barrier1.py` (committed with the result).
Result: `workers/BARRIER1_RESULT.md`. Nothing live is touched; no promote verb.

## 1. Duplicate check (said first)
- README line 6043 (BTC/ETH census): monthly one-touch `KXBTCMAXMON`, `KXBTCMINMON`, `KXETHMAXMON`, `KXETHMINMON` were LISTED and counted
  (3 settled months) and "monthly touch pricing" was recorded as NOT TESTED because the data did not exist. No worker has priced them.
- MAXMIN*, BARRIER*: no file or README entry exists. NEWH1 H2 (round-number barriers) is a different idea (strike clustering). LADLONG1,
  HOURLY1, DERIBIT-IMPLIED, ARB*: terminal ladders (above K at one clock), a different contract; XMET1, COMM1, WX3, RULES1: other
  families. OICORE_SHAPE_INVENTORY: no touch cell. **Verdict: NEW (the touch / one-touch family has never been priced against a
  reflection-principle model).**
- Underlying data: OKX 1-hour klines (BTC, ETH, SOL, XRP, DOGE, BNB, HYPE spot or swap where listed), public. Kalshi 1-hour candles of
  each market (public). Rate limit shared: 1 thread, sleeps, 429 retry.

## 2. Universe rule (fixed now)
Kalshi series, any settled market whose title is "reach / one touch / max / min this month" for a coin with OKX data:
`KXBTCMAXMON KXBTCMINMON KXETHMAXMON KXETHMINMON KXSOLMAXMON KXSOLMINMON KXXRPMAXMON KXXRPMINMON KXDOGEMAXMON KXDOGEMINMON
KXBNBMAXMON KXBNBMINMON KXHYPEMAXMON KXHYPEMINMON` and the monthly/quarterly "when will X hit" series `KXBTCMAXM KXETHMAXM KXSOLMAXM
KXXRPMAXM KXDOGEMAXM KXBTCMAXQ`. Weekly and daily (`KXBTCMAXW`, `KXBTCMAXD`, `KXDOGEMAXW`) returned 0 markets on the census. Yearly, "above K
by date" and "hit 100k" series are census-only (one event a year; reported as counts, not traded). Strike K and direction come from the
market's own fields (floor/cap strike or title); a market whose barrier cannot be parsed is dropped and counted.

## 3. Model (fixed)
Driftless zero-rate diffusion, reflection principle, continuous monitoring:
`p_touch = min(1, 2 * N(-d))`, `d = |ln(K/S)| / (sigma * sqrt(T))` for the barrier on the side of S that is not yet touched (a barrier already
crossed by the OKX path before the look is dropped: the market is decided). S = OKX 1-hour close at the look hour. T = hours from the look to
the market close, in years. **Vol window: sigma = standard deviation of the 336 (14 days) most recent hourly log returns up to the look,
times sqrt(8760).** No other vol window is tried (one is registered; a second would be a counted try). Settlement source differences
(Kalshi's index vs OKX) are an accepted noise.

## 4. Look and entry (fixed)
Look = the first hourly Kalshi candle at or after open + 48 hours (monthly events) or open + 2 hours (a series of shorter life).
One entry per market, held to settlement, at the candle's yes ask (BUY YES) or, for the reverse rule, the no ask = 1 - yes bid. Fee
`ceil(0.07 * C * p * (1-p) * 100) / 100` with C = 10 per 10 contracts, per contract = fee / 10 (rounded up at C = 10). No stop, no exit.

## 5. Rules (2 counted rules, N +4)
- **BAR-CHEAP (long the cheap touch):** BUY YES when the ask is in [0.03, 0.30] and `p_touch >= 2.0 * ask`.
- **BAR-RICH (the reverse, separate try):** BUY NO when the no ask is in [0.03, 0.30] and `(1 - p_touch) >= 2.0 * no_ask`
  (the market over-prices the touch by at least a factor that makes NO twice the price).
Hard limit 0.30 on price paid on both. Internal consistency (touch >= terminal, touch <= 2 x terminal against Kalshi's own terminal ladder)
is reported as information only where a same-horizon terminal ladder exists (it does not at monthly horizons for most coins); it is not a rule.

## 6. Numeric prediction
BAR-CHEAP: win rate on the modelled set about the model mean (0.20 to 0.35), versus a price paid near 0.15; if the market is the naive
terminal price, mean net after fee +4c to +10c per contract with PF 1.5 to 2.5. My honest prior is that it is smaller because makers
see the 2x rule (they price touches already): expect mean net within +-3c and a FALSIFIED or NOT_ENOUGH_DATA verdict.

## 7. Kill rules and verdicts
- **FALSIFIED** for a rule when mean net after fee is not above 0 in BOTH halves (by event close time) of what exists, or PF under 1.5.
- **NOT_ENOUGH_DATA** when a rule has under 150 trades: then report qualifying markets per month and months to 40 and to 150 forward
  trades, and register a dated forward freeze (the market list and rule above, run on each new event, read at 40 fills).
- **Pass** needs both halves positive with a mechanism (retail prices touch at terminal probability), n >= 150, PF >= 1.5, then a capped
  probe spec (1 contract, price <= 0.30, kill rule, worst-day dollars, when 40 fills would exist).
- Frozen holdout: the last third of settled events by close time is not read for any choice or threshold; with so few months it is read
  once, after the development numbers are written, and reported as separate.
- One window of 3 months is NOT a basis for FALSIFIED beyond the small-sample statement: a small n is NOT_ENOUGH_DATA, not falsified.

## 8. Bookkeeping
N +4 (2 rules x 2). Expected read date: this run (2026-11-03). Forward read, if a freeze is registered: 40 fills, dated in the result.
