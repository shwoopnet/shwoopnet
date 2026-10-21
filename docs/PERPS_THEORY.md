# Moving into perpetuals: a theory memo

Written 2026-10-21 for the owner to review. **Theory only. Nothing is built, applied for or traded.** Plain words on purpose. Facts are from Kalshi's public perps market list, Kalshi's Perps API page and help-center titles, and news and CFTC-filing summaries of the fee schedule; none of it has been checked against a real order.

## The question

"Start theorizing moving entirely into perps instead" of Kalshi's prediction markets. This memo asks what we would have to believe, what the costs say, which ideas have any economic reason to work, and how to find out cheaply before anything moves.

## What a perp is, and what is different from what we trade today

- A perpetual future on Kalshi (the Perps API calls it "margin") tracks an underlying price with no expiry. Longs and shorts pay each other a funding rate to keep it near the underlying. Public data on 2026-10-21: 29 live perp markets (crypto, metals including gold and silver, WTI oil, the US500 and a US Tech 100 index).
- **It is a separate account.** Perps are not available to everyone (you apply), use a separate margin balance, and the transfer from the prediction balance was "not yet available" on Kalshi's own page. The production API is "rolling out member by member".
- **L1's edge is a prediction-market edge.** It buys the favourite at 88c to 97c in a 15 minute market and earns about +0.4c to +1c a contract because retail overpays for longshots. A perp has no longshot holders. Its price is the underlying's price, set by deep markets (Ethereum perp about $450M a day, Bitcoin $408M, gold $50M, US500 $6.6M). Leaving the prediction markets means leaving the only edge we have measured.

## The cost arithmetic (the part that decides most things)

- Reported fee tiers (CFTC filing summaries, to be confirmed on Kalshi's own fee page): **taker 12 bps of notional at the base tier, maker 5 bps**, plus a daily funding payment whose size we have not measured. Spreads are tiny (about 0.5 to 1 bp on US500, gold, Bitcoin and Ethereum).
- A round trip as a taker is about **0.24% of notional**; as a maker about 0.10%.
- The S&P's average daily move is roughly 0.75%. To break even on a daily direction bet you must be right about **58% of the time as a taker (53% as a maker)**. Our own research found direction bets negative on large samples, and the crypto and equity strategies both died to cost.
- With a $193 account: at 2x you hold about $390 of notional; one round trip costs about $0.93 (0.5% of the account) as a taker; a 1% move is $3.90. Leverage does not change the odds, it changes how fast a wrong streak ends the account (at 13.7x a 7% adverse move liquidates you; at 2x it takes about 50%).

## Candidate mechanisms and my honest odds

| Idea | Who loses money and why | Cost problem | My chance it passes a strict test |
|---|---|---|---|
| Daily trend following on the liquid perps (Bitcoin, Ethereum, gold, WTI, US500) | Slow money that reacts late to a persistent move | 0.24% a round trip, so only holds of days to weeks make sense | about 10 to 15% |
| Funding carry (take the side that gets paid) | The side paying funding for leverage | Unhedged it is just a direction bet; a hedge needs a second venue we do not use | under 5% |
| Pairs (Ethereum against Bitcoin, gold against silver) | Anyone forced to rebalance | Four legs of fees for a tiny edge | about 5% |
| Market making | Impatient takers | We would pay a 5 bps maker fee, not earn a rebate, and be picked off by faster traders (our own H5 test lost on prediction markets) | under 5% |
| Overnight drift on index perps | Intraday traders closing out | Two round trips a day at 0.24% each against a drift of a few basis points | under 3% |
| Using a perp to hedge L1's flips | Not applicable | A 15 minute binary near expiry has a huge, jumpy delta; hedging it costs more than the edge | under 3% |

None has a strong prior. The best is slow trend following, and our own record on trend strategies (the withdrawn Alpaca figures) says to expect the cost to eat it.

## What "entirely" would mean, and why I advise against it

- It trades a measured, thin, positive-or-zero edge (L1, gold at +4.5c a contract live) for an unmeasured one with higher fees and a faster way to lose the account.
- It breaks the anti-degen purpose of the site: perps are leveraged by design and can liquidate.
- The binding constraint at $193 is capital, not the venue. A strategy that earns 10% a month makes about $19 a month. Adding capital to a small, watched, positive-expectancy lane does more than switching venues.
- **Our own rule** (`CLAUDE.md`): a second strategy must show how it cannot hold a position at the same time as L1 and why it is a different bet. A separate margin account satisfies the first; the second is the whole question above.

## A staged way to find out, with a stop at each step

1. **Stage 0, read only, costs nothing:** a keyless recorder of perp prices, spreads and funding for about six liquid perps (Bitcoin, Ethereum, gold, silver, WTI, US500). Kalshi's perps data is public. The Perps API has no historical endpoints, so recording from now is the only way to get history; two to four weeks would give a first look at funding and spreads. Stop here if funding turns out large against us.
2. **Stage 1, your decision, no code:** apply for perps access, and read Kalshi's fee, margin and liquidation articles end to end. Stop here if the fees or the eligibility rules differ from the summaries above.
3. **Stage 2, only if a pre-registered test passes on recorded data:** a small separate margin balance (an amount you choose and can lose), **1x to 2x leverage at most**, one liquid perp, a hard loss stop, orders as limit orders, its own record on the page and never mixed with L1's. The rule, bar and kill criteria are written first in `kalshi-scalper/README.md`, as for every other test.
4. **Stage 3:** more only from its own live record.

## What I need from you

- Whether to build the Stage 0 recorder (read only, a small Firebase cost).
- Whether to apply for perps access (optional, no obligation).
- Whether you want me to keep this as a side track while the gold-first sizing and the new markets are read, or to make it the main track.
