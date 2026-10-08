# Shwoop project overview

Last refreshed: 2026-10-08 (US Central). Refresh weekly; see `docs/README.md`.

## What it is

Shwoop (Pocket Advisor) is a personal trading app with three parts that live in separate places:

| Part | Where | What it does |
|---|---|---|
| Frontend | this repo, `index.html` | One file, no build step. Firebase auth and Firestore. Hosted on GitHub Pages. Equities journal and settings, plus an admin-only Kalshi page. |
| Cloud Functions | this repo, `functions/` | The Kalshi bot, the order-book recorder, the account reads and the emergency controls. Deployed with `firebase deploy --only functions`. |
| Equities trading server | separate repo `shwoop-server`, on Render | Runs the equities and options cycles against Alpaca for every connected account. Not touched from this repo; reviewed read only. |

This document is mostly about the Kalshi subsystem, because it is where most of the recent work went.

## The Kalshi bot (strategy L1)

**Markets:** the 15 minute Bitcoin (`KXBTC15M`) and gold (`KXGOLD15M`) markets on Kalshi. Equities are untouched by it.

**Rule:** about 6 minutes before a market closes, buy the side priced 88c to 97c at the touch with one immediate-or-cancel order, then hold to settlement. A win pays about 3c to 12c per contract. A loss costs the whole price.

**Runs:** 24/7 since 2026-10-08 (it used to be a 24 hour session). It runs until the owner stops it or a stop ends it.

**Size:** one contract per $85 of balance, raised at most one step a week, lowered at once if the balance falls, hard ceiling 10. First review starts at 3. Half of each NEW net profit high goes to a pool that buys extra contracts, one per full contract cost, with no fixed limit (one order is still held to 2% of cash); the other half is set aside as savings that the sizing never counts.

**Safety, in the order it matters:**
- Orders cannot duplicate. The order id derives from the market, so two server instances during a deploy produce the same id and Kalshi refuses the second.
- The bot stops itself when its own trades over the last 24 hours are down $10 (or 5% of the balance at the last review, about $17 at $344). Open orders count as lost. Manual trades do not count. After a stop it stays off until restarted.
- It fails closed: an unreadable balance, an unreadable order list, an unsaved size review, or a lost order answer all mean no order that minute.
- More than 200 orders in 24 hours pauses it. A halt switch pauses entries. **Flatten all** (in the Running menu, next to **Pause bot**) pauses first, then sells every open position, one order each, never retried. Pause and Resume are the one everyday control; Start also lifts a pause left on after a Flatten.
- Live credentials can only exist for the admin account, enforced in `firestore.rules`. Every function checks the admin first.

## The Kalshi page (admin only)

Account card (balance, bot change since start, stat tiles, by market, a Running menu that holds Start, Pause or Resume, and Flatten all), live books with a small chart per market (Bitcoin and gold price against the "to beat" line), charts (profit and loss, how orders ended, each settled trade), recent trades, open positions. Tools and Layout menus in the header. Times are shown in US Central. Mock-ups are in `docs/mockups/` (fixture data, not live figures).

## Research method

Everything in `kalshi-scalper/` follows one discipline: write the hypothesis, the counterparty (who loses money and why), a numeric prediction and kill criteria BEFORE any code or data. Verdict words are only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. The bar is at least 300 entries on 5 days, day clustered z of at least 2.1 (2.5 for a few tries), both halves positive, and still positive with fees times 1.2. The count of variants tried is kept in the README and every try raises the bar.

State on 2026-10-08:
- 2,582 variants tried, none passing the bar. That includes stops, exits, price bands, resting orders, other minutes and the opposite end (the cheap side scalped early, C1 to C3, which lost 2.3c to 3.3c per contract).
- L1 itself, on 69 days and 3,432 entries: about +0.9c per contract before fee rounding, day clustered z 1.45 against 2.1. It failed its own bar, so running it is the owner's decision and not evidence it works. Forward checks F0 to F9 accumulate until about 2026-10-23.
- Fees were measured on the owner's own fills (21 of them): the reported fee is the order's fee rounded up to $0.0001, not to the whole cent. Earlier cost figures were a little pessimistic.
- Live record so far: 37 settled bot trades, 36 won, about +$3 net. A small sample; one loss costs about the same as 14 wins.

## Quality and process

- About 55 plain-node test files in `test/` and one Python test file for the research code. No test framework. Tests state the consequence ("already-allocated profit must never be allocated twice"), not the mechanism.
- A hand-run mutation check of the money code: 66 mutants, 53 killed, 9 real gaps found and closed.
- `check-frontend.js` (static checks of the single-file frontend) must report clean before every merge.
- Squash-merge only, never straight to `main`. Deploys happen from `main` after merge.
- Security review done 2026-10-08 (stored script injection fixed, dependency fixes, Finnhub input checks). Open items are listed in `docs/ROADMAP.md`.

## Incidents that shaped the code

- **Duplicate real-money orders** (equities server): a random order id protected only a single call, so a deploy overlap sent the same order from two processes. Now keyed on the signal bar.
- **Missing losses on the performance page:** trades that settled after a session ended stayed "open" forever. A settle sweep now runs every minute whether or not a session is running.
- **A 97% win rate that was not the bot's:** a simulated figure was quoted as if it were live. Live figures and research figures are now always labelled apart.
- **GitHub Pages build failure (2026-10-08):** a symlink to a local data folder was committed by accident, the Jekyll build crashed in about a second, and three merges did not go live until it was removed. The path is now ignored.
- **Public repository contents:** Pages publishes the repo's files, including review notes and function source. A `_config.yml` now excludes everything except the app.
