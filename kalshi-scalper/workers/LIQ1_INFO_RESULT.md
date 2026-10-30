# LIQ1-INFO result (information check only, no outcomes)

Worker LIQ1-INFO, 2026-10-30. Registration: `workers/LIQ1_INFO_REGISTRATION.md`
(commit 4bbf4d9, pushed before any liquidation was joined to a Kalshi quote).
Code: `src/scalper/liq1.py`. No outcome was read: no `result`, win, loss,
fill, fee or PF anywhere. **Tries in N: 0.**

## Decision

**No reverting impact, LIQ1 not worth an outcome test.** The impact part of
the rule passes (the mid moves well over 2c), but less than half of it
reverts within 3 minutes in either stage: in discovery it keeps going, in
validation 40% comes back.

## Data

- Deribit BTC-PERPETUAL, every public trade 2026-08-06 to 2026-10-27 (keyless
  history API, cached in `data/liq1/`, git-ignored): 3,291 liquidation
  trades, $26.6M liquidated in 82 days. Deribit liquidations are rare: only
  1.2% of eligible minutes in discovery had any.
- Threshold (99th percentile of 2 minute liquidated USD over 30,499
  discovery eligible minutes, frozen before the join): **$400**. Because 98.8%
  of minutes are zero, the 99th percentile sits at the bottom of the positive
  values, so a "spike" here is effectively "any liquidation in the 2 minutes".
  This is what the registered rule gives; it was not changed.
- Kalshi KXBTC15M one minute candles (l1b, book, fresh), mid = (bid_c + ask_c) / 2.

## Numbers (cents, in the push direction; one spike per market)

| | Discovery Aug 6 to Sep 20 | Validation Sep 21 to Oct 27 |
|---|---|---|
| Markets | 4,357 | 3,512 |
| Spikes (readable) | 133 | 101 |
| Liquidation direction agrees with the perp's 2 min move | 113 of 133 | 86 of 101 |
| I2, 2 minute spike bin (liq. direction) | **+9.62** (sd 15.4) | **+11.99** (sd 15.2) |
| I1, spike minute only | +4.22 | +6.15 |
| P1 / P2 / P3 after | +0.06 / +1.00 / **+2.25** | -1.39 / -2.09 / **-4.83** |
| Reversal fraction -P3 / I2 | **-0.23** (continues) | **+0.40** |
| Share of spikes (I2 > 0) reverting at least half | 0.12 of 115 | 0.27 of 88 |
| Rule: I2 >= 2c | pass | pass |
| Rule: at least half reverts | **fail** | **fail** |

Context (cannot rescue a failure):

- **Same definition, spikes vs control** (direction = sign of the perp's own
  2 minute move): spikes I2 +14.39 / P3 +1.34 (discovery), +13.62 / -4.52
  (validation); offset weighted non-spike control I2 +10.37 / P3 +0.25 (n
  28,673) and +10.59 / +0.42 (n 24,068). Kalshi's mid follows any 2 minute
  Bitcoin move by about 10c at this time-left whether or not a liquidation
  happened; a liquidation minute is a somewhat larger move (+3 to +4c over
  control on the same definition), and with the liquidation's own direction
  the impact is no bigger than an ordinary move (+9.6c against +10.4c in
  discovery).
- Zero-volume candles: every spike candle had volume > 0, so the volume > 0
  split equals the full set.
- Spikes by time-left are front-loaded (40 and 32 at the 10 minute minute),
  as expected with one spike per market taken at the first crossing.

## Reading

The impact on Kalshi's quote is real but it is the impact of a Bitcoin move,
which Kalshi quoters track within the minute; the liquidation adds little
beyond the move itself, and the move does not reliably come back within 3
minutes (continues in discovery, partly reverses in validation, the two
stages disagree in sign). There is no consistent temporary dislocation to be
paid for absorbing, so the counterparty named in brief B (forced liquidations
and quoters marking to the impacted spot) does not show up on Deribit data.
Caveat stated once: Deribit is a small perp venue (about $26.6M liquidated in
82 days), so "liquidation spike" here is mostly small prints; a larger venue's
liquidation feed (Binance, OKX, Bybit) has no public history and would need a
forward recorder, which is a separate brief.
