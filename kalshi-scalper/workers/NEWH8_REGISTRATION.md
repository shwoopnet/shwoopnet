# NEWH8 registration (Strategy Research V2 worker NEWH8, 2026-10-30, research only)

Written and pushed BEFORE any NEWH8 rule was joined to a fill quote after its signal or to any outcome. Code `src/scalper/newh8.py`;
result `workers/NEWH8_RESULT.md`. Scope (owner, 2026-10-28): no buy-the-favourite-and-hold idea and no L1 filter, exit, size, hour or
throttle. Every rule below BUYS the cheap side (ask 5c to 50c) and holds it; none sells the cheap side (that is buying the favourite,
closed). Markets: KXGOLD15M and KXBTC15M only (one rule reads the Ethereum 15 minute market's open interest as an input).

## What was looked at before this was written (disclosure)

1. Ledger: `workers/RULES.md`, README headings, GEN6, FALS3, FALS4, MECH1, SLOTEX, SLOTEX-ETH, UNDER1, REV1, IV1, LAG2, S29/S32/S33,
   NOVIEW, NEWH1 to NEWH7 results, GEN6's feature list (`gen6.window_rows`).
2. **`python -m scalper.newh8 describe`** (printout kept in the scratchpad, numbers below): features at the 180 s signal candle
   only, for windows with a cheap side, OICORE-firing against the rest, by stage. **No result and no quote after the signal candle was
   read.** It is a look at what else is true in the OICORE windows (part 1 of the brief), and it shaped R1 and R4. OICORE itself was
   selected on both discovery and validation, so anything modelled on its windows is not blind to validation: that is stated here and
   is why each rule's overlap with OICORE is reported.

**What the describe shows (Bitcoin, discovery / validation; firing vs rest, medians):**
- the cheap side is cheaper (ask 12c vs 19c; 14c vs 22c);
- it has **not led recently**: the cheap side's mid was above 0.5 within the last 180 s in 11.7% / 14.4% of firing windows against
  34.7% / 37.8% of the rest; fewer flips (median 1 vs 2), smaller fall over the last 3 minutes (10c vs 13c; 9c vs 13c), smaller
  intra-minute range (0.14 vs 0.20);
- much more activity: 3 minute volume 493k vs 369k (615k vs 462k), open interest level 455k vs 331k;
- the last print of the signal minute sat nearer the cheap side's BID (median location 0.33 vs 1.0; 0.0 vs 1.0), i.e. favourite buyers
  took last;
- the spread is the same (1c); the hour leans to 13 to 19 UTC;
- the other markets' open interest jumps at the same time (Ethereum doi 4.7k vs 3.3k; 9.2k vs 5.8k; gold's own top-decile doi windows
  coincide with Bitcoin doi 75k vs 47k, 139k vs 67k).

In words: the exception is **a settled window (the favourite has led for a while and is not moving much) that suddenly gets a wave of
new contracts, at the same time on the other markets**. Gold shows the same pattern with its own doi, but GEN6 found nothing there.

## Common to every rule (fixed now)

- **Data:** 1 minute candles, files as NEWH6/NEWH7 (Bitcoin and Ethereum `l1b`, `book`, `fresh`; gold `l1b`, `book`, `fresh`, `five`;
  first file wins per close). Universe: every settled window in those files, chosen by date only.
- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00; VALIDATION 2026-09-21 00:00 to 2026-10-28 00:00.
  Nothing closing on or after 2026-10-28 00:00 is loaded. The third window is the FORWARD record (a survivor goes to
  `workers/candidates/` with a freeze time after its commit, evaluator `scalper.newh8:forward_eval`, parity against this code).
- **Signal:** the candle ending 180 s before the close. Cheap side: the side whose closing ask there is in [0.05, 0.50], YES checked
  first (YES ask = `ask_c`, NO ask = 1 - `bid_c`). `doi` = open interest at the -180 candle minus at the -360 candle. Side mid = YES
  mid or 1 - YES mid.
- **Fill:** the cheap side's closing ask on the NEXT candle (ending 120 s before the close), strictly inside (0, 1), no band (as
  REF_GEN6_OICORE); else no trade (counted). A missing candle a rule needs, or a missing peer, is a data gap (counted), never a
  no-trade.
- **Held to settlement.** No rule sells, so no bid is used and the zero-bid rule never applies (stated). Fees: 7% x C x p x (1 - p)
  rounded up to the cent per order on the buy (there is no sell). Headline C = 10; C = 1 reported; fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades, and without trades whose signal or fill candle had volume 0.
- **One trade per window per rule.** Day-clustered z reported; the deflated bar (N about 592,000) is z about 5.2.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on >= 50
  trades and net > 0 at fees x1.2.
- **Cut points** (90th percentiles below) are computed once from discovery-dated FEATURES only (no outcome, no fill), printed in the
  result and applied unchanged to validation and forward.
- **Overlap with REF_GEN6_OICORE**, reported for every rule and stage: Jaccard of the traded window sets and the share of OICORE's
  entries the rule also takes (Bitcoin rules), or the share of the rule's entries whose close time is an OICORE entry's close time
  (gold rule). Over 0.5 by either measure: "not independent" is written next to the verdict.

## R1 BUSYCALM, Bitcoin (1 try): a settled window with heavy volume, without reading open interest

- **Rule:** cheap side at -180 as above; vol3 = volume of the candles ending -300, -240 and -180 is above V90 (the 90th percentile of
  vol3 over discovery Bitcoin windows with a cheap side and all three candles); the cheap side's mid is at or below 0.5 at every candle
  ending -360, -300, -240, -180 (it has not led in the last 3 minutes); and the cheap mid fell by less than 0.10 from -360 to -180.
- **Counterparty:** favourite buyers who arrive in bulk late in a settled window (fixed-time favourite programs and humans closing out
  the day's book) and take the favourite ask, pushing the cheap side below its chance; the makers selling them the favourite hedge
  nothing and quote by time decay.
- **Honest alternative:** volume is the outcome of price moves and news, not of a counterparty; FALS4 found 3 minute volume at matched
  counts earns 0.82 to 1.01, and the calm filter selects the most settled windows, where the longshot is most overpriced (UNDER1).
- **Prediction:** FALSIFIED; discovery PF about 1.2, validation about 1.0; Jaccard with OICORE about 0.3 to 0.5.

## R2 PEEROI-X, Bitcoin (1 try): Ethereum's new-contract wave, when Bitcoin's own did not fire

- **Rule:** at the same close, Ethereum doi (-360 to -180) above E90 (90th percentile of Ethereum doi over discovery windows with both
  candles), AND Bitcoin's doi at or below 86,299.56 (OICORE did NOT fire); buy Bitcoin's cheap side as above. Missing Ethereum or
  Bitcoin open interest: gap.
- **Counterparty:** if the OICORE edge is a cross-market writer of cheap-side contracts (a program creating contracts on every 15 minute
  market at once), its arrival on Ethereum marks it on Bitcoin even when Bitcoin's count stays under the fixed threshold.
- **Honest alternative:** Ethereum's open interest follows Ethereum's own price; the OICORE edge may live in Bitcoin's count only.
- **Prediction:** FALSIFIED; discovery PF about 1.0. Overlap with OICORE is 0 by construction (that is the point).

## R3 GOLDX, gold (1 try): gold's cheap side when Bitcoin's open interest jumps

- **Rule:** at the same close, Bitcoin doi (-360 to -180) above 86,299.56 (OICORE's own trigger); buy GOLD's cheap side at -180 as
  above. Missing Bitcoin candles: gap. Gold's own doi is not read.
- **Counterparty:** as R2, a cross-market writer; the describe shows gold's busy windows coincide with Bitcoin's.
- **Honest alternative:** gold's cheap side late in the window loses about a quarter of its stake (GEN6 gold median PF 0.73); a Bitcoin
  count says nothing about gold's price.
- **Independence:** same trigger as OICORE, different market: it is NOT an independent condition; it tests whether the mechanism is
  market-wide. Prediction: FALSIFIED; discovery PF about 0.8.

## R4 SETTLED, Bitcoin and gold (2 tries): the calm part of the exception alone, no volume or open interest

- **Rule:** cheap side at -180 as above; the cheap side's mid was never above 0.5 at any candle from the window's first to -180, or the
  last candle where it was ended at -540 or earlier (it last led at least 6 minutes before the signal); and |cheap mid(-180) - cheap
  mid(-360)| < 0.03 (not moving).
- **Counterparty:** makers who mark a settled longshot down on time alone, while a static price near the strike still leaves a real
  reversal chance.
- **Honest alternative:** the favourite-longshot bias: settled longshots are the most overpriced (UNDER1, TAIL, GEN6 gold).
- **Prediction:** FALSIFIED on both; discovery PF about 0.8 (Bitcoin) and 0.7 (gold).

## Part (3) and what was declined without a try

- **Selling the overpriced cheap side** = buying the favourite and holding: closed by the owner. Not done.
- **Spot distance from the strike / fair value at 180 s:** IV1, LAG2, H7, L8, L9 tested it; reworded. Not spent.
- **Last print location (who took last):** MECH1's taker split showed no edge split; candles in the forward ledger carry no last price
  either, so a survivor could not be read forward. Not spent.
- **Intra-minute range, wick, one-sided pull, compression:** S29, S32, S33. Not spent.
- No other mechanism with a nameable counterparty outside the closed list was found; R2 and R3 are the "other mechanism" (a
  cross-market contract writer).

## Information looks (counted in N, never screened)

- I1, I2: REF_GEN6_OICORE's own entries split by R4's calm condition (calm vs not) and by R1's "has not led in 3 minutes" condition,
  both stages: does the exception live in the settled windows?

## Kill criteria (each try)

Discovery PF < 1.5 on >= 100 trades, or net <= 0 at fees x1.2: FALSIFIED (validation printed for the record). Discovery pass and
validation PF < 1.3 on >= 50 trades, or net <= 0 at x1.2: FALSIFIED. Fewer than 100 discovery or 50 validation trades:
NOT_ENOUGH_DATA. Both passes: NOT_YET_FALSIFIED, a candidate file and a parity check, forward read only. No parameter changes after any
score.

## Count

N tried: **5** (R1, R2, R3, R4 Bitcoin, R4 gold) + 2 information looks = **7**. Running count about 592,086 (after NEWH7) plus other
workers' additions, plus 7.
