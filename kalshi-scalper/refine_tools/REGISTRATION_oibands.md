# S-OIBANDS1: forward watch of OICORE entries by price paid (registered 2026-11-08, before any in-window fill)

Information for the owner only. Nothing here changes a trade; any change needs the owner's approval. Read only, public report data (dash_report.json from the nightly report), no key.

## Groups (by price paid per contract)
paid = avgFill for a YES order, 1 - avgFill for a NO order.
- A: paid <= 0.07
- B: paid > 0.20
- M (reference only, no decision): 0.07 < paid <= 0.20

## Forward window
OICORE slotOrders with status filled, count > 0, settled (result yes or no), and order ts after 2026-11-08T12:44Z. None of the existing record is used. The script is run with that timestamp as its start argument.

## Cash basis
Per fill: net = count x (win ? 1 - paid : -paid) - fee x count, fee = avgFee per contract (matches PR 741's fillCost). Win = result equals side. Net per contract = total net / total contracts.

## Per group report
Fills, wins, win rate with an exact (Clopper-Pearson) 90 percent interval, net dollars, net per contract with a seeded (seed 1, 10,000 draws) bootstrap 90 percent interval resampling fills.

## Priors (stated, not adopted)
- Live record since Nov 1: A had 1 win in 27 (-3.9 dollars, fill-booked). B had 4 wins in 11 (36 percent).
- Simulation: A win rate about 7 percent; B about 45 percent pooled, edge unstable between history halves (win rate 51 vs 39 percent).
- Nothing is adopted from history: about 420 splits were looked at, so any band found there is a multiplicity-inflated pick.

## Read points
- A: 40 fills (about 10 days at the recent pace; the earlier S-HALFSIZE1 under-0.10 group is at 17 of 40, a different key and window, not pooled).
- B: 20 fills.

## Decision language (fixed now)
- A is flagged "does not earn its risk" only if, at 40 fills, net per contract <= 0 AND the 90 percent bootstrap interval upper end is below +1c.
- B is flagged "does not earn its risk" if, at 20 fills, net per contract < 0 AND the upper end of the win rate 90 percent interval is below 45 percent.
- Otherwise "no read" and extend (no early stop, no peeking verdict before the read point).
- A flag is information for the owner, not an action.

## Multiplicity
Two registered tests (A at 40, B at 20), one-sided in spirit, no adjustment; M is reference only. Context: this sits on top of about 420 historical splits that produced the idea, so even a flag is one watch among many, not a confirmed finding. Each flag is a single forward look with no repeat reads at the same point.
