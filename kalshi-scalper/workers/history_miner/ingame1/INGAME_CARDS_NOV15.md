# In-game quick-read cards (History Miner, written Nov 15, 2026 ~21:35Z, before any in-game price or result is opened)

Data: sports-data branch, ingame/ (record_ingame.py: NBA, NHL, NFL moneyline both teams, the spread and total nearest 50c at the first poll; ~20 s while hot, else 120 s). No game clock and no result in the file: results come from a public settled-markets listing (job IG_RESULTS, via Main). Lead-lag between related markets is the closed family and is NOT used. Each card is ONE try. Light gate: one build, Auditor B's quick check, one run, committed blind. Only the windows Auditor B clears are read.

Common: two-sided means 0 < yes_bid < yes_ask < 1. YES ask = yes_ask, NO ask = 1 - yes_bid. Fee per order ceil(round(100 x 0.07 x c x p(1-p), 9))/100, c = 1 (and 10 printed). Haircut h on the entry ask: 0, 1c, 2c; PRIMARY 2c (in-game quotes move fast and the poll is 20 s). Held to settlement; void refunds price, keeps fee. Pass bar: PF at 2c >= 1.3, both floor(n/2) halves (by entry time) >= 1.0, and n >= 100; under 100: "no evidence at n = x". Pooled over NBA, NHL and NFL, with per-league rows printed for information.

## IGFADE1, fade a big in-game jump (shape: overreaction after a scoring event)
- Moneyline tickers only. Two consecutive observations of the same ticker no more than 45 s apart, both two-sided.
- Jump: |mid2 - mid1| >= 0.10 (mid = (bid + ask) / 2).
- Entry at the second observation: buy the side that FELL (if YES mid rose, buy NO at 1 - yes_bid; if it fell, buy YES at yes_ask), only if that ask is 0.15 to 0.60 inclusive.
- At most one entry per game (the first qualifying jump on either team's moneyline ticker of the game, by time). Hold to settlement.
- Counterparty: takers chasing a score; prediction: the side that fell recovers on average, so PF at 2c >= 1.3. Kill: PF at 2c under 1.0.

## IGUNDER1, sell the over in-game (shape: totals drift, over bias of bettors)
- Totals tickers only (YES = over the strike). The FIRST observation of each totals ticker that is two-sided after the game's moneyline has had a hot poll (20 s cadence, so the game is live: two moneyline observations no more than 45 s apart).
- Buy NO (the under) at 1 - yes_bid if it is 0.35 to 0.65 inclusive. One entry per game. Hold to settlement.
- Counterparty: fans buying overs in-game; prediction: NO wins more than its price implies, PF at 2c >= 1.3. Kill: PF at 2c under 1.0.

Tries tonight: 2 (one per card).
