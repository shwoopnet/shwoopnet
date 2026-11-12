# TENNISBREAK, the break after set 1 of a best-of-three tennis match: gap measurement registration (a venue of the MAPBREAK / NHLOT family)

**Registered Nov 12, 2026, before any price or result of a tennis market was read by anyone.** Written by Idea Desk A on the Head of R&D's order of 18:51Z (the History Miner had no rule registered; its `HISTDEPTH_PLAN.md` says so), in the form of `mapbreak/MAPBREAK_REGISTRATION.md` (Desk B, `claude/idea-desk-b`). The reader, the lists job and the scoring are built on the Testing Desk's generic engine `workers/testing/breakplay.py` (`claude/testing-desk`, a8837112): **a new venue is a series file, a small `discover`, and a `VenueConfig`; nothing else.**

`TENNISBREAK | family: a change of game state read from a sibling market while play is stopped; buy the side priced under what the state implies, hold to the end of the match (about an hour) | risk class: mid price, 1 contract, many matches a day, no link to any live strategy | stage Idea, measurement only`

**This stage is a ZERO-TRY gap and cost measurement. No rule is scored, the result of a match is never read, nothing is traded, and nothing here permits an order.**

## Rulings it rests on (Head of R&D)
1. It is the same mechanism as MAPBREAK and NHLOT: a state change while play is stopped, bought and held. **For the owner's count, NHLOT, MAPBREAK and TENNISBREAK are ONE candidate.** It is run because tennis has the events the others lack (hundreds of matches a day across tours).
2. Zero tries at this stage. A rule scored afterwards is 1 try and needs a new go. Held-out refused without the Head's go.
3. Prices come from minute-end candles at the stated instant, two-sided quotes only. Every output carries: "candle freshness measured on Bitcoin 15 minute only, not on tennis".
4. **Wherever this card is quoted, my probability that it reaches the research bar is quoted beside it: 2%.**

## The idea in plain words
A best-of-three match is won by the first player to take two sets. When set 1 ends, Kalshi's set-1 market closes and settles; the players change ends and take a short break. At that moment the match price should jump to what "one set up" is worth. The measurement asks whether, two minutes after set 1 ends, either player's match contract can be bought for clearly less than that.

**Who is on the other side, and why they might not lose:** resting orders left from before the set ended, and bettors anchored on the pre-match favourite. Against that: tennis scores are public point by point and traded by fast participants, and the gap between two sets is only a few minutes, so I expect the measurement to find the gap smaller than the round trip. That is the question.

## What is NOT known yet (pinned from a zero-try structure peek BEFORE anything else is requested)
This file was written before I had seen a tennis ticker. The peek job `TENNISBREAK_PEEK.json` (6 requests, one page of 200 settled markets each in `KXATPSETWINNER`, `KXWTASETWINNER`, `KXATPMATCH`, `KXWTAMATCH`, `KXATPCHALLENGERMATCH`, `KXWTACHALLENGERMATCH`, closes before 2026-10-23, newest first) reads ONLY tickers, event tickers, and open, close and settlement times; **no `result`, price or volume field is read.** From it I will pin, in a dated amendment committed before the series file is frozen: (a) the ticker structure and the key that joins a set-1 market to its match market, (b) whether a set-winner event exists per set (set 1 to 3 or to 5) and how many markets it has, (c) the scheduled-start rule and its guard (set 1 must end between 15 and 120 minutes after the start), (d) which series carry a best-of-three. If the structure does not allow a clean join of a set-1 market to its match market, the card is closed with that finding and no further request is made.

## The state, the instants and the prices (pinned now, in MAPBREAK's form)
1. **Best-of-three only.** Men's Grand Slam matches are best of five and cannot be told from a three-set best-of-three win by the number of set markets, so **the sample starts at 2026-09-15 (after the US Open) and a match is dropped if its date falls inside any Grand Slam fortnight**; the Slam calendar is a date constant in the series file. Matches whose set markets go beyond set 3 are dropped and counted.
2. **The state** is the set-1 winner market: its `close_time` is when set 1 ended and its `result` says which player is one set up. That result is read, because it is the state. **The result of the match market and of any later set is never read; the reader must enforce that in code (the engine asserts it for measurement records).**
3. **Pre-match instant:** the one-minute candle ending at the scheduled start minus 10 minutes (stepping back a minute at a time to minus 40 if not two-sided on the needed contracts); no such candle means "not filled", counted.
4. **The look:** the candle ending at the first whole minute at or after (set-1 close + 120 s); if the two match contracts are not both two-sided there, step FORWARD to set-1 close + 5 minutes; none means "not filled", counted. **Guard:** the set-2 market must close at least 10 minutes after set 1 closed (so the break cannot be confused with play); otherwise the match is dropped and counted.
5. Two-sided means 0 < bid < ask < 1 at the candle's close. Nothing is filled from another minute.

## The model (the engine's `bo3`, one line, and its known leans)
p = the mid, at the pre-match instant, of the match contract of the player who then won set 1; q solved from p = q x q x (3 minus 2q); value one set up V = 1 minus (1 minus q) squared; the other player's value is 1 minus V; the gap for a player = its value minus the ask of its own match contract at the look; the cheaper side is the one with the larger gap. **Known leans, stated before data:** (1) q is treated as fixed, but winning set 1 is evidence the player is better than the pre-match price said (the model undervalues the leader); (2) sets are not independent (momentum, fatigue; a break after a tight set 1 differs from a bagel); (3) a first set lost 6-0 versus 7-6 is not distinguished. The placebo is the point.

## The placebo (what model error alone looks like)
At the pre-match instant no state has changed, and the set-1 winner market prices the very number the model derives: a player's chance of winning one set. So q from the match price is compared with the ask of that player's SET-1 contract at the same minute. Its gap is model error plus quote noise and nothing else; the same statistics are reported for it as for the look. The engine requires it.

## Cells, date constants, what is reported
- **Cells, fixed now:** ATP match, WTA match, Challenger (ATP and WTA together); a pooled line for information; the kill is read per cell.
- **Measurement sample:** matches whose match market closed from 2026-09-15 to before **2026-10-23 00:00 UTC**; the **1,500 most recently closed** best-of-three matches among them, never extended.
- **Held-out:** matches closing from **2026-10-23 00:00 UTC** on. **Not pulled:** the lists job asks only for markets closing before that instant. `heldout_go=True` is the Head's alone.
- **Reported, per cell and pooled (counts first):** matches discovered, dropped and why (counts), filled pre-match, filled at the look, dropped at the pre-match step because the placebo needed two-sided quotes; minutes from set close to the look; the median spread and round trip at the look; the gap distribution (median, quartiles, 90th percentile); the share with a gap of 8c or more and a spread of 4c or less, split by player up and down; the same for the placebo; the registered kill lines (the engine's thresholds: 8c gap, 4c spread, 5c cost, 10 percent share, 150 filled).
- **Try count:** 0 at this stage. If the card survives, ONE rule (buy the cheaper side's own match contract at the look when the gap is 8c or more and the spread 4c or less, 1 contract, hold) is scored once, as 1 try, on a new go.

## What a live version would need (stated now so nobody assumes it)
A second-slot strategy that watches the set-1 market for tennis, reads the match market's candle two minutes after the close and orders a contract, held for about an hour; a new registry entry, caps, kill rules and an owner popup. None of it is proposed here.

READ-ONCE MARKER (held-out): NOT READ.
