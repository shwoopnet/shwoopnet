# breakplay: the generic break-in-play engine (Testing Desk, Nov 12, 2026; Head's 18:24Z request)

`kalshi-scalper/workers/testing/breakplay.py` (tests: `test_breakplay.py`, and `test_mapbreak.py` through MAPBREAK). **A new venue of the family is a series file, a small `discover` function that turns settled lists into records, and a `VenueConfig`; not a new program.** Research only; zero tries at the measurement stage.

## What a venue supplies

- **Records**, one per match: `cell, key, S` (scheduled start, epoch), `state_close` (when the state market closed), `up` and `down` (team ids; `up` is ahead after the state change), `match {team: ticker}` (the contracts bought), `placebo {team: ticker}` (contracts that price the same single-state number at the pre-match instant). The SCORING path may add `result_up` (did `up` win the match); the measurement path must not (asserted: it raises if a record carries a result).
- **A model** from the registry `MODELS` (`bo3`; `bo5_after_map1`, checked at 11/16 for q = 0.5): the pre-match mid of the `up` team's match contract gives the value of each side after the state change and the placebo values.
- **A `VenueConfig`**: model, pre-match back-off (default 10 minutes, searched back to 40), the look (default close + 120 s, stepping forward to + 300 s), thresholds (8c gap, 4c spread, 5c cost, 10 percent share, 150 filled), the held-out constant, the freshness line, and the pack limits for the candle job.

## What the engine does (and enforces)

`measure`: the zero-try gap measurement per cell: filled pre-match, the count dropped at the pre-match step although the match contract was two-sided (what the placebo requirement cost), filled at the look, minutes from state close to the look, median spread and round trip at the look, gap median, quartiles, 90th percentile, the 8c-and-4c share split by team up and down, the same for the placebo, the registered kill lines. `candle_job`: a pull job packed by scheduled start (minutes x tickers at most 9,000, at most 100 tickers). `score_rule`: the REGISTERED RULE (buy the cheaper side's own match contract at its ask at the look when the gap is 8c or more and the spread 4c or less, 1 contract, hold): cash PF with n by window (three chronological windows), event-clustered z (one trade per match) with a day-clustered z beside it, the haircut table, the labels of the standing rules (under 100 trades "no evidence at n = x"). Only two-sided minute-end candles are used (0 < bid < ask < 1), nothing is filled from another minute, the look moves forward only, the pre-match search back only. **A record whose state close is at or after the venue's held-out constant is refused unless `heldout_go=True` (the Head's go).**

## Venues built on it

- **MAPBREAK** (`mapbreak.py`, Desk B's registration 50a1729b): esports best of three; model `bo3`; `discover` = `matches()`. The CLI has `measure` (no result read) and `score` (the registered rule, development read only).
- Coming (Desk B, History Miner): basketball quarter and half breaks, NHL intermissions, tennis set breaks, soccer half time, e-soccer Tie. Each needs: its series file (hash-checked), a `discover` that builds records from the settled lists (using only the state market's own close and result), a model entry if the value formula differs, a lists job builder, and a config.
