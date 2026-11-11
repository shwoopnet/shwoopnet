# GEN13 registration: the GEN12 harness on the MID-PRICE band (ask 0.30 to 0.88), 17 series (Strategy Research V2, research only)

Written 2026-11-11 by worker GEN13 and pushed BEFORE any strategy is scored. It is GEN12 (`workers/GEN12_REGISTRATION.md`, `src/scalper/gen12.py`) with one change of entry band and two added series. Code: `src/scalper/gen13.py` (a copy of gen12.py with the edits listed here), committed with this file and before the first score. Cuts: `workers/GEN13_cuts.json` = GEN12's 15 cuts reused unchanged, plus cuts for XRP and SOL taken the same way (close times only, the market at index floor(2n/3) of the sorted close times): KXXRP15M 1792082700, KXSOL15M 1790760600.

Prior work: GEN12, NONCRYPTO1, SWEEP1, REGIME1 all failed on the cheap side (ask 0.04 to 0.30). The 88c to 97c favourite-late band is declined and banned and is NOT in this grammar. Prediction recorded now: ZERO survivors (a mid-price contract pays about its price; the fee 0.07 p (1-p) is largest here, up to 1.75c per leg at 50c, so a round trip costs up to 3.5c; exits at the bid pay the spread on top).

## Scope
Research only; no live or `functions/` change; no network call (local sqlite only); no Polymarket, ESPN, NHL, MLB, NBA.com, Rotten Tomatoes, no Kalshi API. Traded series (17): silver, WTI, copper, natural gas, platinum, palladium, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, NEAR, ZEC, HYPE, BNB, XRP, SOL. EXCLUDED: Dogecoin, Bitcoin, Ethereum, gold as an L1 series (gold and Bitcoin are loaded only as REFERENCES for partner features). Data: `data/alts2, alts3, alts4, fresh, rep, l1b, book, five` (.sqlite), deduped by ticker (first file wins), settled markets with candles only. XRP and SOL are the "small crypto" family (partner Bitcoin).

## Band
A row exists where the bought side's ASK is 0.30 to 0.88 (both sides, whichever is in the band; at mid near 0.5 both sides give a row and the yes row is taken first at a tie) and the spread is at most 0.03. One trade per market (earliest matching minute in the window).

## Grammar, exits, fee
Identical to GEN12: scope (all, one series, one family), side (yes, no, both), entry window (left 180 to 840 s), 1 to 4 conditions on 19 features at pooled development deciles, one of 226 exits (216 fixed take profit 3/5/8/12/20c or none x stop 5/10/20c or none x time exit 60/120/240 s before close x book exit none/spread>=3c/market against; 9 trailing stops; HOLD to settlement, allowed here because the entry is not favourite-late, but not the focus). Exits fill at the recorded bid of the triggering candle. Fee: UNROUNDED 0.07 p (1-p) per contract on the entry and on every sale, none on settlement. BASIS: CASH, 1 contract. Zero-volume guard: at most 20 percent of a strategy's trades.

## Search size and N
300,000 strategies drawn (seeds 13000001 to 13000004, 75,000 each), every draw scored and counted, no deduplication. Deflation N = 1,100,000 (800,000 shared ledger + 300,000 this sweep); one-sided z bar = inv_cdf(1 - 0.05/N) about 5.33 at that N, and also reported at N 8,795 (the V2 + Refinement ledger), about 4.4.

## Split and gates
Per series the first two thirds by close time are DEVELOPMENT, the last third HELD-OUT (read once, only for the frozen list, in a separate file).
Stage 1 (development): cash PF >= 1.5, n >= 150 on >= 25 distinct days, zero-volume share <= 20 percent. Frozen list = stage 1 passes with day-clustered development z >= 3.0, capped at 500 by z, written to `workers/GEN13_frozen.json` and committed BEFORE held-out is read.
Stage 2 (held-out): cash PF >= 1.5, n >= 50 on >= 10 days.
Stage 3: pooled day-clustered z >= the z bar at N 1,100,000 (also stated at N 8,795), positive mean in both thirds.
SURVIVOR = all three. Only a survivor gets the daily cash P&L correlation with an L1-style favourite-late proxy (gold, ask 0.88 to 0.97 at 330 to 400 s before close, held, same fee, UTC days both trade) and IMPLEMENT, KILL, RETURN rules. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.

## Limits stated in advance
Forex has 15 to 43 days, so forex-only strategies cannot reach 25 development days. 1 minute candle closes: a bid exit is optimistic about speed and depth. Mid-price bid exits cross the spread (up to 3c) each time. Sizes are 1 contract.
