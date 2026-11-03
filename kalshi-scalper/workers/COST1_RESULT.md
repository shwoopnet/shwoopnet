# COST1 result (2026-11-03). Measurement and desk research. No strategy scored, 0 tries, N unchanged (about 728,700).

Code `src/scalper/cost1.py`, `tests/test_cost1.py` (committed before this file). Full 99-row fee table: `python -m scalper.cost1 fees`. Spread: `python -m scalper.cost1 spread` (history + fresh + replicated 15 minute candles; about 3.1M folded candle observations so a NO buyer sees the same spread at 1 - mid).

## 1. Taker fee: ceil_to_cent(0.07 x C x p x (1-p)) per order
Total fee in cents (and per contract, and percent of price) at selected prices; every price 1..99 is in the CSV.

| price | C=1 | C=5 | C=10 | C=50 | C=100 |
|---|---|---|---|---|---|
| 1c | 1c (100%) | 1c (0.20c, 20%) | 1c (0.10c, 10%) | 4c (0.08c, 8%) | 7c (0.07c, 7%) |
| 2c | 1c (50%) | 1c (10%) | 2c (10%) | 7c (7%) | 14c (7%) |
| 3c | 1c (33%) | 2c (13%) | 3c (10%) | 11c (7.3%) | 21c (7%) |
| 5c | 1c (20%) | 2c (8%) | 4c (8%) | 17c (6.8%) | 34c (6.8%) |
| 10c | 1c (10%) | 4c (8%) | 7c (7%) | 32c (6.4%) | 63c (6.3%) |
| 50c | 2c (4%) | 9c (3.6%) | 18c (3.6%) | 88c (3.5%) | 175c (3.5%) |
| 90c | 1c (1.1%) | 4c (0.9%) | 7c (0.8%) | 32c (0.7%) | 63c (0.7%) |
| 95c | 1c (1.1%) | 2c (0.4%) | 4c (0.4%) | 17c (0.4%) | 34c (0.4%) |
| 99c | 1c (1.0%) | 1c (0.2%) | 1c (0.1%) | 4c (0.1%) | 7c (0.07%) |

**Rounding effects.** A single contract never pays less than 1c, so at 1c to 5c a 1-lot pays 20% to 100% of its price (against 0.07 x p x (1-p) = 0.07c to 0.33c unrounded): the rounding is a 3x to 14x surcharge. At C=10 the surcharge is gone by 5c (4c vs 3.3c unrounded) and at C=100 the fee is within 1% of the formula. At 50c a 1-lot pays 2c for a formula value of 1.75c (+14%); at 85c to 97c a 1-lot pays 1c (formula 0.2c to 0.9c, up to 5x at 97c). Rounding is per order, so splitting a size into 1-lots is the worst case; a larger single order is cheaper per contract. Kalshi's developer docs describe a fee accumulator with rebates of rounding overpayment across fills of one order (docs.kalshi.com fee_rounding), so a multi-fill order can recover part of this; I did not verify the rebate against real fills.

## 2. Maker fee (verified against the live API on 2026-11-03)
- `GET /series` lists 15,663 series: **15,468 `quadratic` x1, 159 `quadratic_with_maker_fees` x1, 18 `quadratic` x0.5, 14 `quadratic` x0, 3 `quadratic_with_combo_maker_fees`, 1 `quadratic_with_maker_fees` x0.5.** The standard schedule is taker multiplier 1, **maker multiplier 0** (docs.allium.so series-fee-changes). So on a plain `quadratic` series a resting order that fills pays **no trading fee**.
- Series with a maker fee are 160 (mostly sports game, total, spread and futures series: KXNFLGAME, KXNCAAFGAME, KXNBASERIES, ...). Their maker fee is 0.0175 x C x p x (1-p), one quarter of the taker rate (third-party summaries of kalshi.com/docs/kalshi-fee-schedule.pdf; the PDF itself returned HTTP 429 to me, so this rate is not read first-hand).
- **Every series the bot trades or tests here is plain `quadratic`**: KXBTC15M, KXETH15M, KXGOLD15M (checked live), the 15 minute family, KXBTCD, and the tennis series (KXATP*, KXWTA*). So **maker fee = 0 on L1's markets**, and README's 2026-10-21 note that assumed maker = taker or 0.0175 was conservative. Unverified: whether a real maker fill on these series shows any rounding fee; confirm on one live resting fill before relying on it.
- No separate rebate or `fee_waiver` field was found in the series objects. The fee accumulator (above) is the only rebate mechanism I found.

## 3. Median spread by price band (cents; YES mid band, both sides folded; all 15 minute candles, n in the thousands per cell)
| band | all | crypto | metals/energy | FX | at L1's 6 min look (all) |
|---|---|---|---|---|---|
| 1-5c | 0.4 | 0.2 | 1.0 | 1.0 | 0.3 |
| 5-15c | 1.0 | 1.0 | 1.0 | 2.0 | 1.0 |
| 15-30c | 1.0 | 1.0 | 1.0 | 3.0 | 1.0 |
| 30-70c | 1.0 | 1.0 | 1.0 | 3.0 | 2.0 |
| 70-85c | 1.0 | 1.0 | 1.0 | 3.0 | 1.0 |
| 85-97c | 1.0 | 0.9 | 1.0 | 2.0 | 1.0 |
| 97-99c | 0.3 | 0.2 | 1.0 | 1.0 | 0.2 |
Candles carry closing quotes (a one-minute snapshot, not time-weighted); the "rates" 15 minute series have broken or empty books and are excluded. FX spreads are 2c to 3c and are why FX probes were expensive.

## 4. Round-trip cost, by band (all-series median spread, C=10, taker)
Hold to settlement pays **one** fee; buy then sell pays two fees plus the full spread.
| band | fee/contract C=1 | fee/contract C=10 | hold cost vs mid (half spread + fee), C=1 / C=10 | buy-then-sell cost C=10 (spread + 2 fees) |
|---|---|---|---|---|
| 1-5c | 1.00c | 0.26c | 1.20c / 0.46c | 0.92c |
| 5-15c | 1.00c | 0.66c | 1.50c / 1.16c | 2.33c |
| 15-30c | 1.81c | 1.26c | 2.31c / 1.76c | 3.51c |
| 30-70c | 2.00c | 1.70c | 2.50c / 2.20c | 4.40c |
| 70-85c | 1.81c | 1.26c | 2.31c / 1.76c | 3.51c |
| 85-97c | 1.00c | 0.61c | 1.50c / 1.11c | 2.22c |
| 97-99c | 1.00c | 0.20c | 1.15c / 0.35c | 0.70c |
**Cheapest in cents: 97-99c (0.35c), then 1-5c (0.46c at C=10), then 85-97c (1.1c).** Cheapest as a percent of price: 97-99c (0.35%), 85-97c (1.2% of a 91c mid); the tails are cheap in cents and dear in relative terms: at C=10 the hold cost is 0.46c on a ~3c contract = **15% of price** (C=1: 40%), 11.6% at 10c. A 90c favourite needs a win rate 1.1c (1.2%) above its mid; a 3c tail needs 15% more wins than priced.

## 5. Break-even win-rate excess over mid (cents; hold to settlement; C=10 unless noted)
Taker = half-spread + taker fee. Maker optimistic = rest at the bid, fill at the bid: minus half-spread + maker fee (0 on `quadratic` series; column 'maker 0.0175' shows the fee series). Maker with haircut = the same plus an adverse-selection drag A on the FILLED set.
**Haircut evidence (README, not new estimates):** fill rate 67% for a bid at the bid within 3 minutes (MAKER2, 28,873 L1 opportunities, 83 days), 77% for 1c under the ask by T-119 s on gold (GOLDFILL), 50% to 57% (P2, 30 signals), 70% (MAKER1 tennis, Q=1). A = **2.4c** at L1's 88-97c band: MAKER2's filled entries made -1.19c resting vs -2.31c had they been bought at the ask, while the whole set earned +0.10c, so the filled set underperforms the whole by about 2.4c even though resting saves 1.11c; per opportunity REST was -0.80c vs TAKE +0.10c. A is measured only in that band; for other bands it is unmeasured and A=2.4c is applied as a placeholder, labelled so.
| band | taker C=1 | taker C=10 | maker opt. (fee 0) | maker fee-series (0.0175, C=10) | maker + A=2.4c | worse than taker? |
|---|---|---|---|---|---|---|
| 1-5c | +1.20 | +0.46 | -0.20 | -0.10 | +2.20 | yes if A holds (tails: A unmeasured, a 3c contract's A is bounded by its price) |
| 5-15c | +1.50 | +1.16 | -0.50 | -0.30 | +1.90 | yes |
| 15-30c | +2.31 | +1.76 | -0.50 | -0.14 | +1.90 | about equal |
| 30-70c | +2.50 | +2.20 | -0.50 | -0.03 | +1.90 | slightly better |
| 70-85c | +2.31 | +1.76 | -0.50 | -0.14 | +1.90 | about equal |
| 85-97c | +1.50 | +1.11 | -0.50 | -0.32 | +1.90 (measured) | **yes, worse (MAKER2)** |
| 97-99c | +1.15 | +0.35 | -0.15 | -0.05 | +2.25 | yes |
Per-opportunity capture is the fill rate times the filled edge; at 67% fill a maker rule must clear its break-even on a third fewer orders and the missed third are the winners (MAKER2, MAKER3: the hybrid that crosses after W seconds lost -0.56c to -0.78c per opportunity more than simply buying).
**Meaning.** For 90c favourites the fee is already small (0.6c at C=10) and the measured adverse selection (2.4c) is four times what resting saves; maker does not help L1-style entries. For tail contracts (1-5c) the taker fee is 15% to 40% of price, the biggest relative saving from maker, but the filled set is the one where the tail is about to get cheaper; nothing held measures A for tails. Maker's clear advantage is on the cost side of strategies that must exit (two fees + a spread) and that can post BOTH legs, not on directional entries.

## 6. Previously "falsified at taker cost" families that could flip sign at maker cost (listed, NOT re-scored)
Condition to flip: the recorded gross (before fee, spread included) must be above minus the cost saved, and A must be small. Break-even each would need is the registered gap, not a claim.
| README id | taker result | gross before fee | what maker (fee 0, rest both legs) changes | break-even needed |
|---|---|---|---|---|
| MAKER1 (tennis, rest at bid then at ask) | Q=1, maker fee = taker: -2.80c | n/a | **already positive at fee 0: +0.22c (z 2.30, halves +0.24/+0.20) at Q=1; Q=100: -1.15c; Q=300: -1.99c** | queue position near front; the only held case that is positive at fee 0 |
| OP1 to OP3, F1 to F3 (favourite scalps) | -3.0c to -3.2c | -0.74c to -0.90c (spread in) | fees ~2.3c of the loss vanish, spread ~1c recovered on a resting exit only | gross must rise by about 0.8c; limit exits can rest, entries cannot without selection |
| OW2 A-D (opening scalp) | -3.84c to -4.49c | -0.85c to -1.62c | fees 2.9c to 3.0c vanish | gross +0.9c to +1.6c, i.e. selection-free resting on both legs |
| M1 (early window momentum) | -2.63c | -0.41c | fees 2.23c vanish | gross >= +0.4c with no adverse selection (best margin of the list) |
| TAIL / longshot buys (L1-bias at 1-15c, README L1/LAD1 era) | negative after fee | not re-pulled | fee is 8% to 40% of price | win rate excess 0.46c (C=10) over a 3c mid |
| L1 itself (not falsified; 88-97c) | +0.10c taken | n/a | saves 0.3c to 0.7c but MAKER2 REST -0.80c per opportunity | L1Q1 and MAKER5 (R6, not read before 2026-11-06) test exactly this |
| Cross-leg arbs (sum of bids, ARB1-5, RACELOCK) | locks of 0.1c to 3.7c a set, 1 in ~400 | n/a | a maker leg gets the fee back but the lock needs all legs filled | fills on all legs: not measurable from held candles |
Families that CANNOT flip: any with gross below minus the whole fee-plus-spread (OW2-style at -1.6c, favourite-exit selling at -0.74c to -0.90c unless both legs are free of adverse selection, which MAKER1 Q>1 and MAKER2 show they are not). I did not re-run any of them.

## 7. Plain conclusions
1. Taker fee at 85c to 97c is 0.2c to 1.1c per contract at C>=5 and is NOT what limits L1; at 30c to 70c it is 1.7c to 2.0c and is.
2. Maker fee is **zero** on every plain `quadratic` series (99% of series, all of L1's), not 0.0175. That is a real change for any resting strategy, and it matters only if the fills are not adverse.
3. Measured fill probability 50% to 77% and measured adverse selection 2.4c at 88-97c mean resting is worse than crossing for entries; the clean maker test is already registered (MAKER5, L1Q1, not read before 2026-11-06).
4. Tails and 97-99c are the cheapest bands in cents; tails are the dearest in percent.
