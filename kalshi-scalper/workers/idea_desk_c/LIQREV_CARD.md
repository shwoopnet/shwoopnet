# LIQREV: OKX liquidation cascades against the Bitcoin 15 minute market, the reversal side (Idea Desk C, Nov 13, 2026)

**Written before any OKX liquidation row, Kalshi quote, candle or result was read.** Forward only. A card for the Head of R&D's read, not registered; the Verification Analyst scores it. [research]

`LIQREV | family: forced liquidations on another venue (price-insensitive flow), bet on the partial reversal of the move they cause; entry 12 to 3 minutes before the close, hold to settlement | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 2%`

## Mechanism, and the other side

- **Forced flow.** When leveraged Bitcoin positions on OKX are liquidated, the exchange sells (longs) or buys (shorts) at any price. A burst of them pushes spot, and the Bitcoin index Kalshi settles on, past where unforced traders would put it. Part of that move tends to come back once the forced flow stops.
- **Where the edge would come from.** A Kalshi 15 minute Bitcoin market is priced from the current spot. During a cascade it prices the move as if it will hold. The other side is the market maker and the takers who price from the post-cascade spot. The liquidated traders are the source of the overshoot, not our counterparty.
- **Honest counter:**
  - Kalshi's makers watch spot and may already discount cascades.
  - The reversal may take longer than the minutes left in the window.
  - No size of the reversal is known to this desk; no published figure was checked.
  - Cascades cluster in volatile hours, where the 15 minute market is least predictable.

## Data (all recorded already; nothing new)

- **OKX liquidations:** the OKX recorder (`record-oklq.yml`, BTC-USDT-SWAP and BTC-USD-SWAP, filled liquidations with time, side and size), forward from 2026-11-10 to 2026-12-31, on `quote-data` under `oklq/`. OKX keeps only about 17 hours, so this can never be backfilled.
- **Kalshi quotes:** R6's 2 second book for KXBTC15M (`book15r6/`, to 2026-12-15).
- **Settlement results:** the public settled results.

## The rule (proposed, frozen at registration, never before)

- **Cascade size.** L(t) is the sum of liquidated contracts on one side (long or short), in BTC, over the 3 minutes ending at minute t, across both swaps.
- **Threshold H, a one-time calibration on liquidation sizes only.** The 99th percentile of L over every minute from 2026-11-10T00:00Z to before 2026-11-17T00:00Z. This is computed after registration, from the OKX rows alone. No Kalshi price or result is opened for it, and H is then frozen and committed before any Kalshi row is read.
- **Trigger.** In a KXBTC15M window, the first minute t between 12 and 3 minutes before the close where L(t) for one side is at least H. At most one bet a window.
- **Bet.**
  - **Long liquidations** (forced selling pushed price down): buy YES.
  - **Short liquidations** (forced buying pushed price up): buy NO.
  - In both cases: at the R6 book's ask at the first poll after t, ask 20c to 80c, spread 4c or less, 1 contract, hold to settlement.
  - Fill at the ask seen plus the rounded fee (an upper bound). A void is a fee-only loss, counted as a bet.
- **Conflict rule (lifecycle 7f).** No bet in a window where OICORE placed an order on the opposite side ("the first strategy in holds the market"). Such windows are counted, not bet.

## Numeric prediction, kill lines, windows

- **Prediction:** about 1% of minutes trigger by construction; within the 12 to 3 minute span, about 1 to 3 triggers a day. A partial reversal shows in a minority of triggers. Development cash PF 0.8 to 1.2.
- **Kills:**
  - **Zero-try count, at the end of development, before any price:** closed if fewer than 60 triggered windows have a two-sided R6 quote.
  - **Development:** closed if fewer than 60 bets, a cash PF under 1.0, or a half under 1.2.
  - With fewer than 30 bets: "no evidence at n = x".
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46 (clustered by US Central day), one try.
- **Windows (by window close time, date constants):**
  - calibration of H = liquidation sizes 2026-11-10 to before 2026-11-17, no outcomes;
  - development = closes 2026-11-17T00:00:00Z to before 2026-11-30T00:00:00Z, halves split at 2026-11-23T12:00:00Z;
  - **held-out = closes 2026-11-30T00:00:00Z to before 2026-12-16T00:00:00Z**, the end of R6's Bitcoin recording, read once on the Head's go.
  - These are forward days, so no earlier test can have read them. Rule (h) is still for the Head to check against CFRTI-K, CFRTI1-BTC and W-SPOTLEAD1, which use the same series in November.
- **Held-out line for HELDOUT_REGISTRY.md:** `| LIQREV | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/LIQREV_CARD.md | KXBTC15M (R6 book15r6) with OKX liquidations (oklq) | Calibration H from liquidation sizes 2026-11-10 to before 2026-11-17 (no outcomes); development = closes 2026-11-17 to before 2026-11-30; held-out = closes 2026-11-30 to before 2026-12-16, read once on the Head's go | 2026-11-17; 2026-11-30; 2026-12-16 | NOT READ | card text | card only, not registered; overlap with CFRTI-K, CFRTI1-BTC and W-SPOTLEAD1 windows for the Head to rule |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a different source and field.**
   - Forced-liquidation flow on another venue, which no test has read. Lifecycle 7f lists "OKX liquidation cascades" as an untested idea.
   - Closest: W-SPOTLEAD1 (Kalshi lags spot, betting WITH the move) and OICORE (Kalshi open interest, cheap side). LIQREV bets AGAINST the move, from a different field, in the mid band.
   - Self-score: unique, medium confidence.
2. **Entry and exit:** 12 to 3 minutes before the close, hold to settlement. That is the 15 minute crypto grid, shared with OICORE and gold L1's timing; it stays out of OICORE's opposite side by the conflict rule.
3. **Correlation:** it trades OICORE's market (Bitcoin 15 minute), so correlation with OICORE must be measured in shadow (r under 0.3 over 20 days, lifecycle 7d check 3). Flagged, not assumed.
4. **Declined list:**
   - **Taker order flow on the 15 minute tape:** that row covers Kalshi's own tape. OKX liquidations are another venue's forced fills, a new data source.
   - **Cheap-side grammar on the 15 minute series without a new data source:** this is a new source, and it trades the mid band.
   - **Favourite-late:** excluded by the 20c to 80c band.
   - **Not** a lock, market making, spot lead (opposite direction) or a 15 minute model sweep.
   - The Verification Analyst decides whether "15 minute crypto plus a new outside feed" escapes the closed 15 minute crypto rows.
