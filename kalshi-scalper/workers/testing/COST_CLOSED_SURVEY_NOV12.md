# Rules and cells closed ON COST: a survey for resting limit entries (Testing Desk, Nov 12, 2026, for the Head's 23:00Z request)

No scoring, no outcome opened. Built only from files already landed and from my own registry. A table of where a resting limit entry could change a verdict **if a book and a tape existed to score it honestly**. Saving figures are the half spread (a fill at the mid instead of the ask) and the full spread (a fill at the bid); they are upper bounds on what a resting order could gain, before the risk that it never fills (a resting order is scored only through the through-price rule on a book and tape; unfilled orders are printed, never skipped).

## 1. Rules closed on cost in my registry (the last two weeks)

| rule | line | measured | spread | saving at mid / at bid | book and tape today? |
|---|---|---|---|---|---|
| POL-i2 (politics morning, exit before settlement) | round trip above 5c (Amendment 4) | overall median round trip 9.4c on 73 two-sided quotes, 29 series (evening snapshot, list quotes) | median 6.0c | 3.0c / 6.0c per leg; both legs at the mid would leave about 3.4c of fees alone, under the 5c line | NO: list quotes only (the recorder sample gave 6.3c on 20 series); no book, no tape |

Per series (POLCOST_TABLE_NOV12.csv, politics markets quoted 20c to 80c; 6 of 29 series at or under 5c round trip):

| series | quotes | median spread | round trip | saving at the mid (half spread) | saving at the bid (full spread) | size at touch |
|---|---|---|---|---|---|---|
| KXTRUTHSOCIAL | 2 | 1.0c | 3.6c | 0.5c | 1.0c | 5.5 |
| KXBABELMANDEBWEEKLY | 5 | 1.0c | 4.2c | 0.5c | 1.0c | 4155.3 |
| KXAPRPOTUS | 2 | 1.5c | 4.4c | 0.8c | 1.5c | 1748.7 |
| KXTRUMPACT | 3 | 1.0c | 4.4c | 0.5c | 1.0c | 768.2 |
| KXEOWEEK | 1 | 2.0c | 4.5c | 1.0c | 2.0c | 1.0 |
| KXHORMUZWEEKLY | 3 | 1.0c | 4.5c | 0.5c | 1.0c | 627.9 |
| KXHORMUZPEAK | 3 | 2.0c | 5.1c | 1.0c | 2.0c | 660.1 |
| KXPANAMAWEEKLY | 4 | 2.0c | 5.1c | 1.0c | 2.0c | 6.8 |
| KXDCGOLFVISITCOUNT | 1 | 3.0c | 5.4c | 1.5c | 3.0c | 15.0 |
| KXTRUMPPHOTO | 2 | 3.5c | 6.8c | 1.8c | 3.5c | 255.5 |
| KXTRUMPAPPROVE | 1 | 4.0c | 7.5c | 2.0c | 4.0c | 27.5 |
| KXTRUTHSOCIALD | 2 | 4.5c | 7.6c | 2.2c | 4.5c | 8.5 |
| KXKEVCOUNT | 2 | 5.0c | 8.2c | 2.5c | 5.0c | 1716.4 |
| KXTRUMPNUMSTATES | 1 | 5.0c | 8.3c | 2.5c | 5.0c | 798.8 |
| KXTRUMPMEETM | 9 | 6.0c | 9.2c | 3.0c | 6.0c | 5.0 |
| KXLEAVECONGRESS | 1 | 8.0c | 10.3c | 4.0c | 8.0c | 1.0 |
| KXTRUMPVH | 1 | 8.0c | 10.5c | 4.0c | 8.0c | 3.0 |
| KXTRUMPDELETE | 3 | 8.0c | 10.8c | 4.0c | 8.0c | 24.0 |
| KXTRUMPSTATESMON | 2 | 8.5c | 11.1c | 4.2c | 8.5c | 104.5 |
| KXMAXSHIPSHORMUZ | 2 | 8.5c | 11.4c | 4.2c | 8.5c | 59.0 |
| KXJUDGECOUNTYEAR | 5 | 8.0c | 11.5c | 4.0c | 8.0c | 5.0 |
| KXJUDGECOUNT | 4 | 8.5c | 11.6c | 4.2c | 8.5c | 10.5 |
| KXPRESSBRIEFINGCOUNT | 2 | 9.5c | 12.2c | 4.8c | 9.5c | 101.0 |
| KXTRUMPGOLFD | 3 | 9.0c | 12.2c | 4.5c | 9.0c | 14.0 |
| KXNYTHEAD | 1 | 9.0c | 12.5c | 4.5c | 9.0c | 15.0 |
| KXBILLSSIGNED | 3 | 10.0c | 13.1c | 5.0c | 10.0c | 200.0 |
| KXPARDONSTRUMP | 1 | 10.0c | 13.3c | 5.0c | 10.0c | 200.0 |
| KXTRUMPACTD | 1 | 10.0c | 13.5c | 5.0c | 10.0c | 200.0 |
| KXSUEZWEEKLY | 3 | 28.0c | 31.5c | 14.0c | 28.0c | 20.0 |

## 2. Not in my registry, or not yet measured

- **F7:** not in any file I hold; I cannot fill its row. If it sits on a landed file, send me the path and I add the spread and saving.
- **Sports and esports measurements (TIE3, NHLOT, MAPBREAK, SOCDERIV, ESOCTIE):** NONE has been closed on cost yet, because none has a candle file landed (the lists are landed, the candles are not). Each has a cost kill in its registration and will fill a row the hour its candles are scored. Their cost lines: MAPBREAK, SOCDERIV, ESOCTIE one-way entry cost above 4c; TIE3 is a measurement with no cost kill beyond its spread report.
- **Weather (card 74, WXDAYEND):** closed on existence (0 of 36 city-days with a price at or under 0.96), not on cost.
- **UNRATEROUND:** retired unread on the first-published-vintage count, not cost.

## 3. Data that would let a resting entry be scored

None of the above has a book and tape today. The wheel recorder (Desk B's spec) adds 5-level books for the esports and sports series; the through-price rule also needs a tape, which the spec does not list: ask for it. The pricing functions are in scorekit (taker_exit_net, exit_bid, stop_exit, resting_order, resting_report, round_trip_cost; test_exits.py).
