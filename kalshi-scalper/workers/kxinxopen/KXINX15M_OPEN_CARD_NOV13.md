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

## Dated line, Nov 13, 2026, 21:25Z (the Verification Analyst: NEW, paper list only)
The VA scored OPENGAP1 NEW (V2's OVN1 to OVN4 are gap fades on Kalshi perp reference prices: OVN1, OVN2, OVN3 NOT_ENOUGH_DATA, OVN4 FALSIFIED as a spread measurement; S14 (gold reopen gap fade) NOT_ENOUGH_DATA, n 11; no 7e row names a gap fade; the source differs, so the two-NOT_ENOUGH_DATA closing rule does not close it). Paper list only, slow family.
- **The gap is an index move carried in the listing's strikes, with no fair-value comparison:** it is the first window's floor_strike over the previous trading day's last window's floor_strike, both fields of the Kalshi market objects, and the rule never compares a Kalshi quote with a model price, a futures price or any outside reference, so it is not the closed "quote lags an outside reference" family (the Head to confirm).
- **Paper screen (the VA's lower screen for a slow family):** 30 independent events (qualifying days), positive in both halves, with a pinned cutoff. **Pinned cutoff constant for this card: HELDOUT_FIRST = 2026-12-01T00:00:00Z** (a date constant, never an event count): every qualifying day closing before it is development; the held-out is every day from it, read once, and not before 30 independent qualifying events exist for the paper screen (150 entries for the fuller bar).

## Dated line, Nov 13, 2026, 21:29Z (the Head of R&D's two fixes before registration; Charter 6.8)
- **Own held-out constant, a named line (not a reuse of SPXOI1's or SPXFV1's): HELDOUT_OPENGAP1 = 2026-12-01T00:00:00Z.** Every trading day whose first window closes before it is development; every day from it is the held-out, read once. (The earlier line "HELDOUT_FIRST = 2026-12-01T00:00:00Z" in the previous section is superseded by this name; the value is the same.)
- **Paper screen this card is judged on:** 30 independent events (qualifying days), both halves positive, with the pinned cutoff above (Charter 6.8); a slow family, so the fuller bar (150 entries, PF 1.3) is a long way off.
- **Label: UNPROVEN.** Cards read for the novelty check, as the VA reported: 8 (V2's OVN1, OVN2, OVN3, OVN4; S14; and DEPTH1, IDX1, XLADDER1 for the field). No result of any kind has been read for this card. Status: first new mechanism admitted on Nov 13, 2026, PAPER LIST only.

## Exit variant (dated 2026-11-14, before any data is read; owner's standing rule: one exit variant beside hold, fixed in the card, counted as its own try)
Beside hold to settlement, ONE variant, fixed now: sell at the bid of the candle ending 180 seconds before the close (3 minutes left), at that bid minus the haircut slip s (1c, then 2c), per-order rounded fee on the exit order; a candle that is not two-sided at that minute moves to the next two-sided candle through the close, else the position is held to settlement. Entry, band, spread cap and the 0.25% gap threshold are unchanged, and the variant is its own try (a second read, counted in the deflation), not a sweep. Both arms print at 1c and 2c (rule C7) and carry "upper bound, not fill-checked" (C9). Because the variant exits in the last 3 minutes but before the last 2, 1c stays primary (C8). Nothing is read until the data covers at least 30 independent days, so under the paper-list screen this card still reads as "no evidence at n = x" until then.
