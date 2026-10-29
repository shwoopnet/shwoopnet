# Data page: 40 ideas for self-improvement (Oct 23, 2026)

Written for the owner. Nothing here is built. Every idea keeps the Data page's two rules: **read only** (no control of any kind, `test/dataCenterGates.test.js`) and **no figure without its sample size**. Each one says what question it answers and what it reads. "Needs logging" means the bot would have to record one more field first (a logging-only change, like `rise3` and `rng5`).

What we already record on every order, so most ideas need nothing new: time, market, side, price, contracts, fees (`averageFeePaid`), settled result, the early-sell price, `entryLead` (10 or 6 minute look), `rise3`, `rng5`, `flips`, `flips0`, `earlierCandles`, `askAtDecision`, `minStep`, `climb`, `smooth`, and the book sizes. Plus the session events (started, ended, skipped minutes) and the order book snapshots.

## A. Is the strategy working? (the verdicts, in plain words)

1. **Kill-rule scoreboard.** One row per pre-registered rule (smooth-only: 3 of the first 40 smooth fills lose, combined net under $0 after 100 fills; 10 minute look; one crypto order per window; probe drop at 200 entries), with progress ("17 of 40 fills, 1 loss") and the date each is read. Answers: "has anything crossed its line?" Reads: orders. Replaces the hand-run exports.
2. **Edge confidence band.** Win rate with its plausible range (for example 94% from 91 to 96) next to the break-even rate, so a lucky week is not read as proof. Reads: settled orders.
3. **Break-even distance.** "Wins needed to break even: 93.2%. You are at 94.1%, 0.9 points of room." One line, big. Reads: avg win and avg loss.
4. **Expectancy per contract by month.** Cents per contract by calendar month, so a decaying edge shows as a slope. Reads: settled orders.
5. **Profit factor with a floor.** Profit factor for each of the last 4 windows of 50 trades, drawn as four small bars against 1.00. The window series was the finding in the equities and crypto research; this keeps watching for it live.
6. **Live vs backtest gap.** For each market, the live per-contract result beside the research figure it was promoted on (typed in code with its date and "re-derive, do not quote" label). Answers: "is live worse than what justified it?" Needs the figures stored in code once.
7. **Edge decay alarm.** The last 100 trades per market against the 100 before, as one line each ("XRP: +1.9c, was +3.1c"). Read only; says nothing about what to do.
8. **Sample size ladder.** Every market row shows how far it is from the 30 and 150 trade lines (the repo's own bars), so "too few" has a number.

## B. Where does the money go? (loss anatomy)

9. **Loss autopsy table.** The 10 worst trades, each with market, entry price, look time, `rise3`, `rng5`, `flips`, whether smooth, and what the exit watch did. The self-improvement tool: patterns in the worst trades are the only place new rules come from. Reads: orders.
10. **Loss clusters.** Windows where two or more orders lost together (the 72% finding), listed with a count per week. Confirms the one-crypto-order rule is working or not.
11. **Exit watch ledger.** Every 25c exit: what it sold at, what holding to settlement would have paid (the resolved result), and the running total of "sells versus holding". Already computed for Copy all stats; this makes it a card.
12. **Fee drag.** Fees as a share of gross profit, by market. Shows where cost, the binding constraint, is eating the edge.
13. **Price paid vs result heat strip.** For 88c to 97c, a row of cells (one per cent) coloured only by count, labelled with win rate. Shows whether the band edges hold. Replaces the hidden "By price paid" fold.
14. **Tail risk line.** "A loss costs about 14 wins" (average loss over average win), updated live. Makes the structure of this strategy impossible to forget.
15. **Biggest single-window exposure.** The largest combined money in one window this week, against the 5.5% limit. Proves the limit is binding or slack.

## C. When does it work? (conditions)

16. **Hour-of-day grid.** Result per hour on the US Central clock, as a 24 cell strip with trade counts. Reads: orders. Answers whether some hours are drag.
17. **Day-of-week strip.** Same, 7 cells.
18. **Weekend vs weekday.** Two numbers. Crypto and forex behave differently on weekends.
19. **Session heat calendar.** A month grid, one square per day, grey scale by result (no red or green), click-free, hover for the figure. Fits the calm rule.
20. **Volatility regime split.** Results split by the day's market mood word from the Brief (Calm, Normal, Elevated, High). Reads the tape's stored mood at order time (needs logging: one field, the mood word).
21. **Time-to-close effect.** Win rate by minutes left at entry (the look times actually achieved, since a late tick buys later). Reads `entryLead` and order time against close time.
22. **Gold session effect.** Gold only: result by hour, because the metal's liquidity changes with the New York and London clocks.

## D. Are the new tests paying? (the live experiments)

23. **Smooth-climb report.** Smooth fills versus the unfiltered Bitcoin and Ethereum orders from before the change, side by side: count, win rate, per contract, plus how many windows the gate skipped ("no order placed, path not smooth") and what those would have done at the settled result. The only way to see what the filter costs in missed wins.
24. **Skipped-signal ledger.** Every window the bot saw a candidate and did not buy (gate, loss stop, window limit, thin fill) with the market's eventual result. Needs logging: skip reasons are in the session note but not kept per ticker.
25. **10 minute vs 6 minute, matched.** Paired on the same market and day where both exist, instead of the two groups that are not the same markets. Fixes the known weakness of the Entry timing card.
26. **Logged-field correlation table.** For every field we log (`rise3`, `rng5`, `flips0`, `climb`, `minStep`, `askAtDecision`), the win rate and per contract in the top and bottom third. A research notebook on the page: shows which logged lead is worth a rule. Honest about multiple comparisons: printed with "N fields tried" so the deflation floor is visible.
27. **Probe watchlist.** AUD/USD, USD/CAD and natural gas: entries so far, running net, and the distance to the 200 entry drop rule, one line each.
28. **Window-limit effect.** How many orders were cut to fewer contracts or refused by the 5.5% limit, and what that cost or saved.

## E. Account and size

29. **Balance curve.** The account total over time (needs the balance logged hourly into a small collection), with deposits and withdrawals marked so the line is the bot, not you. Needs logging.
30. **Size ladder history.** Gold's contract count over time against the balance, with each review date. Shows the ladder doing what the rules say.
31. **Reinvest pool timeline.** Pool value after each win and each use.
32. **Drawdown curve.** Depth and length of every drawdown, with the current one highlighted ("down 2.1% for 9 hours").
33. **Stop distance.** The 12% stop as a percentage and how far the last 24 hours is from it, as a thin bar. (The Bot page's risk card is the live version; this keeps the history of closest calls.)
34. **Shard balance history.** Money on each shard over time and the days a market went unfunded. Would have caught the forex starvation in days, not weeks. Needs logging with the shard split.

## F. Health of the machine

35. **Uptime ribbon.** One day as 1,440 thin cells: looked, skipped, stopped. Reads session events and the heartbeat log. Shows gaps at a glance.
36. **Skip reasons chart.** Why minutes were skipped this week (time, busy 429, no candidate, stop), counted.
37. **Fill quality.** Average fill versus the price at decision (`askAtDecision`), per market: slippage in cents. Reads orders.
38. **Order latency.** Time from the look to the fill, if logged. Needs logging.
39. **Alert log.** A plain list of every alert sent (buy, sell, stop, issue) with its time, so a missed push is findable.

## G. Habits and honesty (the anti-degen set)

40. **"What would doing nothing have done?"** The bot's net against holding the starting balance in cash for the same period, in one line. Keeps the comparison honest.
41. **Intervention log.** Every time the owner pressed Stop, Start, Flatten or raised the size, with the result of the following 24 hours. A read-only mirror of the control events, so changes made in a bad hour are visible later. Reads: `kalshiLiveEvents`.
42. **Rule change journal.** A dated list of every rule change merged (series order, smooth gate, 12% stop), each with a "check again on" date. Lives in code as data, shown here, so a number is never compared across a rule change without a line saying so.
43. **Weekly review card.** The health check's verdict (working, watch, not working) with the thresholds written beside it, generated from the same figures, every Monday. Replaces a manual run.
44. **Monthly statement preview.** The printable statement as a live page, so the month is readable before it is printed.

## Recommended first five

Ranked by value for the effort, and each needs no new logging:

1. **Kill-rule scoreboard (1).** It turns the pre-registered rules into something you read in ten seconds.
2. **Loss autopsy table (9).** The only source of new, real rules.
3. **Smooth-climb report (23).** Proves or kills the newest change on the live record, with missed wins counted.
4. **Intervention log (41).** The most useful guard against a bad-hour decision.
5. **Exit watch ledger (11).** Settles whether the 25c exit earns its keep.

## What to avoid

- Any colour that says good or bad outside Today, the end label, losing bars and the lost slice (the calm rule).
- Any control on the page (the Data page is read only).
- A number without its sample size. Most of these ideas are about a few dozen trades; the page should say so.
- Slicing by many conditions: with 44 cuts available, something will look significant by chance. Idea 26 shows how many cuts were tried so the deflation floor stays visible.
