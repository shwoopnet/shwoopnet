# GEN8 result (2026-10-30): mid-price round trips (30c to 70c, sell 1 to 5 minutes later, never held). Bitcoin and gold FALSIFIED at discovery

Registration `workers/GEN8_REGISTRATION.md` (commit 2a5e623, pushed before any row was built). Discovery frozen in `workers/GEN8_FROZEN.md` (commit dae1a36; sha256 btc 735b3a22..., gold 7402cb26...; control lists hashed there) before any validation row was built. Validation read once, for the controls and, as information only, the ten best discovery rules per market. Code `src/scalper/gen8.py`. Fills at the next candle's closing ask, sale at a candle's closing bid, C = 10, fee rounded up per order on both legs. Nothing closing on or after 2026-10-28 00:00 UTC was read.

## What was new against GEN1 (stated in the registration before scoring)

GEN1 already covered this zone (its asks 3c to 85c and entries 840 to 180 s include it) with before-settlement exits (take profit / stop / sell at 240, 120, 60 s left) and found nothing (best 1.25 at size). New in GEN8 only: GEN7's 11 open interest features (GEN1 had one raw `doi`), the 30c to 70c restriction as every rule's universe, exits timed 60 to 300 s after the fill and always at least 120 s before the close, next-candle fills, each market alone on GEN6 / GEN7's date split. None of it changed the answer.

## Funnel

| | Bitcoin | Gold |
|---|---|---|
| Discovery windows / rows / days (Aug 6 to Sep 20) | 4,357 / 47,651 / 46 | 3,192 / 34,024 / 45 |
| Validation windows / days (Sep 21 to Oct 27) | 3,512 / 37 | 2,453 / 32 |
| Generated (all in N) | 18,363 | 17,365 |
| rejected: exit not allowed (fallback later than 120 s left) / under 30 trades / duplicate | 3,693 / 3,631 / 6,039 | 3,626 / 3,075 / 5,664 |
| Distinct | 5,000 | 5,000 |
| Discovery PF over all distinct: median / 95th pct | 0.55 / 0.80 | 0.52 / 0.75 |
| Median distinct rule's mean net per trade (C = 10) | -3.97c | -4.29c |
| Distinct at screen size (100+ trades, 15+ days) | 4,204 | 4,145 |
| ... with discovery PF 1.0 or more / 1.3 or more | 17 / 0 | 3 / 0 |
| **Passed discovery (PF 1.5, size, zero volume 20% or less)** | **0** (best at size 1.14) | **0** (best at size 1.09) |
| Validation: survivors / passes | none to read | none to read |
| Family control (discovery failures at size passing the validation screen) | 1 of 4,204 (0.02%); validation PF median 0.55, 95th pct 0.78 | 0 of 4,145; median 0.54, 95th pct 0.82 |

Unconditioned base (information looks, counted): the first in-zone entry of every window, sold H seconds after the fill, PF at C = 10:

| hold | 60 s | 120 s | 180 s | 240 s | 300 s |
|---|---|---|---|---|---|
| Bitcoin discovery / validation | 0.37 / 0.38 | 0.50 / 0.49 | 0.57 / 0.60 | 0.63 / 0.64 | 0.66 / 0.69 |
| Gold discovery / validation | 0.33 / 0.35 | 0.47 / 0.50 | 0.56 / 0.58 | 0.63 / 0.61 | 0.65 / 0.64 |

The base rises with the hold only because a longer hold spreads the same fixed cost (two fees of about 1.8c each at 50c, plus the spread) over a larger price move; it never comes near 1. That is the whole story of this shape: the mid over 1 to 5 minutes carries no drift any feature here can call, and the round trip costs about 4c.

**Zero bids:** a fallback bid of 0 booked at 0 happened in about 0.005% (Bitcoin) and 0.009% (gold) of all distinct-rule trades in discovery, and in 1 of the 1,364 validation trades of the ten best Bitcoin rules. No fallback candle was ever missing (late-candle share 0). No zero-volume flag in any best-10 rule.

## Best 10 per market (by discovery PF at size; information only, none passed a gate)

PF at C = 10. Validation read once for the record; C = 1, fee stress and signal-candle fill in the result printout (scratch, not committed).

| market | rule | Disc PF (n) | Val PF (n, days) | Val z |
|---|---|---|---|---|
| BTC | both 420..360s, npv5 <= 0.27 & sdoi5 > 0.71, sell 180 s after | 1.14 (207) | 0.62 (156, 37) | -2.51 |
| BTC | yes 360s, gold d2 <= 0.03 & d2 <= -0.17, TP +5 stop -20 else 120 s | 1.12 (103) | 0.94 (96, 27) | -0.31 |
| BTC | both 480..300s, doi3 <= 19.5k & vol <= 101k, TP +15 stop -20 else 120 s | 1.09 (392) | 0.80 (199, 37) | -1.53 |
| BTC | yes 840..540s, d5 > 0.2 & ETH mid > 0.455, TP +8 stop -20 else 240 s | 1.08 (135) | 0.61 (109, 34) | -1.96 |
| BTC | no 540..480s, npvw <= 0.36 & hour > 21 & ask <= 0.57, TP +12 stop -15 else 240 s | 1.07 (107) | 0.90 (92, 36) | -0.46 |
| BTC | no 360s, bid <= 0.61 & vol > 79k & hour <= 4, TP +5 stop -20 else 180 s | 1.05 (175) | 0.65 (161, 36) | -2.07 |
| BTC | no 540..420s, ETH mid <= 0.455 & sdoi3 > 0.51 & doi1 <= 36k, TP +12 stop -20 else 240 s | 1.05 (203) | 0.98 (113, 34) | -0.12 |
| BTC | yes 660..300s, d1 <= -0.08 & vol > 169k & ETH d2 > -0.075, TP +12 stop -5 else 120 s | 1.04 (108) | 0.83 (172, 35) | -0.91 |
| BTC | both 720..540s, sdoi5 > 0.71 & gold mid > 0.81 & d5 > 0.08, TP +12 stop -10 else 240 s | 1.04 (136) | 0.65 (66, 23) | -1.44 |
| BTC | no 720..480s, gold mid <= 0.32 & d3 > 0.12, TP +15 stop -15 else 300 s | 1.04 (262) | 0.65 (200, 29) | -3.06 |
| GOLD | no 480s, doi5 > 18.9k, TP +8 stop -20 else 180 s | 1.09 (131) | 0.80 (333, 27) | -1.85 |
| GOLD | yes 660..420s, ETH d2 > 0.19 & d5 > 0.08, TP +15 stop -10 else 180 s | 1.08 (117) | 0.52 (96, 28) | -3.14 |
| GOLD | yes 540..420s, hour <= 14 & d2 > 0.11 & doi1 <= -39, sell 240 s after | 1.06 (123) | 0.73 (148, 27) | -1.54 |
| GOLD | the next seven have discovery PF 0.93 to 0.97 (below 1) | 0.93 to 0.97 | 0.59 to 2.29 (the 2.29 on 18 trades) | -1.98 to 1.50 |

Ten of ten Bitcoin rules fell in validation (0.61 to 0.98). The one Bitcoin control that passed the validation screen (both sides at 600 s, hour > 17 & sdoi1 > 0.13 & gold mid <= 0.625, TP +3 stop -15 else 300 s) had discovery PF **0.47** (n 122) and validation 1.31 (n 71, z 1.08): noise at the top of 4,204, which is the control rate the rule exists to measure.

## Distinct bets, overlap with REF_GEN6_OICORE

Not applicable as a gate: nothing survived. For the record, the ten best Bitcoin rules' validation entries overlap OICORE's windows by Jaccard 0.01 to 0.07 (4 to 32 entries each): GEN8 is a different trade in different windows, and it shares nothing with the open interest core's edge. Gold has no OICORE reference.

## Verdicts

- **Bitcoin: FALSIFIED** (0 discovery survivors of 4,204 at size; best 1.14; control 1 of 4,204).
- **Gold: FALSIFIED** (0 of 4,145 at size; best 1.09; control 0).
- No candidate file, no `forward_eval` parity run (nothing to check; the evaluator is in `gen8.py` and unused).
- **N added: 18,363 + 17,365 draws + 10 information looks = 35,738**; running count about **627,838**, Bonferroni z bar about **5.24**.
- **Prediction check.** Median discovery PF 0.55 / 0.52 (predicted about 0.55 / 0.45: Bitcoin right, gold slightly better than predicted); survivors 0 / 0 (predicted 0 to 10 / 0 to 5: right); both families FALSIFIED (predicted, prior 85%); zero bids under 0.1% (right).

## For the lead

A short round trip in the coin-flip zone is the cleanest test yet of "does anything here predict the next few minutes of the quote", since it never touches settlement and never sits near L1's band. The answer on both markets is no, with GEN7's open interest features included: the best of 5,000 conditioned rules barely covers its cost in discovery, and the base pays about 4c a round trip. This shape (and GEN1's before it) should be marked closed for candle data; only a sub-minute source (the R6 book or a quote lag study such as RECORD1) could change it.

## Files

`src/scalper/gen8.py`, `workers/GEN8_REGISTRATION.md`, `workers/GEN8_FROZEN.md`, `workers/GEN8_frozen_btc.json`, `workers/GEN8_frozen_gold.json`, this file. Row, distinct, control and validation files in `data/gen8_*` (not committed).
