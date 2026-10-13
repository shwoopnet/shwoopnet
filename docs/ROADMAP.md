# Roadmap

Last updated: 2026-10-12. Written in plain words on purpose.

## The goal

Make money on Kalshi without having to watch it. Right now one bot trades for you. The plan is to keep that bot safe and cheap to run, and look for a second thing that could earn on its own.

## Where we are today

- **One bot is live (L1).** About 6 minutes before each Bitcoin, gold and Ethereum 15 minute market closes, it buys the side that is almost certain to win (priced 88c to 97c) and waits for the result. It earns a few cents on most trades and loses a lot on the rare one that goes wrong. So far it is about break-even: 105 trades, 95% wins, slightly down.
- **Safety:** it stops itself if it loses 5% of the balance in a day, it sells a trade early if the price falls to 25c, and you can pause it or flatten everything with one button.
- **The website** has three pages: Market Brief, Kalshi and Settings.
- **We tried about 4,600 other trading ideas on the same markets. None worked.** The fees and the gap between buy and sell price eat any small gain. What changed on 2026-10-13 is that L1's own rule was checked on 28 older days it was never tuned on: +1.3c a contract after fees (z +3.2), +0.8c over all 68 days. See `kalshi-scalper/README.md` (L1B) and `docs/PROPOSALS.md` (proposal 6, XRP and Dogecoin at the end of the list, a decision for after 2026-11-16).

## What you need to do now

1. Merge the open pull request when you are ready (I will open it on request).
2. In the project folder run `git pull origin main`, then `firebase deploy --only functions`.
3. When it asks to delete a function, answer `y` only for `kalshiOpeningTick`. Anything else, stop and paste it to me.
4. Open the Kalshi page and check it still says **Running**.

## What I am doing next

| Job | In plain words | Done when |
|---|---|---|
| Find a second way to make money | Look at Kalshi markets other than the 15 minute crypto ones (daily weather, inflation and jobs numbers, crypto and stock ranges, news-driven markets) and check where free public data could beat the posted price | A ranked short list, each with a test written down before it runs |
| Lower the Firebase bill | Already cut the busy work. Check the bill again in two days | The bill drops |
| Fix two small risks in the bot | Pressing Flatten at the same moment the exit fires could sell twice. Positions you sell by hand are counted as if held to the end | Fixed and tested before the bot gets bigger |
| Keep the Market Brief fresh and add the ticker | Built: a free scheduled function writes prices and headlines every 5 minutes, and a strip shows S&P, Nasdaq, Dow, Russell, bonds, the 10 year yield, VIX, gold and Bitcoin | Check the strip fills after the next deploy |
| Tidy the site | The look stays exactly as it is (Ledger palette, Mono Ink skin, the current layout). Nothing is cut unless you name it | Only on your request |

## Proposals for money you oversee

See `docs/PROPOSALS.md`. In short: core savings in a retirement account first, keep only a working balance on Kalshi, keep L1 small and watched, and paper-track anything else before it gets money.

## How a new idea gets in

1. I write down the rule and what would make it fail, before testing.
2. I test it once on past data.
3. If it passes, it only earns a watch period on new days. It never gets real money straight away.
4. The bot you have now (L1) stays the only one trading real money until something passes.

## Dates to remember

- **2026-10-15:** the bot's weekly size review. It only raises size if the balance supports it.
- **2026-11-16:** the single forward reads of new days: XRP and Dogecoin (E3F), the live series (FWD1), a busy-minute filter (VOL1), a Polymarket-disagreement filter (PM3), plus the earlier opening-window read. Nothing changes unless it passes and you decide.

## Parked on purpose

- **Equities day trading and a stocks tab.** Shelved on 2026-10-13. At $500 with cash-account settlement the same dollars can be reused about once a day, every stock idea tested so far lost to cost, and a strategy that nets +0.1% a day earns about $10 a month on $500. It also repeats the first equities bot's path (capital too small, then day-only, then profits given back before the close). The full plan (brokers, dashboard mapping, safety rules, phases) is kept in the handoff folder as `09_equities_plan.md`. Revisit when the account is past $2,000 to $25,000, or if a pre-registered research pass on free data clearly beats the old tests.

## Can wait

- A better gold price feed.
- Auto-restart after the loss stop.
- Moving the scheduled jobs off Firebase if the bill stays high.
- The separate shwoop-server on Render still trades stocks through Alpaca for any account with keys. The page can no longer pause it, so decide whether to switch it off.

## Done recently

- Only L1 now: the opening strategy and its tabs are gone.
- Tried and ruled out: opening scalps, entry filters, 216 scalp variants and more.
- Exit moved from 70c to 50c to 25c at your request.
- Safety fixes, cost cuts, simpler wording, the site slimmed down to three pages.
