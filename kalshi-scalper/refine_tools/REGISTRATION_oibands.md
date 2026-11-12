# S-OIBANDS1: [live figure removed, ask Main]

Information for the owner only. Nothing here changes a trade; any change needs the owner's approval. Read only, public report data (dash_report.json from the nightly report), no key.

## Groups (by price paid per contract)
[live figure removed, ask Main]
- A: paid <= 0.07
- B: paid > 0.20
- M (reference only, no decision): 0.07 < paid <= 0.20

## Forward window
[live figure removed, ask Main] None of the existing record is used. The script is run with that timestamp as its start argument.

## Cash basis
[live figure removed, ask Main] Win = result equals side. Net per contract = total net / total contracts.

## Per group report
[live figure removed, ask Main]

## Priors (stated, not adopted)
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- Nothing is adopted from history: about 420 splits were looked at, so any band found there is a multiplicity-inflated pick.

## Read points
- [live figure removed, ask Main]
- [live figure removed, ask Main]

## Decision language (fixed now)
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- Otherwise "no read" and extend (no early stop, no peeking verdict before the read point).
- A flag is information for the owner, not an action.

## Multiplicity
Two registered tests (A at 40, B at 20), one-sided in spirit, no adjustment; M is reference only. Context: this sits on top of about 420 historical splits that produced the idea, so even a flag is one watch among many, not a confirmed finding. Each flag is a single forward look with no repeat reads at the same point.
