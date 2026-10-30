# GEN6 registration: a generator of LATE-window underdog strategies, gold and Bitcoin 15 minute markets (Strategy Research V2, research only)

Written 2026-10-30 by worker GEN6 and pushed BEFORE any GEN6 row is built, any strategy is generated or any outcome is read. Before this commit I read only: `workers/RULES.md`, `workers/candidates/README.md`, `workers/FALS3_RESULT.md`, `workers/GEN4_*`, `workers/GEN5_*`, the UNDER1 and REV1 entries of `kalshi-scalper/README.md`, `src/scalper/gen1.py`, `src/scalper/fwdeval.py`, `src/scalper/fwdledger.py` (loader), and the market counts and close ranges of `data/l1b`, `book`, `fresh`, `five` (plus the list of candle `end_ts` offsets of one Bitcoin window, to see that candles end on the minute from 840 s left to 60 s after the close). No quote path, price or result of any window was looked at by GEN6.

## Ledger check (why this is not a reworded tested idea)

- **GEN1 / GEN1S / GEN2 / GEN3 / GEN5**: same 1 minute grammar, but entries only 840 to 180 s left. GEN6 enters at 240, 180, 120 or 60 s left, and only on the cheap side (ask 5c to 50c). The 240 and 180 s looks overlap GEN1's last grid points; 120 and 60 s were never reached by a 1 minute generator.
- **UNDER1** (cheap side, whole grid of series x time x band x side, no conditions, FALSIFIED as a grid) and **REV1** (Bitcoin cheap NO, ask 0.03 to 0.45, 120 or 180 s, held, no conditions; forward from 2026-10-28 00:00 UTC, read 2026-11-05): GEN6 requires 1 to 3 conditions, so neither bare rule is in the grammar. To avoid near-duplicates, any Bitcoin strategy whose HOLD exit and discovery entry set have Jaccard above 0.5 with REV1's rule (one entry per window, the first of 180 then 120 s) is rejected as a REV1 duplicate, and any strategy with a HOLD exit and Jaccard above 0.5 with the ledger references `REF_BTC_UNDERDOG_180` / `REF_GOLD_UNDERDOG_180` (ask 15c to 49c at 180 s, held) is rejected the same way. Rejected draws count in N.
- **REV1's data window is not touched:** Bitcoin VALIDATION ends at 2026-10-27 23:59:59 UTC, the moment before REV1's forward window opens (a deliberate deviation from the brief's Oct 29, stated now). Gold VALIDATION runs to 2026-10-29.
- **HUNT2** (bare time x price grid): GEN6 has no bare cell. **GEN4** (seconds-resolution, recorder, last 150 s): different data and resolution; FALS3 showed its core loses on candles. **FALS3** read the FAVOURITE side at 180 and 120 s on all 85 days; its mirror (the underdog base at those looks) is therefore partly known on every day used here. This is disclosed: the validation window is NOT clean for the unconditional base; what is new is the conditions and exits. The family control below exists for exactly that reason.

## Universe (time and cost only)

Bitcoin `KXBTC15M` and gold `KXGOLD15M`, run separately. Every settled window (result yes or no) in `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite`, `five.sqlite` (gold only in `five`), a ticker found in two files taken once from the first file in that order. Peers (same close time): Bitcoin uses Ethereum (`xa`) and gold (`xb`); gold uses Bitcoin (`xa`) and Ethereum (`xb`).

## Date split, fixed now (UTC, by the window's close time)

| market | DISCOVERY | VALIDATION (read once) | FORWARD |
|---|---|---|---|
| Bitcoin | 2026-08-06 00:00 to 2026-09-20 23:59:59 | 2026-09-21 00:00 to 2026-10-27 23:59:59 | close after 2026-10-30 02:00 |
| Gold | 2026-08-06 00:00 to 2026-09-20 23:59:59 | 2026-09-21 00:00 to 2026-10-29 23:59:59 | close after 2026-10-30 02:00 |

Validation rows are built only after the discovery survivor files are frozen, their sha256 committed and pushed (`workers/GEN6_FROZEN.md`). Bitcoin windows closing 2026-10-28 00:00 to 2026-10-30 02:00 are not used by GEN6 at all.

## Grammar (per market; every strategy is exactly one of these)

**Looks.** A look is the 1 minute candle ending L seconds before the close, L in {240, 180, 120, 60}. A strategy has a look range [L_hi, L_lo] with L_hi >= L_lo, both from that set (10 ranges); looks are tried from L_hi down to L_lo, the FIRST look where the rule qualifies enters; at most one entry per window.

**Side.** YES, NO or BOTH. A side qualifies at a look when its ask (YES ask = `ask_c`; NO ask = 1 - `bid_c`) at the signal candle is in [0.05, 0.50] (the cheaper side), and every condition holds. With BOTH, YES is tried before NO (in a sane book only one side can be at 50c or under).

**1 to 3 conditions**, each `feature <= q` or `feature > q`, q a decile (10th to 90th) of that feature over all of the market's DISCOVERY rows (every look, every side in the 5c to 50c band; feature values only, no outcome). Features, all from candles ending at or before the signal candle, side-relative (bid and ask of the side bought):
- GEN1's Kalshi features: `ask`, `bid`, `spread` (yes_ask - yes_bid, identical for both sides of one book, which is why "the other side's spread" is not a separate feature here), `d1`, `d2`, `d3`, `d5` (side bid change over 1, 2, 3, 5 minutes), `rng5` (max minus min of the side bid over the 6 marks t, t-60 ... t-300), `vol` (signal candle volume), `doi` (open interest change over 3 minutes), `hour` (UTC hour of the signal), `xa_d2`, `xa_mid`, `xb_d2`, `xb_mid` (peer mid change over 2 minutes signed toward the side: + for YES, - for NO; peer mid).
- The side's own path, new: `m1`, `m3`, `m5` (side MID change over 1, 3, 5 minutes), `wrng` (max minus min of the side mid over every candle of the window up to the signal), `wgap` (side mid minus its window maximum so far, at most 0), and the peers' spreads `xa_spr`, `xb_spr`.
- NOT used: GEN1's spot and perp features `z`, `r3`, `tb1`, `tb5` (their bars are not refreshed automatically, so a forward candidate using them would never be scored; gold has none).
- A feature whose input candle is missing is MISSING and its condition is false (no trade at that look). GEN1 used 0; GEN6 does not.

**Fill (gates).** The NEXT candle's closing side ask (the candle ending L - 60 s before the close), for L = 240, 180, 120. For L = 60 the next candle ends AT the close, which is not a tradeable quote, so the fill is the signal candle's ask **plus 2c** (capped at 0.99), fixed now as a conservative stand-in for the one minute lag. A missing next candle means no entry at that look (later looks may still be tried). **Also reported:** the signal candle's ask as the fill, same exits.

**Exits (51).** Bids are the side's closing bid on candles ending strictly after the fill candle and at most 60 s before the close (the scan); for the L = 60 look there is no scan candle, so only HOLD is allowed.
- `hold`: held to settlement (pays 1 or 0, no fee).
- `time X`, X in {120, 60}: sell at the bid of the first scan candle ending at or after close - X; allowed only if X < L_lo - 60 (so `time 120` needs L_lo = 240, `time 60` needs L_lo >= 180). If no such candle, held (counted).
- `tp`: take profit TP in {+3, +5, +8, +12, +20, +30c} on the closing bid, stop in {none, -5, -10, -20c}, checked on every scan candle; if neither hits, fallback `hold` or `sell at the 60 s candle` (48 combos). Allowed only if L_lo >= 180.
Draws that pick an exit not allowed for their look range are redrawn and still counted in N.

**Fees.** 7% x C x p x (1 - p) rounded up to the cent per order, entry and any sale; settlement free. Gates at C = 10 (per contract); C = 1 reported; fees x1.2 stress.

**Zero volume.** An entry whose signal candle, or an exit whose candle, has volume 0 is flagged. A strategy with more than 20% flagged trades fails the screen. For the best 10, PF is also reported with the flagged trades removed.

## Generation, dedupe and counting

Seeded random draws (seed 6, per market) until **5,000 distinct** strategies per market or 300,000 draws. To count as distinct a draw needs at least 30 discovery trades, must not be a REV1 / REF duplicate (above), and must not match a kept strategy: a match is discovery entry sets (window ids) with Jaccard above 0.5 AND exits within one step (same family; time: same or adjacent X; tp: TP and stop within one step each and the same fallback; hold equals hold). **N added = every draw, distinct or not, on both markets** (plus the reported signal-fill variant, which is information only and not counted separately). Running count before GEN6 about 501,174; the Bonferroni z bar for the new total is reported.

## Screens (fixed now)

- **DISCOVERY pass:** PF at C = 10 (next-candle fill) at least **1.5**, at least **100 trades on at least 15 days**, zero-volume share at most 20%.
- Survivor lists frozen to `workers/GEN6_frozen_btc.json` and `workers/GEN6_frozen_gold.json`, sha256 in `workers/GEN6_FROZEN.md`, committed and pushed before any validation row is built.
- **VALIDATION pass (read once):** PF at C = 10 at least **1.3** on at least **50 trades**, stressed-fee PF above 1.0, zero-volume share at most 20%.
- **Family control (registered kill rule, as GEN4):** discovery FAILURES with at least 100 trades on 15 days (the screen's size) are run through the same validation screen. If the survivors' validation pass rate is not at least 5 points above the control's, discovery carried no information and the family is reported `FALSIFIED` as a whole; the individual validation passes still go to the forward ledger, labelled "family control not met".
- **RULES bar (information only here):** PF 1.5 in each of three windows after fees, positive at x1.2, deflated z at the bar for N. Day-clustered z is reported per survivor; it is not a GEN6 gate because FORWARD decides.
- Every validation survivor gets a candidate file `workers/candidates/GEN6_<B|G><nn>.json`, stage `validation`, source `candles`, evaluator `scalper.gen6:forward_eval`, freeze time at or after its commit. The evaluator is checked against the history scorer on the validation rows (identical trades and nets) before the files are committed.

## Counterparty (who would pay, if anything passes)

Late-window holders of the favourite in Bitcoin and gold who pay too much for "nearly certain" in the last 4 minutes (FALS3: Bitcoin favourites at 50c to 85c win 2.7 to 4.3 points less often than their price at 180 s, PF 0.77 over 85 days, z -4.97; gold 0.85), and the liquidity that sells the cheap side to them. A condition on the side's own path (a reversal under way, a quiet window, a peer moving the same way) would pick the windows where that overpricing is largest. Honest alternative: the favourite's overpricing is a few points, the cheap side's spread and fee take most of it, and any condition that looks better is selection on noise.

## Numeric prediction (before the run)

Bitcoin: the unconditional underdog at 120 to 180 s is mildly positive on these days (UNDER1, FALS3's mirror), so many conditioned rules clear PF 1.5 on 100 discovery trades by chance on top of it: **100 to 400 discovery survivors; 25% to 45% pass validation; the control within 5 points, family FALSIFIED by the control rule (prior about 70%).** Gold: **30 to 150 discovery survivors, 10% to 25% validation, control not met (prior about 75%).** Underdog PF is noisy (wins pay 2 to 19 times the stake), so the best validation PFs will be 2 or more on 50 to 80 trades and every survivor's z will be far below the deflation bar (about 5.2). Forward will shrink survivors toward the base. Prior that any survivor later reaches READY FOR THE FALSIFIER: about 10%.

## Kill criteria

Fewer than 1,000 discovery windows in a market = `NOT_ENOUGH_DATA` for that market. A strategy failing a gate is `FALSIFIED` at that gate. The family control rule above. Grammar, thresholds, splits, fills, exits and gates are not changed after any outcome is read. Verdict words only: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## Files

`src/scalper/gen6.py` (build, search, freeze, validate, `forward_eval`), this file, `workers/GEN6_FROZEN.md`, `workers/GEN6_frozen_*.json`, `workers/GEN6_RESULT.md`, `workers/candidates/GEN6_*.json`. Row files in `data/gen6_*` (not committed).
