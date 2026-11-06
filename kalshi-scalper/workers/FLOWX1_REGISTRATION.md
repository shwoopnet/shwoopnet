# FLOWX1 registration: taker flow on the contract's own public tape as information about the CHEAP side of hourly, daily and weekly Financials, Crypto and Commodities markets (Strategy Research V2 worker, 2026-11-06)

Written and pushed BEFORE any candle, trade or outcome of this study was fetched. What was read first: the README ledger (searched FLOW1, PERPFLOW1, LIQ1, TAPE, BIGPRINT, FLOWHR1, BOOKIMB1), FLOW1_RESULT, FLOWHR1_REGISTRATION and RESULT, the forward runbook. What was fetched before this file: the public settled-market LIST of 228 series (ticker, event, open and close time, total volume; the `result` field was never stored; `src/scalper/flowx1.py census`). No candle, no trade, no outcome.

**Owner rules obeyed.** Cheap side only: ask 3c to 30c, taker at the ask, held to settlement, fee 7% x C x p x (1-p) rounded up with C=10 (and C=1, and x1.2 stress). No favourite or near-certain side is scored anywhere (the code only admits an entry ask in 0.03 to 0.30; a test asserts it). No 15 minute candle trigger: the trigger here is the contract's own trade tape on markets that are not 15 minute. The frozen last third (closes on or after 2026-10-03T16:00Z) is never listed or fetched (`CUT` in the code).

## Not a duplicate

FLOW1: Bitcoin 15 minute, FALSIFIED. FLOWHR1: hourly Bitcoin ladder KXBTCD on the forward recorder (NOT_ENOUGH_DATA, sign wrong). PERPFLOW1: perpetuals. BOOKIMB1 and BOOKCH1: book sizes, not trades. LIQ1: spread and volume, not signed flow. BIGPRINT (the owner's footprint view) is a page tool, never scored. New here: signed taker flow of a non-Bitcoin, non-15-minute cheap tail, over every series in the universe, scored pooled and by family.

## Mechanism and counterparty

If informed takers lift the offer on the cheap side before a look, the cheap side wins more often than its price implies; the counterparty is the resting maker who sold it cheap. The null (already measured by CALIB1 and FLOW1) is that cheap-side takers are noise and pay the spread, so the cheap side loses about 5.5c to 6c per contract pooled. A result needs the high-flow cheap side to beat that baseline by at least 6c.

## Universe (fixed from the series catalogue and the market list; no price or outcome used)

Series with category Financials, Crypto or Commodities and frequency hourly, daily or weekly, excluding 15M series, TEST series and the Bitcoin family (title contains Bitcoin, or ticker starts KXBTC, or BTC, BTCD, BTCD-B). 228 series; 72 have settled markets in window. Window: closes 2026-09-06 00:00Z up to but not including 2026-10-03T16:00Z (live /markets and /markets/trades tier only; the historical endpoints were rate limited on 2026-11-06, so August is not used). Census file sha256 prefix 84135e0333897ea5 (1,444,008 settled markets, 72 series, 10,961 events). Halves: D1 closes before 2026-09-20 00:00Z, D2 after.

**Candidate markets.** Total volume at least 100 contracts; at most 40 markets per series, taken in ascending md5 of the ticker (so any prefix is a random sample and giant ladders such as KXETH do not dominate); the whole list is then ordered by md5 of the ticker and processed in that order under a fetch time box of 150 minutes; whatever prefix is done when the box ends is the sample, and its size is reported. Events with more than 3 candidates keep their first 3 in md5 order (cluster control).

## Exact feature and look

- Look L = close minus 60 minutes. Skip a market whose open is after L minus 20 minutes (no flow window).
- Signal candle: the 1 minute candle ending at L. Cheap side = the side with the lower ask (yes ask, or 1 minus yes bid for NO); tie or missing candle = skip. Signal ask must be in [0.03, 0.30].
- Entry: taker at that side's ask on the candle ending at L + 1 minute; hard limit 0.30 (above it, no trade). One entry per market.
- Flow window W = [max(open, L - 60 minutes), L]. Over every public trade of the market in W, cheap-side flow = (contracts a taker bought on the cheap side minus contracts a taker sold on it) / total contracts, where a taker_side equal to the cheap side is a buy and the other side is a sell. Skip if total contracts in W is under 10 (NoFlow, counted).
- **Treated arm (primary, one rule): HIGH flow, flow >= +0.30.** Control: every cheap-side entry (flow-agnostic) in the same sample, and the complement (flow under +0.30).
- **Secondary arm (counted as its own try): LOW flow, flow <= -0.30**, the direction FLOW1's lead used. Both thresholds are round numbers fixed now; nothing is tuned.
- Outcome joined only after the entry list is frozen, from GET /markets/{ticker} on the entries only.

## Numeric prediction (stated before any outcome)

Primary: high-flow cheap-side entries earn at least +0.5c per contract after fee (that is, at least 6c above the -5.5c pooled baseline), PF at least 1.5 in both halves. My expectation, from FLOW1 and CALIB1, is that it will not: expected treated mean about -5c and no ordering between high and low flow.

## Kill criteria and verdict words

- NOT_ENOUGH_DATA: fewer than 150 treated entries, or fewer than 40 distinct events among them, or fewer than 8 days.
- FALSIFIED: n at least 150, and treated mean after fee under +0.5c, or PF under 1.5 in either half, or treated minus complement not above 0 (event-clustered permutation one sided p above 0.10).
- LEAD (not a promotion): n at least 300 treated on at least 60 events, PF at least 1.5 in both halves at fee x1.2, treated minus control at least 6c, and day-clustered z of the treated mean at least the deflated bar 5.27 (it will almost surely not be reachable at this n; a near miss is reported as such, not as a lead). Holdout (the frozen third) is NOT read and needs the coordinator in writing.
- Reported always: treated, control and complement n, win rate against mean price paid, net per contract at C=10 and C=1, PF, halves, by family (crypto, commodities, FX, indices, rates), flow-window volume, NoFlow and NoCandle counts, one read only.

## Count

Tries: 2 (high-flow arm, low-flow arm). N +2 on the running count of about 730,451 (about 730,453), deflated z bar about 5.27.

## One-read guards

Code `src/scalper/flowx1.py` (subcommands `list`, `fetch`, `score`); `score` refuses to run twice (marker file) and prints the registered bars beside the result. Fetch stage writes candles and trades only; no result field is read until `score`.
