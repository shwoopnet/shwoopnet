# VOIDSNAP stage 1: independent second build (Forensics desk)

**Written Nov 13, 2026, about 01:55Z, on the Head of R&D's order (VOIDSNAP first, then POLGAPH).** Built from Desk B's card with Amendments 1 and 2 alone
(`claude/idea-desk-b` at `a0cdeebe`, `kalshi-scalper/workers/voidsnap/VOIDSNAP_CARD.md`, sha256 `da37859d...`). Desk B's `voidsnap.py` was not read.
No candle of any of these markets has been requested or read by anyone. No Kalshi request was made for this build. It is a hindsight measurement, not a rule.

## Files

| File | sha256 (first 8) | What it is |
|---|---|---|
| `voidsnap_second.py` | `037c29f5` | the second build: `sample` (rules 1 to 4) and `measure` (rules 6 to 18 with Amendment 2, all three carries) |
| `make_voidsnap_fixture.py` | `23f6a045` | invented lists and candles in the pull-run shape; three variants |
| `VOIDSNAP_SECOND_OUTPUT_fixture_seed5_{plain,mixed,worth}_MADE_UP_DATA.{txt,json}` | | my build's figures on the three fixtures |

Commands:

```
python3 -I make_voidsnap_fixture.py <dir> 5 plain      (also: mixed, worth)
python3 -I voidsnap_second.py sample  --lists <lists run> --compare <VOIDSNAP_SAMPLE.json>
python3 -I voidsnap_second.py measure --lists <dir>/lists --candles <dir>/candles
```

## Result 1: the sample is reproduced

From the landed lists `pull/MAPBREAK_LISTS/2026-11-12T1919Z_43289005222`, opening only the five answers to request `live_KXCS2GAME` (the `hist_` answers were not opened),
rules 1 to 4 give 195 voids, 1,811 played events, no drops, and the same 195 pairs in the same order as Desk B's `VOIDSNAP_SAMPLE.json` (sha256 `583561d0...`).
The compare is a whole-file equality of window, base, drops and pairs.

## Result 2: figures on three made-up fixtures (mine only so far)

Each fixture has 165 voids and 900 played events at seed 5, the awkward cases listed in the generator's header, and a `hist_` answer that must not be opened.

| Variant | D1 | D2 | D3 | Verdict |
|---|---|---|---|---|
| plain | fails | fails | fails | CLOSED, no try spent |
| mixed | mixed | mixed | fails | depends on the carry: not decided |
| worth | worth a rule | worth a rule | fails | worth a rule |

The comparison with Desk B's build on the same rows is still to come: this note is updated with "same output, every printed figure" or the first difference.

## Places where the card leaves a choice

My build prints these with its output (`readings`). The ones most likely to move a figure are first.

1. **A minute after the window's end** (rule 7), for example S when the market closed before S. I carry the last candle inside the window to it, under the carry in force.
   The card's detectors have their own "closed" test; question 1 and line 3 do not. 35 of the real voids closed before the start, so this can move line 3.
2. **Window edges** (rule 6). I count a candle ending exactly at S minus 185 minutes and one ending exactly at the window's end as inside.
   A batched request also returns candles outside an event's own window; I do not see them.
3. **What is "one side missing"** (rule 7). I need a bid above 0.00 and an ask under 1.00. A bid of 0.00 with a real ask is not a quote.
4. **The 60 minute carry**: a candle that ended exactly 60 minutes before the minute counts.
5. **D1**: a present candle after S that is not a quote fails D1. Only the first-named contract's candles are looked at.
6. **D2**: an event with no candle after S has volume 0 and is flagged unless it has closed. "Closed" is the event's close (the later of the two contracts).
7. **Line 1 and the carry**: the void must be flagged by the detector under the same carry as the run.
8. **Line 1's band count**: five consecutive minutes in which the same side is buyable and its ask is 15c to 64c.
9. **Question 2's printed summaries**: the first run's minute is the earliest over a void's two sides, printed as lowest, median, highest; the median shortfall and the
   one-way cost are over every buyable (void, side, minute); the fee is taken at the ask plus 1c and rounded up to the cent.
10. **The implied share with no flagged event** is "n/a" and line 2 fails.
11. **Line 3's best reference** is chosen under each carry on its own; a tie names the earlier reference.
12. **Drop order** (rules 2 and 3): not two contracts, no close time, no ticker clock, outside the window, neither void nor played. All are zero on the real lists.
13. A void contract with no listed settlement value is never buyable and is a miss in question 1. None on the real lists is expected; it is counted.

## Limits

- The fixtures are invented. Agreement on them shows the two builds read the card the same way on the planted cases, not that either is right about the market.
- The real candle answers may hold shapes neither build has met (as REMATCH's omitted minutes did). The first run on landed candles is compared line by line again.
