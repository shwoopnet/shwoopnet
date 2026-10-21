# Roadmap

Last updated: 2026-10-21. Written in plain words on purpose.

## The goal

Make money on Kalshi without having to watch it. One bot trades for you. The plan is to keep that bot safe and cheap to run, and to test, with real small money, whether other markets can earn on their own.

## Where we are today

- **One bot is live (L1), on eight markets.** About 6 minutes before each 15 minute market closes, it buys the side that is almost certain to win (priced 88c to 97c) and waits for the result. Five markets are fully sized: Bitcoin, gold, Ethereum, XRP, Dogecoin. Three are one contract each, as a live test: AUD/USD, USD/CAD and natural gas (merged 2026-10-21, **not live until the deploy is run**).
- **The live record so far (bot only, 2026-10-21):** 303 settled trades, 93.3% won, net **-$2.93**, profit factor 0.98. A win earns about $0.41 and a loss costs about $5.95, so the bot needs 94 wins in 100 to break even and has been at 93.3. Gold is +$28.35 on 98 trades; every other market is slightly negative (Bitcoin -$20.91, Ethereum -$4.18, XRP -$3.53, Dogecoin -$2.66). The exit at 25c fired on 16 trades and sold 14; the page reports those 14 sells as -$73.73 realised in total, which is most of what the 20 losing trades cost. Only 1 of the 4 positions whose result is known would have won if held, which is what a 25c line predicts.
- **Safety:** one combined limit per 15 minute window (5.5% of the base), a stop at **12%** of the base (changed from 6% on 2026-10-20 after a full open window plus ordinary losses ended the bot with only $6.06 actually lost; open trades are still counted as lost), a sell at 25c, a one-click pause and flatten, and phone alerts for every buy, sell, settle and stop.
- **The website** has three pages: Market Brief, Kalshi and Settings. New look: bubbly SHWOOP wordmark over FINANCIALS, a short footer with the legal disclosure. The paper-candidates card is gone.
- **We have tried about 4,630 ideas on the same data. None passed the bar.** On 2026-10-21 three more were tested on history in one sitting and all failed: the gas price ladder (-7.5c a contract), commodity daily ladders (-7.3c, z -4.3) and the approval-rating ladder (not enough data, and its model scored worse than the market). In each, the market's own prices predicted the outcome about three times better than our models. Cost and a well-informed market are what keep winning.

## What you need to do now

1. Merge any open pull request you want live (I open them on request).
2. From `~/shwoopnet`, after `git pull origin main`, run `bash functions/deploy-sizing.sh` then `bash functions/deploy-push.sh`. Start right after an entry minute has passed (about :11, :26, :41 or :56 on the clock). This puts the 12% stop and the three new markets live.
3. Open the Kalshi page and check it still says **Running** and that the rules text says "down 12%".
4. Tap **Tools, then Copy all orders**, and send me the result, so I can line every trade up against what was changed when.

## What I am doing next

| Job | In plain words | Done when |
|---|---|---|
| Read the first fills on the three new markets | They are thin (about 1,600 contracts a market), so some orders will show "no fill". That is a real result | A short note on fill rate, fees and result per market |
| Compare the bot's profit with what we added | The more markets and size we add, the bigger the losses and the same small wins. Check it against the order list | A table of result by change, with the noise caveat |
| Gold first | Gold is the only market that clears the bar on its own (+1.54c a contract, z 2.9 on 68 days, and +$28 live). Build a forward scoreboard per market, then give more size only to the ones that keep earning | Rules written first, then built |
| Maker (resting) orders | Fees are about half the edge. Test resting orders live at one contract, as their own pull request with a cancel path | Only after real fills come in on the new markets |
| Fix the hand-sold problem | A position you sell by hand is still booked at the market result. Built (#407), not merged | You confirm the first alert, then merge and run `deploy-sizing.sh` |
| US500 perpetuals (parked) | Kalshi launched a leveraged S&P perpetual on 2026-10-06. Different product, different API, 13.7x to 15.3x leverage, fees of 12 bps a side for a taker. Not a fit for an anti-degen site | Only if you ask |

## Proposals for money you oversee

See `docs/PROPOSALS.md`. In short: core savings in a retirement account first, keep only a working balance on Kalshi, keep L1 small and watched, and test anything else with a small live probe before it gets more.

## How a new idea gets in

1. I write down the rule and what would make it fail, before testing.
2. I test it once on past data. If it clearly fails, it stops there.
3. If it passes or cannot be settled on history, it can go live as a **one-contract probe** (your decision on 2026-10-21: live forward testing, no more paper). It sits last in line, inside the same window limit and loss stop.
4. It earns more size only from its own live record, not from a backtest.

## Dates to remember

- **2026-11-16:** the registered forward reads (E3F, FWD1, VOL1, PM3, and the OW7 look). One run each; nothing changes unless it passes.
- **2026-11-30:** the paper tracker's registered read on the three FX and gas markets. The page card is gone and live trading on them replaces it, but the server still records, so the read is free.
- **About 2026-12-01:** a second snapshot of the research data (Kalshi's history only reaches back about 69 days).
- **The first weekly size review after a stop:** a loss stop holds size increases for 7 days.

## Can wait

- Resting orders on the three probes (after real fills).
- Removing the server-side paper tracker (needs a deploy; costs very little).
- State-by-state gas ladders, a gasoline-futures input for gas, and the daily index markets (about one a day, so 300 days to test).
- The separate shwoop-server on Render still trades stocks through Alpaca for any account with keys. The page can no longer pause it, so decide whether to switch it off.
- Auto-restart after the loss stop.

## Done recently

- 2026-10-21: three live probe markets merged; the stop set to 12%; paper card removed; "Copy all orders" button; new logo, icon and share card; footer disclosure; strategy ideas list (`docs/STRATEGY_IDEAS.md`).
- 2026-10-20: phone alerts (Web Push, no third party), sound alerts, XRP and Dogecoin added, window limit 5.5%, shared Flatten and exit claim, cash-out at 99c tested and ruled out (TP1).
- Earlier: only L1; opening strategy removed; exit moved from 70c to 50c to 25c; the site slimmed to three pages.
