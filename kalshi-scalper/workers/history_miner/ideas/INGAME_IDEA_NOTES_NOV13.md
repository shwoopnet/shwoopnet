# In-game sports recorder: structure, counts and idea notes for the VA (History Miner, 2026-11-13 ~22:35Z)

At the Head of R&D's order of 22:23Z. **Counts and structure only:**
- no quote, price, size or result value was read;
- the counts come from the coverage files (polls and times) and line counts of the obs files;
- the structure comes from `scripts/record_ingame.py` on main.
Nothing is registered. Each note goes to the VA only after Desk B confirms it has not sent the same idea.

## Structure (from the recorder code)
- **Markets per game:** NBA, NHL and NFL. The moneyline (both teams), plus the two spread and two total markets nearest 50c at the first poll, fixed for the game.
- **Columns:** t_recv_ms, server Date, event, kind, ticker, strike, yes_bid, yes_ask, bid_size, ask_size, last_price, volume. Top of book only, no depth.
- **Cadence:** 20 s while "hot" (a moneyline move of 2c or more since the last poll starts three hot hours), else 120 s. At most 8 hot games and 4 cold games a cycle.
- **No game clock, score or period field:** the state of play can only be inferred from prices and volume.

## Counts (coverage files: every ingame/ run on sports-data, Nov 8 to 13)
- **Games:** 180 events (NBA 67, NHL 80, NFL 33).
- **Successful polls:** 505,080 (NBA 137,538; NHL 231,379; NFL 137,163).
- **Quote rows:** 1,012,160 in the obs files.
- **Followed hours:** NBA 3,841, NHL 5,653, NFL 2,774. These run from a game's first listing poll to its last, so they include long cold pre-game stretches; NFL games are listed days ahead.

## Ideas screened out before any note (closed or a version under 7e and 7g)
| Idea | Why not |
|---|---|
| Book imbalance, or a size wall at the touch, as a directional signal | The same logic as BOOKIMB1 and DEPTH1 on another market, so a version under 7g item 2 |
| Volume burst with no price move (absorption), or the last print far from the mid | Taker order flow (closed family, 7e) |
| Moneyline, spread and total coherence | Lock and parity scans (closed, 7e) |
| Late-game favourite, or a nearly decided total | The favourite-and-hold ban; WXDAYEND's decided-fact count found 0 of 40 |
| Lag between related markets after a jump | INGAMELAG1, INPLAYJUMP (closed for this search by the Head's list) |
| Line drift from listing to kickoff | PREMOVE on another market, so a version |
| Two-sided quoting | Market making closed by evidence (MMSIM1, QUOTE2B) |

## Notes for the VA (held until Desk B replies)
**N1, INTERMISSION:** no-information quote drift during breaks in play.
- **Trigger**, inferred with no clock: a hot game whose moneyline volume does not change for at least 9 consecutive hot polls (3 minutes) after play has begun. That is a break with no trades.
- **Signal:** the moneyline mid's change during that quiet stretch.
- **Bet:** the side that the quiet-time drift moved AGAINST, entered at the first poll after volume resumes, held to settlement (or to a fixed later poll as its own try).
- **Mechanism and counterparty:** makers re-centre their quotes during a break, with no new information, to manage inventory, and the drift is noise to be faded. The counterparty is a maker quoting on inventory, not on information. Weak.
- **What makes it different:** the trigger is the ABSENCE of trades. That is not a jump, a lag, a tie, a parity check or taker flow.
- **Data limits:**
  - top of book only;
  - a fill at the ask seen is an upper bound;
  - about 6 days, so likely "no evidence at n = x" unless many breaks per game qualify.

**N2, SLATE STRAIN:** quote quality when many games are live at once.
- **Note:** this is close to Desk B's SHAREDSTART (a crowded start slot) and is only sent if Desk B and the VA say it differs.
- **Trigger:** the number of games hot at the same time (from the recorder's own polls).
- **Bet:** none fixed. The prior claim is only that spreads widen and quotes go stale when makers are stretched. It is a measurement first; a directional rule would be written before any value is read.
- **If SHAREDSTART is ruled NEW,** this would be a version of it (crowding at start time against crowding in play), so it is likely dropped.
