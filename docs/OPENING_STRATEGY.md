> **Retired 2026-10-12.** The paper recorder and the page's Opening view were removed so that L1 is the only strategy. This file is kept as the record of what was tried and why. See "L1 is the only strategy" in CLAUDE.md.

# Opening window test (OW1): synopsis, theory, and what it says about bigger wins

Written 2026-10-12 at the owner's request. Refresh when OW1 is read (2026-11-03). **Paper only: nothing in this feature places an order.** The rules, predictions and kill criteria are fixed in `kalshi-scalper/README.md` ("Pre-registration: OW1"); this file is the readable version.

## In one paragraph

OW1 looks at each 15 minute Bitcoin, gold and Ethereum market about five minutes after it opens (10 minutes before the close) and records, on paper, what two simple rules would have bought. **Lane F** is the early favourite: the side priced 82c to 87c. **Lane U** is the early underdog, the flips: the side priced 20c to 30c. Both buy at the ask, hold to settlement, are sized the way L1 would be sized today, and sit under L1's per-trade limits. Each has its own profit and loss on the Kalshi page. **My prediction, written down before any record existed: U loses about 4c a contract, F is indistinguishable from zero, and neither gets near the bar for real money.** It is worth building because you asked for a strategy for the opening window and for the flip instinct, and a paper scoreboard answers both without touching the account. On 2026-11-03 it also tests the history on days nobody has looked at.

## What the history says (29 days, 4,560 settled markets, Bitcoin and gold)

Buy the side priced in the bucket with 10 minutes left, at the ask, hold to settlement, after the 7% fee. The **margin** is win rate minus the price paid: in a fair market it is zero.

| Price paid | Entries | Win rate | Paid | Margin | Net a contract | z | Average win | Average loss |
|---|---|---|---|---|---|---|---|---|
| 5c to 10c | 226 | 5.3% | 7.7% | -2.4 | -2.94c | -2.2 | +91.5c | -8.2c |
| 10c to 15c | 307 | 9.1% | 12.5% | -3.4 | -4.18c | -3.1 | +86.4c | -13.3c |
| **20c to 25c** | 532 | 19.5% | 22.0% | -2.5 | -3.66c | -2.2 | +76.9c | -23.2c |
| **25c to 30c** | 531 | 23.4% | 27.1% | -3.7 | -5.09c | -3.4 | +71.5c | -28.4c |
| 30c to 35c | 586 | 30.5% | 32.0% | -1.5 | -3.02c | -1.6 | +66.4c | -33.6c |
| 70c to 78c | 881 | 75.6% | 73.5% | +2.1 | +0.77c | +0.8 | +25.1c | -74.4c |
| **82c to 87c** | 459 | 85.0% | 84.1% | +0.9 | -0.06c | -0.0 | +15.0c | -84.9c |
| 87c to 92c | 400 | 91.5% | 89.1% | +2.4 | +1.71c | +1.7 | +10.2c | -89.2c |
| 92c to 97c | 173 | 94.8% | 93.9% | +0.9 | +0.45c | +0.3 | +5.7c | -94.3c |

Buckets are half open at the top (82c to 86.99c), so lane F, which includes an ask of exactly 87c, has 549 entries rather than 459.

For comparison, L1 itself (88c to 97c, 6 minutes left) on the same 29 days: 1,377 entries, 93.7% wins at a mean price of 92.7c, **+0.50c a contract, z +0.85**. Its longer record is +0.87c, z 2.42, on the days it was found on, and it has never passed its own forward bar.

What to take from it:

- **The price is the win rate.** Every margin is within about three points of zero. A contract priced at 25c won 23.4% of the time.
- **The cheap end is negative everywhere.** All 15 cells for 5c to 30c (five buckets, three decision times) lose money after fees, and the two flip buckets are the worst of them (z -2.2 and -3.4). This agrees with every earlier cheap-side test in the README (C1 to C3, T4, T5).
- **A bigger win costs exactly a smaller win rate.** Move down the table and the average win grows (+5.7c, +10.2c, +15.0c, +25.1c) while the win rate falls by about the same number of points. The profit stays near zero at every step. That is what a calibrated market looks like.

## The theory, and why it is a weak one

**Lane F.** The only reason to expect a payoff is the favourite-longshot bias: people overpay for the unlikely side, so the likely side is slightly underpriced. L1 is that bias at 88c to 97c with 6 minutes left. F asks whether it also holds a little lower and earlier, where a win is about three times bigger. The earlier reads say it is a noisy zero: H1 (a favourite at 10 minutes left) +1.13c with z 1.34, B4 (84c to 88c at 6 minutes) -0.05c, and on this history F is -0.05c with z -0.03. Nobody has to be wrong for F to be fair, so I expect it to fail the bar.

**Lane U.** There is no counterparty here, and the history says you are it. L1 earns its small edge from the people who buy flips, because the flip buyer is on the other side of the favourite it buys. When you buy a 25c flip by hand you take the trade L1 collects from. The lane exists so you can watch that instinct get scored without paying for the scoreboard.

**What a flip costs, in dollars.** At 25c the measured cost is -3.9c a contract, about 15% of the stake (plausible range 8% to 23%, two standard errors). A $25 flip costs about $3.90 on average; $10 costs $1.56; $50 costs $7.80. It wins about once in 4.5 tries (22.5%), which is the feeling you like and the reason it is expensive. L1's expected profit at current size is roughly $1 to $2 a day (+0.5c to +0.9c a contract on 7 to 10 contracts and about 25 fills a day), so one $25 flip a day is expected to cost two to four times what L1 earns in a day.

## Where the average win can and cannot come from

Your numbers: 101 settled, 96 wins and 5 losses, average win +$0.37, average loss -$8.13, profit factor 0.87, net -$5.13.

- **The break-even win rate is 95.6%** (8.13 / (8.13 + 0.37)). You are at 95.05%. That gap is one loss. It sits 0.3 standard deviations below break-even and 0.7 below what L1's measured edge predicts, so a profit factor of 0.87 over 101 trades is well inside the noise for a strategy that should be near 1.0 to 1.1.
- **Bitcoin 4 losses in 60, Ethereum 1 in 4, gold 0 in 37.** Gold's 37 of 37 is what a 95% win rate does 15% of the time. It is not evidence that gold is safer.
- **Average win per trade is the price premium times the contract count.** At about 7.7 contracts and 5c a contract it is $0.37. There are only two ways to raise it: a lower entry price, which lowers the win rate by about the same amount (the table above), or more contracts, which raises the average loss in step. At $1.00 an average win you would need about 20 contracts, an average loss of about $22, and a single loss would be about 4.4% of $500 against a 5% stop. The size ladder and the stop are built to forbid exactly that.
- **What would be free** is a better probability estimate than the market's. That is what the strategy search in this README looked for (2,591 variants tried, none passed), and none found it.

So I do not have a way to get "a lot larger wins at a similar win rate", and I would distrust any rule that claims to. The honest options, in the order I would take them:

1. **Leave L1's entry alone.** Its edge is the premium at 88c to 97c; changing the band changes the win rate with it.
2. **Let lane F run.** It is the closest thing to what you asked for: wins about three times larger at a win rate about ten points lower. The prediction is that it earns nothing, and 2026-11-03 tells us.
3. **Use lane U as the flip outlet.** It scores the instinct on paper at the size L1 would trade.
4. **Not recommended:** lowering L1's floor live, buying flips live, or raising size after a winning streak. Each is a larger version of a trade the history already prices at zero or below.

## What the page shows

A **Closing / Opening / Both** switch near the top of the Kalshi page applies to the whole page. Closing is L1, the live bot, and is exactly what the page showed before. Opening shows OW1's paper results: totals, a table by lane, open paper positions, settled paper trades and the bar charts, each tagged "paper F" or "paper U". Both shows the two one after the other under headings and **never adds them together**: the live net in Both is the same number Closing shows. The choice is remembered in your browser, and it filters the display only; it changes nothing that trades.

## Limits, and what is deliberately not built

- **Same per-trade limits as L1:** at most $2.00 a contract and size from the same stake rule and weekly cap. The two limits that tie several orders together (the 200 orders in 24 hours, 4.5% of the account per 15 minute window) are worked out and recorded on every paper record, not enforced, so the research sample is not cut by the clock.
- **No live path.** The recorder has no signing, no key, no portfolio call and no way to send an order, and a test pins each. Going live would be a separate reviewed change under its own written waiver, with every gate L1 has and a code gate of its own that is not `CODE_KILL_SWITCH`, so restarting L1 can never start OW1.
- **No switch, no setting.** There is nothing on the page that turns OW1 on or changes its bands. A knob you can move in a bad hour is the thing you asked me not to build.
- **Ethereum is recorded** (the bot trades it) but is outside the research readout, which uses Bitcoin and gold only.

## When we will know

- The recorder starts when the functions are deployed. The research readout counts markets that close after 2026-10-12 16:00 UTC.
- **First read 2026-11-03, once.** Expect about 850 entries in U and about 400 in F. Before that date the research code prints numbers and no verdict.
- A lane that is short of data gets one final read on 2026-11-16.
- Bar for each lane: at least 300 entries on 5 days, a day-clustered z of at least 2.1, positive in both halves, and still positive with fees 20% higher. Any miss is `FALSIFIED`. Passing would be `NOT_YET_FALSIFIED`, which means keep testing forward and nothing more.

## Questions for you

1. **Keep lane U on the page after it is falsified?** My answer is yes: it is the flip outlet and it costs nothing. Say if you want it gone.
2. **Do you want an opening-window idea that is not on this list tested?** The README's list of opening-window ideas (O1 to O50) tagged 22 as new and a few have since been run, so check it first. Most are resting entries that avoid the taker fee. Cost is the binding constraint, so those are the only ones I would spend a try on.
