# REMATCH stage 1: independent second build (Forensics desk, 2026-11-13)

Ordered by the Head of R&D under rule 16b (a verdict is recorded only when the audit is CLEAN and an independent second build prints the same figures on the same landed file). Built from Desk B's registration and Amendments 1 to 6 (`rematch/REMATCH_REGISTRATION.md`, `REMATCH_SERIES.json` on `claude/idea-desk-b`).

**Disclosure.** This desk leak-tested Desk B's stage 1 scripts on Nov 12 and scanned them for float comparisons on Nov 13, so it had seen their code. The second build was written from the text; the ten places where the text leaves a choice are listed in the scorer and printed with every run.

**What was read.** Development only: the candles run `REMATCH_STAGE1_CANDLES/2026-11-13T0010Z_43334957211` and two lists runs (below). Counts and cost only; no bet scored. The result of an earlier match is read only to name its loser; the result of a later match is never read (the results table is deleted before any candle is opened).

## Result: the same output, every printed figure

On the lists the stage 1 pairs were built from (`INPLAYJUMP_LISTS/2026-11-13T0001Z_43333651862`):

| Figure on Desk B's page | Desk B | Second build |
|---|---|---|
| Events left out (not two team codes, no clock, no close time) | 0, 0, 0 | 0, 0, 0 |
| Matches in the slice | 3,823 | 3,823 |
| Start check, closed 4 to 90 minutes after the ticker clock | 3,680 (96.3%) | 3,680 (96.3%) |
| Pairs qualifying by schedule | 2,934 | 2,934 |
| Earlier match had a winner | 2,450 | 2,450 |
| Earlier match closed 300 s or more before the decision minute | 2,404 | 2,404 |
| No candle at the reference minute or the 5 minutes before | 2,276 | 2,276 |
| One-sided at the reference minute | 43 | 43 |
| Two-sided at the reference minute | 85 | 85 |
| Of those, spread 4c or less (tradeability) | 0 | 0 |
| No candle at the decision minute or the 5 before | 62 | 62 |
| One-sided at the decision minute | 0 | 0 |
| Two-sided at the decision minute | 23 | 23 |
| Of those, no candle at the entry minute or the 5 before | 1 | 1 |
| Instants read from the exact minute / from an earlier candle | 614 / 1,010 | 614 / 1,010 |
| State: fell 5c or more | 19 | 19 |
| Entries that pass the band and the spread | 3 | 3 |
| Placebo pool / placebo entries | 0 / 0 | 0 / 0 |
| Days in the slice | 8 | 8 |
| Projected development bets over 15 days | 6 | 5.6 |
| Projected tradeable pairs | 0 | 0 |
| One-way entry cost, all quotes: median over n | 3.5c over 3 | 3.5c over 3 |
| One-way entry cost, exact-minute quotes only | 3.0c over 1 | 3.0c over 1 |
| The worse of the two | 3.5c | 3.5c |
| Entries priced from the exact entry minute | 1 of 3 | 1 of 3 |
| Diagnostic: close minus ticker clock, minutes | 10, 13, 14 | 10.4, 13.4, 13.7 |
| Closed under 9 minutes after the clock | 0 of 3 | 0 of 3 |
| Stage 1 line | CLOSED | CLOSED (tradeability 0 under 300; projected bets 5.6 under 300) |

Of the 18 state pairs with a two-sided entry instant, the second build also shows why 15 are not entries: 10 on an entry spread over 4c, 5 on an entry ask outside 20c to 80c.

## One point for the record (it moves no verdict figure)

Desk B's page names `ESOCTIE_LISTS/2026-11-12T2031Z_43301161879` as its lists input. That file also holds Oct 8 to Oct 14. Read on it, the second build forms 16 more pairs by schedule (2,950) and 13 more eligible pairs (2,417): the later match closes in the slice on Oct 15, the earlier one closed on Oct 14, just before it. Their tickers were never in the candle job (it was built from INPLAYJUMP's lists, which start at Oct 15), so all 13 fall into "no candle" (2,289) and every other figure is unchanged. The registration does not say whether the EARLIER match must close inside the slice. One sentence would settle it; either reading gives CLOSED.

## The Head's extra count: were the 2,276 unquoted or just quiet? (presence of a candle only, no price read)

| Of the 2,276 eligible pairs with no candle at the reference minute or the 5 minutes before | Count |
|---|---|
| Ticker was asked for in a candle request | 2,276 |
| Some candle somewhere in the pulled file | 2,265 |
| No candle anywhere in the pulled file | 11 |
| A candle at or before the reference minute, more than 5 minutes before it | 1,080 |
| First candle only after the reference minute | 1,185 |
| A candle between the reference minute and the entry minute | 2,226 |

What it does and does not say:
- Almost all of these markets (2,265 of 2,276) produced candles in the pulled window, and 2,226 produced one between the reference minute and the entry minute. They were not dead markets.
- 1,080 had a candle earlier than the 5 minute reach of the missing-candle rule. If Kalshi leaves out a candle when nothing changed, those were quiet for more than 5 minutes at the reference minute, not unquoted. The count cannot prove the quote was two-sided (no price was read, by design).
- 1,185 show nothing from the start of their request's window up to the reference minute. That is either no quote yet, or a quote unchanged since before the window began (the window starts 8 minutes before the earliest reference minute in its request). The file cannot tell the two apart.
- Among the 85 pairs that WERE two-sided at the reference minute, 82 were read from an earlier candle and only 3 from the exact minute, and over all eligible pairs 1,010 of 1,624 present instants were carried. So on these markets a missing minute is the normal case, unlike the Bitcoin 15 minute markets, where every minute had a candle. That fits "a candle is left out when nothing changed", but it was not measured against a book here.
- The registered rule (Amendment 4) drops all 2,276 either way, and the tradeability count is 0 of the 85 that were two-sided. The verdict does not rest on this count.

## Files

`rematch_stage1_second.py` (the second build; `python3 -I rematch_stage1_second.py <lists run> <candles run>`), `REMATCH_STAGE1_SECOND_OUTPUT_inplayjump_lists.json`, `REMATCH_STAGE1_SECOND_OUTPUT_esoctie_lists.json`.
