# ROUNDCOUNT: round-cent clustering and weekend staleness, a zero-try count (Idea Desk C, Nov 13, 2026)

Quotes only (book.csv levels). No trades, no coverage files, no results, no outcome joined. 0 tries. Script `roundcount.py`; full output `ROUNDCOUNT_OUTPUT.json`. [research]

**Guard (from HELDOUT_REGISTRY.md on rnd-queue):**
- R6: only rows received and markets closing from 2026-10-30T00:00Z to before 2026-11-03T00:00Z, before the earliest held-out date on any of its five series. 2,206 rows outside that span were skipped unopened.
- NC15: only KXAUDUSD15M, closes before 2026-11-19, because every other NC15 series is held out from Nov 3 to 5, before NC15 began. 225,359 other-series rows were skipped by ticker, unparsed.
- The local copies were deleted after the run.

**Sample:** R6 has 4,255,300 level observations (5 YES-bid and 5 NO-bid levels a poll, five series, 4 days including the Oct 31 to Nov 1 weekend). NC15 AUD/USD has 223,257 (Nov 11 to 13, weekdays only).

## (a) Round cents against the four neighbouring cents (ratio; 1.0 = no clustering)

| Cent | R6 resting size | R6 quote presence | R6 best YES bid | NC15 resting size | NC15 presence | NC15 best YES bid |
|---|---|---|---|---|---|---|
| 10c | 2.35 | 2.63 | 1.59 | 1.09 | 1.06 | 1.54 |
| 25c | 1.15 | 1.01 | 1.04 | 1.02 | 1.15 | 1.22 |
| 50c | 1.06 | 1.01 | 1.01 | 0.99 | 1.03 | 1.13 |
| 75c | 1.01 | 1.00 | 0.94 | 0.99 | 1.01 | 1.08 |
| 90c | 0.60 | 0.96 | 0.74 | 0.90 | 0.93 | 0.81 |

**Reading:**
- Only 10c stands out, on R6: about 2.4 times the resting size and 2.6 times the quote presence of its neighbours.
- 25c, 50c and 75c are flat, within about 15%.
- 90c is below its neighbours.
- The 10c pile is on cheap prices near the end of the window, which the cheap-side price rules (row 190) cover.

## (b) Weekend against weekday staleness (R6; US Central day)

| | Book changes | Median time between changes | 90th percentile |
|---|---|---|---|
| Weekday | 204,473 | 2,000 ms | 2,047 ms |
| Weekend | 238,520 | 2,000 ms | 2,039 ms |

**Reading:** the book changes at almost every 2 second poll on both weekdays and weekends. The poll rate is the limit, so this count cannot see staleness finer than 2 seconds, and at that resolution there is no weekend difference.

## Verdict, against the Head's caution (row 190)

**The lead closes.**
- Round cents show no clustering at 25c, 50c or 75c. The one pile, at 10c, is a price-level feature of cheap contracts: any rule built on it is a cheap-side price rule on the same series (row 190), and it gives no non-price field to use.
- Weekend books are no staler than weekday books at the recorder's resolution.
- Nothing here gives a structure that a non-price rule could use.
