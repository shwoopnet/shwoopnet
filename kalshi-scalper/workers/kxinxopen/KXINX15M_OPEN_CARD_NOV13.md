# KXINX15M-OPEN, card OPENGAP1: the first S&P 500 15 minute window of the day, against the overnight gap carried in Kalshi's own strikes. Desk B, Nov 13, 2026, written 21:20Z by this desk's clock. NO DATA READ (tonight's NC15 and KXINX run was not opened).

CLASSIFICATION CARD (7f): family = open gap fade: cheap-or-near-50c side bought in the day's FIRST window, direction set by the overnight gap; exit style = hold to settlement; risk class: 1 contract, small fixed; signal check: a Kalshi-native field (the index level carried in the strikes), not futures, not open interest, not price at the touch; stage Idea; prior of a pass about 3%; slow family, PAPER LIST.

## What is different about the first window (stated from the Head's description; the exact open time is a time-only fact to read first)
The series' first window of the day starts right after the US cash open (14:30Z) and its strike is the start candle's close, set while the cash market is still settling. Every KXINX15M market object carries that strike (`floor_strike`, an S&P 500 index level) and its `open_time` and `close_time`. So Kalshi's own listing already contains the index level at each window start: **the overnight gap is the first window's strike minus the previous day's last window's strike**, with no outside price, no futures and no Yahoo.

## Mechanism and named counterparty
The first window opens near 50/50 on "above the strike" because the strike is a fresh print. But an overnight gap that is large relative to the first window's normal range has historically partly retraced in the opening minutes (a known opening-gap fade, a weak effect in large caps). The counterparty who loses is the taker or maker who quotes the first window as a coin flip regardless of the gap: they sell the side the gap's retracement favours too cheaply. I name no better counterparty than that quoter; the effect itself may not exist.

## Rule (one threshold, fixed now, no sweep)
For each trading day: gap = (strike of the day's FIRST window) / (strike of the previous trading day's LAST window) - 1, both read from the listing (floor_strike). If |gap| >= 0.25%: in the day's first window, at the decision poll (the last poll at or before 6 minutes before the close, no more than 10 s earlier; NC15 or R6 convention for the KXINX book), buy the side that bets on a RETRACE (an up gap: buy NO; a down gap: buy YES) at its ask if the ask is 0.20 to 0.80 and the spread is at most 0.04; fill check the next poll within 6 s; 1 contract; held to settlement; fee 7% x p x (1 - p) rounded up per order, cash basis. One look, one entry a day, nothing carried.

## Numeric prediction
If the effect exists, the retrace side wins at least 55% against an ask-implied 50% to 52%, cash PF 1.3 or better, positive in each half. The likeliest outcome (my honest read): about 50%, PF under 1.0.

## n needed, and the honest answer: SLOW FAMILY, PAPER LIST
One first window a weekday and the rule fires on perhaps a third of days (my guess, not measured): about 80 to 90 entries a year, so 150 entries is about 20 months away. The series has only a few settled days. **It goes to the paper list; it cannot be a forward test inside the programme's horizon.** A forward shadow could log the gap and the first window's quote each day at no cost (the listing and the KXINX book are public), and the paper count is the number of qualifying days.

## Kill lines and the held-out date
- NOT_ENOUGH_DATA: fewer than 150 entries (the expected outcome for years).
- Early kill: after 40 entries, net below 0 or PF under 1.0: FALSIFIED.
- Pass bar (the lifecycle's): cash PF 1.3 or better over at least 100 fills in 2 of 3 windows, then the research bar PF 1.5 with the held-out read once.
- **Held-out:** HELDOUT_FIRST = 2026-12-01T00:00:00Z (as SPXOI1 and SPXFV1); every day before it is development; it is read once, not before 150 entries exist.

## The four uniqueness checks and the declined list
1. Signal: the index gap carried in Kalshi's strikes, a different field from open interest (SPXOI1), futures (SPXFV1, closed) and price at the touch (DEPTH1). A Kalshi-native field counts as different only if it is a different field with different logic: here it is a cross-day level difference.
2. Counterparty: the first-window quoter anchored on 50/50 (named, weak).
3. Correlation with live strategies: none computable (a series nobody trades); EVENT830 does not list it.
4. Not on the declined list: not flow, not favourite-late (the ask band is 20c to 80c, a retrace bet), not market making, not a time-of-day sweep (one rule with a signal, not a table of hours), not futures. Closest registered ideas: the overnight family (OVN*) in the research registry, which I have not read; the Verification Analyst should check that name by name before any shadow entry.

## Prerequisites before any read (times only)
(a) From a lists run (the SPXOI1 lists run holds KXINX15M markets): the first window's open_time and close_time each day, to confirm "first window" and its length; no prices or results. (b) Count of trading days with a previous day's last strike. No Kalshi request is made by this desk.
