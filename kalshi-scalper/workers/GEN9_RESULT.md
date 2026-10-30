# GEN9 result (2026-10-30): sub-minute round trips from the public trade tape (10 second bars, 20c to 80c, sold 30 to 180 s later, never held). Bitcoin and gold FALSIFIED at discovery

Registration `workers/GEN9_REGISTRATION.md` (commit 8fb921c, pushed before any study-period tape was fetched). Discovery frozen in `workers/GEN9_FROZEN.md` (gold commit 620b6ed, Bitcoin commit c0cdcee; sha256 gold 951c20a2..., Bitcoin d6fb6d55...; control lists hashed there) before either market's validation rows were built. Validation read once per market, for the family control and, as information only, the ten best discovery rules. Code `src/scalper/gen9.py`. Nothing closing on or after 2026-10-28 00:00 UTC was read; the settlement result was never read.

**Fill model, stated plainly:** entries and sales are APPROXIMATIONS from trade prices (side's last trade + half the candle spread + 1c to buy, - half spread - 1c to sell), not a book. No depth, queue or latency beyond the 10 s bar. Fees 7% x C x p x (1 - p) rounded up per order on both legs, C = 10. A survivor would have needed R6's real book (recording since 2026-10-29) to confirm it; none survived, so no R6 evaluator is proposed.

## Fetch (as registered: 50% of days by seed 909, then a 6 hour budget, seeded order 919)

| | Bitcoin | Gold |
|---|---|---|
| Sampled days (discovery / validation) | 23 / 19 | 23 / 19 |
| Sampled markets | 3,983 | 3,072 |
| Fetched within the budget | **1,004** (front prefix + tail suffix of the seeded order) | **3,072** (all; 1 had no trades) |
| Trades read (900 s to 120 s before the close) | 26.9 million | 11.1 million |
| MAKER4 cache reused (only 900 to 750 s fetched) | 17 markets | 113 markets |
| Discovery windows / rows / days | 558 / 48,206 / 23 | 1,704 / 141,121 / 23 |
| Validation windows / days | 446 / 19 | 1,368 / 17 |

Bitcoin cleared the registered minimum (300 discovery windows, 15 days), so both markets were searched.

## Funnel

| | Bitcoin | Gold |
|---|---|---|
| Generated (all in N) | 27,783 | 23,272 |
| rejected: exit not allowed / under 30 trades / duplicate | 1,611 / 2,444 / 18,728 | 1,296 / 1,395 / 15,581 |
| Distinct | 5,000 | 5,000 |
| Discovery PF over all distinct: median / 95th pct | 0.25 / 0.53 | 0.24 / 0.46 |
| Median distinct rule's mean net per trade (C = 10) | -6.11c | -6.33c |
| Distinct at screen size (100+ trades, 15+ days) | 2,795 | 4,151 |
| ... with discovery PF 1.0 or more | 0 (best 0.979) | 0 (best 0.845) |
| **Passed discovery (PF 1.5, size, stale 20% or less)** | **0** | **0** |
| Validation: survivors / passes | none to read | none to read |
| Family control (failures at size passing the validation screen) | 0 of 2,795; validation PF median 0.24, 95th pct 0.50 | 0 of 4,151; median 0.24, 95th pct 0.46 |

Stale exit prices (no trade in the last 60 s) and missing-candle spreads: 0.00% on both markets.

**Unconditioned base** (information looks, counted): first in-zone entry of every window, both sides, sold H seconds later, PF at C = 10 (mean net):

| hold | 30 s | 60 s | 90 s | 120 s | 150 s | 180 s |
|---|---|---|---|---|---|---|
| Bitcoin discovery | 0.10 (-6.5c) | 0.20 (-6.5c) | 0.27 (-6.7c) | 0.33 (-6.6c) | 0.39 (-6.5c) | 0.41 (-6.4c) |
| Bitcoin validation | 0.10 (-6.4c) | 0.22 (-6.2c) | 0.35 (-5.3c) | 0.42 (-4.9c) | 0.46 (-5.1c) | 0.46 (-5.5c) |
| Gold discovery | 0.11 (-6.8c) | 0.18 (-6.7c) | 0.27 (-6.5c) | 0.31 (-6.8c) | 0.37 (-6.6c) | 0.41 (-6.5c) |
| Gold validation | 0.11 (-6.9c) | 0.19 (-6.9c) | 0.25 (-6.9c) | 0.29 (-7.1c) | 0.34 (-6.7c) | 0.38 (-6.7c) |

**Where the money goes.** The mean net is flat at about -6.5c whatever the hold, which is the cost of the round trip with a price move of about zero: half spread 0.50c (Bitcoin) / 0.65c (gold) plus the 1c pad, on each leg (about 3c), plus two fees of about 1.8c at 50c and C = 10 (about 3.5c). PF rises with the hold only because a longer hold spreads the same fixed cost over a wider move.

## Best 10 per market (by discovery PF at size; information only, none passed a gate)

| market | rule | Disc PF (n, mean) | Val PF (n, days, mean) | Val day z |
|---|---|---|---|---|
| BTC | no 360..300s, big30 > 2,199 & c60 > 972 & dp10 > 2, stop -10 else 150 s | 0.98 (123, -0.2c) | 0.41 (113, 18, -7.2c) | -4.55 |
| BTC | yes 540s, i60 <= -0.124, TP +12 else 120 s | 0.87 (104, -0.7c) | 0.50 (85, 19, -4.3c) | -3.64 |
| BTC | yes 540s, i60 <= -0.124, TP +5 else 180 s | 0.78 (104, -1.0c) | 0.40 (85, 19, -4.8c) | -3.91 |
| BTC | no 420..300s, dp60 > 14, stop -10 else 180 s | 0.76 (165, -2.7c) | 0.41 (126, 19, -7.7c) | -4.98 |
| BTC | yes 540..480s, f10 <= 0 & dp10 <= -5, stop -10 else 180 s | 0.75 (162, -2.4c) | 0.45 (106, 19, -6.1c) | -3.88 |
| BTC | both 300s, big30 > 1,000 & c60 <= 1,996 & dp10 > -3, sell 180 s after | 0.75 (113, -3.9c) | 0.51 (67, 19, -8.8c) | -3.05 |
| BTC | no 420..300s, dp60 > 2 & big30 <= 3,881 & c60 <= 1,669, TP +12 else 150 s | 0.75 (174, -2.3c) | 0.40 (86, 19, -7.3c) | -3.58 |
| BTC | yes 420..360s, c10 > 266 & i60 <= -0.124, sell 180 s after | 0.72 (117, -3.4c) | 0.68 (117, 19, -4.5c) | -1.92 |
| BTC | yes 780..720s, px <= 50 & i30 > -0.359 & f30 <= 0, sell 150 s after | 0.72 (204, -2.4c) | 0.37 (143, 19, -6.3c) | -5.00 |
| BTC | no 360s, px > 39, sell 180 s after | 0.70 (178, -4.0c) | 0.46 (141, 19, -9.1c) | -3.67 |
| GOLD | no 420..360s, dp30 <= 3 & c60 > 260 & f60 > 2,064, sell 180 s after | 0.85 (118, -1.7c) | 0.49 (270, 15, -6.8c) | -6.27 |
| GOLD | no 240s, c10 <= 51 & dp10 <= 5 & bigdir30 <= -1, stop -10 else 120 s | 0.73 (188, -2.8c) | 0.50 (57, 13, -6.2c) | -3.92 |
| GOLD | yes 720..300s, px <= 39 & dp60 > 14, sell 180 s after | 0.70 (148, -3.8c) | 0.47 (158, 15, -7.4c) | -4.23 |
| GOLD | no 300s, burst > 0.80 & i30 <= 0.24, sell 180 s after | 0.69 (387, -4.5c) | 0.71 (370, 17, -4.2c) | -2.94 |
| GOLD | no 240s, dp30 <= 3 & dp60 <= 5 & f60 > 1,123, stop -10 else 90 s | 0.69 (100, -2.9c) | 0.46 (109, 15, -5.6c) | -3.14 |
| GOLD | no 300s, c30 > 88 & burst <= 0.80, stop -10 else 150 s | 0.69 (123, -3.2c) | 0.56 (154, 16, -5.2c) | -3.79 |
| GOLD | both 300s, big30 <= 492 & i60 <= 0 & dp30 <= -2, TP +8 else 150 s | 0.68 (106, -3.1c) | 0.56 (44, 14, -4.4c) | -2.29 |
| GOLD | yes 480..420s, big30 <= 400 & i60 > -0.091 & dp10 > 0, sell 180 s after | 0.66 (535, -3.6c) | 0.50 (217, 17, -6.1c) | -3.72 |
| GOLD | no 240s, c30 > 115 & dp30 <= -2, sell 120 s after | 0.64 (155, -4.8c) | 0.59 (215, 15, -5.6c) | -6.18 |
| GOLD | no 360s, f10 > -98 & dp60 > 2, stop -10 else 150 s | 0.63 (385, -3.7c) | 0.49 (288, 17, -5.5c) | -6.35 |

Twenty of twenty fell further in validation, every one with a negative day z. The conditioned best of 5,000 barely reaches the base's level in validation: nothing in sub-minute flow, bursts, short price changes or print size calls the next 30 to 180 s of the quote.

**Fill-model sensitivity (information).** Dropping the brief's two 1c pads adds 2c to every trade: every best-10 rule would still lose in validation (best -2.2c, gold "no 300s, burst" and Bitcoin "yes 540s TP +12"), and the base would be about -4.5c. R6's real touch (1c spread at the ask and bid, no pad) is close to that pad-free case, so a book-priced re-run would not change the verdict; no R6 evaluator is proposed.

## Verdicts

- **Bitcoin: FALSIFIED** at discovery (0 of 2,795 at size; best 0.98; validation control 0 of 2,795).
- **Gold: FALSIFIED** at discovery (0 of 4,151 at size; best 0.85; control 0 of 4,151).
- No candidate file, no forward ledger entry, no R6 evaluator proposal (nothing survived).
- **N added: 27,783 + 23,272 draws + 12 information looks = 51,067**; running count about **678,905**, Bonferroni z bar about **5.26**.
- **Prediction check.** Median discovery PF 0.25 / 0.24 (predicted about 0.40: worse than predicted, because the conservative fill costs about 6.5c and the price move over 30 to 180 s averages about zero); base 0.10 to 0.46 (predicted 0.25 to 0.55: lower at short holds); survivors 0 / 0 (predicted 0 to 3); both families FALSIFIED (predicted, prior 90%); Bitcoin was searched (the budget fetched 1,004 markets, more than the 500 to 700 expected); stale exits 0% (predicted under 2% / 2% to 8%: gold trades more often than assumed).

## For the lead

GEN1 and GEN8 closed the coin-flip round trip on 1 minute candles; GEN9 reopened it at 10 second resolution with the tape's own flow features and finds the same answer, more firmly: over 30 s to 3 minutes the 15 minute quote does not drift in any direction the tape can call, and a round trip costs 4.5c to 6.5c however it is priced. With TAPE20 (flow adds nothing to the favourite held) and MECH1 (no taker type carries the open interest core), the public tape has now been read three ways on these two markets with nothing found. This trade shape should be marked closed on gold and Bitcoin for both candle and tape data; only a cheaper fill (a resting maker entry, which is MAKER4 / MAKER5's question, not this one) could change the arithmetic.

## Files

`src/scalper/gen9.py`, `workers/GEN9_REGISTRATION.md`, `workers/GEN9_FROZEN.md`, `workers/GEN9_frozen_btc.json`, `workers/GEN9_frozen_gold.json`, this file. Bars (`data/gen9/bars.sqlite`, 4,076 markets of 10 s bars, reusable for later tape work on the same sampled days), distinct, control, validation and log files in `data/gen9/` (not committed).
