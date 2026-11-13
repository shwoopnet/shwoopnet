# SHAREDSTART: crowded start slot, underdog arm (DRAFT, NOT REGISTERED, NO VALUE READ)

Status: DRAFT Nov 13, 2026. VA ruling: provisionally NEW as a trigger (no attention or dilution row on the 7e table), with conditions. Not counted toward the 20 to 30 until the three gates below pass. Only the underdog arm is runnable (the favourite arm is the favourite-and-hold ban). A first draft named college basketball; no basketball candles are landed, so this draft is for NHL and esports (the NHLOT and MAPBREAK runs). The college basketball version is parked until a pull is allowed.

## Gates before ANY value is read
1. The VA confirms `occurrence_datetime` is the game start for hockey and esports (the field exists in both lists runs; what it means is unchecked; tennis has no fixed start and the expected-expiration time is a different thing).
2. Auditor B rules on overlap with NHLOT's and MAPBREAK's held-out windows (both MAPBREAK places are withdrawn, their cards' held-out still binds, rule 17).
3. The VA rules NEW on this market set, with the uncrowded-underdog control below.
Also: scorer frozen by commit and sha256 and audited CLEAN before any landed file is opened (16/16b); expected figures written first.

## Treatment (fixed before data)
- Slot: markets whose `occurrence_datetime` is the same minute. Crowd count N = number of distinct games in that slot. Crowded = N of at least 5 (hockey) and at least 8 (esports maps); the thresholds are fixed now and not tuned.
- Entry: in the last hourly candle before the start, buy the UNDERDOG side (the side priced under 50c) when its ask is 5c to 40c and the YES spread is 3c or less. One entry per game.
- Exit: headline hold to settlement; variant out at the start (hockey) or at the first in-play candle. Exit variant counted as its own try.
- Size: 1 contract, read only.

## Control (the VA's condition 1)
Every UNCROWDED underdog (N below the threshold) on the same candles, same price band and spread rule. The claim is only that crowded minus uncrowded is positive; if the crowd count adds nothing over the control the rule is a cheap-side price rule and is ruled a version (not counted).

## Costs and reads (C1 to C10, haircut d3b5f24e)
Entry ask +1c, exit bid -1c, fees per-order rounded, every figure at 1c AND 2c, a rule counts only at PF 1.3 with both halves 1.0 or better at 1c AND PF 1.0 or better at 2c, void refunds the price and keeps the fee and the void count is reported, every line "upper bound, not fill-checked". Cluster by slot or date (games in one slot share a day).

## Counterparty and prediction
Counterparty guess: no competing makers in a crowded slot, so quotes on thin games are stale (weak; "none named" if the VA does not accept it). Numeric prediction: crowded-minus-uncrowded cash PF difference at least 0.3 at 1c. Kill: crowded PF under 1.0 in either half or the difference under 0 at 2c.

## Data and held-out
Development: landed NHLOT and MAPBREAK candle runs only, before a date constant set by Auditor B's overlap ruling; held-out after it, read once. No new pull. Sample size is unknown until the lists are counted; "no evidence at n" if under 30 independent slots.
