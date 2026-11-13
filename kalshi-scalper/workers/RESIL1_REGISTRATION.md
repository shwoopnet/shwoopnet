# RESIL1 (registered Nov 12, 2026, BEFORE any RESIL1 event is built or scored)

Order-book resilience after a sweep. Idea Desk A, on the Head of R&D's order (Nov 12 16:00Z). Research only: no order, no key, no Kalshi request (files already held). Card: `IDEA_DESK_A_NOV11.md` card 6. Not a duplicate: DEPTH1 and BOOKIMB1 use static sizes, FLOW1 and TAPEFLOW1 use signed flow totals; this uses whether the touch PRICE comes back after a sweep. Family: order flow (FLOW1 and TAPEFLOW1 FALSIFIED; a third FALSIFIED closes it). Counterparty (hypothesis): resting quotes one level behind a swept price that are slow to move; if the result cannot support it, "no counterparty named".

## The rule (one, fixed now)
- Data: `quote-data:book15r6/` (books, 2 s, exchange time per the run's Date-header offset) and its `trades.csv.gz` tape (`created_time`, `yes_price_dollars`, `count_fp`, `taker_outcome_side`), five series (KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M), pooled, one test.
- **Sweep (from the tape):** within one whole second (`created_time` truncated to the second), taker prints of ONE side at two or more distinct prices. Event time = the end of that second. A taker "yes" sweep buys YES upward; "no" the reverse.
- **Only sweeps 12 to 4 minutes before the close** (so the entry below is 3 or more minutes before the close). The FIRST qualifying sweep of a market window is its event; later sweeps in the same window are ignored (one unit per window).
- **Refilled (price-based; no size is used anywhere):** the swept side's best ask (for a "yes" sweep the YES ask = 1 minus the best NO bid; for "no" the NO ask = 1 minus the best YES bid) at the first R6 poll at least 2 s after the event, and at the next poll within 6 s of the event, is at or below its value at the last poll at least 0.25 s before the sweep's first print. Refilled = both polls. NOT refilled = either poll above the pre-sweep ask. A missing poll = no event (counted).
- **Trade:** only when NOT refilled: buy the swept side (taker "yes" sweep: YES; "no": NO) at its best ask at the first R6 poll at least 60 s after the event (the bot's one minute cadence), ask 0.10 to 0.90 with at least 1 contract displayed, else no trade; 1 contract; held to settlement; fee 0.07 x p x (1 - p) unrounded, cash. No resting order, no exit.
- Descriptive only, no try: the same entry for the REFILLED arm, printed beside it.

## Sample, labels, count
- **Development:** windows closing from 2026-10-29T22:15Z to before 2026-11-05T00:00Z with an R6 book and tape. **Held-out:** closes on or after 2026-11-05T00:00Z; the folders with closes of Nov 9 to Nov 13 stay unopened until DEPTH1's single read has been committed (not before 2026-11-14); the held-out is read ONCE, after that, by this script. Marker: NOT READ.
- **Labels:** development cash PF under 1.0 with n of 100 or more = FALSIFIED on development; n under 100 = "no evidence at n = x"; anything else carried to the held-out. Held-out: cash PF 1.3 or better with a positive mean on 100 or more trades = RE-TEST lead; under 1.0 on 100 or more = FALSIFIED; else "no evidence at n = x". The research bar (cash PF 1.5 in each third, z 5.46 on the shared strict N of about 2,113,000) is reported beside it; a clear is never called a research-bar pass.
- **Tries: N +1** (one rule, one pooled figure). Script: `desk_a_verify/resil1.py`, committed and self-tested before any event is scored.

## Dated line (Nov 13, 2026)
RESIL1 was FALSIFIED on development (independently re-run by the Verification Analyst, Nov 12, 2026). It holds nothing: no forward window and no held-out read remain for this card; the held-out window named above is void.
