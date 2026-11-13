# Order book and tape field cards, Desk B, Nov 13, 2026, written 18:51Z by this desk's clock

NO DATA READ. These cards come from the recorder schemas only (`scripts/record_15m_book.py`: per poll the best 5 YES and 5 NO bid prices and sizes; per window every public trade with price, count and the taker's side; `scripts/record_nc_book.py`: the same columns for the 11 non-crypto 15 minute series at a 5 second poll). The recorders do NOT log cancellations: a cancellation can only be INFERRED as a drop in resting size at a price that the window's own trade tape does not explain. I have not seen DEPTH1's feature list (it is not in the repo); the DEPTH1 uniqueness check below is by what the Head named (depth at the touch) and is for the Verification Analyst to confirm against the real list.

Markets: only markets no live strategy trades. NC15 non-crypto: AUD/USD, USD/CAD, natural gas, and the other eight only OUTSIDE EVENT830's listed release windows. (ETH on R6 is a possible second source but its recording ends 2026-11-20, too short for a held-out.)

## What I rejected, and why (so it is not re-proposed)
| Idea | Why it fails |
|---|---|
| Trade size distribution (block prints, median size) | Unsigned size has no direction, so nothing to buy; signed by taker side it is the declined flow family. |
| Book imbalance beyond the touch (levels 2 to 5 total size, YES against NO) | A filter on OICORE's side and the same field family as DEPTH1: a version (7g), not a strategy. |
| Queue position at levels 2 to 5 for resting quotes | That is MMSIM1 (liquidity provision, simulation). |
| Cancellation counts alone | No direction and no counterparty. |

## CARD 1: WITHDRAW1 (quote withdrawal on one side)
- **Mechanism and counterparty:** market makers who watch the spot price faster than a taker can pull resting bids on the side they now expect to lose, without any trade hitting them. The signal is size that VANISHES from levels 2 to 5 of one side of the book with no matching print on the tape. The buyer on the other side of a withdrawn quote is a taker who has not seen the spot move; the market maker is the better-informed party, and we copy their side. Named counterparty: the taker who buys the side the makers just left.
- **Field and uniqueness:** a CHANGE in resting size at levels 2 to 5, reconciled against the tape. Not open interest (OICORE), not taker flow (declined), not size at the touch (DEPTH1). Classification: family = book-change signal plus hold; correlation with every live strategy cannot be computed because the markets are disjoint from L1 (gold) and OICORE (Bitcoin); EVENT830 windows are excluded.
- **Rule (one threshold, fixed, no sweep):** on each market, from the poll ending 480 s before the close to the poll ending 300 s before the close, for each side add up (size at levels 2 to 5 at the start) and (the part of the decrease at those levels not explained by trades on that side in the same span; an increase anywhere does not offset). If one side lost at least 40% of its starting levels 2 to 5 size and the other side lost under 10%, BUY the OPPOSITE of the withdrawing side's own direction (withdrawn YES bids: buy NO; withdrawn NO bids: buy YES) at the ask of the poll ending exactly 300 s before the close, only if that ask is 20c to 60c, the spread is 3c or less, and the starting levels 2 to 5 size on the withdrawing side was at least 200 contracts. One look, nothing carried. 1 contract, held to settlement. Fee: 7% x p x (1 - p) per contract on a 10 contract order rounded up to the cent, slip 1c, cash basis.
- **Numeric prediction:** the entry's win rate is at least its price plus 4 points on average (a 40c entry wins 44% or more), cash PF 1.3 or better in each half.
- **Kill / NOT_ENOUGH_DATA:** fewer than 150 entries over the development window = NOT_ENOUGH_DATA; cash PF under 1.0 in either half, or a net below zero = FALSIFIED. Prior of a pass: about 4%.
- **Dates:** development windows closing 2026-11-17T00:00Z to 2026-12-14T23:59:59Z; held-out 2026-12-15T00:00:00Z to 2026-12-31T23:59:59Z (the NC15 recorder stops 2026-12-31), read once. A scorer, an invented-rows fixture and a pre-committed expected file come before any read, as with ENDNET.

## CARD 2: AIRGAP1 (air pocket below the favourite)
- **Mechanism and counterparty:** when the favourite's resting bids sit far apart (a hole between the best bid and the second bid), one sell order can walk the price down several cents; the thin book is a convex payoff for the cheap side. The party who loses is the maker who left a hole while holding the favourite's inventory. The signal is the PRICE GAP between levels 1 and 2 on the favourite's bid side, not a size.
- **Field and uniqueness:** price spacing of levels 1 and 2 (not size, not open interest, not trades), so not DEPTH1's size at the touch as the Head described it. Same exit style as OICORE (cheap side, hold) but a different trigger and different markets, so entry signal check passes; the Verification Analyst scores the correlation check, which is trivially uncomputable against OICORE (Bitcoin only).
- **Rule (fixed):** at the poll ending 240 s before the close, if the favourite side (the side whose bid is 80c or more) has a best bid minus second bid of at least 3c AND the favourite's best bid is 85c to 95c, BUY the other side at its ask if that ask is 5c to 20c and the spread is 3c or less. 1 contract, held to settlement, same fee and slip. One look.
- **Numeric prediction:** the cheap side wins at least 3 points more often than its price (a 10c entry wins 13% or more); cash PF 1.3 or better in each half.
- **Kill:** fewer than 150 entries = NOT_ENOUGH_DATA (a rule this selective may never reach it, which then closes the card on the data); cash PF under 1.0 in either half or net below zero = FALSIFIED. Prior of a pass: about 3%.
- **Dates:** same development and held-out windows as CARD 1.

## CARD 3: none
I looked for a third mechanism that is not a filter, flow, depth at the touch or liquidity provision, and found none from these fields: size distribution has no direction, and the remaining book and tape features are the declined or versioned families. Reported plainly rather than padded.

## Open items for the Head
1. Send DEPTH1's feature list so CARD 2 and CARD 1 can be checked against it by name.
2. The recorders log the book at 2 s (R6) and 5 s (NC15), so a cancellation shorter than the poll is invisible: CARD 1's reconciliation is an estimate.
3. Both cards sit in the sparse part of the book (levels 2 to 5), where the recorders keep only five levels per side.

## Dated line, Nov 13, 2026, 18:52Z (the Head of R&D, on the Verification Analyst's scoring)
Both cards are CLOSED AT INTAKE as NOT UNIQUE. WITHDRAW1's field is DEPTH1's f6 (thin side depletion) and a second try of BOOKCH1; AIRGAP1's field is DEPTH1's f8 and f9 (holes and slope) with a price zone gate. They count as tries for the book-shape family. No scorer, fixture or read is written for either. If tonight's DEPTH1 read shows the family alive, a version of either may be revisited then, as a DEPTH1 version and not a new card.
