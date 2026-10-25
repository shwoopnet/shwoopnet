# Shwoop project overview

Last refreshed: 2026-10-25 (US Central). Refresh weekly; see `docs/README.md`. The bot rules, page and incident sections are updated for 2026-10-25. **The live record figures (settled trades, wins, net, balance) were NOT re-read in this refresh** (they come from an order export only the owner can copy), so any such figure below keeps its own date; the 2026-10-08 research notes keep theirs.

## What it is

Shwoop (Pocket Advisor) is a personal trading app with three parts that live in separate places:

| Part | Where | What it does |
|---|---|---|
| Frontend | this repo, `index.html` | One file, no build step. Firebase auth and Firestore. Hosted on GitHub Pages. Three pages: the Market Brief, the admin-only Bot page (called Kalshi in the code) and Settings. The Data page lived from 2026-10-21 to 2026-10-24 and was removed. The equities pages, the broker and market-data integrations and sign-up were removed on 2026-10-12. |
| Cloud Functions | this repo, `functions/` | The Kalshi bot, the order-book recorder, the account reads and the emergency controls. Deployed with `firebase deploy --only functions`. |
| Equities trading server | separate repo `shwoop-server`, on Render | Runs the equities and options cycles against Alpaca for every connected account, and writes the shared market snapshot the Brief reads. Not touched from this repo; reviewed read only. **The page no longer shows or pauses it.** |

This document is mostly about the Kalshi subsystem, because it is where most of the recent work went.

## The Kalshi bot (strategy L1)

**Markets (2026-10-25):** the 15 minute gold (`KXGOLD15M`), XRP, Bitcoin, Dogecoin and Ethereum markets (that list order since 2026-10-23), then three one-contract probe markets last in the list: AUD/USD, USD/CAD and natural gas. Gold is first and is the only market that keeps the size ladder. Fixed sizes since 2026-10-23: Dogecoin 3 contracts, natural gas 2, everything else one; **XRP went back from 3 to 1 on 2026-10-25** (24 fills, 4 losses, -$4.87 since 2026-10-23; merged, goes live with `deploy-sizing.sh`). The capped markets earn the ladder back only from its own live record (gold-first, `docs/GOLD_FIRST_PROPOSAL.md`). The list is a hard list in `functions/kalshiLiveLib.js` (`L1_SERIES`, `CAPPED_SERIES`, `PROBE_SERIES`); nothing stored can add a series. Equities are untouched by it.

**Rule:** buy the side priced 88c to 97c at the touch with one immediate-or-cancel order, then hold to settlement. Gold, Ethereum, Dogecoin and the currency probes enter about 6 minutes before the close. **Bitcoin, XRP and natural gas enter about 10 minutes before it instead (live test since 2026-10-21 about 2:15 PM CT, orders tagged `entryLead: "10m"`).** A market is decided once. A win pays about 3c to 12c per contract. A loss costs the whole price.

**One crypto order per window (2026-10-22):** of Bitcoin, Ethereum, XRP and Dogecoin only the first in list order places an order in a given 15 minute window; an order that did not fill does not hold the window. Gold and the probes are not part of it. It came from the research session's diagnosis of the live account (below) and is a test, read on the live record. **Logging only, no effect on any order:** every new order records `rise3` (how far the bought side's price rose over 3 minutes) and `rng5` (its 5 minute range) from public candles, written after the minute's orders are sent. **A refused read is asked once more:** a Kalshi read answered with 429 (too many requests) is retried once after 1.2 seconds; an order is never retried.

**Probe drop rule (2026-10-21):** a probe market is dropped when its last 200 settled entries net negative. It is an admission filter for unproven markets only; the five main markets are never subject to it. It cannot fire for 2 to 4 days after deploy.

**Bitcoin and Ethereum trade only on a smooth climb (2026-10-23):** at the 6 minute look the bought side's 1 minute path must have at least 4 earlier candles, no minute change below -0.005 and a total climb of at least 0.10, or no order is placed (`smoothGate`). Kill rules are registered: remove them if 3 of the first 40 smooth fills lose, or their net is under $0 after 100 fills, or the 2026-11-12 read is falsified. **More logging only (2026-10-23 to 10-24):** `flips`, `flips0`, `earlierCandles`, `askAtDecision` and the two-stage look (`ask10`, `side10`, `inBand10`, `ask8` ... `twoStageLeft`), all from public candles and none read by any order. The full order export carries them all.

**Runs:** 24/7 since 2026-10-08 (it used to be a 24 hour session). It runs until the owner stops it or a stop ends it.

**Size:** one contract per $43 of balance (about 2%), raised at most one step every 3 days, lowered if a fall holds for 2 hours (cash locked in an open trade does not count as a fall), hard ceiling 40. First review starts at 3, but a Start goes straight to the balance target. Half of each NEW net profit high goes to a pool that buys extra contracts, one per full contract cost, with no fixed limit (the account-funded part of an order is held to 1% of cash, two markets about 2%; the profit-funded add-on sits outside that rule, bounded by the pool, which holds only profit); the other half is set aside as savings that the sizing never counts.

**Safety, in the order it matters:**
- Orders cannot duplicate. The order id derives from the market, so two server instances during a deploy produce the same id and Kalshi refuses the second.
- One combined limit per 15 minute window: the account money put into one window is held to 5.5% of the base, and the series are sent in list order, so the later ones are the ones that go without.
- The bot stops itself when its own trades over the last 24 hours are down $10 (or **12% of the base at the last review**; it was 5%, then 6%, and was raised on 2026-10-20 after a full open window plus ordinary losses ended it with only $6.06 actually lost). Open orders count as lost, but the part of a lost or open order that was bought with reinvested profit (the add-on) does not count toward the stop, so a large add-on cannot lock the bot out after one loss. Manual trades do not count. After a stop it stays off until restarted.
- It fails closed: an unreadable balance, an unreadable order list, an unsaved size review, or a lost order answer all mean no order that minute.
- Hand-sold check (fixed 2026-10-21): an order is only called "sold by hand" when the account shows a sale that is not the bot's own entry or exit. Before the fix every NO order the bot bought was misread as a hand sale and left out of the stats; the fix repairs the old ones.
- More than 200 orders in 24 hours pauses it. A halt switch pauses entries. **Flatten all** (in the Running menu, next to **Pause bot**) pauses first, then sells every open position, one order each, never retried. Pause and Resume are the one everyday control; Start also lifts a pause left on after a Flatten.
- Live credentials can only exist for the admin account, enforced in `firestore.rules`. Every function checks the admin first.

## The Kalshi page (admin only)

**Bot page:** the account result line with a date filter (Today to All) and real percent and date axes with a touch scrub, the Account card (balance, stake, pool, **Today** result, Running menu with Start, Pause or Resume, and Flatten all, and Stop Loss and Risk at the bottom), Bot status, open positions with a small chance chart each, and recent trades. A silent-market warning ("Needs a look") appears when a market stops sending orders for far longer than its own usual gap. Privacy (masks dollar amounts as ****, kept in this browser only) and Tools menus in the header. **Notification center (2026-10-25):** a bell in the top navigation, left of Brief, admin only, with a red unread bubble, Important and Everything tabs and Mark all as read; the worst cases (bot stopped itself, an order needing a check, no check for minutes) also raise a red banner across the Bot page. **The Data page, the Print statement and Copy all stats were removed (2026-10-24).** The Brief's charts have percent and Central hour axes and a hover scrub; gold and crude now fall back to the last session when their futures are closed. Titan One is used only for the SHWOOP wordmark; headings and every number are plain Public Sans. Times are US Central. Order exports (Copy order diagnostics, Copy all orders) carry the entry tag. Mock-ups in `docs/mockups/` are older fixture renders.

## Research method

Everything in `kalshi-scalper/` follows one discipline: write the hypothesis, the counterparty (who loses money and why), a numeric prediction and kill criteria BEFORE any code or data. Verdict words are only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. The bar is at least 300 entries on 5 days, day clustered z of at least 2.1 (2.5 for a few tries), both halves positive, and still positive with fees times 1.2. The count of variants tried is kept in the README and every try raises the bar.

State on 2026-10-21 (information; the 2026-10-08 notes below are kept as they were):
- About 4,640 variants tried, none passing the bar (the research README holds the exact running count). Added this week and falsified: decision trees and kNN pattern skip rules, volatility-managed ETFs (QQQ, QLD, TLT, GLD, Bitcoin), risk parity, factor ETFs, hedges and scale-outs on the L1 favourite, TP1, GAS1, CMD1 and APP1. Admission filter DL1 (drop a series after a bad stretch) passed pooled but would have hurt the five live series, so it is applied to probes only. In each commodity ladder the market's own prices scored about three times better than our models.
- Live forward tests running (read dates in the research README): FWD5 (do the probes earn money), FWD6 (best-hour claims), FWD7 and FWD8 (the 10 minute entry on Bitcoin, XRP and natural gas), FWD2, FWD3 and GOLD1-F. All state small samples up front and may read NOT_ENOUGH_DATA.
- **Live record, bot only, 2026-10-22 about 11 AM CT (Data page):** 414 settled trades, 93% won, net **-$9.91**, average trade -$0.02, worst trade -$20.36. By week: Oct 5 -$5.13 (101 trades), Oct 12 +$7.30 (174), Oct 19 -$12.09 (139). At 386 trades (the last export read) the deepest drawdown was -$34.69 (about 17% of the account) and the win rate 93.0% against a break-even of about 93.5%. By market at 386: gold +$21.73 (113 trades, +3.1c a contract), Bitcoin -$23.39 (140, -2.3c), Ethereum -$1.54 (84), XRP -$6.24 (20), Dogecoin -$1.54 (20), natural gas -$0.40 (9). Entries at 95c to 97c won 99% (+$22.39 over 120 trades) while 88c to 95c lost $33.35 over 265; the research session found no such gradient in 69 days of history and advised against a price floor, so it stays a lead. The 21 real 25c sells cost $2.20 against holding them (17 right, 4 wrong), so the exit is not the leak. Most of the loss is the two big Bitcoin losses at 12 and 22 contracts on Oct 9 to 10 (about -$31, capped since) and windows where two crypto markets lost together.
- **Live record, bot only, 2026-10-21 about 2:15 PM CT (Data page, kept for comparison):** 365 settled trades, about 93% won, net **-$4.55**, average trade -$0.01, worst trade -$20.36. By market: gold +$28.81 (110 trades, +4.2c a contract), Bitcoin -$23.34 (139, -2.3c), Ethereum -$1.99 (78), XRP -$6.50 (16, -13.2c), Dogecoin -$1.07 (14), natural gas -$0.47 (8). Gold is the only market clearly earning; the small markets are small samples. These are live figures, never to be mixed with the research figures above.

State on 2026-10-08:
- 2,582 variants tried, none passing the bar. That includes stops, exits, price bands, resting orders, other minutes and the opposite end (the cheap side scalped early, C1 to C3, which lost 2.3c to 3.3c per contract).
- L1 itself, on 69 days and 3,432 entries: about +0.9c per contract before fee rounding, day clustered z 1.45 against 2.1. It failed its own bar, so running it is the owner's decision and not evidence it works. Forward checks F0 to F9 accumulate until about 2026-10-23.
- Fees were measured on the owner's own fills (21 of them): the reported fee is the order's fee rounded up to $0.0001, not to the whole cent. Earlier cost figures were a little pessimistic.
- Live record so far: 37 settled bot trades, 36 won, about +$3 net. A small sample; one loss costs about the same as 14 wins.

## Quality and process

- 33 plain-node test files in `test/` (about 330 named gates) and 6 Python test files for the research code. No test framework. Tests state the consequence ("already-allocated profit must never be allocated twice"), not the mechanism.
- A hand-run mutation check of the money code: 66 mutants, 53 killed, 9 real gaps found and closed.
- `check-frontend.js` (static checks of the single-file frontend) must report clean before every merge.
- Squash-merge only, never straight to `main`. Deploys happen from `main` after merge.
- Security review done 2026-10-08 (stored script injection fixed, dependency fixes, Finnhub input checks). Open items are listed in `docs/ROADMAP.md`.

## Incidents that shaped the code

- **Gold and crude had no charts at weekends (found and fixed 2026-10-25):** Yahoo answers a closed futures market's one-day read with a price and no bars, so the Brief drew a price with no line. The tape now asks for 5 days and keeps the last session (#557, test T21c). Needs `marketTapeTick` redeployed.
- **The scroll bar behind the sign-in screen and a Today figure that did not match (2026-10-24 to 10-25):** the signed-in page laid out under the fixed sign-in layer (now locked), and the result line's Today started at 06:00 UTC all year instead of Central midnight (#554, #555).
- **The live account lost money in clusters (diagnosed 2026-10-22):** 72% of recent loss dollars came from three windows where two crypto series flipped together, plus the two large Bitcoin losses before the one-contract cap. The 25c exit and the fill rule were checked and are not the cause. Fix for the clusters: one crypto order per window (#459, test OC1). Not yet readable: it went live the same morning.
- **A refused Kalshi read skipped a minute and blanked the account card (2026-10-22):** one 429 on the balance read meant no entries that minute and an error line on the Bot page. Reads are now retried once (#460, test RR1; gate L10 narrowed to keep orders unretried).
- **Every NO order read as sold by hand (found 2026-10-21):** Kalshi books a NO buy on the YES side, so the bot's own entry fill looked like a manual sale and those orders, losses included, were left out of the stats, the loss stop and the pool. Fixed in #432 with a repair pass; tests H5 and H11 to H13.
- **A chunky font made numbers hard to read, and a hover colour turned the logo black (2026-10-21):** Titan One is now the wordmark only; the hover is a letter hop (tests P1 and P7).

- **The loss stop ended the bot on a worst case, not a loss (2026-10-20):** the stop counts open orders as lost, and a full window at the 5.5% limit left only about $0.80 to $2.30 of room under a 6% stop, so $6.06 of ordinary settled losses plus an open window stopped it. The stop is now 12% of the base (test W5 pins the book from that night).

- **Duplicate real-money orders** (equities server): a random order id protected only a single call, so a deploy overlap sent the same order from two processes. Now keyed on the signal bar.
- **Missing losses on the performance page:** trades that settled after a session ended stayed "open" forever. A settle sweep now runs every minute whether or not a session is running.
- **A 97% win rate that was not the bot's:** a simulated figure was quoted as if it were live. Live figures and research figures are now always labelled apart.
- **GitHub Pages build failure (2026-10-08):** a symlink to a local data folder was committed by accident, the Jekyll build crashed in about a second, and three merges did not go live until it was removed. The path is now ignored.
- **Public repository contents:** Pages publishes the repo's files, including review notes and function source. A `_config.yml` now excludes everything except the app.
