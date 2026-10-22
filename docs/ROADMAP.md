# Roadmap

Last updated: 2026-10-21, afternoon. Written in plain words on purpose.

## The goal

Make money on Kalshi without having to watch it. One bot trades for you. The plan is to keep that bot safe and cheap to run, and to test, with real small money, whether other markets can earn on their own.

## Where we are today

- **One bot is live (L1), on eight markets.** It buys the side that is almost certain to win (priced 88c to 97c) and waits for the result. Gold keeps the size ladder (6 contracts now). Bitcoin, Ethereum, XRP and Dogecoin are capped at one contract. AUD/USD, USD/CAD and natural gas are one-contract probes. **Since about 2:15 PM CT on 2026-10-21, Bitcoin, XRP and natural gas enter about 10 minutes before the close instead of 6** (a live test); the first one, XRP, won +$0.12.
- **The live record so far (bot only, 2026-10-21):** 365 settled trades, about 93% won, net **-$4.55**. Gold is +$28.81 on 110 trades; every other market is slightly negative (Bitcoin -$23.34, Ethereum -$1.99, XRP -$6.50, Dogecoin -$1.07, natural gas -$0.47). A win earns about $0.40 and a loss costs about $6, so the bot needs 94 wins in 100 to break even and sits at about 93.
- **Safety:** one combined limit per 15 minute window (5.5% of the base), a stop at **12%** of the base, a sell at 25c (a study this week found the line barely matters on Bitcoin, XRP and natural gas, so it stays), a one-click pause and flatten, phone alerts, and a rule that drops a probe market whose last 200 trades net negative.
- **The website** has four pages: Market Brief, Bot, Data (read only) and Settings. This week: Privacy toggle, a Today line, readable light themes, plain headings and numbers with the bubble font only on the logo, and a layout fix so the trades list no longer squeezes into four-line rows.
- **We have tried about 4,640 ideas on the same data. None passed the bar for a deployable edge.** This week's tries (decision trees, volatility-managed ETFs, risk parity, factor ETFs, hedges, scale-outs) were all falsified. Capital, not ideas, is the limit: slow strategies tested so far are worth about $5 to $9 a year at $200.

## What you need to do now

1. Merge [#454](https://github.com/shwoopnet/shwoopnet/pull/454) (order exports carry the entry tag) so the research reads can split 10-minute from 6-minute orders. It only changes the exports.
2. Merge the tidy and fixes pull request when you are ready (it has this refresh in it).
3. Send a Recent trades screenshot now and then, or use **Tools, Copy all orders**, so the first reads of the 10-minute entry can be checked.
4. Nothing about Render: it is free and left running (decided 2026-10-22).

## What I am doing next

| Job | In plain words | Done when |
|---|---|---|
| Render (decided 2026-10-22) | The equities server is on Render's free plan, so it costs nothing, and it feeds the Brief's movers and earnings. The owner chose to leave it running as is | Revisit only if it starts trading unexpectedly or the free plan changes |
| Read the 10 minute entry | Bitcoin, XRP and natural gas now enter earlier. Orders are tagged `10m`. Few markets are in the band at 10 minutes, so this fills slowly | FWD8 reads at 60 filled orders per series or 2026-12-01 |
| Read the probes | AUD/USD, USD/CAD and gas, one contract each, plus the drop rule | FWD5 reads at 100 orders per group or 2026-12-01 |
| Gold first, forward scoreboard | Gold earns; the others have to earn the ladder back from their own live record (150 settled trades, a result above +0.5c in both halves) | Rules already written, reads as the trades arrive |
| Maker (resting) orders | Fees are about half the edge. Test resting orders live at one contract, as their own pull request with a cancel path | Only after real fills come in on the probes |
| US500 perpetuals (parked) | Different product, high leverage, not a fit for an anti-degen site | Only if you ask. A research recorder already logs Kalshi's perps hourly to a data branch |

## Proposals for money you oversee

See `docs/PROPOSALS.md`. In short: core savings in a retirement account first, keep only a working balance on Kalshi, keep L1 small and watched, and test anything else with a small live probe before it gets more.

## How a new idea gets in

1. I write down the rule and what would make it fail, before testing.
2. I test it once on past data. If it clearly fails, it stops there.
3. If it passes or cannot be settled on history, it can go live as a **one-contract probe** (your decision on 2026-10-21: live forward testing, no more paper). It sits last in line, inside the same window limit and loss stop.
4. It earns more size only from its own live record, not from a backtest.

## Dates to remember

- **From 2026-10-22:** the forward reads FWD5 and FWD6 start counting; FWD7 and FWD8 count from the 10 minute go-live (2026-10-21, about 19:15 UTC).
- **2026-11-16 and 2026-11-17:** the registered forward reads (E3F, FWD1, VOL1, PM3, OW7, then FWD2, FWD3 and GOLD1-F). One run each; nothing changes unless it passes.
- **2026-12-01:** the default read date for FWD5, FWD6, FWD7 and FWD8, and a second snapshot of the research data (Kalshi's history only reaches back about 69 days).
- **About 3 to 4 weeks:** a rerun of the funding study on the perps data the recorder is collecting.
- **The first weekly size review after a stop:** a loss stop holds size increases for 7 days.

## Can wait

- Resting orders on the probes (after real fills).
- A recorder for the economics markets (CPI, payrolls): parked, the history is too short and the owner said not now.
- State-by-state gas ladders and the daily index markets (about one a day, so 300 days to test).
- Auto-restart after the loss stop.

## Done recently

- 2026-10-21 (afternoon): the 10 minute entry for Bitcoin, XRP and natural gas went live; the probe drop rule and a cost cut (about $2 a month, and roughly $3 a month of that is given back by the exit watch running through the early minutes) went live; light themes made readable; numbers and headings in the plain font, the bubble font kept for the logo and a hop on hover; Today line; order exports with the entry tag (open); a perps recorder; the hand-sold fix and repair; gold-first sizing; the Data page.
- 2026-10-21 (morning): three live probe markets; the stop set to 12%; paper card removed; Copy all orders; new logo, icon and share card; footer disclosure.
- 2026-10-20: phone alerts, sound alerts, XRP and Dogecoin added, window limit 5.5%, shared Flatten and exit claim, cash-out at 99c tested and ruled out (TP1).
- Earlier: only L1; opening strategy removed; exit moved from 70c to 50c to 25c; the site slimmed to three pages.
