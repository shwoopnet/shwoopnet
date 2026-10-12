# Roadmap

Last refreshed: 2026-10-12. Now / Next / Later, with the gate for each item. A date is a read date, not a promise. Nothing here is a performance claim: every figure is a measurement with its sample.

## Where we are

- **One live strategy, L1.** The bot buys the side priced 88c to 97c about 6 minutes before each Bitcoin, gold and Ethereum 15 minute close and holds to settlement. It runs 24/7 with size scaling (one contract per $43, weekly steps), a loss stop (5% of the balance), a window cap (4.5%), and an exit that sells a position if its price falls to 25c. Its measured edge is about +0.5c a contract against a fee of about 0.46c. It has not passed its own forward bar. Profit factor on the live record is about 0.9 over 105 trades.
- **Everything else was tried and failed.** 2,816 strategy variants on the 15 minute crypto and gold markets, none passing. The cause is cost: a taker round trip is about 3c in fees plus 1c to 1.6c of spread, which is bigger than any early move. See the ledger in `kalshi-scalper/README.md`.
- **The site is three pages:** Market Brief, Kalshi, Settings. The Kalshi page shows L1 only. The opening window paper strategy was retired on 2026-10-12 so the strategies cannot overlap.
- **Firebase cost is being cut:** an idle exit watch, capped order reads, the book recorder off (PR 389, deployed once you run the functions deploy).

## Now (this week)

| Item | Gate or check |
|---|---|
| Deploy the cost cuts and the 25c exit (`git pull origin main`, `firebase deploy --only functions`) | Account card still says Running, an open position still shows and settles, Rules text reads "Exit at 25c" |
| Deploy the L1-only change when merged; answer `y` for the one deletion `kalshiOpeningTick` | The deploy lists no other deletion |
| First weekly size review | 2026-10-15: the cap steps up only if the balance supports it |
| Read the Firebase bill again after two days | Reads under the free 50K a day; the top SKU is no longer Cloud Functions compute |
| Flatten against the exit watch can double-sell a position | Shared claim between the two sellers, with a test, before size grows |
| Positions sold by Flatten or by hand are booked as held to settlement | Settle them from the real fills, with a test |

## Next (to about 2026-11-16)

| Item | Gate or check |
|---|---|
| Research program for a passive edge (below) | Each candidate pre-registered before it runs, run once, recorded in the README with its count |
| OW7 forward read (open interest filter on L1 entries, offline) | 2026-11-16, once: `python -m scalper.backfill 30` then `python -m scalper.ow3 --forward 2026-10-13`. Boundary fixed at 0.2395, bar as registered. A pass changes nothing in L1 by itself |
| Forward checks F0 to F9 read | At least 300 entries on at least 5 days; z, halves and fees x1.2 as registered |
| Exit line at 25c: first read | After at least 30 triggered exits, compare to the 50c line's records, kept apart on the page |
| Brief data: keep the Market Brief fresh without paid feeds | Decide who writes `shared/marketSnapshot` (shwoop-server today, only 08:00 to 17:00 ET); news and earnings need a Finnhub key on Render |
| Broad-market ticker (S&P, QQQ, Dow, bonds) | SPY, QQQ and DIA are already in the snapshot; bonds is one symbol (TLT) added on the server. The page makes no market-data call |
| UI and text pass 2: Tools exports, Layout menu, Start dialog checkboxes, stats block, Brief movers and earnings | Owner picks what to cut; tests updated together |
| Size ladder decision | The owner overrode the evidence gates on 2026-10-08. After the forward read, keep or step back to 1 contract per the README |

## Research program: a passive edge on Kalshi

The goal: something that runs without daily touch, trades money on Kalshi, and has an information advantage that survives costs. The 15 minute crypto markets look efficient, so the program looks elsewhere. Every candidate is registered (rules, prediction, kill criteria) before it runs, run once, and counted.

| Direction | Why it might have an edge | Data and status |
|---|---|---|
| Weather (daily highs, lows, precipitation) | Public forecasts exist and may beat retail pricing; settlement is an objective official number | Survey running: market counts, liquidity, a free forecast archive for backtesting |
| Economic data (CPI, jobs, rates) | Public nowcasts (Cleveland Fed, FRED) against posted odds | Survey running |
| Volatility models on daily crypto and index range markets | An options-implied or realised-volatility probability against the price (H7 found 15 minute crypto calibrated within about 4c, so look at longer horizons) | Survey running; Deribit public data reachable |
| Order flow and volume on the 15 minute markets | Signed taker flow could say who is on which side before settlement | Feasibility study running: the public trades tape, how far back it goes, download time, spot history for lead and lag |
| Media and news | Coverage volume or sentiment (GDELT is reachable) might lead prices on event markets | Survey running; usable history is the open question |

Rules of the program:
- **Cost first.** A candidate must beat 0.07 p (1 - p) per taker leg, so prefer hold-to-settlement, extreme prices, or resting orders.
- **No tuning on the test data.** Selection, if any, happens on a training part; one frozen rule is read once on a part it never saw; a forward read on new days decides.
- **L1 stays the only live strategy** until something passes a forward read. A new strategy must show how it cannot hold a position at the same time as L1 and why it is a different bet.
- **There is no promote.** `FALSIFIED`, `NOT_YET_FALSIFIED` and `NOT_ENOUGH_DATA` are the only verdicts. A pass earns a forward paper read, never money.

## Later

- A real gold price feed that matches Kalshi's Pyth source (the current line is gold-api.com and can sit a dollar off).
- Weekday spread measurement for crypto (the one reading was a Sunday afternoon).
- Auto-resume after a loss stop with a cooldown (today it stays off until restarted, on purpose).
- App Check on the callables, a content security policy (needs a nonce build step), and requiring a verified email for the admin check.
- Weekly digest of the bot's real results against the forward-check thresholds.
- Move the scheduled jobs off Firebase onto the Render service already paid for, if the bill is still high after the cost cuts. Firestore and login stay.
- shwoop-server (separate repo, owner decides): it still trades Alpaca for accounts with keys and the page can no longer pause it; timing-safe secret compare; fail closed when the bar time is missing; `firebase-admin` bump.

## Decisions waiting on the owner

1. Merge and deploy the L1-only change and the Performance rename.
2. Whether to fix the Flatten and exit-watch double-sell now or after the next size step.
3. Which UI clutter to cut next (Tools exports, Layout menu, Start checkboxes, extra stats, Brief movers and earnings).
4. Whether shwoop-server should keep trading Alpaca at all.

## Done recently

- 2026-10-12: L1 only. The opening paper recorder and its tabs were removed; `OW1` stays as history in `docs/OPENING_STRATEGY.md`.
- 2026-10-12: strategy search. `OW2` (opening scalp, 4 variants), `OW3`, `OW4`, `OW7` (hold-to-settlement contrasts) and `SS1` (216 scalp cells, train and validation) all falsified; total tried 2,816. OW7 has a registered forward read.
- 2026-10-12: exit moved from 70c to 50c to 25c at the owner's request; the pool always rebuilds after every win; the two page switches for them were removed.
- 2026-10-12: bot safety fixes (no Start on a running bot, halt re-read before each order), Firebase cost cuts, simpler wording, the Kalshi bot is live.
- 2026-10-12: the blank slate. The site is the Brief, Kalshi and Settings; the trading pages, Alpaca, Finnhub, Twelve Data and sign-up are gone.
- Earlier: 24/7 bot, weekly size scaling, reinvest and skim, Flatten all, performance tracker, readable open positions, market charts, Central time, security fixes, Pages build and exclusion of non-app files.
