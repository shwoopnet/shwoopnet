# REV1 amendment: split the Nov 5 read by whether OICORE fired (REV1SPLIT, 2026-11-03)

**Added BEFORE the Nov 5 read and before any forward outcome of this split was seen.** The registered REV1 claim, bar and verdict words (README, "Pre-registration: REV1") are unchanged. This only adds a readout that is printed beside the registered one.

**Why.** The owner wants the cheap-side Bitcoin rule live as a third strategy that trades only the Bitcoin windows where OICORE does not fire, so it never doubles OICORE's bet. The question the split answers is whether the cheap-NO rule has anything outside OICORE's windows.

**OICORE fired in a window** when Bitcoin open interest rose by more than the threshold over the 3 minutes before the candle ending 180 s before the close: `doi = oi(candle ending 180 s before close) - oi(candle ending 360 s before close)`, the same definition as `REF_GEN6_OICORE` and `mechoi1`. The window is classed the same way for both of REV1's entry times (120 s and 180 s), because OICORE decides at 180 s.

Two versions, both reported, neither chosen after seeing a result:
- **Fixed:** `doi > 86299.56000000001` (as in `workers/candidates/REF_GEN6_OICORE.json`).
- **Trailing 24h p90:** `doi` above the 90th percentile of `doi` over Bitcoin windows that closed in [close - 24 h, close - 900 s]; classed "unknown" with fewer than 40 such windows (`mechoi1.trailing_thr`).

A window with no usable open interest pair is classed **unknown** and shown on its own line, never moved into either half.

**Readout (printed by `python -m scalper.rev1 run`, after the registered line, labelled NOT the registered verdict):** for fired, not fired and unknown, under each version: n, days, win rate against mean price paid, mean net cents (day-clustered z), halves of the days, and the number of entries that sit in a window where OICORE fired (the overlap). It says in words if the NOT-fired half alone has a negative mean. The registered verdict is still the pooled one with the registered bar. The split is analysis (+0 tries). Reading it cannot rescue a pooled FALSIFIED or NOT_ENOUGH_DATA; a pass of the not-fired half alone would be a new claim needing its own registration and its own forward days.

## History information (2026-11-03, NOT the registered read; `python -m scalper.rev1_split_history`)

Bitcoin candles Aug 6 to Nov 3, dates split in thirds as MECHOI1 does; only W1 (Aug 6 to Sep 4) and W2 (Sep 5 to Oct 4) were read, **the last third (Oct 5 on) was not read**. Fee 7% x C x p x (1-p) rounded up, C=10. REV1 was found as the best of 13 cells on this history and OICORE's threshold came from Aug 6 to Sep 21, so both are in sample here. Fixed threshold, W1+W2 pooled:

| REV1 (NO, ask 0.03 to 0.45, 120/180 s) | n (windows) | win vs paid | PF | mean | day z | W1 / W2 |
|---|---|---|---|---|---|---|
| all | 2,909 (1,956) | 20.4% / 16.9% | 1.21 | +2.63c | +2.60 | +2.10 / +3.13c |
| OICORE fired | 359 (252) | 21.7% / 13.3% | 1.81 | +7.64c | +2.86 | +7.23 / +7.94c |
| OICORE not fired | 2,550 (1,704) | 20.2% / 17.4% | 1.15 | +1.93c | +1.68 | +1.48 / +2.37c |

Trailing p90: fired 120 entries +12.14c; not fired 2,777 entries +2.22c (z +2.11). The not-fired half is positive but thin (z under 2, W1 z +0.91, W2 z +1.47) and rests on a 3.3c win-rate gap over price paid; most of the pooled rule's mean comes from the fired half. For the both-sides 0.15 to 0.49 reference (REF_BTC_UNDERDOG_180) the not-fired half is **negative** (-0.49c, n 1,667; W1 -1.12c, W2 +0.06c) and all of its pooled +1.24c is the fired half (+20.30c, n 151). Overlap: 252 of 1,956 REV1 windows (13%) also fire OICORE.
