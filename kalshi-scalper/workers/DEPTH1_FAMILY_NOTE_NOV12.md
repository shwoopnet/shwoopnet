# DEPTH1 and NC15DEPTH1: which family? (Idea Desk A, Nov 12, 2026; written before any DEPTH1 row is opened; for the Head of R&D's ruling)

Lifecycle 7f: family = entry mechanism plus exit style. No data was opened to write this; the facts are from the two registrations (`DEPTH1_REGISTRATION.md` on V2's branch, `NC15DEPTH1_POOLED_REGISTRATION.md` here).

## DEPTH1 (V2, registered 2026-10-30; gold and Bitcoin 15 minute books, R6)
- **Entry mechanism:** a taker buys the implied side (1 contract at the best ask, 1 s after a fixed look 8 minutes before the close, ask 0.10 to 0.90) when one of 10 frozen features of the order book says so; one try per feature per market (20 tries).
- **Exit style:** none; hold to settlement.
- **What the signal is:** mostly RESTING BOOK STATE, with two flow-like features. Eight features read the book alone: five-level imbalance (f1), touch imbalance (f2), size-weighted mid minus mid (f3), the change in imbalance over 30 s and 60 s (f4, f5), hole asymmetry (f8), book slope (f9), imbalance within 3c (f10). One (f6, thin-side depletion over 60 s) is a change in book sizes, which is flow-like in effect. One (f7, net sweeps in the last 60 s) is TAPE flow: taker sweeps counted from the trade tape.
- **Against the closed family:** FLOW1 and TAPEFLOW1 used signed taker flow totals and RESIL1 used a tape sweep plus a price refill, so the closed family is "taker order flow from the tape". DEPTH1's f7 is inside it; f6 is at its edge (a book change); f1 to f5 and f8 to f10 are static or slowly changing book SHAPE, which none of the three closed tests used (RESIL1 deliberately used no size). So DEPTH1 is a MIXED test: eight features outside the family, f7 inside, f6 arguable. **My answer: classify by feature, not as a block: if a feature clears, it takes the family of the feature that cleared (f7, and f6 if ruled so, inside the closed family; the rest in a book-shape family).** A caveat that cuts the other way: the Verification Analyst found R6 sizes change every 2 s at every level, so book SHAPE features may measure noise; the read prints a no-label noise description beside the result (`DEPTH1_READ_NOTES_DESK_A.md`).

## NC15DEPTH1's pooled cell (registered here today)
- **Entry mechanism:** a taker buys the thin side (1 contract at its best ask, 1 s after a look 10 minutes before the close, ask 0.10 to 0.90) when the five-level imbalance is 0.50 or more in absolute value, on the eleven non-crypto 15 minute series pooled.
- **Exit style:** none; hold to settlement.
- **What the signal is:** RESTING BOOK STATE ONLY (the same quantity as DEPTH1's f1); no tape, no flow, no sweep. So it is outside the closed taker-flow family by its signal; it is the same sub-family as DEPTH1's static book-shape features, and it should be ruled together with them (a book-shape family). It shares DEPTH1's size-noise caveat.

## What I am not claiming
That a book-shape family is open for new tries: DEPTH1 and NC15DEPTH1 are both registered and counted, and nothing about either's rule, cutoff or script changes with the ruling. If the Head of R&D rules both inside the closed family, they run once as registered for the record only.
