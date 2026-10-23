# Why costs "kill" the bot when a manual scalper does not pay much (written 2026-10-21, for the owner)

**Short version.** The fee is small in dollars. What is tiny is the edge it is taken from. The bot risks 93c to win 7c, so it has to be right about 94 times in 100 just to break even, and it is right about 93.

## The numbers (the bot's own 303 settled, filled orders, Oct 7 to Oct 21)

| | |
|---|---|
| Contracts bought | 2,147 |
| Entry fees (Kalshi's 7% x price x (1 - price), about 0.44c a contract) | about 0.47% of the money staked |
| Result before fees | **slightly positive** |
| Result after fees | **slightly negative** |
| Win rate | 93.4% |
| Average win / average loss | +$0.41 / -$5.95 (one loss cancels about 14 wins) |
| Win rate needed to break even at the average price paid (about 93.4c plus 0.44c fee) | about **93.9%** |

So fees did not create the problem, they decided the sign: a +0.29c a contract edge before fees became -0.15c after. Any change that saves half a cent a contract moves the bot from losing to roughly even; no change in fees makes it rich, because the gross edge is 0.29c on a 93c stake.

## Where a manual scalp differs (and what we measured about it)

1. **Resting orders (maker) versus crossing the spread (taker).** The bot sends immediate-or-cancel orders at the ask: it always pays the taker fee and the spread. A manual scalper who rests a buy at the bid and a sell at the ask pays no spread and may pay a lower fee. This is real money.
2. **But it did not rescue our rule when we tested it on recorded books.** Resting at the bid saved the spread (-2.4c against -3.5c for taking the ask), yet the orders that FILLED lost -4.3c while the 9% that never filled would have made +17.9c. A bid fills when the price falls through it and is left behind when the price rises, so fills concentrate on the losers (adverse selection). `kalshi-scalper/README.md`, "Hypothesis ... maker entry".
3. **Kalshi's maker fee is not written down in this repo.** The series data says `fee_type: quadratic, fee_multiplier: 1` and the docs I could reach did not state a maker rate, so no maker saving is assumed anywhere. The owner's own fills show the fee actually charged on a resting order; that one number would settle it.
4. **A person chooses the moment.** A scalper skips the minutes that look wrong. The bot has no such filter (we tried several, all failed on history), which is part of why the spread-over-3c rule is being forward tested (FWD2).

## What would actually change the answer
- Take the orders that are already resting-and-filled by hand, read the fee column and the win rate, and compare with the bot's 93.4% on the same price band. If manual orders beat the bot after fees on 100+ trades, the thing to copy is whatever the person is skipping or waiting for, not the fee.
- Maker entries for the bot are the right next experiment only on recorded 10 second books (P2 in the research README), and its own pre-registered expectation is `FALSIFIED`.
