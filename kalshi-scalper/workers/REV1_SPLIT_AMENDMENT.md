# REV1 amendment: split the Nov 5 read by whether OICORE fired (REV1SPLIT, 2026-11-03)

**Added BEFORE the Nov 5 read and before any forward outcome of this split was seen.** The registered REV1 claim, bar and verdict words (README, "Pre-registration: REV1") are unchanged. This only adds a readout that is printed beside the registered one.

**Why.** The owner wants the cheap-side Bitcoin rule live as a third strategy that trades only the Bitcoin windows where OICORE does not fire, so it never doubles OICORE's bet. The question the split answers is whether the cheap-NO rule has anything outside OICORE's windows.

**OICORE fired in a window** when Bitcoin open interest rose by more than the threshold over the 3 minutes before the candle ending 180 s before the close: `doi = oi(candle ending 180 s before close) - oi(candle ending 360 s before close)`, the same definition as `REF_GEN6_OICORE` and `mechoi1`. The window is classed the same way for both of REV1's entry times (120 s and 180 s), because OICORE decides at 180 s.

Two versions, both reported, neither chosen after seeing a result:
- **Fixed:** `doi > 86299.56000000001` (as in `workers/candidates/REF_GEN6_OICORE.json`).
- **Trailing 24h p90:** `doi` above the 90th percentile of `doi` over Bitcoin windows that closed in [close - 24 h, close - 900 s]; classed "unknown" with fewer than 40 such windows (`mechoi1.trailing_thr`).

A window with no usable open interest pair is classed **unknown** and shown on its own line, never moved into either half.

**Readout (printed by `python -m scalper.rev1 run`, after the registered line, labelled NOT the registered verdict):** for fired, not fired and unknown, under each version: n, days, win rate against mean price paid, mean net cents (day-clustered z), halves of the days, and the number of entries that sit in a window where OICORE fired (the overlap). It says in words if the NOT-fired half alone has a negative mean. The registered verdict is still the pooled one with the registered bar. The split is analysis (+0 tries). Reading it cannot rescue a pooled FALSIFIED or NOT_ENOUGH_DATA; a pass of the not-fired half alone would be a new claim needing its own registration and its own forward days.
