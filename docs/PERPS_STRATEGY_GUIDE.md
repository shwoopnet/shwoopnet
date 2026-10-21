# How to build a perps strategy: a plain-words guide

Written 2026-10-21 for the owner, who likes leverage ("bigger gains on small moves", "using less of my money") and has not built a strategy before. **Nothing here is built, tested or traded.** Fees and rules are from news and CFTC-filing summaries and Kalshi's help-center titles, not Kalshi's own fee page; confirm them before any money moves.

## 1. What a strategy is: six decisions, written down before you trade

| # | Decision | Example |
|---|---|---|
| 1 | **Market** | Gold perp (about $50M traded a day, spread about half a basis point) |
| 2 | **Signal** | The price closes above its highest close of the last 20 days |
| 3 | **Entry** | A limit order the next day, at the price you wrote down, never chased |
| 4 | **Exit** | A stop 1.5 daily ranges below entry, and out when the price closes below its 10-day low |
| 5 | **Size** | Risk 2% of the perps balance on this trade (see section 2) |
| 6 | **Who loses money to you, and why** | Slow holders and stop-hunters who sell late into a long move |

If you cannot fill in row 6, it is probably noise. Every rule above is written into code and a README before the first test, so a bad run cannot be argued into looking fine (this is how every test in this project works).

## 2. How size and leverage really work

- **Notional** is the full value of what you hold. **Margin** is the money you put up. **Leverage** is notional divided by margin. Nothing about leverage adds an edge; it only changes how much of your money a wrong trade uses.
- **The risk number is size times the distance to your stop.** You choose the risk first, then the stop decides the position, and leverage falls out of that.

Worked example, a $40 perps balance, risking 2% ($0.80) on a trade:

| Stop distance | Position (notional) | Leverage | Fees for one round trip (about 0.24%) |
|---|---|---|---|
| 2% | $40 | 1x | about $0.10 |
| 1% | $80 | 2x | about $0.19 |
| 0.5% | $160 | 4x | about $0.38 |

- **Fees are a big part of the risk at this size:** at 2x, the fee ($0.19) is about a quarter of the $0.80 you are risking. That is why slow ideas with wider stops beat fast ones.
- **Cap leverage at 3x.** If a tight stop asks for more, take a smaller position instead (risk less than 2%).
- **Liquidation** is the exchange closing you out when your margin runs low. Your stop must trigger long before that. Kalshi's exact liquidation rules are in its help article "Understanding Liquidation"; read it before any money moves.
- **At $40 the profits are small** (a good trade makes a dollar or two). That is the point: this size is for finding out whether an idea works, not for income.

## 3. Three starter ideas, ranked by how testable they are

All three can be tested on years of free daily prices (gold, Bitcoin, Ethereum, the S&P) before any money, with Kalshi's fees included. My odds that each passes a strict test are honest guesses.

### A. Daily trend breakout (best first test)
- **Idea:** buy when the price closes above its 20-day high; sell short when it closes below its 20-day low; exit on the opposite 10-day extreme or the stop.
- **Who loses:** slow, late holders and people trading against a persistent move.
- **Trades:** about 8 to 15 a year per market, held days to weeks.
- **Why it suits you:** few trades, so fees are a small share of each move; a trend of 5% to 10% on 2x leverage is a 10% to 20% gain on the margin.
- **What kills it:** choppy markets (many small stop-outs). Our own record on trend strategies says expect this to be thin.
- **My odds:** about 10 to 15%.

### B. Buy the dip in an uptrend
- **Idea:** only when the price is above its 100-day average, buy after three down days in a row; exit when the price makes a 5-day high or the stop hits.
- **Who loses:** panic sellers after a short drop.
- **Trades:** more often (20 to 40 a year per market), shorter holds, so fees matter more.
- **What kills it:** a trend that breaks, turning a dip into a big loss.
- **My odds:** about 8%.

### C. Gold against silver (pairs)
- **Idea:** when the gold-to-silver price ratio is unusually high against its 60-day range, short gold and long silver in equal dollars, exit when it returns to normal.
- **Who loses:** anyone forced to rebalance between the two metals.
- **Trades:** a few a year, two legs each time, so double fees.
- **What kills it:** the ratio drifting for months.
- **My odds:** about 5%.

## 4. How we find out (the test, in order)

1. Write the rule, the costs and the pass bar in `kalshi-scalper/README.md` before touching any data. Costs: about 0.24% a round trip as a taker plus a funding charge I assume against you (funding rates are unmeasured; the recorder would measure them).
2. Run it **once** on 5+ years of daily prices for each market. The verdict words are `FALSIFIED`, `NOT_YET_FALSIFIED` and `NOT_ENOUGH_DATA`; none means "trade".
3. Pass bar: at least 100 trades across the markets, a positive result in both halves of the years, still positive with fees 20% higher, and a day-clustered z score of at least 2.1 (stricter with each extra try).
4. If it passes, it earns a live probe on a small separate balance, not a bigger one. If it fails, we move on the same day.

## 5. A rulebook for any live perps balance (written now, so a bad hour cannot change it)

- A small separate margin balance you choose and can lose (my suggestion: $40 to $50), never topped up from the prediction balance by a button on the page.
- Leverage never above 3x. Every position gets its stop placed with the entry. One position per market.
- Risk at most 2% of the perps balance per trade. A weekly loss stop of 15% of the perps balance ends trading until you restart it.
- Never add to a losing position. Never move a stop further away.
- No page control changes any of these (same reason as the exit watch: a setting you can change can be changed in a bad hour).
- Its own record on the page, never mixed with the prediction bot's.

## 6. Words you will see

- **Perp (perpetual future):** a contract that tracks a price with no expiry.
- **Funding:** a payment between longs and shorts, every few hours or once a day, that keeps the perp near the real price. You pay or receive it while holding.
- **Maker / taker:** a maker rests an order and waits; a taker crosses the spread and pays more.
- **Mark price:** the price the exchange uses to decide if you are liquidated.
- **Stop / TP-SL:** an order that closes your position at a price you set (Kalshi lists "Take Profit and Stop Loss" in its help center).

## 7. Mistakes to avoid

- Picking the leverage first and the stop second (it should be the other way round).
- Trading many times a day at 0.24% a round trip.
- Adding to a loser, or moving a stop because "it will come back".
- Judging an idea on ten trades.
- Believing a backtest that has not been run once, honestly, with costs.
