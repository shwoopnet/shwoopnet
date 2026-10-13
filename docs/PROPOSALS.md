# Proposals for money you oversee while L1 runs

Written 2026-10-12 in plain words. This is general information from our own testing and public research, not personal financial advice. Nothing here starts by itself: each item says what you would do, what it should realistically earn, the worst case, what you watch, and when you stop.

## What the evidence says, in four lines

- We tested about 4,600 ideas on Kalshi's 15 minute markets, 17 stock ideas, about 6,000 dividend variants, about 8,000 option structures and about 15,000 fund and trend variants. Every one that looked good on the data it was chosen on failed on days it had not seen, and fair-market luck produces the same winners.
- Retail option traders lose on average, mostly to spreads and fees. The structures with real evidence need about $78,000 for one contract.
- Dividend funds do not beat the market. A dividend tilt is a value tilt that paid in some decades and not in others.
- The one honest result in our own data is L1. On the 40 days it was tuned on it earned +0.4c a contract after fees (not proven, z about 1.5). On the 28 days before that, which it was never fitted to, it earned +1.3c (z +3.2), and over all 68 days +0.8c (z +2.5), with gold the strongest (+1.5c) and Bitcoin the weakest (+0.45c). That is the first out-of-sample check it has passed, still thin, and the most recent weeks were not the best. A forward read of new days is registered for 2026-11-16.

## The proposals, best supported first

### 1. Core savings: automatic monthly investing in a broad fund, inside a retirement account

- **What:** a fixed monthly amount into a broad index fund or a target-date fund. Take any employer 401(k) match first (that is an instant return), then an IRA. A robo-advisor does the same job fully hands-off for about 0.25% a year; check current pricing.
- **Why:** the only thing here with decades of evidence. Long-run US stocks with dividends reinvested have averaged about 10.5% a year (7.3% after inflation) since 1926, with drops of 50% or more along the way.
- **Size:** most of the $500 to $2,000 a month.
- **Worst case:** a 50% drop, which has happened (2008). It recovered, and it needs years of patience.
- **You watch:** nothing monthly. Check once a year.
- **Overlap with L1:** none. It is a different account.

### 2. Idle cash: keep only a working balance on Kalshi

- **What:** Kalshi pays interest on balances of $250 or more at a variable 3.5% (confirm in the app, it can change). Three month Treasury bills pay about 4.2% and top savings accounts about the same. Keep on Kalshi only what L1 needs.
- **Why:** it is a small, certain gain. The difference is about 0.7 points a year.
- **Size:** whatever L1 needs. Move the rest.
- **Worst case:** none beyond keeping cash somewhere slightly worse.
- **You watch:** the balance when L1 gets its weekly size review.

### 3. A drawdown rule on part of the core fund (optional, inside an IRA)

- **What:** hold a broad index fund while its price is above its 200 day average, and T-bills when it is below. It trades a few times a year, so it belongs in a tax-advantaged account.
- **Why:** in our test of 1927 to 1995 it cut the worst drop from -84% to -56% for a small cost in return. Over 1997 to 2026 the best versions did not beat plain SPY after the search was corrected for luck. So this is drawdown control, not extra return.
- **Size:** a slice of the core fund, not all of it.
- **Worst case:** you get whipsawed in a choppy year and lag the market.
- **You watch:** a monthly glance. We would paper-track it before using money.
- **Overlap with L1:** none.

### 4. L1 itself, kept small and watched

- **What:** the live bot stays as it is: 88c to 97c favorites about 6 minutes before each close, hold to the result, 25c exit, a 5% daily loss stop.
- **Why:** the only live strategy with a measured positive edge, and it held on 28 days it was not tuned on (see above). Still an experiment with a thin edge, not a plan.
- **Size:** money you can afford to lose entirely.
- **Worst case:** the whole stake, and a long period with no gain.
- **You watch:** the Kalshi page and the weekly size review. Stop it if it falls below the forward test's kill line, or if you stop being comfortable.

### 5. A small patient-order experiment on long-dated Kalshi favorites (paper first)

- **What:** place resting bids on tight, deep, long-dated contracts priced 90c to 97c and wait to be filled.
- **Why:** research finds a small bias in favor of favorites at short horizons. Our own look at weeks and months found margins between -1c and +2c, which is zero within noise.
- **Size:** none until a paper record exists. Typical size at the top of the book is only about $180.
- **Worst case:** one loss costs about 16 wins, and the headline 12% a year assumes the 6% never fails.
- **You watch:** a pre-registered paper record. Do not fund it unless it beats Treasury bills by a clear margin.
- **Overlap with L1:** none if it only touches long-dated markets, never the 15 minute ones.

### 6. Add XRP and Dogecoin to the END of L1's list (decision for after the 2026-11-16 forward read)

- **What:** two more series under the same rule, size, 25c exit and loss stop. In code this is the hard list `L1_SERIES` in `functions/kalshiLiveLib.js` plus its tests, and a deploy of the armed function; nothing else changes. They go LAST, so they only take the second slot of a window when Bitcoin, gold and Ethereum left room.
- **Why:** the same rule earned +1.4c and +1.5c a contract on XRP and Dogecoin over 41 days and +1.8c on 29 older days nobody had looked at (z +4.0 pooled). On the 68 days of candles, appending them roughly doubles the expected net per day (from +0.65 to +1.30 contracts' worth a day, one contract each) with the same worst window, because the 4.5% window limit is unchanged. See the ORDER1 note in `kalshi-scalper/README.md`.
- **Size:** unchanged per entry. More entries a day.
- **Worst case:** they lose together with Bitcoin about 40% of the time (windows where both entries lose went from 28 to 52 in the sample), and their books are thinner (median spread 0.4c to 0.7c, about 1,200 contracts in the entry minute) so fills may be worse than the candles say. If the edge is really +0.5c rather than +1.5c it is still positive; if it is zero it adds trades and fees for nothing.
- **You watch:** whether the forward read (new days, one look on or after 2026-11-16) is still positive before turning it on, and the weekly review afterwards.
- **Overlap with L1:** it IS L1, on two more markets. Not independent diversification.
- **Not done yet.** This is a proposal only. The bot has not been changed and nothing has been deployed.

## What we are not proposing

- **Buying cheap options.** They lose on average and are the opposite of what you asked for when you wanted an anti-degen site.
- **A dividend bot.** Nothing beat plain SPY after costs and a fair test.
- **Selling options for income** at your capital. The version with real evidence needs about $78,000, and your own paper record did poorly.
- **Leverage, VIX products or 0DTE.** Leveraged funds did not improve results after financing, short-volatility funds lost over 90% in a day in 2018, and retail 0DTE traders lost over $70 million in two years.
- **More Kalshi 15 minute variants.** About 4,620 are tried. More search only raises the bar for luck. What is different now is testing the SAME rule on other series and on older days, which does not raise that bar.

## Decisions for you

1. Do you have an employer match or an IRA you are not filling? That is the biggest single step.
2. Do you want a read-only "slow money" page on the site in the current style (contributions and a spread of outcomes, no buy buttons)?
3. Should I paper-track proposal 3 or 5 so there is a real record before any money goes in?
