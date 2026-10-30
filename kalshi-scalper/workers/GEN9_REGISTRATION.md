# GEN9 registration: a generator of SUB-MINUTE ROUND TRIPS on the gold and Bitcoin 15 minute markets, from the public trade tape in 10 second bars (Strategy Research V2, research only)

Written 2026-10-30 by worker GEN9 and pushed BEFORE any tape of the study period is fetched, any row is built, any strategy is generated or any outcome is read. Before this commit I read: `workers/RULES.md`, `workers/GEN8_REGISTRATION.md`, `workers/GEN8_RESULT.md`, `workers/DIRECTOR_2026-10-30.md`, the README entries of TAPE20 (result), SWEEP1 (registration, amendment, retirement), FP2 (registration title), T1 to T4 (result table), MAKER4 (amendment), GOLDFILL and MECH1 (result paragraphs), `src/scalper/mech1.py` (fetch code), `src/scalper/gen7.py` and `gen8.py` (loaders, fee, scorer). **One timing probe was run before this file** (to size the fetch, no prices or features looked at): one Bitcoin and one gold market closing 2026-10-29 16:00 UTC (outside the study period), 900 s to 120 s before the close: Bitcoin 35,405 trades in 43.8 s (36 pages), gold 7,169 trades in 6.6 s. The day sample and fetch order below were printed by `python -m scalper.gen9 plan`, which reads only the market list (tickers, close times, whether settled) and touches no tape. The code `src/scalper/gen9.py` is committed with this file; its row builder was smoke-tested on a synthetic random tape only.

## Scope (fixed by the brief)

No buy-the-favourite-and-hold, no L1 work (owner, 2026-10-28), not the cheap-side-late-held trade (director, 2026-10-30). GEN9 is a round trip: **buy a side priced 20c to 80c by the last trade, at a 10 second bar between 840 s and 240 s before the close, and sell it 30 to 180 s later, never later than 120 s before the close. Nothing is ever held to settlement, and the settlement result is never read** (the universe needs only "settled", for the candle files).

Note for the lead: SWEEP1 was retired on 2026-10-28 as "a flow pattern on the same contracts as L1" under the owner's process rule 3. GEN9 runs on the same two series as GEN8 (which the lead also briefed) and never buys the favourite band nor holds; it is run because the brief assigns it.

## Ledger check: what is already closed, and what is new

- **GEN1, GEN2, MUT1, GEN8** (1 minute candles): round trips in this zone, with take profit, stop and time exits, found nothing (GEN8 best at size 1.14 Bitcoin, 1.09 gold; median 0.55 / 0.52; base PF 0.37 to 0.69). Candles can only enter and exit on minute closes and price at the closing quote.
- **TAPE20**: tape flow in the 2 minutes before the 6 minute decision, as a filter on the L1 favourite HELD to settlement. Not repeated: GEN9 never holds and never uses the favourite band.
- **SWEEP1**: big prints and sweeps on Bitcoin with a 1 minute entry lag and scale-out exits that hold part to settlement; retired before any trigger was scored. GEN9 enters at the bar after the signal (10 s), never holds, and print size is only one of 16 features.
- **FP2**: gold footprint as a loss warning on L1 entries (held). Not repeated.
- **T3 / T4** (tapeflow, first 300 s after the open): a tape-priced early drift scalp, -4.11c, FALSIFIED. GEN9 is mid-window (840 to 240 s left), conditioned, with a different exit set.
- **MAKER4 / GOLDFILL / MECH1**: resting orders, fill models and the open interest core's counterparty. Not related trade shapes.

**New, and only this:** entries and exits timed to 10 seconds instead of a minute, priced from trade prints, with conditions on sub-minute taker flow, trade-count bursts, short price changes and print size. This is the only route the brief leaves to reopen GEN1 / GEN8, and the prior against it is strong: GEN8 found the mid near a martingale over 1 to 5 minutes, and GEN9's fill model is MORE expensive than GEN8's (it adds 1c on each leg).

## Data

- **Source:** Kalshi's public trade tape (`/historical/trades` for closes before 2026-10-01 first, else `/markets/trades`, the other as fallback; `ticker`, `min_ts`, `max_ts`, cursor to the end; keyless). Each market: trades in (close-900, close-120]. Polite: one request at a time per stream, 0.5 s after every page, a 429 waits 3 s doubling to 60 s.
- **Reuse:** MAKER4's cached tape (`data/maker4/tape_*.json`, (close-750, close-115], complete) is used where it exists, with only (close-900, close-750] fetched. MECH1's cache ((close-360, close-180]) and GOLDFILL's (about 254 s around the 6 minute decision) do not cover the range and are not used.
- **10 second bars** (`data/gen9/bars.sqlite`, raw trades not kept): bar j covers (close-900+10j, close-900+10(j+1)], 78 bars. Per bar: trade count, YES-taker contracts, NO-taker contracts, largest print and its taker side, last trade's YES price and time.
- **1 minute candles** (spread only): `l1b`, `book`, `fresh`, `five` sqlite, first file wins (GEN7's files).

## Sample: 50% of days, then a fixed time budget (both fixed now, before any fetch)

The full fetch is about 3,000 gold markets x 5 s and 8,000 Bitcoin markets x 44 s, about 50 hours on one stream, so:
1. **Days:** `random.Random(909)`, `sample` of ceil(half) of the DISCOVERY days and then of the VALIDATION days (UTC dates of the close). Drawn: discovery 23 of 46: 08-06, 08-08, 08-18, 08-19, 08-21, 08-23, 08-24, 08-25, 08-27, 08-29, 08-30, 08-31, 09-01, 09-02, 09-04, 09-06, 09-07, 09-10, 09-15, 09-16, 09-17, 09-18, 09-20; validation 19 of 37: 09-21, 09-22, 09-23, 09-24, 09-25, 09-27, 09-29, 09-30, 10-02, 10-05, 10-09, 10-10, 10-11, 10-13, 10-16, 10-21, 10-22, 10-24, 10-26.
2. **Markets:** every settled market of the series closing on a sampled day with candles: Bitcoin 3,983 (discovery 2,175), gold 3,072 (discovery 1,704).
3. **Order:** each list shuffled by `random.Random(919 + 1)` (Bitcoin) and `random.Random(919 + 2)` (gold); discovery and validation interleaved, so any prefix is a uniform random sample of the sampled days.
4. **Two streams, one budget:** stream A fetches gold in its order, then Bitcoin from the END of Bitcoin's order; stream B fetches Bitcoin from the front. A market is claimed once. **No market is started more than 6 hours after the first stream starts.** The analysed set is whatever was fetched (a front prefix plus a tail suffix of a random permutation, still a uniform random subset).
5. **Expected:** gold complete or nearly (about 4 to 5 h); Bitcoin about 500 to 700 markets (about 300 to 400 discovery windows). **Bitcoin may be NOT_ENOUGH_DATA by this budget.** An extension in the same order is allowed only by an amendment pushed before any Bitcoin discovery row is built.

## Three windows (UTC, by the window's close)

| | DISCOVERY | VALIDATION (read once) | FORWARD |
|---|---|---|---|
| both markets | 2026-08-06 to 2026-09-20 (sampled days) | 2026-09-21 to 2026-10-27 (sampled days) | R6's real book, from 2026-10-29 (proposal only, see below) |

Nothing closing on or after 2026-10-28 00:00 UTC is read. Validation rows are built only after the discovery survivor files are frozen, hashed in `workers/GEN9_FROZEN.md`, committed and pushed.

## Grammar (per market; every strategy is exactly one of these)

- **Entry bars:** bar ends at L = 840, 830, ..., 240 s before the close (61). A strategy has a range [L_hi, L_lo] with both ends from {840, 780, ..., 240} (66 ranges); bars are tried from L_hi down to L_lo every 10 s, YES before NO, and the FIRST qualifying row enters. **At most one entry per window.**
- **Side:** YES, NO or BOTH. The side's price by the last trade at or before the bar end (YES = the trade's YES price, NO = 100 minus it) must be in **[20c, 80c]**, and that last trade must be at most 60 s old.
- **1 to 3 conditions,** `feature <= q` or `> q`, q a decile (10th to 90th) of that feature over all of the market's DISCOVERY rows (every bar, both sides), no feature twice, from 16 features, all signed toward the side (s = +1 YES, -1 NO) and computed only from bars ending at or before the entry bar:
  `f10, f30, f60` (s x (YES-taker minus NO-taker contracts) over the last 10, 30, 60 s), `i10, i30, i60` (the same divided by total contracts), `c10, c30, c60` (trade counts), `burst` (c10 / max(1, c60 / 6)), `dp10, dp30, dp60` (s x change of the last trade price over 10, 30, 60 s, cents; dp60 at 840 s is missing because the tape starts at 900 s), `big30` (largest print in the last 30 s), `bigdir30` (s x its taker side), `px` (the side's price). A missing input fails its condition.
- **Fill model (APPROXIMATE, stated plainly):** entry at the side's last trade price **+ half the median spread + 1c**, where the spread is the median of the closing spreads (ask minus bid) of the 1 minute candles ending at E-120, E-60 and E, E the end of the minute holding the bar (no candle: no entry). Sale at the side's last trade price at the exit bar **- half spread - 1c** (floor 0; no candle at the exit: half spread 1.5c, flagged). **These fills are derived from trade prices, not from a book: no depth, no queue, no latency beyond the 10 s bar. A survivor would need recorder R6's real book (recording since 2026-10-29) to confirm it.**
- **Exits (90), never held:** H in {30, 60, 90, 120, 150, 180} s after the entry bar, x take profit {none, +3, +5, +8, +12c} x stop {none, -5, -10c} on the sale price of every 10 s bar after entry up to the entry + H (sell at that bar's sale price), else sell at entry + H. **An exit is allowed only if entry + H is at least 120 s before the close at every bar of the range: H <= L_lo - 120.** Draws picking an exit not allowed are redrawn and still counted in N.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, **both legs**, gates at **C = 10**; C = 1 and fees x1.2 reported. A sale at 0 pays no exit fee.
- **Stale-price flag (the tape's zero-volume analogue):** an exit priced from a last trade more than 60 s old is flagged; more than 20% flagged fails a screen; PF reported with and without flagged trades for any survivor.

## Generation, dedupe and counting

Seeded draws (`random.Random(9000 + 1)` Bitcoin, `9000 + 2` gold) until **5,000 distinct** per market or 300,000 draws. Distinct: at least 30 discovery trades, and no kept strategy with discovery entry window sets of Jaccard above 0.5 AND an exit within one step (H, take profit and stop each within one index). **N added = every draw on both markets (all of them, rejected or not) + 12 information looks** (the unconditioned first in-zone entry, both sides, range 840 to max(240, H+120), sold H seconds later, each H, per market). Running count before GEN9 about 627,838; the Bonferroni z bar for the new total is reported.

## Screens (fixed now)

- **Minimum data:** a market with fewer than **300 discovery windows or 15 discovery days** is `NOT_ENOUGH_DATA` and is not searched (its N is 0).
- **DISCOVERY:** PF at C = 10 at least **1.5**, at least **100 trades on at least 15 days**, stale share at most 20%.
- Survivors frozen to `workers/GEN9_frozen_btc.json` / `workers/GEN9_frozen_gold.json`, sha256 in `workers/GEN9_FROZEN.md`, committed and pushed before any validation row is built.
- **VALIDATION (read once):** PF at C = 10 at least **1.3** on at least **50 trades**, PF at fees x1.2 above 1.0, stale share at most 20%.
- **Family control (kill rule, as GEN6 to GEN8):** discovery FAILURES at the screen's size (100+ trades, 15+ days) go through the same validation screen. If the survivors' validation pass rate is not at least 5 points above the control's, the market's family is `FALSIFIED` as a whole; individual passes are then labelled "family control not met".
- **RULES bar (information):** PF 1.5 in each of three windows after fees, positive at x1.2, deflated z at the bar. Day-clustered z reported. A pass here earns only an R6 forward registration.
- **Survivors of validation** are NOT put in the candles-based forward ledger. They are written up for an R6 forward check: the result file proposes an R6 evaluator (same bars rebuilt from R6's `trades.csv.gz`, entry at R6's recorded ask walked through the 5 levels at the first poll after the entry bar, sale at the recorded bid at the exit poll) with its own registration before any R6 row is read.
- The result reports: funnel, best 10 per market (discovery and the one validation read), N added.

## Counterparty (who would pay, if anything passes)

Sub-minute: if takers who move the quote within seconds (a burst of same-side flow, a large print) are informed about the underlying and the quoters reprice over the next 30 to 180 s, a follower who enters at the next 10 s bar earns the rest of the move from the slow quoter; if the burst is an impatient taker overpaying, the fade earns the reversion from that taker. Honest alternative (my expectation): Kalshi's 15 minute quotes reprice within seconds (TAPE20, MECH1: flow carries no information the price lacks), and the round trip here costs about 3c of spread-plus-1c on two legs plus two fees of about 1.75c at 50c, about 6.5c, against 30 to 180 s moves that are mostly noise.

## Numeric prediction (before any fetch)

Discovery PF median about **0.40** on both markets (cost about 6.5c a round trip); unconditioned base PF 0.25 to 0.55 rising with H. **Survivors: gold 0 to 3, Bitcoin 0 to 3 (if searched).** Validation pass rate 0% to 10%, control within 5 points, **both families FALSIFIED (prior about 90%)**, Bitcoin possibly `NOT_ENOUGH_DATA` by the budget (about 40%). No rule near the deflation bar. Stale exits under 2% on Bitcoin, 2% to 8% on gold. Prior that anything later passes on R6: about 2%.

## Kill criteria

The minimum-data rule above. A strategy failing a gate is `FALSIFIED` at that gate. Zero discovery survivors in a market = that market `FALSIFIED` at discovery. The family control rule. Grammar, thresholds, splits, fills, exits, sample and budget are not changed after any outcome is read. Verdict words only: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## Files

`src/scalper/gen9.py` (plan, fetch, bars, rows, search, freeze, validate), this file, `workers/GEN9_FROZEN.md`, `workers/GEN9_frozen_*.json`, `workers/GEN9_RESULT.md`. Bars, distinct, control and validation files in `data/gen9/` (not committed).
