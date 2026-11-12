# CFRTI development replay joined to outcomes (Idea Desk A, Nov 12, 2026). Development rows only (closes before 2026-11-05).

Forensics replayed my 68 development signal rows on the R6 books (`claude/forensics-desk`, `CFRTI_DEV_REPLAY.csv`); only 28 have an R6 book (three-venue 16 of 36, Kraken-only 12 of 32; the rest are before the recorder began or in gaps). Joined to the outcomes by `desk_a_verify/cfrti_replay_join.py`. Limit = ask seen, 1 contract, cash PF. **No evidence at n = 16 and n = 12; these are rows to join, not rates.**

| Rows with an R6 book | registered, same rows | R6 replay +2 s | R6 replay +6 s |
|---|---|---|---|
| three-venue (16) | PF 2.14, n 16, 5 wins | PF 3.44, filled 9, 3 wins | PF 3.05, filled 10, 3 wins |
| Kraken-only (12) | PF 1.49, n 12, 3 wins | PF 2.92, filled 7, 2 wins | PF 2.85, filled 7, 2 wins |

Reading: on these rows the misses are NOT the best rows. Three-venue missed 7 at +2 s, 2 of them winners (5 winners in all); the filled set's mean is higher than the registered mean (+20.8c against +13.2c), because the misses include 5 losers. Kraken-only the same (misses 5, 1 winner). The haircut warning of FILLHAIRCUT1 is not visible at this n, and it is not refuted either. 

## Correction (Nov 12, 2026, after Forensics' QUOTEVSBOOK1, `claude/forensics-desk`, 56cca50)
The quote recorder's market list is a copy refreshed about every 11 seconds, so a quote "2 s later" from that recorder is very often the same copy. The quote-recorder replay columns that stood in this note are removed (see STRUCK below); only the R6 book replay is an execution model. Forensics also finds that on the picked (edge) rows the quote ask sits below the book ask more often than on the others (three-venue 31% against 6% of 89, Kraken-only 33% against 6%; no evidence at n = 16 and n = 12 as a rate, direction as a stale-quote selection predicts). What the Nov 20 read measures is for the Head of R&D to rule; this desk has not written a book-signal rule because it would be a new rule and a new try.


## STRUCK (Nov 12, 2026, ordered by the Head of R&D after Forensics' STALE_QUOTE_AUDIT row 18)
The figures of my earlier quote-recorder replay (three-venue +2 s PF 2.48 on 29 of 36 and +6 s 2.24 on 25 of 36; Kraken-only +2 s 1.24 on 29 of 32 and +6 s 1.26 on 26 of 32, with the 13/10/12/9 filled counts on the 16 and 12 rows) are STRUCK from every file. Reason: `replay()` in `cfrti_heldout.py` walked later rows of the same `quotes.csv` list, which is a delayed copy refreshed about every 11 seconds, so a quote "2 s later" is often the same cached copy; it was a quote-recorder replay printed under a book label. The script now fills only from the R6 order book (`r6_replay`).
