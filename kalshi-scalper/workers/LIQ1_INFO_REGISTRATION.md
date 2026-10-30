# LIQ1-INFO registration (information check only, no outcomes)

Worker LIQ1-INFO, 2026-10-30. Brief B of `workers/DIRECTOR_2026-10-30.md`.
Written and pushed BEFORE any liquidation is joined to a Kalshi quote.

## Question

Does a Bitcoin perpetual liquidation spike move Kalshi's 15 minute Bitcoin
quote (KXBTC15M) in the direction the liquidation pushed, and does that move
revert within 3 minutes? This is the gate in front of an outcome test of LIQ1.
**No outcome is read anywhere**: the loader selects `ticker, close_ts` from
`market` and `end_ts, bid_c, ask_c, volume` from `candle`; it never selects
`result`, never computes a win, a loss, a fill, a fee or a profit factor.
Cost in N: **0 tries** (no outcome is looked at).

Ledger check: no liquidation study is in `README.md`, the scoreboard or the
no-view mechanisms note (the only "liquidation" mentions are the CARRY1
margin caveat). Not a reworded tested idea.

Counterparty (for the later outcome test, named by the brief): forced
liquidations, and Kalshi quoters marking to the impacted spot. If Kalshi's
mid does not move on a spike, or moves and stays, there is nobody to be paid
for absorbing a temporary dislocation and LIQ1 is not worth an outcome test.

## Data

- **Liquidations.** Deribit public history API, keyless:
  `history.deribit.com/api/v2/public/get_last_trades_by_instrument_and_time`,
  instrument `BTC-PERPETUAL`, 2026-08-06 00:00 UTC to 2026-10-28 00:00 UTC,
  10,000 trades a request, paced (at least 0.5 s between requests, backing
  off on 429 or errors), cached per day in `kalshi-scalper/data/liq1/`
  (git-ignored). A trade is a liquidation when it carries the `liquidation`
  field. USD size = the trade's `amount` (BTC-PERPETUAL is an inverse
  contract, `amount` is USD notional).
- **Kalshi.** KXBTC15M one minute candles from `data/l1b.sqlite`,
  `data/book.sqlite`, `data/fresh.sqlite` (same files and first-file-wins rule
  as `src/scalper/fals4.py`), close from 2026-08-06 to before 2026-10-28.
  Mid at a candle = (bid_c + ask_c) / 2, the quote at the candle's end. A
  missing bid or ask makes that measure unreadable (counted, not filled).
- Universe chosen on time only: every KXBTC15M market in the dates.

## Definitions (fixed)

- Minute bins: a trade at time T (ms) belongs to the minute ending at
  ceil(T / 60 s), matching Kalshi candles that cover (end - 60 s, end].
- **L2(t)** = liquidated USD (all liquidation trades, both sides) in the two
  minutes ending at t (minutes ending t - 60 and t).
- **Eligible minutes:** t - close in {-600, -540, -480, -420, -360, -300,
  -240} s (the minute ends 10 to 4 minutes before the 15 minute close).
- **Threshold:** the 99th percentile (nearest rank) of L2(t) over all
  eligible (market, t) pairs whose market closes on a discovery day
  (2026-08-06 to 2026-09-20), zeros included. Computed from Deribit data only,
  before any Kalshi quote is joined, and frozen for validation. If that
  percentile is 0 (fewer than 1% of eligible minutes have any liquidation),
  the threshold is the smallest positive L2 at or above the 99th percentile
  of the positive values; this is printed.
- **Spike:** eligible t with L2(t) >= threshold. One per market: the first
  eligible t (earliest) that crosses. A minute is a spike minute also when
  some liquidation ran in the minute before; that is what the 2 minute sum
  means.
- **Push direction D.** Forced flow F over the 2 minutes: a liquidation
  `T` (taker liquidated) counts +amount for a taker buy, -amount for a taker
  sell; `M` (maker liquidated) counts the opposite sign of the taker
  direction; `MT` counts 0 (both sides forced). D = sign(F). If F = 0,
  D = sign of the perp's last trade price at t minus at t - 120 s; if that is
  also 0 or missing the spike is dropped (counted). D = +1 means the forced
  flow pushed Bitcoin up, which pushes YES up.
- **Measures** (in dollars, x100 = cents), with m(x) the Kalshi mid at the
  candle ending x:
  - I2 = D x (m(t) - m(t - 120)), the move over the 2 minute spike bin
    (the primary "impact");
  - I1 = D x (m(t) - m(t - 60)), the move in the spike minute alone;
  - P1, P2, P3 = D x (m(t + 60k) - m(t)), the next 1, 2, 3 minutes.
  - Reversal fraction = -mean(P3) / mean(I2).
  - Reversal share = share of spikes with I2 > 0 whose P3 <= -I2 / 2.
- **Matched control:** every eligible non-spike (market, t) in the same
  stage at the same offset (L2(t) below threshold), direction = sign of the
  perp's price change over the same 2 minutes (zero change dropped). Control
  means are weighted to the spikes' offset mix. Spikes are also reported
  with this same price-change direction, so spike and control are compared
  on one definition.
- **Zero-volume candles reported both ways:** every measure for all spikes,
  and for spikes whose Kalshi candle ending t had volume > 0.
- Stages by close date: discovery 2026-08-06 to 2026-09-20; validation
  2026-09-21 to 2026-10-27. There is no third window here: this is not a
  strategy test; the outcome test, if earned, registers its own windows.

## Prediction

A liquidation spike on Deribit moves Kalshi's mid by about 1c to 3c in the
push direction (I2), and less than half of it reverts in 3 minutes (Kalshi
quoters mark to spot, and spot after a liquidation cascade usually does not
fully come back within 3 minutes). Predicted result: **no reverting impact**.

## Decision rule (fixed in advance)

Proceed to an outcome test of LIQ1 only if, **in discovery AND in
validation separately** (all spikes with readable quotes, liquidation
direction D):

1. mean(I2) >= 0.02 (2c in the push direction), AND
2. -mean(P3) >= 0.5 x mean(I2) (at least half of it reverts within 3 minutes).

If either fails in either stage: record **"no reverting impact, LIQ1 not
worth an outcome test"**. If a stage has fewer than 20 spikes with readable
I2 and P3, the check is **NOT_ENOUGH_DATA** for that stage, which also means
no outcome test is earned now. The control and the volume > 0 split are
context and cannot rescue a failure. Counts of spikes per stage are reported.

Code: `src/scalper/liq1.py`. Result: `workers/LIQ1_INFO_RESULT.md`.
