# GEN7 registration: a generator of open interest flow strategies EARLIER in the window, gold and Bitcoin 15 minute markets (Strategy Research V2, research only)

Written 2026-10-30 (about 00:35 UTC) by worker GEN7 and pushed BEFORE any GEN7 row is built, any strategy is generated or any outcome is read. Before this commit I read only: `workers/RULES.md`, `workers/candidates/README.md` and the reference candidate files, `workers/GEN6_REGISTRATION.md`, `workers/GEN6_RESULT.md`, `workers/GEN6_FROZEN.md`, `workers/FALS4_RESULT.md`, `src/scalper/gen6.py`, `src/scalper/gen1.py`, `src/scalper/oidrift.py` (threshold code), `src/scalper/rev1.py` (header), the ledger lines of `kalshi-scalper/README.md` that mention open interest, and the market counts, close ranges and null / zero counts of the `oi` column in `data/l1b`, `book`, `fresh`, `five` (no price, path or result). Nothing from Oct 28 onward is read for any purpose except the trailing threshold of REF_GEN6_OIDRIFT, which uses open interest changes only and only for days before each discovery window.

## Ledger check (why this is not a reworded tested idea)

- **GEN1** (840 to 180 s, ask 0.03 to 0.85, Bitcoin, Ethereum and gold pooled or per asset): it DID carry one open interest feature, `doi` (3 minute change, raw, a missing input set to 0), as one of 19 optional features; no condition was required to use it and none of its 5,000 passed discovery (best at size 1.25). GEN7 differs in that every rule MUST condition on open interest flow, has 11 open interest features (1, 3 and 5 minute changes raw and as a share, the change since the window's first candle, and new contracts per traded contract over each span), treats a missing input as a failed condition, and runs each market on its own. This is a family test of the brief's question, not a new idea free of priors: GEN1's null on `doi` among many features is a prior against it.
- **S36** (new money continuation, oi up 10% with price, FALSIFIED), **IDEAS20** OIBUILD / OIFLAT (filters on the L1 favourite), **OW7** (open interest per volume over 4 minutes as an L1 filter), **SMOOTH2** (open interest non-decreasing as a stacked filter), **AUTO3** (open interest rising in a 3.5 minute tree, holdout 1.24): each was one fixed rule or an L1 filter. GEN7 is a grammar on the cheap side and on favourites at 50c to 95c with exits; L1 filters are excluded (below).
- **GEN6 / FALS4 / OIDRIFT** (the 180 s cheap side after a 3 minute open interest jump): GEN7's looks are 840 to 240 s, never 180, and every rule whose discovery entry windows overlap a forward reference row by Jaccard above 0.5 is rejected (below).
- **The owner's ban on L1 and its variants** (README, "I do not want to research that idea ... any further"): a favourite rule whose discovery entry windows overlap L1's (side ask 0.88 to 0.97 at the candle ending 360 s or 600 s before the close) by Jaccard above 0.5 is rejected as an L1 variant and counted in N.

## Universe (time and cost only)

Bitcoin `KXBTC15M` and gold `KXGOLD15M`, run separately. Every settled window (result yes or no) in `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite`, `five.sqlite`, a ticker found in two files taken once from the first file in that order (as GEN6). Peers (same close time): Bitcoin uses Ethereum (`xa`) and gold (`xb`); gold uses Bitcoin (`xa`) and Ethereum (`xb`).

## Date split, fixed now (UTC, by the window's close time)

| market | DISCOVERY | VALIDATION (read once) | FORWARD |
|---|---|---|---|
| Bitcoin | 2026-08-06 00:00 to 2026-09-20 23:59:59 | 2026-09-21 00:00 to 2026-10-27 23:59:59 | the forward ledger, windows closing after each candidate's freeze |
| Gold | same | same | same |

Windows closing 2026-10-28 00:00 up to the freeze are not used by GEN7 at all (REV1's and GEN6's forward window). Validation rows are built only after the discovery survivor files are frozen, their sha256 committed and pushed (`workers/GEN7_FROZEN.md`).

## Grammar (per market; every strategy is exactly one of these)

**Looks.** A look is the 1 minute candle ending L seconds before the close, L in {840, 720, 600, 480, 360, 300, 240}. A strategy has a look range [L_hi, L_lo], L_hi >= L_lo, both from that set (28 ranges); looks are tried from L_hi down to L_lo and the FIRST look where the rule qualifies enters; at most one entry per window.

**Price class and side.** Class `cheap`: the side's ask at the signal candle in [0.05, 0.50]. Class `fav`: in (0.50, 0.95]. Side YES, NO or BOTH (YES tried before NO). YES ask = `ask_c`, NO ask = 1 - `bid_c`.

**1 to 3 conditions, at least one of them on open interest.** Each `feature <= q` or `feature > q`, q a decile (10th to 90th) of that feature over all of the market's DISCOVERY rows (every look, both classes, both sides; feature values only, no outcome). The first condition is drawn from the open interest features, the others from all features, no feature twice. All inputs from candles ending at or before the signal candle t; oi is the candle's end-of-period open interest (FALS4 check 2).
- **Open interest features (11):** `doi1`, `doi3`, `doi5` = oi(t) - oi(t - 60, 180, 300); `sdoi1`, `sdoi3`, `sdoi5` = the same divided by oi(t - lag) (missing if that is 0); `doiw` = oi(t) - oi(first candle of the window, the earliest candle ending after close - 900); `npv1`, `npv3`, `npv5`, `npvw` = the same change divided by the summed volume of the candles ending in (t - lag, t] (for `npvw`, after the first candle up to t); missing if any of those candles is absent or the sum is 0 (so `npvw` is missing at a look on the window's first candle).
- **GEN1's Kalshi features (14):** `ask`, `bid` (of the side), `spread` (yes_ask - yes_bid), `d1`, `d2`, `d3`, `d5` (side bid change over 1, 2, 3, 5 minutes), `rng5` (max minus min of the side bid over t, t-60 ... t-300), `vol` (signal candle volume), `hour` (UTC), `xa_d2`, `xa_mid`, `xb_d2`, `xb_mid` (peer mid change over 2 minutes signed toward the side, peer mid). GEN1's `doi` is `doi3` here.
- NOT used: spot and perp features (`z`, `r3`, `tb1`, `tb5`; not refreshed for forward, none for gold).
- A feature whose input is missing fails its condition (no trade at that look; later looks may still be tried).

**Fill (gates).** The NEXT candle's closing ask of the side (the candle ending L - 60 s before the close). A missing next candle means no entry at that look. A next-candle ask of 0 or 1 or above is no entry at that look. **Also reported:** the signal candle's ask as the fill, same exits (information).

**Exits (47).** The scan is the side's closing bid on candles ending strictly after the fill candle and at most 60 s before the close. A bid of 0 is never a sale (that candle is skipped).
- `hold`: to settlement (1 or 0, no fee).
- `time X`, X in {600, 480, 360, 240, 120, 60}: sell at the bid of the first scan candle ending at or after close - X; allowed only if X < L_lo - 60. If none, held (counted).
- `tp` (GEN1's take-profit levels): TP in {+3, +5, +8, +12, +20c} on the closing bid, stop in {none, -5, -10, -20c}, checked on every scan candle; if neither hits, fallback `hold` or `sell at the 60 s candle` (40 combos).
Draws that pick an exit not allowed for their look range are redrawn and still counted in N.

**Fees.** 7% x C x p x (1 - p) rounded up to the cent per order, entry and any sale; settlement free. Gates at C = 10; C = 1 reported; fees x1.2 stress.

**Zero volume.** An entry whose signal or fill candle, or an exit whose candle, has volume 0 is flagged. A strategy with more than 20% flagged trades fails a screen. PF is reported both with and without flagged trades for the best 10.

## Exclusions (rejected draws count in N)

Discovery entry window sets compared by Jaccard; above 0.5 with any of these is rejected, whatever the exit:
- Bitcoin: `REF_GEN6_OICORE` (cheap side at 180 s, doi3 > 86,299.56), `REF_GEN6_OIDRIFT` (same with the trailing 30 day 90th percentile, `scalper.oidrift.threshold`), REV1 (NO ask in (0.03, 0.45) at 180 then 120 s), `REF_BTC_UNDERDOG_180` (ask 15c to 49c at 180 s).
- Gold: `REF_GOLD_UNDERDOG_180`.
- Both markets, favourite rules only: L1 (side ask 0.88 to 0.97 at 360 s or at 600 s).

## Generation, dedupe and counting

Seeded random draws (seed 7, per market) until **5,000 distinct** strategies per market or 300,000 draws. A draw is distinct if it has at least 30 discovery trades, is not excluded above, and does not match a kept strategy: a match is discovery entry sets with Jaccard above 0.5 AND exits within one step (same family; time: adjacent or same X; tp: TP and stop within one step each, same fallback; hold equals hold). **N added = every draw, on both markets.** Running count before GEN7 about 563,361; the Bonferroni z bar for the new total is reported.

## Screens (fixed now)

- **DISCOVERY:** PF at C = 10 (next-candle fill) at least **1.5**, at least **100 trades on at least 15 days**, zero-volume share at most 20%.
- Survivors frozen to `workers/GEN7_frozen_btc.json` and `workers/GEN7_frozen_gold.json`, sha256 in `workers/GEN7_FROZEN.md`, committed and pushed before any validation row is built.
- **VALIDATION (read once):** PF at C = 10 at least **1.3** on at least **50 trades**, stressed-fee PF above 1.0, zero-volume share at most 20%.
- **Family control (kill rule, as GEN4 and GEN6):** discovery FAILURES at the screen's size (100+ trades, 15+ days) run through the same validation screen. If the survivors' pass rate is not at least 5 points above the control's, the market's family is `FALSIFIED` as a whole; individual validation passes still go to the forward ledger labelled "family control not met".
- **RULES bar (information here):** PF 1.5 in each of three windows after fees, positive at x1.2, deflated z at the bar for N. Day-clustered z is reported; FORWARD decides.
- Every validation survivor gets `workers/candidates/GEN7_<B|G><nn>.json`, stage `validation`, source `candles`, evaluator `scalper.gen7:forward_eval`, freeze at or after its commit rounded up to the hour. The evaluator is checked against the history scorer on every validation window (identical trades and nets) before the files are committed.
- The result also reports each survivor's entry overlap (Jaccard, validation windows) with `REF_GEN6_OICORE`'s entries, and whether the survivors are distinct bets or one rule with filters (shared conditions, a greedy Jaccard clustering of validation entry sets).

## Counterparty (who would pay, if anything passes)

When open interest rises, new contracts are being created: someone is opening a position rather than trading out of one. If the openers are price-insensitive late-favourite buyers (bots buying the near-certain side 6 to 10 minutes out, of which L1 is one), the cheap side they sell to the market maker is underpriced in those windows, and the cheap-side holder is paid by them; if instead the openers are informed (a spot move not yet in the quote), the side they open is the one to follow, and the counterparty is the slower quoter. Honest alternative: earlier in the window the favourite is not yet certain, quotes are calibrated (LATECAL from 120 s on, UNDER1 grid flat), so open interest flow is just volume, and anything that looks good is selection on noise.

## Numeric prediction (before the run)

Bitcoin: median discovery PF about 0.85 (spread and fees on a calibrated quote); **20 to 120 discovery survivors; 3% to 15% pass validation; control within 5 points; family FALSIFIED by the control rule (prior about 70%).** If GEN6's effect extends earlier, survivors will cluster at 240 to 300 s on the cheap side with `doi3` / `doi5` conditions, and that is the only place I expect a real pass. Gold: median PF about 0.75, **5 to 60 survivors, 0% to 10% validation, control not met (prior about 80%).** Every survivor's day z below the deflation bar (about 5.2). Prior that any GEN7 survivor later reaches READY FOR THE FALSIFIER: about 7%.

## Kill criteria

Fewer than 1,000 discovery windows in a market = `NOT_ENOUGH_DATA` for that market. A strategy failing a gate is `FALSIFIED` at that gate. The family control rule above. Grammar, thresholds, splits, fills, exits, exclusions and gates are not changed after any outcome is read. Verdict words only: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## Files

`src/scalper/gen7.py` (build, search, freeze, validate, `forward_eval`, parity), this file, `workers/GEN7_FROZEN.md`, `workers/GEN7_frozen_*.json`, `workers/GEN7_RESULT.md`, `workers/candidates/GEN7_*.json`. Row files in `data/gen7_*` (not committed).
