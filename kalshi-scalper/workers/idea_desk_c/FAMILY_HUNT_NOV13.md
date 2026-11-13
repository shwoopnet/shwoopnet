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
