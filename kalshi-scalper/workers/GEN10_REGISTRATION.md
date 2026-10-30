# GEN10 registration: a generator on GOLD'S trade tape, mid-window entries HELD TO SETTLEMENT (Strategy Research V2, research only)

Written 2026-10-30 by worker GEN10 and pushed BEFORE any GEN10 row is built, any strategy is generated or any settlement outcome is joined to a tape feature. Before this commit I read: `workers/RULES.md`, `workers/GEN9_REGISTRATION.md`, `workers/GEN9_RESULT.md`, `workers/GEN9_FROZEN.md`, `src/scalper/gen9.py`, `workers/GEN7_REGISTRATION.md` and `GEN7_RESULT.md`, `workers/DIRECTOR_2026-10-30.md`, `workers/candidates/README.md`, `studies/FOOTPRINT_VIEW_REQUEST_2026-10-26.md`, `studies/RECORDER_SPEC_R6_15MIN_BOOK_2026-10-29.md`, and the README entries of T1 to T4, TAPE20, FP2, SWEEP1 (registration and retirement), FLOW1, PERPFLOW1, GEN6, MECH1, the owner's 2026-10-28 process rules and ban. The data file `data/gen9/bars.sqlite` was opened only for its schema, its per-series market counts and one market's first and last three bars (no result). The code `src/scalper/gen10.py` is committed with this file; its row builder was smoke-tested on a synthetic random tape only.

## Scope (fixed by the brief and the owner's bans)

Not L1, not a variant of L1, not the cheap-side-late trade (owner, 2026-10-28; director, 2026-10-30): the signal bar ends between **840 s and 420 s** before the close (minutes 1 to 8 of the window); **nothing in the last 6 minutes** (360 s and later). The side is chosen by the tape, either side, priced **15c to 85c** at the signal bar; a rule whose only condition is the price band is rejected and counted. GEN9 traded short round trips and is FALSIFIED (the round trip costs about 6.5c). GEN10 is a different trade: enter on a tape signal and HOLD TO SETTLEMENT, so there is ONE spread and ONE fee, and the settlement outcome decides.

## Ledger check: what is already closed on tape or flow entries held to settlement on gold

- **T1** (early taker flow in the first 5 minutes, held to settlement, Bitcoin and gold pooled): 13 observations, -8.92c, FALSIFIED; its contract-counted flow measure was dominated by cheap lottery buying. **T2** (the same, sold at 7 minutes), **T3** (early drift scalp, -4.11c on 780, z -10), **T4** (cheap side scalp in the first 3 minutes): all FALSIFIED; T3 and T4 are round trips in the first 5 minutes, not held.
- **TAPE20** (16 flow rules from the 2 minutes before the 6 minute decision, as filters on the L1 favourite HELD, five series pooled, 2,322 entries): no pass; "taker flow does not add information the price lacks". The entries are L1's (88c to 97c at 6 minutes), not mid-window and not the 15c to 85c band.
- **FP2** (gold footprint, opposing taker flow in the 3 minutes before the 6 minute decision as a loss warning on L1 entries, held): an L1 filter at 9 to 6 minutes, gold only; closed with the L1 ban.
- **SWEEP1** (big prints and sweeps, Bitcoin, scale-out exits that held part to settlement): retired 2026-10-28 before any trigger was scored, as a flow pattern on L1's contracts. Never run; Bitcoin only.
- **FLOW1** and **PERPFLOW1** (Binance and perpetual order flow): filters on the L1 entry, and the perpetual's own returns; not Kalshi's tape, not gold.
- **GEN6** (late window, 240 s and later, cheap side, candle and open interest features) and **GEN7** (840 to 240 s, candle and open interest features, "hold" among 47 exits; gold 0 of 5,000 passed discovery, best at size 1.47): 1 minute candles, no tape feature; GEN7 is the closest prior and says mid-window open interest and candle features carry nothing on gold held to settlement.
- **GEN9** (10 s tape bars, 840 to 240 s, 20c to 80c, round trips of 30 to 180 s, never held): gold FALSIFIED at discovery (best at size 0.85, median 0.24). Same bars as here, a different trade.
- **MECH1** (who is on the other side of the Bitcoin open interest core, public tape): no taker type carries the edge; no whales (top 10 prints about 5% of volume).
- The owner's footprint view (`studies/FOOTPRINT_VIEW_REQUEST_2026-10-26.md`, built and then removed from the page on 2026-10-27) is a reading tool; its note says TAPE20 found no tape rule that predicts the 15 minute outcome.

**What GEN10 adds that none of those did:** tape features at **10 second resolution** (not 1 minute candles), over the **whole mid-window** (840 to 420 s, not the 2 to 3 minutes before an L1 decision and not the first 5 minutes), on **gold specifically** (not pooled with Bitcoin), choosing **either side** in the 15c to 85c band by the tape (not a filter on a favourite already chosen by price), **held to settlement** with one fee (not GEN9's two-legged round trip). The prior against it is strong: GEN7 (candles, same window, same hold) found nothing on gold, and TAPE20 found flow adds nothing the price lacks.

## Data (already on disk, public tape only)

- `data/gen9/bars.sqlite`: 10 second bars built by GEN9 from Kalshi's public trade tape for every settled `KXGOLD15M` market closing on GEN9's sampled days (seed 909: 23 of 46 discovery days, 19 of 37 validation days), 3,072 markets, 11.1 million trades, bars covering (close-900, close-120]. Per bar: trade count, YES-taker and NO-taker contracts, largest print and its taker side, last trade's YES price and time. Not re-fetched.
- 1 minute candles (`l1b`, `book`, `fresh`, `five` sqlite, first file wins) for the spread at the fill time and for the market's settlement `result` (yes or no), read only inside `build`, which is first run by `discovery`.

## Three windows (UTC, by the window's close)

| DISCOVERY | VALIDATION (read once) | HOLDOUT |
|---|---|---|
| 2026-08-06 to 2026-09-20 (sampled days) | 2026-09-21 to 2026-10-27 (sampled days) | **none in this file** (the bars end 2026-10-27) |

**No holdout exists here.** The bars file ends on 2026-10-27 and nothing closing on or after 2026-10-28 00:00 UTC is read. The RULES bar needs three windows, so **nothing in GEN10 can meet it**; any survivor of validation would need a forward check on recorder R6 (`book15r6` on `origin/quote-data`, recording since 2026-10-29: 5 book levels every 2 s and the full trade tape of every gold window) before it means anything. Validation rows are built only after the discovery files are frozen, hashed in `workers/GEN10_FROZEN.md`, committed and pushed.

## Grammar (per market; every strategy is exactly one of these)

- **Signal bars:** the 10 s bar ending L = 840, 830, ..., 420 s before the close (43). A strategy has a range [L_hi, L_lo] with both ends from {840, 780, ..., 420} (36 ranges); bars are tried from L_hi down to L_lo every 10 s, YES before NO, and the FIRST qualifying row enters. **At most one entry per window.**
- **Side:** YES, NO or BOTH. The side's price by the last trade at or before the signal bar end (YES = the trade's YES price, NO = 100 minus it) must be in **[15c, 85c]**, and that trade at most 60 s old.
- **Conditions: 1 to 3,** `feature <= q` or `> q`, q a decile (10th to 90th) of that feature over all of the market's DISCOVERY rows (every bar, both sides; feature values only, no outcome), no feature twice, from **20 features**: GEN9's 16, all signed toward the side (s = +1 YES, -1 NO) and computed only from bars ending at or before the signal bar: `f10, f30, f60` (s x (YES-taker minus NO-taker contracts) over the last 10, 30, 60 s), `i10, i30, i60` (the same divided by total contracts), `c10, c30, c60` (trade counts), `burst` (c10 / max(1, c60 / 6)), `dp10, dp30, dp60` (s x change of the last trade price over 10, 30, 60 s, cents; dp60 missing at 840 s), `big30` (largest print in the last 30 s), `bigdir30` (s x its taker side), `px` (the side's price); **plus 4 new ones, defined now:** `fw` (s x (YES-taker minus NO-taker contracts) from the window's first bar through the signal bar: signed flow since the open), `iw` (fw divided by all contracts since the open), `dpw` (s x (the side-signed last price at the signal bar minus the first traded YES price of the window), cents: the move since the open), `tbig` (seconds from the end of the latest bar at or before the signal bar that holds a BIG print to the signal bar end; a big print is a bar's largest print of at least 50 contracts and at least 5 times the window's mean print size up to that bar; missing if none yet). A missing input fails its condition.
- **Signed condition required:** at least one condition must be on a side-signed feature (`f*`, `i*`, `dp*`, `bigdir30`, `fw`, `iw`, `dpw`), so the side is chosen by the tape and never by the price band alone. A draw without one is rejected and counted in N.
- **Fill (APPROXIMATE, stated plainly):** at the NEXT 10 s bar (ending L - 10 s; a trade at most 60 s old is required there), the side's last trade price **+ half the median spread + 1c**, the spread being the median of the closing spreads of the 1 minute candles ending at E-120, E-60 and E, E the end of the minute holding the fill bar (no candle: no entry; a fill under 1c or over 99c: no entry). **This fill is derived from trade prices, not from a book: no depth, no queue, no latency beyond the 10 s bar.** It is GEN9's entry model one bar later.
- **Hold to settlement.** Net per contract in cents: (100 - fill - fee) if the side settles yes (YES bought and result yes, or NO bought and result no), else (-fill - fee). No exit, no stop, no sale, no settlement fee.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, ONE order, **gates at C = 10**; C = 1 and fees x1.2 reported.

## Generation, dedupe and counting

Seeded draws (`random.Random(10002)`) until **5,000 distinct** or 300,000 draws. Distinct: at least one signed condition, at least 30 discovery trades, and no kept strategy whose discovery entry set (window and side pairs) has Jaccard above 0.5 with it. **N added = every draw (rejected or not) + 3 information looks** (the unconditioned 840 to 420 s entry, YES, NO and BOTH, held) **+ one unconditioned same-side-and-range look per discovery survivor** (information, read in validation). Running count before GEN10 about 678,929 (z bar 5.26); the Bonferroni z bar for the new total is reported.

## Screens (fixed now)

- **Minimum data:** fewer than 300 discovery windows or 15 discovery days is `NOT_ENOUGH_DATA` (its N is 0).
- **DISCOVERY:** PF at C = 10 at least **1.5**, at least **100 trades on at least 15 days**.
- **Freeze:** the survivors, the best 10 at size by discovery PF and the control list are written; `workers/GEN10_frozen.json` (survivors and best 10) with its sha256, and the sha256 of the control and distinct files, in `workers/GEN10_FROZEN.md`, committed and pushed before any validation row is built.
- **VALIDATION (read once):** PF at C = 10 at least **1.3** on at least **50 trades**, PF at fees x1.2 above 1.0.
- **Side-shuffle control (the brief's family control), per survivor:** in validation the survivor's entries keep their window and signal bar and each takes the OPPOSITE side's row with probability one half (200 shuffles, seed 1010; a trade whose opposite row does not exist is kept). The survivor must have validation PF **above the 95th percentile** of the 200 shuffled PFs; otherwise its edge is the band and the time, not the side the tape chose, and it is `FALSIFIED` whatever its PF.
- **Family control (kill rule, as GEN6 to GEN9):** discovery FAILURES at the screen's size go through the same validation screen. If the survivors' validation pass rate is not at least 5 points above the control's, the family is `FALSIFIED` as a whole and individual passes are labelled "family control not met".
- **RULES bar (information):** PF 1.5 in each of three windows after fees, positive at x1.2, a named counterparty, deflated z at the bar. **Cannot be met here (two windows).** A pass of both screens and both controls earns only an R6 forward registration.
- **Survivors of validation** are not put in the candles-based forward ledger (their features need the tape). A candidate JSON in `workers/candidates/` is written only if an evaluator can honestly run on R6 data (`source: "r6"`: the same 10 s bars rebuilt from R6's `trades`, the entry at R6's recorded YES ask or NO ask walked through its levels at the first poll after the signal bar, held); otherwise the result file describes what it would need.

## Counterparty (named before drawing)

A taker who follows the tape mid-window (buys the side the flow is buying, or the side the price is moving toward) is filled by **the resting quoters** (market makers posting both sides from a spot feed); for the follower to be paid, the quoters must be slow to move their quotes on their own fills, so the side still sits below its true chance for a few seconds after informed flow arrives. A taker who fades the tape (buys the side the flow is selling) is paid by **impatient takers who crossed the spread on the other side** (MECH1: small prints lean to the cheap side, lottery buying), if they pushed the price past its fair chance. Honest alternative, which I expect: at 7 to 14 minutes left gold's quote is a calibrated function of spot and time, Kalshi's quoters reprice within seconds (TAPE20, MECH1: flow carries no information the price lacks; GEN9: the quote does not drift in any direction the tape can call over 30 to 180 s), and a position held to settlement at 15c to 85c pays about 1.65c of spread and padding plus about 1.5c of fee for a coin whose chance is its price.

## Numeric prediction (before any row is built)

Unconditioned base PF (both sides, 840 to 420 s, held, C = 10) about **0.88 to 0.95** (the cost of about 3.2c on a fairly priced side). Over 5,000 distinct rules: **median discovery PF about 0.90**, 95th percentile about 1.25; at screen size (100+ trades, 15+ days), **survivors at PF 1.5: about 3 (0 to 12)**, all by selection (a held binary outcome has far more variance per trade than GEN9's round trip, so the best of 5,000 spreads wider). Validation: survivor pass rate 0% to 15%, control pass rate 2% to 6%, **no survivor beats the side-shuffle 95th percentile with validation PF 1.3 or better; family FALSIFIED (prior about 85%)**. Best 10 validation PF about 0.8 to 1.1, day z under 2. Prior that anything later passes an R6 forward check: about 2%.

## Kill criteria

The minimum-data rule. A strategy failing a gate is `FALSIFIED` at that gate. Zero discovery survivors = gold `FALSIFIED` at discovery. The side-shuffle and family control rules. Grammar, thresholds, splits, fills, features and seeds are not changed after any outcome is read; validation is run once (`validate` refuses a second run). Verdict words only: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## Files

`src/scalper/gen10.py` (build, discovery, freeze, validate), this file, `workers/GEN10_FROZEN.md`, `workers/GEN10_frozen.json`, `workers/GEN10_RESULT.md`. Distinct, control and validation files in `data/gen10/` (not committed).
