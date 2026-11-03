# FLOWHR1 result (DEV scored once 2026-11-03; registration commit 60243c5; code `src/scalper/flowhr1.py`): NOT_ENOUGH_DATA (14 of 150 low-flow trades), sign negative

Signed taker flow on the contract (10 minutes before the 25 minute look, threshold -0.036 fixed, cited from S-FLOW1, not tuned) as a filter on cheap-tail TAKER buys (ask 3c to 30c, ask size >= 10, one per close per side, highest ask) of the hourly Bitcoin ladder KXBTCD, held. Cheap side only; no favourite result exists in the code. DEV = closes 2026-10-29 to 2026-11-01: 97 selected tails in 53 closes, 8 NoData (tape hole), 0 NoFlow. The coordinator had seen MAKERTAIL1's DEV tail outcomes (disclosed in the registration).

| set | n | win vs mean price paid | net per contract (fee x1.0) | PF | z |
|---|---|---|---|---|---|
| low flow (<= -0.036) | 14 | 21.4% vs 23.9% | -3.74c | 0.80 | -0.50 |
| high flow (complement) | 75 | 14.7% vs 15.9% | -2.14c | 0.84 | -0.81 |
| all-flow control | 89 | 15.7% vs 17.1% | -2.39c | 0.83 | -0.86 |

Fee x1.2: low -4.00c (PF 0.79), high -2.33c, all -2.59c. Low-flow halves (n 8 / 6): PF 0.44 / 1.52 (noise at this n). Low minus high: **-1.59c**, the wrong sign for the claim. By side, readouts only: low YES 9 trades PF 0.83, low NO 5 trades PF 0.75; high YES 33 trades PF 0.47 (z -2.96), high NO 42 trades PF 1.15. By ask bucket (low): 3-9c n 0, 10-19c n 4 (all lost), 20-30c n 10 PF 1.10.

**Verdict word: NOT_ENOUGH_DATA** (14 of 150). Sign check: a kill rule would already fire (low-flow PF under 1.5 in the first half and the low-minus-high difference not above 0). HOLDOUT not opened. Counts only, no outcome, for the other windows: HOLDOUT 59 tails (10 low), FORWARD so far 10 tails (5 low).

**Rate and plan.** Low-flow trades per day about 3.5, so 150 needs about 43 days from the start of the data: the forward read (closes from 2026-11-03 16:00Z, `python -m scalper.flowhr1_fwd forward`) will most likely run on its calendar date 2026-12-15 with about 100 trades and report NOT_ENOUGH_DATA unless the rate rises. The flow filter did not separate winners from losers on DEV, and the only visibly different cell (high-flow YES-side PF 0.47) is the opposite of the lead's direction and is not a claim. Tries: 2 (rule and all-flow control). N +4.
