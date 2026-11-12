# CFRTI-K development rows on the R6 order book: the fill line (2026-11-12)

Asked by the Head of R&D: the 6 second book-replay line for the part of Desk A's CFRTI-K development read that R6 covers. The same test's rows (`desk_a_verify/cfrti_k_dev_rows.csv` on `claude/idea-desk-a`: 65 trades closing 2026-10-29 22:15Z to before 2026-11-05, no outcome column), replayed with the fixed convention (1 contract, walk the levels to the limit, first poll at least 2 s or 6 s after the decision and within 4 s of that). Outcome from the R6 coverage file. Fee unrounded, as CFRTI-K registered. No new try. Scripts `cfrti_dev_replay_grid.py`, `cfrti_k_replay_line.py`; output `results/CFRTI_K_DEV_REPLAY_GRID.csv`, `results/CFRTI_K_REPLAY_LINE.json`.

53 of the 65 rows have an R6 book and a result (the other 12 fall in recorder gaps).

| Line, 53 rows | Trades | Wins | Cash PF | Mean per trade |
|---|---|---|---|---|
| Paper, at the candle ask (the registered line on these rows) | 53 | 8 | 1.06 | +0.7c |
| Book replay, 2 s, limit at the ask seen | 37 of 53 fill | 6 | 1.45 | +4.4c |
| Book replay, 2 s, limit +1c | 44 of 53 | 6 | 1.21 | +2.1c |
| **Book replay, 6 s, limit at the ask seen** | **38 of 53 fill** | **5** | **1.23** | **+2.2c** |
| Book replay, 6 s, limit +1c | 40 of 53 | 5 | 1.17 | +1.6c |
| The 15 rows that MISS at 6 s, at their paper price | 15 | 3 | 1.35 | +4.5c |

**Label: no evidence at n = 38.** Eight winners in 53 rows decide every figure here.

## What it says about line (b) of the development read

Line (b) dropped the rows whose ask was 1c or more higher in the NEXT one minute candle and read PF 0.16 on the rest, and the result page concluded that the whole registered edge sits in rows that could not be filled. On the part where real fills can be checked, that conclusion is not supported:

- A real 6 second order fills 72% of these rows (38 of 53), and the filled set keeps 5 of the 8 winners. It is not worse than the paper line; at this size it is not distinguishable from it.
- "The ask was higher 60 seconds later" is not a fill test for an order that arrives in 2 to 6 seconds. With two minutes left, a cheap side that is going to win is the side whose ask is rising over the next minute. So line (b) removes rows by a value measured after the decision that is itself partly the outcome arriving: it is biased AGAINST the rule, and PF 0.16 overstates the damage.

This does not rescue CFRTI-K. Its registered line is PF 1.07 on 601 trades with z 0.60, nowhere near any bar, and the replay line is "no evidence". The correction is only to the stated reason: the honest reading is "no edge shown", not "an edge that exists but cannot be filled".

## Limits

53 rows, six days. Book polls 2 s apart. The book's ask at the decision is 0.65c above the candle's ask on average on these rows and within 1c on 75% (single prior poll, up to a few seconds old). Not checked by the Verification Analyst.
