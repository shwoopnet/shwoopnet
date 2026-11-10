# Gold L1 kill latch (Nov 10, 2026, DRAFT until the owner merges and deploys)

The owner's decision (Nov 10, 2026): gold L1 gets a coded KILL and RETURN. This note records the design options, the one chosen and why, and the honest risks.

## What it does

**KILL (hard latch, cash basis, fees included).** Gold L1 stops placing new orders, with no automatic restart, when either rule fires, measured on gold's own settled orders since the re-arm date (`GOLD_KILL.rearmAt`, first value 2026-11-10 00:00 UTC):

1. drawdown from gold's own cash peak of **$58.75, a fixed dollar line** (6% of the $979.25 base when written; re-set only by a reviewed code edit when the base grows; the peak starts at 0), or
2. cash net under **-$20** once **40 trades** have settled since the re-arm.

**ALERT ONLY (no latch, no order change).** Each writes a `gold alert` event (the Bot page notification center shows it as a warning): rolling-60 cash profit factor under 0.7, rolling-100 under 1.0, 3 early sells in the last 40 trades. An alert that stays on is written once, not every minute.

**What stays running.** The exit watch never looks at the latch and still sells an open gold position at the 25c line. The other L1 markets are paused in code anyway. Sizes, bands, the 12% stop, the window cap and every other strategy are unchanged.

**RETURN.** Only a reviewed edit moves `GOLD_KILL.rearmAt` past the latch (a latch recorded for an older generation is ignored). Written bar for that edit: the shadow GOLDALL rows show **profit factor 1.3 or better over at least 60 trades and at least 7 days, and 1.3 or better in the second half**, then the owner approves. In the same edit set `rearmIsReturn: true`: the first **30** gold trades after the re-arm go out at **half size** (the count is halved, never below 1, the add-on is zeroed so the loss stop counts the whole order against the account). **Honest risk of this bar:** the refinement chat warned that 1.3 on 60 trades is stricter than gold's own long-run record (PF 1.40 on 307 trades, with rolling-60 values that wander well below it), so a normal gold could be kept out for a long time. The bar is the owner's choice; if it proves too strict the cost is idle gold, not lost money.

## Design options (the constraint: runL1Tick may make no new read or write)

`runL1Tick` only has the last 24 hours of orders plus a cached older block, not gold's history, and the off-equivalence fixtures (`offEquivalence.json`, `offEquivalenceIndex.json`, gates SW0 and SI0) pin every read and write the tick and `index.js` make.

| Option | Cost | Fixtures |
|---|---|---|
| A. Compute inside `runL1Tick` from the orders it has | cannot see all-time peak or 40 trade nets | unchanged, but wrong |
| B. Extend the tick's order read back to the re-arm date | a new, larger read every minute (hundreds of documents, about $1 a month and slower ticks), changes the reader | changes (new query args) |
| C. Add a post-tick hook inside `kalshiLiveArmed` that reads and writes the latch | new reads and writes inside the minute function | changes (`offEquivalenceIndex.json`) |
| D. **A separate scheduled function replays gold's orders and caches the verdict as a field on the sizing document the tick already reads; the tick only looks at that field** | one small extra function (about the cost of the tick's own cached reader), one new field | **unchanged** |

**Chosen: D** (`functions/kalshiGoldKillLib.js`, scheduled `kalshiGoldKillCheck` in `functions/index.js`, every minute). It is the only option that keeps the fixtures byte identical without a hidden state.

- **Replay, not stored state.** The checker re-derives the verdict from the orders every minute (the way OICORE's ladder is replayed), so two instances agree and the cache can always be rebuilt. The stored value is only a cache the tick can read for free.
- **Carrier.** `kalshiLiveControl/sizing.goldKill` = `{ tripped, rearmAt, rule, trippedAt, detail, alerts, half }`. The tick reads the sizing document at the top of every tick already, and its `setSizingState` writes `{...state}` back whole, so the field survives. `runL1Tick` adds no read and no write: `goldKillActive(args.sizingState, series)` is a pure look at what it received.
- **Sticky.** Within the replay the first breach trips for good, and a stored latch is never cleared by the checker. The line is a constant and the replay never reads the sizing base, so a latch lost to a clobber is re-derived identically by the next minute's replay on every instance. The only write that ever clears one is a new generation (a later `rearmAt` in code).
- **Cash basis.** A win or loss at the close is re-derived with `settledFields` (real fill and fee through `fillCost`); an early sell keeps its stored `settledPnl`; hand-closed and unfilled orders are skipped.
- **Order of effects.** The latch is written first, the event second, so a failed event write can never leave gold trading.
- **Read cost.** The checker reuses `makeRecentOrderReader` with a fixed start, the re-arm date: orders since `rearmAt` only (never a 30 day read), and the three alerts are computed from that same set (so they need 60 or 100 trades since the re-arm). The older part is read once every 15 minutes, then only the last 30 minutes of orders each minute. Gold places roughly 10 to 15 orders a day, so a 15 minute refresh reads about 100 to 150 documents in the first ten days and about 400 by day 30; with 96 refreshes a day plus a few documents each other minute, the expected read count is about 10,000 a day early on, rising to about 40,000 a day at 30 days (about $0.02 a day at $0.06 per 100K). It only grows until the next re-arm date moves the start forward.

### Known gaps of D (stated, not hidden)

1. **A clobber race (closed in effect).** If the checker writes the latch between the tick's sizing read and the tick's `setSizingState`, the tick's stale full write can erase it. Because the drawdown line is a fixed dollar constant and the replay does not read the base, the next checker run (at most about a minute later) derives the same trip and writes it again, whatever the base is by then; at most one more gold order could be sent in that gap. Making `setSizingState` a merge would close the gap itself but would change the fixtures, so it was not done.
2. **Lag.** An order settles in the tick (or the exit watch), then the checker sees it within a minute. A gold order placed in that gap is possible but is bounded by the 12% stop, the window cap and the 15 contract size.
3. **No phone push.** The latch writes a `gold kill` event (critical in the notification center and in the bell) but does not push to the phone; adding it means `kalshiPushLib` and a deploy of the push functions. The Bot page's silent-market warning will also say gold has gone quiet.
4. **The line does not follow the balance.** $58.75 is fixed; if the base grows a lot the line becomes a smaller share of it until a reviewed edit re-sets it. A missing or unreadable base no longer matters (the old fail-open note is gone).
5. **First value of the re-arm date.** 2026-11-10 00:00 UTC, so gold's earlier trades set no peak and raise no alert.
6. **Thresholds are untested on a real failure.** Whether 6% and -$20 would have fired on past gold stretches was not replayed here; the lifecycle doc's own warning applies (a Nov 6 rolling-60 dip was followed by 50 trades at PF 99, which is why that rule is an alert, not a latch).

## Deploy

`bash functions/deploy-sizing.sh` (it now also deploys `kalshiGoldKillCheck`) and `bash functions/deploy-push.sh` (the exit watch lives in the same library file; its behaviour is unchanged). No new secret, no rule change, no key on the checker. Until `kalshiGoldKillCheck` is deployed the latch never trips (the tick treats a missing field as not tripped).
