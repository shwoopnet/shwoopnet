# TRUMPTOPIC1 result (2026-11-04, run once; registration `workers/TRUMPTOPIC1_REGISTRATION.md`, sha256 `1c07ea5d8b7a8effbc77f06577c96813ac7c1bb0da4846f3ff59676b1e73f113`, README ledger entry pushed in commit 9514422 before any price or outcome of these events was joined)

**Verdict: NOT_ENOUGH_DATA (0 treated trades on 0 events; 25 events and 150 trades were the bars). Nothing tuned, nothing promoted.**

## What was run
Held-out third of history only (48 events, 2026-08-06 to 2026-10-02; 794 word markets in the 28 events that had a feed trigger candidate). Model fitted on the first 96 events (to 2026-08-05) only. Candles for every market of the 28 candidate events (794 markets, one process, cache outside the repo). Fit-third trading results were not run (the model saw those outcomes).

## Numbers
- Feed candidates (stem in at least 2 posts in the prior 24 hours): 100 markets in 28 events.
- Of the 100 candidates, **58 had a valid yes bid and ask in the 60 minutes before the look**; **2 had an ask in 3c to 30c**; **0 passed model >= 3x ask**. Treated = 0.
- Why so few: the market already agrees with the feed. Candidate asks sit at the top or the bottom of the scale: many at 0.01 (a word the event already made impossible or the market gave up on; below the 3c floor) and many at 0.5 to 1.00 (the topic is priced in). The model probability for candidates is about 0.56 (median), so the 3x rule asks for an ask under 0.19 on a word that the speaker's own posts say is live, and the market does not leave that. In the whole 794-market set only 557 had a valid quote at the look and 237 had no candle at all.
- Control (every YES with a valid quote and ask 3c to 30c in the same 28 events): **n 28, mean net -8.49c, PF 0.39** (this is the registered control; it is NOT a result of the rule). Win rate and price for the treated: n/a.
- No favourite-side figure was computed.

## Prediction check
Registered: 20 to 45 treated, PF 0.6 to 1.1, NOT_ENOUGH_DATA about 95%. The verdict held; the take-up was wrong by more than 10x (0 against 20 to 45).

## Forward consequence (correction to the registered take-up; the registration is not edited)
The registered forward take-up of 15 to 25 treated a month assumed about half of the candidates survive the price band and the 3x test. Measured: 2 of 100 candidates reach the price band and none the 3x test, so the honest rate is **about 0 to 2 treated a month** (28 events a month, 2 in-band candidates per 48 events). The forward read at 150 treated or 2027-06-30 will therefore be NOT_ENOUGH_DATA with certainty (at most about 10 treated by then); P(pass) is under 1%. The snapshot is cheap (one candle request per market of each new event) and stays as the registered forward record, but it is not worth more than a monthly look. A larger test would need a different entry (the cheap side is rarely both live and cheap here), which is a new registration, not an edit of this one.

## Commands and code
`python -m scalper.trumptopic1 census|history|snapshot|forward`; `src/scalper/trumptopic1.py`; `tests/test_trumptopic1.py` (9 tests, synthetic). Snapshot file `data/trumptopic1_snapshots.csv` (git-ignored; the coordinator keeps it). The snapshot was not run live (no forward event exists yet; first events from 2026-11-05).
