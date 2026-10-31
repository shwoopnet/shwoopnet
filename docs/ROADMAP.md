# Roadmap

Last updated: 2026-10-25. The live record line below is still the 2026-10-22 reading; it was not re-read this week. Written in plain words on purpose.

## The goal

Make money on Kalshi without having to watch it. One bot trades for you. The plan is to keep that bot safe and cheap to run, and to test, with real small money, whether other markets can earn on their own.

## Where we are today

- **One bot is live (L1), on two markets (as of 2026-10-31).** It buys the side that is almost certain to win (priced 88c to 97c) and waits for the result. Gold and Dogecoin follow the same size ladder and the same risk rules and trade around the clock. XRP, Bitcoin, Ethereum and the probe markets (AUD/USD, USD/CAD, natural gas) are paused in code. A second strategy, OICORE (Bitcoin only, 10 contracts, held to settlement), runs as a capped probe with a forward read on 2026-11-13. The notes below are dated history; `CLAUDE.md` has the current rules.
- **The live record so far (bot only, 2026-10-22 about 11 AM CT):** 414 settled trades, 93% won, net slightly negative. At 386 trades gold was clearly positive and every other market slightly negative. A win earns about $0.36 and a loss costs about $5, so the bot needs about 93.5 wins in 100 to break even and sits at 93. The diagnosis: about two thirds of the loss is the two big Bitcoin losses on Oct 9 to 10 (capped now) and windows where two crypto markets lost together. The 25c exit is not the leak.
- **New on 2026-10-22:** only one of Bitcoin, Ethereum, XRP and Dogecoin may place an order per 15 minute window (a test: it should roughly halve crypto profit and remove the worst clusters); a refused Kalshi read is retried once; every order also logs `rise3` and `rng5` for the research reads. None of the logging changes an order.
- **Safety:** one combined limit per 15 minute window (5.5% of the base), a stop at **12%** of the base, a sell at 25c (a study this week found the line barely matters on Bitcoin, XRP and natural gas, so it stays), a one-click pause and flatten, phone alerts, and a rule that drops a probe market whose last 200 trades net negative.
- **Since 2026-10-23:** series order gold, XRP, Bitcoin, Dogecoin, Ethereum; fixed sizes at that date (Dogecoin 3, natural gas 2, **XRP back to 1 on 2026-10-25**; Dogecoin moved onto gold's ladder on 2026-10-30); Bitcoin and Ethereum only on a smooth climb (kill rules registered, read 2026-11-12 and 2026-11-17); extra logging fields (flips, two-stage look) that no order reads.
- **The website** has three pages: Market Brief, Bot and Settings (the Data page was tried and removed). New this week: a notification center (bell left of Brief, red bubble, banner for the worst cases), the account result line with date filter and axes, chart hover and axes on the Brief, a silent-market warning, a trimmed Bot page, phone tap targets. Before that: Privacy toggle, a Today line, readable light themes, plain headings and numbers with the bubble font only on the logo, and a layout fix so the trades list no longer squeezes into four-line rows.
- **We have tried about 4,640 ideas on the same data. None passed the bar for a deployable edge.** This week's tries (decision trees, volatility-managed ETFs, risk parity, factor ETFs, hedges, scale-outs) were all falsified. Capital, not ideas, is the limit: slow strategies tested so far are worth about $5 to $9 a year at $200.

## What you need to do now

1. Run `bash functions/deploy-sizing.sh` (XRP to 1 contract) and `npx firebase-tools deploy --only functions:marketTapeTick --project shwoopnet` (commodity charts), then re-copy **Tools, Copy all orders** so the smooth-climb and two-stage fields can be read.
2. Send your balance history since Oct 7, and whether the loss stop fired during the gap from Oct 17 to Oct 20.
3. Watch the Bot page for "Running" and for any repeat of the "HTTP 429" line.
4. Merge this refresh when you are ready.
5. Render: the old equities server was suspended on 2026-10-26 to stop a cost. Finish the cut: delete the Alpaca fields from your user document and revoke the Alpaca keys.

## What I am doing next

| Job | In plain words | Done when |
|---|---|---|
| Render and Alpaca (decided 2026-10-26) | The equities server was suspended. It cost nothing on Render but its Firestore reads from outside Google cost about $15 a month in data transfer | Billing, SKU report: data transfer out near zero within two days |
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
- **2026-11-17:** the review of the new rules: continue, pause or narrow, read on the live record (FWD7, FWD8, GOLD1-F, the research session's live diagnosis). Suggested tripwires, yours to edit and none automatic: net result since the #453, #458 and #459 deploys at or below -$15 means stop and look; two windows in a week where two filled crypto orders both lost means look (it should be zero now).
- **2026-11-16 and 2026-11-17:** the registered forward reads (E3F, FWD1, VOL1, PM3, OW7, then FWD2, FWD3 and GOLD1-F). One run each; nothing changes unless it passes.
- **2026-12-01:** the default read date for FWD5, FWD6, FWD7 and FWD8, and a second snapshot of the research data (Kalshi's history only reaches back about 69 days).
- **About 3 to 4 weeks:** a rerun of the funding study on the perps data the recorder is collecting.
- **The size review after a stop:** a loss stop no longer holds size increases (removed Oct 23, 2026 at the owner's request).

## Can wait

- Resting orders on the probes (after real fills).
- A recorder for the economics markets (CPI, payrolls): parked, the history is too short and the owner said not now.
- State-by-state gas ladders and the daily index markets (about one a day, so 300 days to test).
- Auto-restart after the loss stop.

## Done recently

- 2026-10-23 to 2026-10-25: notification center and red banner; account result line with date filter, percent and date axes, and touch scrub; Brief chart axes, times and hover; silent-market warning; Bot page trim (shards, usual-day bar, next-7-days chart, print statement and Copy all stats removed; Stop Loss and Risk into the Account card); landing page wallpaper and scroll fix; Today figure fix; XRP back to 1 contract; fixed sizes; smooth climb for Bitcoin and Ethereum; two-stage and flips logging; the order export carries every logged field; gold and crude charts when futures are closed; phone tap targets.
- 2026-10-22: live-account diagnosis with the research session; one crypto order per window (#459); a refused Kalshi read retried once (#460); `rise3` and `rng5` logged on every order (#458, #461); order exports carry entry time, fills, fees, book sizes, `rise3` and `rng5`; the Bot page Today line; the weekly health check rewritten for the Kalshi bot.
- 2026-10-21 (afternoon): the 10 minute entry for Bitcoin, XRP and natural gas went live; the probe drop rule and a cost cut (about $2 a month, and roughly $3 a month of that is given back by the exit watch running through the early minutes) went live; light themes made readable; numbers and headings in the plain font, the bubble font kept for the logo and a hop on hover; Today line; order exports with the entry tag (open); a perps recorder; the hand-sold fix and repair; gold-first sizing; the Data page.
- 2026-10-21 (morning): three live probe markets; the stop set to 12%; paper card removed; Copy all orders; new logo, icon and share card; footer disclosure.
- 2026-10-20: phone alerts, sound alerts, XRP and Dogecoin added, window limit 5.5%, shared Flatten and exit claim, cash-out at 99c tested and ruled out (TP1).
- Earlier: only L1; opening strategy removed; exit moved from 70c to 50c to 25c; the site slimmed to three pages.
