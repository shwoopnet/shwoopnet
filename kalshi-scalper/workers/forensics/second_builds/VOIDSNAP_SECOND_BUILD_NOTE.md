# VOIDSNAP stage 1: independent second build (Forensics desk)

**Written Nov 13, 2026, about 01:27Z, on the Head of R&D's order (VOIDSNAP first, then POLGAPH).** Built from Desk B's card with Amendments 1 and 2 alone
(`claude/idea-desk-b` at `a0cdeebe`, `kalshi-scalper/workers/voidsnap/VOIDSNAP_CARD.md`, sha256 `da37859d...`). Desk B's `voidsnap.py` was not read.
No candle of any of these markets has been requested or read by anyone. No Kalshi request was made for this build. It is a hindsight measurement, not a rule.

## Files

| File | sha256 (first 8) | What it is |
|---|---|---|
| `voidsnap_second.py` | `32243990` (aligned to Amendment 3; the first version was `037c29f5`) | the second build: `sample` (rules 1 to 4) and `measure` (rules 6 to 18 with Amendment 2, all three carries) |
| `voidsnap_compare.py` | `62288c63` | compares Desk B's printed lines with my output, figure by figure; reads printed output only |
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

## Result 2: SAME OUTPUT as Desk B's build on three made-up fixtures (Nov 13, about 01:40Z)

Each fixture has 165 voids and 900 played events at seed 5, the awkward cases listed in the generator's header, and a `hist_` answer that must not be opened.
Desk B ran its frozen scorer (`voidsnap.py`, sha256 `c176146b...`) on the same rows and committed its printed lines (`claude/idea-desk-b` at `8b7fe5ab`,
`voidsnap/fixture_outputs/`). `voidsnap_compare.py` reads those lines and my output and compares every figure.

| Variant | Figures compared | Differ | D1 | D2 | D3 | Verdict in both builds |
|---|---|---|---|---|---|---|
| plain | 166 | 0 | fails | fails | fails | CLOSED, no try spent |
| mixed | 166 | 0 | mixed | mixed | fails | depends on the carry: not decided |
| worth | 166 | 0 | worth a rule | worth a rule | fails | worth a rule |

The 166 figures are: the sample counts and drops; the base rate; voids with no settlement value, with no window, events with any candle; and under each of the three carries
question 1's four references (have it, within 1c, within 3c), question 2 (runs of 5, the same with the ask 15c to 64c, the quartiles of the first run's minute, buyable
side-minutes, median shortfall, one-way cost), each detector's flags, implied share, line 1 count and band count, line 2, line 3's share and pass; which carries each detector
passes under; and the reading.

**How it got there.** My first build (commit `ff481e96`) differed from Desk B's in two places the card had not settled. Desk B wrote both into Amendment 3
(`1af7b80b`, card sha256 `cfababd6...`), each as the stricter reading and as its frozen scorer already read it, and I aligned (my build is now `voidsnap_second.py`, hash below):

1. **No quote after the window ends.** I had carried the last candle to a minute after the market's close. That raised line 3's share by 2 to 5 points on the fixtures.
2. **Question 2 and line 1 count minutes from S minus 180**, not from S minus 185. A difference of at most 16 side-minutes a fixture.

Two print-only notes: on a tie for line 3's best reference the builds may name different references (none did on these fixtures); Desk B's "events with any candle"
counts candles returned for the event, not candles inside its window (my output prints both).

## Result 3: SAME OUTPUT on the landed candle run (Nov 13, 05:35Z): stage 1 reads CLOSED in both builds

Desk B read stage 1 once on its audited scorer (`voidsnap.py`, sha256 `c176146b...`) after Auditor B's structure check of the landed run, and asked for this build on
the same files under rule 16b. The files: candle run `pull/VOIDSNAP_CANDLES/2026-11-13T0244Z_43354200129` on `kalshi-pull-data` (79 of 79 requests answered, none
truncated); lists run `pull/MAPBREAK_LISTS/2026-11-12T1919Z_43289005222`, development answers only; card with Amendments 1 to 3 (`cfababd6...`).

**Order kept:** my output was printed and committed (`b10f83da`, 05:33:57Z, `VOIDSNAP_SECOND_OUTPUT_landed_VOIDSNAP_CANDLES_2026-11-13T0244Z.{txt,json}`) BEFORE I opened
Desk B's printed lines (`voidsnap/stage1_read/desk_b_printed_lines.txt` at `b4ba1a37`). I have not opened Desk B's read note.

**Comparison:** `voidsnap_compare.py` parsed all 53 of Desk B's lines: 157 figures compared, 0 differ, and no tie in a reference name. The sample is the same 195 pairs
(whole-file equality with `VOIDSNAP_SAMPLE.json`).

**What both builds print (a hindsight measurement on voids chosen by their result; an upper bound, not a rule):**

| | Registered carry | 60 minute carry | No carry |
|---|---|---|---|
| Voids with a side buyable 10c under its settlement for 5 minutes in a row, of 195 | 24 | 24 | 14 |
| D1 (frozen after the start): voids flagged, played flagged, implied share of voids | 22, 7, 25.3% | 22, 7, 25.3% | 7, 3, 20.1% |
| D2 (no trade after the start) | 48, 13, 28.4% | 48, 13, 28.4% | 48, 13, 28.4% |
| D3 (ran before the start) | 25, 16, 14.4% | 25, 16, 14.4% | 7, 9, 7.7% |
| Line 1 (needs 40 voids flagged and buyable from the detector's minute): D1, D2, D3 | 0, 0, 7 | 0, 0, 7 | 0, 0, 2 |
| Line 2 (implied share 30% or more) | none | none | none |
| Line 3 (settlement within 3c of a known mid in 70% of voids): best share | 35.9% | 35.4% | 23.1% |

Every detector fails all three lines under every carry. **Reading in both builds: CLOSED, no try spent.** The three carries agree. The one-way cost on buyable minutes
is 3.5c at the median. 16 of the 195 voids had no window at all (closed more than 185 minutes before the start) and stay in every denominator.

In plain words: the fair price was not knowable from the market's own earlier mids (about a third of voids settled within 3c of them, against the 70% the card asked
for), and almost no voided match showed a book standing 10c under its settlement after any of the three detectors could have seen it.

## Places where the card leaves a choice

My build prints these with its output (`readings`). The ones most likely to move a figure are first.

1. **A minute after the window's end** (rule 7): SETTLED by Amendment 3, no quote there. 35 of the real voids closed before the start, so this reading matters on the real rows.
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
- The landed candle answers were compared line by line (Result 3): no shape arose that the two builds read differently.
