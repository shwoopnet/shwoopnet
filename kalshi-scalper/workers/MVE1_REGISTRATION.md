# MVE1 registration: Kalshi multi-leg combo (KXMVE*) cheap side versus the product of its legs' own prices (written 2026-11-05 before any combo candle, any leg quote or any combo outcome of this study was scored)

Worker: Strategy Research V2, family MULTI-LEG COMBO. N +2 (tries A and B below), running count about 730,449 -> about 730,451, deflated z bar about 5.27. Research only, paper only, no trading code touched.

## Ledger check (README searched for KXMVE, MVE, combo, parlay, multivariate, multigame, cross-category)
Only mentions: USWEEP1/USWEEP2/NEWLIST1 EXCLUDED the KXMVE collections as "combinatorial, no stable resolution". No study of combo prices against their legs exists. Not covered by ARB1 to ARB5, ladder coherence or SPORTCONS1 (those compare siblings in one event; a combo spans events).

## What the combo market is (metadata read 2026-11-05, no price scored)
`/markets?mve_filter=only` lists combos. They are created on demand (RFQ): `mve_selected_legs` names 2 to 21+ single markets with sides, YES pays only if every leg is as chosen. Observed today: about 40,000 combos settled in one hour (creation 15:27 to 16:31 UTC), 5,572 with any volume, all KXMVECROSSCATEGORY-R. Most settle within minutes of creation (`can_close_early`, a leg that loses ends the combo). A traded combo has ONE print in its candle history; the standing yes ask afterwards is 1.00 and the bid 0. Settled combos with volume exist back to 2026-09-06 (60 day listing limit). Aggregate result counts of the first 1,000 listing rows (734 no, 266 yes, all untraded-dominated) were SEEN while probing the API; no per-combo outcome, price or leg was used to choose anything below.

## Mechanism and counterparty
The combo's quote is set by an RFQ maker who prices the conjunction with a vig. Fair value is about the product of the legs' prices if the legs are independent (cross-category legs mostly are) and above it if positively correlated. Hypothesis tested: the maker prices the conjunction systematically differently from the product of the legs' own market mids at the same minute, and the gap is exploitable on the cheap side. Counterparty: the RFQ maker (and, through it, the legs' market makers who hedge it). Honest prior: the maker charges a vig, so the combo is OVERPRICED against the product and the cheap side loses more than the pooled cheap-side baseline; a pass needs the opposite sign in the sub-set where the combo is UNDERpriced against its legs.

## Fillability caveat (stated before scoring)
There is no standing ask on a combo. The print is the price a maker quoted to one RFQ taker at that instant. A trade at "the print" is therefore the price the first taker got, not a price a later buyer could lift. Every result below is an UPPER BOUND on what a rule could earn (it assumes the print was available), and a pass could not be promoted without a forward test of getting an RFQ quote. Say this in the verdict.

## Universe, chosen now (before any outcome)
- Combos: `/markets` with `mve_filter=only`, `status=settled`, close time from 2026-09-06T00:00Z to before 2026-10-03T16:00Z (the global frozen cut; nothing later is fetched). Halves D1 = closes before 2026-09-20T00:00Z, D2 = from then.
- Sample: for each UTC date in the window, two 20 minute close windows, 12:00 to 12:20 and 20:00 to 20:20 UTC, first 1,000 listed rows of each (cursor stops at 1,000). Only combos with volume above 0 are kept. Outcome fields are dropped at read in the census step (`src/scalper/mve1.py census`).
- Cheap side: first print (open of the first candle with volume, 1 minute candles from creation) between 3c and 30c, bought YES at that print, held to settlement, fee 7% x C x p x (1-p) rounded up, C = 10 (also 1 contract and x1.2 stress).
- Legs eligible for the product: combos with 2 to 5 legs, all sides yes, every leg a single market with a 1 minute candle covering the print minute; leg price = mean of yes bid and ask close of that minute (the bid or ask close alone if the other is missing; leg dropped from the product test, and the combo from treated, if it has neither). Candidate combos are capped at 400 by md5(ticker) rank, and leg candle calls are cached.

## Rules and tries (N +2)
- Gap R = combo print / product of leg mids.
- TRY A (TREATED): cheap-side combos with R at most 0.80 (combo priced at least 20 percent under the independence product). Buy YES.
- TRY B (TREATED): cheap-side combos with R at most 0.50. Buy YES. (Nested in A, counted as a second try.)
- CONTROL: all cheap-side candidates in the capped set with a computable R. Also reported, not a try: mean R and mean realized win rate against mean print (calibration), and R above 1.25 (information only, a NO buy of a likely-NO outcome is banned).

## Numeric prediction (before scoring)
CONTROL mean about -7c to -10c a contract (long shots plus maker vig), win rate below the mean print; mean R about 1.1 to 1.6; treated A and B no better than CONTROL minus 0, PF 0.3 to 0.9; likeliest verdict FALSIFIED (about 70 percent), NOT_ENOUGH_DATA if fewer than 150 treated (about 25 percent), LEAD under 3 percent.

## Kill criteria and bar
LEAD needs ALL of: at least 150 treated combos on at least 60 distinct creation hours; profit factor at least 1.5; net per contract positive and at least 6c above CONTROL; clustered z (by creation hour) at least 5.27; positive in both D1 and D2; positive at fees x1.2. Any failure is FALSIFIED (or NOT_ENOUGH_DATA if n is under 150). A single combo can share legs with another, so clustering by creation hour is the floor; leg-overlap is reported. A scorer bug found before the read is an amendment pushed first.

## Code
`src/scalper/mve1.py` (census, then `score`). Read once; the result file and README line refuse a second read.
