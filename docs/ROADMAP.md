# Roadmap

Last updated: 2026-10-20. Written in plain words on purpose.

## The goal

Make money on Kalshi without having to watch it. Right now one bot trades for you. The plan is to keep that bot safe and cheap to run, and look for a second thing that could earn on its own.

## Where we are today

- **One bot is live (L1).** About 6 minutes before each Bitcoin, gold and Ethereum 15 minute market closes, it buys the side that is almost certain to win (priced 88c to 97c) and waits for the result. It earns a few cents on most trades and loses a lot on the rare one that goes wrong. So far it is about break-even: 105 trades, 95% wins, slightly down.
- **Safety:** it stops itself if it loses 5% of the balance in a day, it sells a trade early if the price falls to 25c, and you can pause it or flatten everything with one button.
- **The website** has three pages: Market Brief, Kalshi and Settings.
- **We tried about 4,600 other trading ideas on the same markets. None worked.** The fees and the gap between buy and sell price eat any small gain. What changed on 2026-10-13 is that L1's own rule was checked on 28 older days it was never tuned on: +1.3c a contract after fees (z +3.2), +0.8c over all 68 days. See `kalshi-scalper/README.md` (L1B) and `docs/PROPOSALS.md` (proposal 6, XRP and Dogecoin at the end of the list, a decision for after 2026-11-16).

## What you need to do now

Merged on 2026-10-20 from the owner's Daily Recap page (written that morning from Oct 12 to 14 data, so several items were already done) and the Kalshi Research Log page (2026-10-13). Status is as of the end of 2026-10-20.

**Open, waiting on you**

1. **Check the two failed 25c exits.** On the Kalshi page, Tools, Copy order diagnostics, paste the exit notes to me. Latest live record: the price touched 25c 14 times, 12 sold, 2 did not. Cheapest money fix on the list (one unsold fall costs about 21 wins at $0.39 each).
2. **Confirm the 25c exit is the code that is running.** `functions/deploy-sizing.sh` deploys only `kalshiLiveArmed` and `kalshiBooks`. A full `firebase deploy --only functions` (answer `y` to deleting `kalshiOpeningTick` only) was asked for in the roadmap on Oct 12 and not confirmed since. Until it is, the exit watch may still be on an older line.
3. **Stock and options automation on Render.** The old server can still trade Alpaca for any account with keys saved, and the site cannot pause it. Parked by the owner on 2026-10-20, nothing changed. The safe minimum when you want it: set the four auto-trade override fields to false on the user document.
4. **Decide how the daily recap gets real numbers.** Option A: a public `stats.json` with totals only. Option B: a private GitHub repo connection. Without one, every recap carries stale snapshots.

**Done since the recap was written**

- Deploy of the pool fix and sizing from a laptop (2026-10-20, `deploy-sizing.sh`). The bot says **Running**.
- XRP and Dogecoin added at the end of the series list (Proposal 6, option chosen by the owner 2026-10-20). Forward read still due Nov 16.
- Size review: the cap was 1 because a loss stop on 2026-10-17 triggers a 7 day hold on step-ups. The owner raised `cap` to 4 by hand in `kalshiLiveControl/sizing` on 2026-10-20 (the code was not changed). The page shows 4 contracts, $3.55 (1.7%).
- Market Brief ticker built (S&P, Nasdaq, Dow, Russell, bonds, 10 year yield, VIX, gold, Bitcoin).

**Open, mine to do**

- Fix the Flatten and exit overlap (pressing Flatten as the 25c exit fires could sell a position twice). Needs a shared claim before the bot gets bigger, which it now has.
- Fix hand-sold positions being counted as held to the end (makes a trade look better than it was).
- Re-read the Firebase bill (it was $14.76 for Oct 1 to 12). If Cloud Functions compute has not fallen, the plan is to move the scheduled jobs to Render.
- Second-strategy research (still open; nothing qualifies for real money yet).

**Decisions still open** (numbers are from the Research Log and the live record of 2026-10-20)

| Decision | What we know |
|---|---|
| Keep, hold or raise size | At 4 contracts the stop is about $9.80 (5% of the balance at the last review). Edge over 68 days +0.79c a contract (z +2.5); live 275 trades +$2.20, cannot be told from zero. The 25c line was touched in 14 of 17 losses. |
| Raise the 40 contract ceiling to 80 | Simulation: +20% to 30% on the year-end median at a similar drawdown. Even with zero edge the median worst fall in a year is about 25%. Not a recommendation. Irrelevant until the balance is near $1,860. |
| The 90c to 92c band | Live: 56 trades, 93% won, -$19.34. 95c to 97c: 92 of 92 won, +$23.31. Backtest does not agree with the live pattern. A 95c floor would need a pre-registered forward test. |
| Bitcoin | Live -$22.21 on 124 trades; gold +$27.03. Backtest ranks it last too (+0.45c over 68 days, +0.55c, z 0.88 on the 28 older days). Options: move it last in the series list, lower size, narrow the band, or keep collecting. |
| Polymarket disagreement skip, live | Failed its registered test (z -1.34), but skipped entries lost about twice as often (9.8% vs 4.6% Bitcoin, 8.7% vs 3.7% Ethereum). Needs a Polymarket read at order time. Forward read PM3 on Nov 16. |
| Why the 25c exit did not sell, and whether to keep it | Unknown: position already closed, no buyer, or skipped by design. Backtest says the line is neutral (-0.03c to +0.13c a contract). Live realised -$67.45 on 12 sells. Settle it with the diagnostics. |
| Is the edge real | Two windows agree in sign, which is not proof of stability. Decide how long to run before scaling up, holding or stopping. |
| Keep the Render server and its news data key | Costs money and still holds the old Alpaca automation. |

**Ranked next steps**

1. Pull the exit diagnostics for the two failed 25c exits.
2. Confirm the full functions deploy (item 2 above).
3. Close the Flatten and exit double-sell gap.
4. Decide how the recap gets its numbers.
5. Hold XRP and Dogecoin results, the ceiling change and any 90c to 92c or Bitcoin rule change until the Nov 16 reads and a fresh batch of trades. Half the older-days gain rides on five days, and 17 losses cannot support a rule change yet.
6. Turn off the Alpaca auto-trade overrides on Render whenever you decide (parked).

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

- **2026-10-17 to 2026-10-24:** the size-ladder hold after the 2026-10-17 loss stop (the cap was set by hand on 2026-10-20, so it does not bind now). Ladder steps resume after 2026-10-24.
- **2026-11-16:** the single forward reads of new days: XRP and Dogecoin (E3F), the live series (FWD1), a busy-minute filter (VOL1), a Polymarket-disagreement filter (PM3), plus the earlier opening-window read. Nothing changes unless it passes and you decide.

## Parked on purpose

- **Equities day trading and a stocks tab.** Shelved on 2026-10-13. At $500 with cash-account settlement the same dollars can be reused about once a day, every stock idea tested so far lost to cost, and a strategy that nets +0.1% a day earns about $10 a month on $500. It also repeats the first equities bot's path (capital too small, then day-only, then profits given back before the close). The full plan (brokers, dashboard mapping, safety rules, phases) is kept in the handoff folder as `09_equities_plan.md`. Revisit when the account is past $2,000 to $25,000, or if a pre-registered research pass on free data clearly beats the old tests.
- **The Alpaca question (2026-10-20).** The old `shwoop-server` can still trade Alpaca for accounts with keys stored. The owner parked deciding what to do about it. Nothing was changed.
- **SCHD and JEPQ research (2026-10-20).** Cancelled at the owner's request. What was found is in `kalshi-scalper/README.md` (BUYDIP1: waiting for "key levels" lost to monthly buying on SCHD, SPY and QQQ). No further work planned.

## To do later (owner's request, 2026-10-20)

- **Alternative strategies.** Look for ways to make money besides L1. Start from what is already crossed off (`kalshi-scalper/README.md`, and `research/MECHANISMS.md` in `shwoop-server`) so nothing is tried twice; each new idea is written down with its pass bar before it is run.
- **Alternate markets.** Look beyond the 15 minute Bitcoin, gold, Ethereum, XRP and Dogecoin markets. Already tried without an edge: sports favourites, weather, hourly ladders, long-dated favourites, other commodities and coins, Polymarket as a second price. Not yet runnable: options (the chain recorder is built on a `shwoop-server` branch and not deployed). Equities day trading is parked (see above).
- **Waiting on data, not on you:** the 2026-11-16 forward reads (XRP and Dogecoin, the live series, the busy-minute filter, the Polymarket filter).

## Can wait

- A better gold price feed.
- Auto-restart after the loss stop.
- Moving the scheduled jobs off Firebase if the bill stays high.
- The separate shwoop-server on Render still trades stocks through Alpaca for any account with keys. The page can no longer pause it, so decide whether to switch it off.

## Done recently
- 2026-10-20: the research data (Kalshi market history, 44 MB compressed) is archived on the `research-data` branch with a manifest and a restore script, because the early August days could not be downloaded again. Take a second snapshot before about 2026-12-01.
- 2026-10-20: the SHWOOP wordmark is bubbly graffiti with a straight extrusion and a ghost wordmark sits behind the page (#411, #412).
- 2026-10-20: 4 contracts live (cap edited by hand after the loss-stop hold); XRP and Dogecoin added to the series list; Yes label and phone layout on the market cards; charts only while in a trade (desktop; no charts on phones); optional sound alerts on the Kalshi page (#400); Flatten and the 25c exit share a claim per market (#401, needs a full functions deploy); phone alerts via Web Push (#403, needs the same deploy; the ntfy phone push was declined by the owner).
- 2026-10-20: **TP1, a 99c take-profit on L1, FALSIFIED** in both windows (flip rate from 99c 0.50% and 0.27%, below the 1% to 1.5% break-even). Nothing built.

- Only L1 now: the opening strategy and its tabs are gone.
- Tried and ruled out: opening scalps, entry filters, 216 scalp variants and more.
- Exit moved from 70c to 50c to 25c at your request.
- Safety fixes, cost cuts, simpler wording, the site slimmed down to three pages.
