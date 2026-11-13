# Lanes (b) combos and (c) perps (Idea Desk C, Nov 13, 2026)

For the Head of R&D. No Kalshi request; public pages only; nothing stored. [research]

**Counts:** sources read 21. Candidates 1, from lane (b): COMBODONE, low prior, with a count-first go/no-go. Lane (c) EMPTY.

## Lane (b): COMBODONE, a combo whose early leg has already settled YES

**The contract facts.**
- **Kalshi help center** (https://help.kalshi.com/markets/combos): a combo pays the product of its legs and can settle at $0 "immediately" when one leg settles at $0. A leg settling at a fraction scales the payout. Combo prices come from a request-for-quote system, and each combo also has "its own dedicated order book".
- **The combo template** (FOOTBALLSTATS, served as NFLPREPACK.pdf on kalshi-public-docs):
  - "Outcomes may resolve at different times";
  - an impossible outcome resolves the combo to No at once;
  - "Last Trading Date ... will be the same as the Expiration Date";
  - tick $0.001.
- **So a combo whose EARLY leg settled YES appears to keep trading,** now worth only the product of its remaining legs. Not stated explicitly by Kalshi; Gemini's combo docs say exactly that for theirs.
- **Kalshi's request-for-quote docs:** a request fails when "a leg is not open for trading". So once a leg has settled, new maker quotes may be impossible, and only the combo's existing resting book is left.

**Mechanism.** After an early leg settles YES, an order resting in the combo's own book was priced while that leg was still uncertain. Its owner may not have moved it, and makers cannot re-quote through the request system. An ask priced off the old, lower probability is cheap against the product of the remaining legs' current mids.

- **Who is on the other side:** whoever left a resting combo order: a holder posting an exit, or a maker whose quote (valid up to 30 seconds) or leftover order was not pulled.
- **Why they might lose:** they did not update after a decided leg, and the request system cannot reprice it for them.
- **Honest counter:**
  - makers answer requests in under 200 ms (Oddpool, 126 requests, 13 maker ids) and almost certainly price from live legs;
  - our earlier pass found almost no resting asks on sampled combos;
  - "most" of about 37 million combo tickers never traded (Predicted, June 2026).
  So the book may simply be empty.
- **Closest closed or registered work, and why it differs:**
  - Lock and price-consistency scans (closed) look for riskless sets across live markets; this is one held position priced against a fair value after a decided fact.
  - The registered combo house-side paper test and the leg-count markup buy NO before any leg is decided.
  - The in-game lag (closed) is between live markets at one minute. Here the fact is settled, hours old, and the stale price sits in a market that cannot be re-quoted.
  - Not favourite-and-hold, provided the band excludes 88c and up.
- **Forward log:** the combo recorder already holds quotes, the top 5 book and trades every 30 minutes, with each combo's leg tickers.
- **Zero-try go/no-go:** count, on recorded combos, the snapshots taken after one leg settled YES and before the combo settled that show ANY resting ask. If fewer than about 30 independent combos a week show one, close it as "nothing to buy". Only then compute the gap between the ask and the product of the remaining legs' mids at the same poll.
- **Weakness:** a 30 minute poll misses a stale order that lives seconds. A burst poll after a leg settles would be a recorder change for the owner.
- **Signals:** unknown until the count. **Prior:** low, about 2%.

## Lane (c): perps, EMPTY

- **Kalshi's CFTC filing for single-stock perps** (Nov 4, 2026, https://www.cftc.gov/filings/ptc/ptc11042642345.pdf, read in full):
  - trading runs 6:00 pm ET Sunday to 5:00 pm ET Friday, NOT on weekends or market holidays;
  - while the cash market is closed the reference is "the official closing price from the most recent regular trading session" (frozen);
  - funding is paid once a day at the cash close from minute-by-minute divergence during regular hours only, with "No Premiums ... computed while the U.S. equity cash market is closed";
  - trading continues through after-close earnings unless a regulatory halt applies.
- **Weekend Monday-open prediction:** ruled out for stock perps, which are shut at weekends. For the index perps the hours are unverified. The only size found (a vendor's 80 bp against 113 bp error) is unverified.
- **After-hours earnings drift:** efficient after 2016 (Christensen, Timmermann and Veliyev, arXiv 2601.08962; Jiang, Likitapiwat and McInish, JFQA 2012). No drift size clears 50 bp after fees of 2.6 to 12 bp a side.
- **8:30 am ET releases:** ES, NQ and premarket all trade then, so the perp is the slowest venue, not the best informed.
- **One question for our own data (not a candidate):** overnight, deviations from the frozen close carry no funding. So a perp lagging premarket is a pure lead-lag test. But there is no permitted source for ES or premarket prices, and spot-lead work is already running.
