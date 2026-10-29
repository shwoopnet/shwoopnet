# SPREAD1: forward test of a spread filter on L1 (spec, registered 2026-10-29)

Docs only. No code, no bot change, no order is affected by this file. It is written
BEFORE any forward data is read, so the result counts either way.

## What the research found (quoted from `kalshi-scalper/README.md` on branch `claude/epic-ptolemy-0amjd9`, "Results: EXIT1, REGIME1, GOLD1D", run 2026-10-29)

The numbers below match the figures given in the request. L1's history, 32,499 entries,
windows by close-date thirds, profit factor (PF) per contract at 1 contract with
per-order rounded fees:

- Hold to settlement, unfiltered: 0.961 / 0.928 / 0.898.
- REGIME1 (c), skip entries with spread at entry of at least 2c: **kept set 1.051 / 1.006 / 0.984; removed entries 0.798 / 0.753 / 0.716.** The README calls it "a consistent lift of about 0.09 in every window, information for the L1 upkeep lane, not a pass".
- The other four REGIME1 filters (hours, weekends, recent volatility, loss within 2 hours) were FALSIFIED with no consistent lift. REGIME1 registered a gate of PF 1.5 in every window; (c) fails it. All five were FALSIFIED.
- EXIT1 was FALSIFIED (every new exit shape is worse than holding). GOLD1D's stability claim FAILED (gold PF about 1.2 to 1.3 in history, not 1.5).

If the README text changes, the README wins and this section must be corrected.

## Claim, stated before any forward data

On live L1 orders from 2026-10-30 00:00 UTC onward, orders whose spread at entry was
2c or more have a lower result per contract than orders whose spread was under 2c, and
the kept set (spread under 2c) has a higher PF than the unfiltered set.

**This is not a claim that L1 is profitable.** Even filtered, the history PF is 1.051 /
1.006 / 0.984, which is at or below 1.0 in the last two windows and nowhere near the
1.5-in-three-windows bar. At best the filter would reduce losses. It is a hypothesis
about which entries lose more, not a path to the bar.

Counterparty story: a wide quote means a thin book. At 88c to 97c the buyer pays the
ask, so a spread of 2c or more is a larger immediate cost on a payoff of 3c to 12c, and
a market whose makers are quoting wide is one where they see more risk than the price
shows. The history already agrees; the forward test asks whether it holds out of sample.

## Spread measure (from fields live orders already record)

`functions/kalshiLiveLib.js`, `bookSeen(m)` stores on every L1 order a `seen` object:
`seen.bid`, `seen.ask`, `seen.bidSize`, `seen.askSize`, `seen.at`, taken from the YES
book (`yes_bid_dollars`, `yes_ask_dollars`, `yes_bid_size_fp`, `yes_ask_size_fp`) of the
market the order was decided on. The order exports (Copy all orders, Copy order
diagnostics in `index.html`) carry them as `seenBid`, `seenAsk`, `bidSize`, `askSize`,
`seenAt`, and the full export also carries `avgFill` and `askAtDecision`.

**Spread = `seenAsk - seenBid`, in dollars; "wide" means spread >= 0.02** (compare with
a 1e-9 tolerance, since these are floats). It is the same number for a YES and a NO
order, because a NO buy is booked against the YES book. So a per-order spread can be
computed from stored fields, with no new logging and no new read.

Limits, stated plainly:

- `seen.bid` or `seen.ask` is null when Kalshi omitted it. Those orders are NOT skipped by the shadow rule; they are counted and reported separately ("unreadable").
- The book is read once, in the minute the order was decided. If the history's "spread at entry" was measured on a different candle, the two are close but not identical. The README does not say which; this is unverified and the first forward read must report the share of orders in the wide set next to the history's share, as a sanity check.
- Result per contract is `settledPnl / count` (an exit sold at the 25c line is `result: "exit"` and counts as its realised `settledPnl`). Orders marked hand-closed or unsettled are left out, as the stats already do. Gold orders may carry a larger `count` and an add-on; PF is on per-contract results so size does not change the read.

## The forward read

- **Start:** orders with `ts` at or after 2026-10-30 00:00 UTC. Orders before it are the history and are not reused.
- **Shadow rule:** nothing changes in the bot. For each settled live L1 order, label it WIDE (spread >= 0.02), TIGHT (spread < 0.02) or UNREADABLE. "Would have skipped" = WIDE.
- **Reported, per window and overall:** filled orders, WIDE share, per-contract net and PF for ALL, TIGHT, WIDE and UNREADABLE; losses in each set; the same split by market and by entry lead (`entryLead`), because gold, the capped crypto and the early probes have different books.
- **Source:** the order export or the nightly report's `?orders=1` rows. If the report rows do not carry the book fields, use Copy all orders.

## Minimum sample, and why

Payoff: a win is about +6c, a loss about -90c, loss rate about 7% (break-even about
6.25% before fees). Per contract that is a mean near -0.7c and a standard deviation of
about 24c, almost all of it the rare big loss.

- **Number of losses is what matters, not number of orders.** With about 7% losses, 30 losses in the WIDE set needs roughly 400 WIDE orders; fewer than that and a single loss moves PF by more than the effect.
- **Effect size is small.** The history lift is about 0.4c per contract (PF 0.96 to 1.05). To see a 0.4c difference in means at z of 2 with sd 24c needs about (2 x 24 / 0.4)^2, roughly 14,000 orders in a set. L1 will not produce that in a useful time. So **this test cannot confirm the effect size; it can only fail to contradict it.** The honest uses of the forward read are directional: is WIDE worse than TIGHT, in both halves.
- **Trigger:** read once, on the first of (a) 400 settled WIDE orders and 1,500 settled orders total, or (b) 2026-12-15. If (b) comes first with fewer than 30 WIDE losses, the verdict is NOT_YET_FALSIFIED and the report says the sample was too small to mean anything, not that the filter works.
- The read is done once per trigger, split into halves by time. No peeking and re-running until it looks right; each extra look counts as another try for the deflation floor.

## Verdict words and kill criteria

Only FALSIFIED or NOT_YET_FALSIFIED. There is no promote verb.

**FALSIFIED** if any holds at the read:

1. WIDE PF is not below TIGHT PF in each half.
2. TIGHT PF is not above ALL PF in each half.
3. WIDE net per contract is at or above TIGHT net per contract overall.
4. The WIDE share is under 3% or over 60% of readable orders (the measure does not match the history's, so the test is not the one registered).

**NOT_YET_FALSIFIED** otherwise. That is the whole result. It is not a pass, and it does not by itself justify any change.

Prediction, recorded now: TIGHT PF lands between 0.95 and 1.10, WIDE PF below 0.9, TIGHT still at or under 1.1, so the 1.5 bar is not met. Deflation applies: this is the filter picked as the one consistent survivor of five tries, so a forward result is worth less than a fresh one.

## If it passes (NOT_YET_FALSIFIED at the trigger)

The owner decides, in a reviewed code edit, whether to add a spread gate to the L1 tick. Constraints for that edit, so it cannot be mistaken for a new strategy:

- It only REMOVES orders. Same side, band (88c to 97c), size ladder, stops (12% loss stop, 5.5% window limit, 25c exit), caps and entry times.
- It reads the book the tick already reads (`bookSeen`), no new read, no key use beyond today's.
- Fails closed on an unreadable book is a choice for the owner: skipping those orders is safer, but changes the count; say which in the PR.
- A pull request, with gates in `test/` stating the consequence (a wide-spread market gets no order; nothing else changes), a Changelog line, and the deploy note (`functions/deploy-sizing.sh`). Merge only when the owner says so.
- Because it only removes orders, it also shrinks the window limit's use, which may let a later series in `L1_SERIES` order take a window it did not before. The edit must state that.

## Risks, said plainly

- **It can remove trades without adding edge.** The filtered set is still at or below PF 1.0 in two of three windows. Skipping the worst entries makes the bot lose less per order and trade less; it does not turn a losing rule into a winning one.
- **This is not a pass of the 1.5 bar.** Nothing here moves L1 toward it. The realistic best case is a smaller loss per order.
- **One filter picked from five tries** on the same history. The forward data is the only out-of-sample check, and with the power above it is weak.
- **Fewer orders means less data for other reads.** A gate would also shrink the sample for every other forward read (FLOOR1, THIN1, the smooth-climb kill rules); the owner should weigh that.
- Regime change: spreads are wider at certain hours and in thin markets, so the filter may be a proxy for those, which REGIME1 (a) and (b) did not find as filters on their own.

## Not in scope

No change to `functions/`, `index.html`, `firestore.rules` or any trading constant. No new field is logged. No page card.
