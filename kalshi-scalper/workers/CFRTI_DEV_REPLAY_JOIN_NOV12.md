# CFRTI development replay joined to outcomes (Idea Desk A, Nov 12, 2026). Development rows only (closes before 2026-11-05).

Forensics replayed my 68 development signal rows on the R6 books (`claude/forensics-desk`, `CFRTI_DEV_REPLAY.csv`); only 28 have an R6 book (three-venue 16 of 36, Kraken-only 12 of 32; the rest are before the recorder began or in gaps). Joined to the outcomes by `desk_a_verify/cfrti_replay_join.py`. Limit = ask seen, 1 contract, cash PF. **No evidence at n = 16 and n = 12; these are rows to join, not rates.**

| Rows with an R6 book | registered, same rows | R6 replay +2 s | R6 replay +6 s | my quote-recorder replay +2 s / +6 s |
|---|---|---|---|---|
| three-venue (16) | PF 2.14, n 16, 5 wins | PF 3.44, filled 9, 3 wins | PF 3.05, filled 10, 3 wins | 2.05 (13) / 1.75 (12) |
| Kraken-only (12) | PF 1.49, n 12, 3 wins | PF 2.92, filled 7, 2 wins | PF 2.85, filled 7, 2 wins | 1.79 (10) / 1.46 (9) |

Reading: on these rows the misses are NOT the best rows. Three-venue missed 7 at +2 s, 2 of them winners (5 winners in all); the filled set's mean is higher than the registered mean (+20.8c against +13.2c), because the misses include 5 losers. Kraken-only the same (misses 5, 1 winner). The haircut warning of FILLHAIRCUT1 is not visible at this n, and it is not refuted either. Fill status at +2 s agrees with my quote-recorder replay on 12 of 16 (three) and 9 of 12 (Kraken-only) rows; the quote-recorder replay fills 13 and 10 where R6 fills 9 and 7, so it is more generous (it uses 1 quote stream, no size test, no 2 s arrival lag). Forensics' point 2 (the R6 ask just before t0 already above the ask seen on several rows) means part of the model edge on those rows was an ask already gone; I have not tried to correct for it.
