# GEN8 registration: a generator of MID-PRICE ROUND TRIPS on the gold and Bitcoin 15 minute markets (Strategy Research V2, research only)

Written 2026-10-30 by worker GEN8 and pushed BEFORE any GEN8 row is built, any strategy is generated or any outcome is read. Before this commit I read only: `workers/RULES.md`, `workers/candidates/README.md`, `workers/candidates/REF_GEN6_OICORE.json` and `GEN7_B01.json`, `workers/DIRECTOR_2026-10-30.md`, `workers/GEN7_REGISTRATION.md`, `workers/GEN7_RESULT.md`, `workers/GEN7_FROZEN.md`, `src/scalper/gen1.py`, `src/scalper/gen7.py`, the head of `src/scalper/gen6.py` and its registration's family control lines, `data/gen1_result.txt`, the README lines of GEN1, GEN1S, GEN2 and MUT1, and `src/scalper/fwdledger.py` (`net_per_contract`). The code `src/scalper/gen8.py` is committed with this file and has not been run.

## Scope (fixed by the brief)

No buy-the-favourite-and-hold, no L1 work (owner, 2026-10-28), and not the cheap-side-late-held trade (director, 2026-10-30). GEN8 is a different trade shape: **buy a coin-flip side (ask 30c to 70c) between 14 and 5 minutes before the close and sell it 1 to 5 minutes later, always before 2 minutes before the close.** Nothing is ever held to settlement, so the settlement result never enters a net.

## Ledger check: what GEN1 already covered, and what is new

**GEN1's grammar did cover this zone with similar exits.** GEN1 drew entries at 840 to 180 s left on asks 3c to 85c (so 30c to 70c was inside it), with exits that were all before settlement: take profit {3, 5, 8, 12, 20c, none} x stop {none, 5, 10, 20c} x time {sell at 240, 120, 60 s left} x book exits. 5,000 distinct, **none passed discovery (best 1.25 at 150+ trades, median 0.62)**; MUT1 found no plateau around its near-misses; GEN2 (more series, trailing stops, scale-out) median 0.49. That is a strong prior against GEN8, stated before scoring. What GEN8 adds, and only this is new:
1. **Open interest features (11, GEN7's):** `doi1`, `doi3`, `doi5`, `sdoi1`, `sdoi3`, `sdoi5`, `doiw`, `npv1`, `npv3`, `npv5`, `npvw`. GEN1 had one (`doi`, raw 3 minute change, a missing input set to 0). GEN7 used them, but on the cheap side and favourites with hold or late exits, never a short round trip in the coin-flip zone.
2. **The 30c to 70c restriction** as the universe of every rule (GEN1 could land there only through a condition on `ask`).
3. **Exits timed from the entry** (sell 60 to 300 s after the fill), always at least 120 s before the close. GEN1's time exits were at 240, 120 and 60 s LEFT, mostly later than GEN8 allows; its 840 s entries with a 240 s exit held for 10 minutes.
4. **Fill at the next candle's ask** (GEN1 filled at the signal candle's ask), each market alone, and GEN6 / GEN7's date split.
Not used: spot and perp features (`z`, `r3`, `tb1`, `tb5`).

## Universe (time and cost only)

`KXBTC15M` and `KXGOLD15M`, run separately. Every settled window in `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite`, `five.sqlite`, a ticker in two files taken once from the first file in that order (GEN7's `load_windows`, unchanged). Peers: Bitcoin uses Ethereum (`xa`) and gold (`xb`); gold uses Bitcoin (`xa`) and Ethereum (`xb`).

## Three windows, fixed now (UTC, by the window's close time)

| | DISCOVERY | VALIDATION (read once) | FORWARD (holdout) |
|---|---|---|---|
| both markets | 2026-08-06 00:00 to 2026-09-20 23:59:59 | 2026-09-21 00:00 to 2026-10-27 23:59:59 | the forward ledger: windows closing after each candidate's freeze |

Nothing closing on or after 2026-10-28 00:00 UTC is read by GEN8 for any purpose. Validation rows are built only after the discovery survivor files are frozen, hashed in `workers/GEN8_FROZEN.md`, committed and pushed.

## Grammar (per market; every strategy is exactly one of these)

- **Looks:** the 1 minute candle ending L seconds before the close, L in {840, 780, 720, ..., 360, 300} (10 looks). A strategy has a range [L_hi, L_lo] from that set (55 ranges); looks are tried from L_hi down to L_lo, YES before NO, and the FIRST row that qualifies enters. **At most one entry per window.**
- **Side:** YES, NO or BOTH. The side's ask at the signal candle must be in **[0.30, 0.70]**. YES ask = `ask_c`, NO ask = 1 - `bid_c`.
- **1 to 3 conditions,** `feature <= q` or `> q`, q a decile (10th to 90th) of that feature over all of the market's DISCOVERY rows (in-zone rows, every look, both sides; feature values only), no feature twice, drawn from the 25 features: GEN7's 11 open interest features (above) and GEN1's 14 Kalshi-side features `ask`, `bid` (of the side), `spread`, `d1`, `d2`, `d3`, `d5` (side bid change over 1, 2, 3, 5 minutes), `rng5`, `vol`, `hour` (UTC), `xa_d2`, `xa_mid`, `xb_d2`, `xb_mid`. The feature code is GEN7's (`scalper.gen7._oi_feats` and the same row code). Inputs from candles ending at or before the signal candle only. A missing input fails its condition.
- **Fill:** the NEXT candle's closing ask of the side (the candle ending at fill_t = close - L + 60). A missing next candle, or a next-candle ask of 0 or 1 or above, is no entry at that look (later looks may still be tried). **Also reported:** the signal candle's ask as the fill (information).
- **Exits (105), always before settlement.** The scan is the side's closing bid on candles ending strictly after fill_t. Fallback time T = fill_t + H, H in {60, 120, 180, 240, 300} s.
  - `time H` (5): sell at the bid of the candle ending at T.
  - `tp` (100): take profit {+3, +5, +8, +12, +15c} and stop {-5, -10, -15, -20c} on the closing bid of every scan candle ending at or before T (sell at that bid); if neither hits, sell at T as above.
  - **Zero bid:** a bid of 0 is never a sale before T (that candle is skipped, the scan moves on). At T, a bid of 0 is **booked at 0** (the whole stake lost). If the candle ending exactly at T is missing, the first later candle ending by 60 s before the close is used (its bid, or 0 if its bid is 0), flagged "late"; if no candle exists, booked at 0. How often each happens is reported.
  - **An exit is allowed only if T is at least 120 s before the close at every look of the range: H <= L_lo - 180.** Draws picking an exit not allowed are redrawn and still counted in N.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, **both legs**, gates at C = 10; C = 1 reported; fees x1.2 stress. A sale booked at 0 pays no exit fee.
- **Zero volume:** an entry whose signal or fill candle, or an exit whose candle, has volume 0 is flagged; more than 20% flagged fails a screen; PF reported with and without flagged trades.

## Generation, dedupe and counting

Seeded random draws (seed 8, per market) until **5,000 distinct** per market or 300,000 draws. Distinct: at least 30 discovery trades and no kept strategy with discovery entry window sets of Jaccard above 0.5 AND exits within one step (same family; time: adjacent or same H; tp: TP, stop and H each within one step). No reference exclusion is needed: no rule can hold to settlement, enter at 180 s or buy above 70c, so none can be L1, OICORE, OIDRIFT, REV1 or UNDERDOG_180; the entry overlap with REF_GEN6_OICORE is reported instead. **N added = every draw on both markets, plus 10 information looks** (the unconditioned first in-zone entry with each of the 5 time exits, per market). Running count before GEN8 about 592,100; the Bonferroni z bar for the new total is reported.

## Screens (fixed now)

- **DISCOVERY:** PF at C = 10 (next-candle fill) at least **1.5**, at least **100 trades on at least 15 days**, zero-volume share at most 20%.
- Survivors frozen to `workers/GEN8_frozen_btc.json` and `workers/GEN8_frozen_gold.json`, sha256 in `workers/GEN8_FROZEN.md`, committed and pushed before any validation row is built.
- **VALIDATION (read once):** PF at C = 10 at least **1.3** on at least **50 trades**, stressed-fee PF above 1.0, zero-volume share at most 20%.
- **Family control (kill rule, as GEN6 and GEN7):** discovery FAILURES at the screen's size (100+ trades, 15+ days) are run through the same validation screen. If the survivors' validation pass rate is not at least 5 points above the control's, the market's family is `FALSIFIED` as a whole; individual passes still go to the forward ledger labelled "family control not met".
- **RULES bar (information here):** PF 1.5 in each of three windows after fees, positive at x1.2, deflated z at the bar. Day-clustered z reported; FORWARD decides.
- Every validation pass gets `workers/candidates/GEN8_<B|G><nn>.json` (stage `validation`, source `candles`, evaluator `scalper.gen8:forward_eval`, freeze at or after its commit rounded up to the hour), after a parity check of `forward_eval` against the history scorer on every validation window (identical trades and nets at C = 10).
- The result reports: funnel, best 10, N added, distinct bets or one rule with filters (shared conditions, pairwise Jaccard of validation entry sets), and each survivor's overlap with REF_GEN6_OICORE (Jaccard, entries in OICORE windows, PF inside and outside them).

## Counterparty (who would pay, if anything passes)

In the coin-flip zone a 15 minute market's quote is a bet on the next few minutes of the underlying. If new positions (open interest rising per traded contract) are opened by takers with information about the underlying the quoter has not yet priced, the quote drifts their way over the next 1 to 5 minutes and the counterparty is the slower market maker who sold to them; or, if the openers are uninformed and push the quote, the counterparty is the overreacting taker and the trade is the reversion. Honest alternative (and my expectation): the mid is close to a martingale over minutes, LATECAL and UNDER1 found the quotes calibrated, and a round trip pays two fees of about 1.8c at 50c plus the spread, so the median rule loses about 3 to 5c per trade and survivors are the top of thousands of draws.

## Numeric prediction (before the run)

Discovery PF median about **0.55** on Bitcoin and **0.45** on gold (two fees plus spread against a near-martingale mid); unconditioned base at every hold below 0.7. **Bitcoin: 0 to 10 discovery survivors; gold 0 to 5.** Validation pass rate 0% to 15%, control within 5 points, **both families FALSIFIED (prior about 85%)**. No rule near the deflation bar (z about 5.2). Zero bids at the fallback: under 0.1% of trades (a 30c to 70c side rarely loses its whole bid in 5 minutes). Prior that any GEN8 rule later reaches READY FOR THE FALSIFIER: about 3%.

## Kill criteria

Fewer than 1,000 discovery windows in a market = `NOT_ENOUGH_DATA` for that market. A strategy failing a gate is `FALSIFIED` at that gate. The family control rule above. Zero discovery survivors in a market = that market `FALSIFIED` at discovery. Grammar, thresholds, splits, fills, exits and gates are not changed after any outcome is read. Verdict words only: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## Files

`src/scalper/gen8.py` (build, search, freeze, validate, `forward_eval`, parity), this file, `workers/GEN8_FROZEN.md`, `workers/GEN8_frozen_*.json`, `workers/GEN8_RESULT.md`, `workers/candidates/GEN8_*.json`. Row, control and validation files in `data/gen8_*` (not committed).
