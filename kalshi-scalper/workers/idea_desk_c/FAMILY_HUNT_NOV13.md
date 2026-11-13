# Untried-family hunt, Nov 13, 2026 (Idea Desk C)

For the Head of R&D, under the 15:19Z instruction. No Kalshi request; no price, candle or result read. Only Desk B's family table, the RND_QUEUE census, the registry and the census listing's NON-price fields (series metadata, rules fields, early-close and settlement-timer fields) were read. [research]

**Counts:**
- 12 places checked; 0 cards; 3 "what it would need" lines.
- Earlier today, ONRRPCAL was ruled a version of SOFR1, and the overtime idea, a version of SOCDERIV, was not written.

## (a) Kalshi's own non-price fields

| Field or place | What was looked for | Why no card |
|---|---|---|
| `can_close_early`, `early_close_condition` | "will close early if the event occurs" markets | The mechanism is a "nothing happens" or hazard bet. That is the politics nothing-happens rule (already in POLITICS_RULES) and the favourite side above about 70c |
| `settlement_timer_seconds` (1 s to 1,800 s) | a window between the determination and the settlement that could be traded | Trading closes at the determination; the timer is the wait before payout, not a tradable window |
| `created_time`, new strikes added to a ladder | mispriced first quotes on a new strike | NEWLIST1 (registered) and the ladder parity row (declined) |
| `rules_primary` edits, `last_updated_ts` | prices around a rule amendment | Series metadata shows bulk updates (Oct 15, Nov 5), not per-market amendments; no event count to test |
| Settlement on the initial print, revisions ignored (claims, CPI index, OER) | the revision gap | An official-series calendar bet (excluded); CPI and claims are covered by NOWCAST1, CPI1, ECONNEW1 |

## (b) Official, permitted non-price sources for an unread family

| Family | Source considered | Why no card |
|---|---|---|
| Texas power peak demand (sweep only) | ERCOT public reports | Thin: 39 contracts a market on Nov 10; ERCOT's public API needs a registered key, terms unread |
| Truflation daily (sweep only) | none official | Thin (84 contracts); private index |
| State daily gas prices (17 states, never registered by series) | EIA weekly state and region retail prices (US government) | Inside the gas family (GAS1, GAS2 falsified) and an official-series bet |
| CPI component ladders (CPI index, OER, core goods, CPI combo) | BLS (US government) | NOWCAST1, CPI1 and the parity row; a combo of CPI legs is a lock or parity reading |
| Election night markets | state and county official returns (public records) | No election market closes before 2027 (Refinement's ELECTIONS_CENSUS); forward zero |
| FX and Treasury "after economic events" (USD/CAD, GBP/USD, 5 year) | release calendar | The EVENT830 and EVENT1 family |
| Hourly Treasury and commodity ladders | Treasury daily (already used) | Dead or thin (8 and 59 contracts a market) |

## What a card would need (the floor rule)

1. **ERCOT:** its terms read by Main and a registered-key decision by the owner, AND real volume in the Texas power market (it is thin now).
2. **Election night official returns:** a list of 2027 election nights with Kalshi markets, and the terms of each state's results site.
3. **State gas:** a reason the state-level market behaves differently from the national one, which GAS1 and GAS2 closed. None is known.

## Follow-up, six workers (Nov 13, 2026, 15:30Z to 15:50Z; public pages only, 0 Kalshi requests)

**Counts:**
- 6 places followed up; 1 card (GASCYCLE, `GASCYCLE_CARD.md`); 5 closed with reasons.
- One saved ERCOT PDF that a fetch tool wrote by itself was deleted unread.

| Opening | What the worker found | Verdict |
|---|---|---|
| ERCOT and Texas peak demand (KXTXERCOTPEAKD) | The Public API needs a free key, a human-registered account and at most 30 calls a minute. The website terms (clause 5) let raw public data be used and redistributed unmodified; clause 6 bars anything that degrades the site; there is no scraping clause. ERCOT publishes a 168 hour forecast; a vendor puts its day-ahead hourly error at about 1.9%. The settlement figure was not confirmed (Kalshi's rules page returned 429). | Closed for now. The market is thin (about 39 contracts a market). ERCOT's own forecast is public, so it is the market's anchor, not an edge. A forecast-against-market rule on a weather-driven load is very close to the closed weather family. Needs: real volume, the settlement report confirmed, and the owner's word on a registered key. |
| 2027 election nights | About 10 nights: the Wisconsin court, the Chicago mayor, Kentucky, Mississippi and Louisiana governors, the New Jersey and Virginia legislatures, and the Philadelphia and Houston mayors. Only New Jersey's terms explicitly allow copying; Kentucky, Virginia and Louisiana are silent ("All rights reserved"); Chicago and Mississippi blocked the read; the rest were unread; the feed vendors' terms were unread. | Closed for now: a slow family (about 10 events a year) and forward only; terms are mostly silent, and silence is not permission. Needs: Kalshi listings for those nights, the vendor terms, and a per-state terms read before any recorder. |
| State gas prices | Tax changes are 1c to 3c and public months ahead, so no edge. The Edgeworth price cycle in the upper Midwest (restorations of 10c or more after 1 to 2 weeks of decline; FTC WP303, Lewis and Noel, Noel 2010) is a real state-level mechanism. | **Card: GASCYCLE** (066159b6), zero-try count first |
| AI and compute (Ramp AI Index, OpenRouter, H100 OCPI, LMArena) | The settlement source is the earliest public value. OpenRouter's terms bar automated reads. Ornn, arena.ai and Ramp terms were unread. What remains is a late "already shown" read (favourite-late) or "the leader stays leader" (favourite-and-hold). | Closed |
| Company KPI markets | Four events a year per company. The free leads (Tesla registration trackers) are public and likely priced. App and web panels are paid. EDGAR bars crawlers outside its policy. | Closed |
| Health and transport | Measles is V2's HEALTHCOUNT1 idea, with about 4 events. There is no live COVID market. Flight cancellations settle on FlightAware (banned), access is restricted, and airlines are the informed side. | Closed |
