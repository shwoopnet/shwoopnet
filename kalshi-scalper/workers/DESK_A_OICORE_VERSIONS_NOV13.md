# Up to three OICORE VERSION cards (7g), Desk A, Nov 13, 2026 (written only; no test run; no live fill and no outcome read)
The Head's order of 19:20Z (the owner's priority: a strategy that clears the proven bar, OICORE first). OICORE (CLAUDE.md, live second-slot probe): Bitcoin 15 minute market, the cheaper side from 8c (`SLOT_SKIP_BELOW`) to 50c, only when open interest rose by the threshold (86,300) over the 3 minutes to 180 s before the close (the candle ending at close - 180 s minus the one ending at close - 360 s), enter 180 to 120 s before the close, limit 1c above the touch, held to settlement, size by its own ladder. Each card below changes ONE parameter or adds ONE condition to that rule, so under 7g it is a VERSION of OICORE: not unique, no shadow slot, no counted idea; it counts one try. Each rests on a stated MECHANICAL reason that does not come from looking at OICORE's fills (I read none, and no outcome of any window). One version is tested at a time; nothing here is run.

## The 7g takeover bar, and an honest warning about it
A version replaces its parent only if its cash PF beats the parent's by 0.10 at 60 signals, its net dollars per contract-week are not lower, its second half is not worse, and it has 60 signals (STRATEGY_LIFECYCLE 7g). A FILTER version trades a subset of the parent's signals, so the 60-signal comparison is on overlapping windows; at 60 signals the sampling noise of a PF is far larger than 0.10 (a cheap-side rule wins about 1 in 4, so a couple of trades move PF by several tenths). I therefore expect **no filter version to reach a trustworthy takeover on forward data inside a quarter**, and I say so rather than promise a lift. The cheapest honest use of each is the history screen below (a try), then forward shadow beside the parent; none is proposed for live.

## Shared registration facts for all three
- **History source:** KXBTC15M 1 minute candles with open interest and yes bid and ask (the source of OICORE's own research) for spread and price conditions; R6 books (Oct 29 on, Bitcoin) only for a book-state card.
- **Held-out:** HELDOUT_FIRST = 2026-12-01T00:00:00Z (the same constant as SPXOI1: windows closing on or after it, read once; forward signals from the registration commit are shadow only); development is every Bitcoin window closing before it, read once on its own and never tuned.
- **Try count:** N +1 per version (one parameter set each); a changed number is a new try.
- **Row 190 caution, for Auditor B to rule:** a price-band or spread tweak is on cheap-side price features, which row 190 closes for SWEEPS "without a new data source". These are single, pre-registered, inherited constants (no grid, no search), which is what 7g allows for a version; but if Auditor B reads row 190 as covering them, cards 1 and 2 stand down and only card 3 (a field not yet tried) remains.

## Ranking by expected gain against the risk of fitting noise
1. **OIVER-SPREAD (rank 1).** 2. **OIVER-CAP30 (rank 2).** 3. **OIVER-DEPTH (rank 3).**

### 1. OIVER-SPREAD (V1): add "YES spread at most 3c" at the decision poll
- **Mechanical reason:** OICORE's entry has no spread condition. A buy at the ask plus 1c pays half the spread plus the limit slack against the mid; on a wide book that cost is a fixed deduction from a cheap-side bet whose edge is small, so a wide-spread signal needs a bigger real edge than a tight one to break even. 3c is not chosen here: it is CFRTI-K's registered spread constant on this same market (`CFRTI_K_REGISTRATION.md`), so the number is inherited, not fitted.
- **Rule:** OICORE unchanged, plus: skip when (YES ask - YES bid) at the decision candle exceeds 0.03 (a missing bid or ask skips and is counted).
- **Pre-data prediction (an assumption):** it removes the thinnest-book signals and lifts cash PF by 0.05 to 0.15 on development; the share of signals removed is unknown until read and is printed first.
- **Kill:** removes more than half of the parent's signals (then it is a different, smaller strategy and is reported as such, not taken over); or cash PF below the parent's on development; or a forward 60-signal read under the 7g bar closes it.
- **Expected gain against noise:** modest gain, lowest fitting risk (one inherited constant, a cost mechanism).

### 2. OIVER-CAP30 (V2): lower the price ceiling from 50c to 30c
- **Mechanical reason:** the quadratic fee is 0.07 x p x (1 - p), largest at 50c (1.75c a contract) and about 0.5c at 8c, so the absolute edge a contract must show to break even is 3 to 4 times larger in the 30c to 50c part of the band than at the cheap end; the open-interest signal's claimed payoff is a mispriced TAIL, which is a cheap-side claim. 30c is CFRTI-K's registered ceiling (the Head's band 5c to 30c), inherited, not fitted.
- **Rule:** OICORE unchanged, plus ceiling 0.30 on the side's ask (the 8c floor stays).
- **Pre-data prediction (an assumption):** removes the 30c to 50c entries and lifts cash PF by 0.00 to 0.10; the sign is not obvious because the same removal also drops entries with larger per-win payoffs.
- **Kill:** removes more than half the signals; or cash PF below the parent's on development; or a forward 60-signal read under the bar.
- **Expected gain against noise:** small to modest gain, moderate fitting risk (a price cut can be a pattern in disguise even with an inherited number; this is the one most exposed to the row 190 question).

### 3. OIVER-DEPTH (V3): require a book-state confirmation, displayed size at the touch of at least twice the order size
- **Mechanical reason:** a 10 contract (and up to 30 on the ladder) order against a thin touch walks the book above the limit or is not filled, so the signal's realised price is worse than the quote it was priced at; a size-at-touch condition is a fill-quality condition, from a field OICORE does not use (book sizes; DEPTH1 and NC15DEPTH1 use imbalance, not size at the touch as a fill gate). The factor 2 is a round number chosen before any data and is not tuned.
- **Rule:** OICORE unchanged, plus: skip when the contracts displayed at the touch the order would meet (the YES ask size for a YES buy, the YES bid size for a NO buy) are under 2 x the order size (a missing size skips and is counted).
- **History source:** R6 Bitcoin books only (Oct 29 on, about 2 weeks), so a development screen has few signals ("no evidence at n = x" under 100) and will probably stay NOT_ENOUGH_DATA; a forward shadow log (depthAtLimit is already recorded on every new order) is the real test.
- **Pre-data prediction (an assumption):** lifts cash PF by 0.05 to 0.20 only through avoided bad fills; it cannot raise the signal's win rate.
- **Kill:** fewer than 100 signals with a recorded touch size by 2027-02-26 (NOT_ENOUGH_DATA, closed); or cash PF below the parent's; or a forward read under the bar.
- **Expected gain against noise:** the largest possible gain if fills are the loss, the smallest sample, so the highest noise risk; ranked last for that reason.

## Rejected before writing (so they are not re-proposed)
Entry time (180 s against 120 s before the close) and the open-interest threshold's level: both are parameters OICORE's own research already scanned; a change is a sweep (row 190) and cannot be defended by a mechanism I can state without looking at its trades. A stop or profit target: OICORE holds to settlement by an owner exception and the exit research (EXIT1) found holding better.

## Dated line (Nov 13, 2026, the Head of R&D, 19:52Z): the OIVER-SPREAD scoring convention
For the history screen of card 1 (the scorer is `desk_a_verify/oiver_spread.py`): the decision is at the candle ending close - 180 s; the price is the ASK SEEN at that candle (the cheaper side's price, ties to YES), with NO +0.01 slip (OICORE's slip was switched off in PR 895); it is filled at that ask, with NO next-candle fill check; C = 20 contracts for the fee rounding; halves are by COUNT (date order, the first ceil(n / 2) and the rest); the open-interest threshold 86,300 is inclusive; the band is 0.08 <= ask <= 0.50. This replaces the limit and fill-check wording in my build 1 (ef5bf7b9) description. The spread condition (yes ask - yes bid at that candle at most 0.03, inclusive) and the rest of the card are unchanged.
