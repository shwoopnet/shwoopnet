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

## Amendment 1 (2026-11-15 ~21:45Z): Auditor B's dated line (21:23Z), before any read
- Readable: NBA rows and events before 2026-11-13T00:00:00Z (INGAMELAG1 reserves NBA from then on); NHL and NFL Nov 8 to Nov 15 entire. Nothing else.
- Thirds, by the market's close time (from the settled listing), the same for both cards and separate from INGAMELAG1's: third 1 = 2026-11-08T00:00Z (1794096000) to 2026-11-11T00:00Z (1794355200); third 2 = to 2026-11-13T00:00Z (1794528000); third 3 = from 2026-11-13T00:00Z, NHL and NFL only, HELD OUT, read once, and NOT listed or read in this quick read. NBA has no third 3 here.
- Quick read uses thirds 1 and 2 only; recorder rows with t_recv on or after 2026-11-13T00:00Z are dropped before any price is read, and so is any market whose close is on or after that time.
- Bar replaces the halves: PF at 2c >= 1.3 pooled, and >= 1.0 in third 1 and in third 2 separately, n >= 100 over thirds 1 and 2.
- Tip-off (IGUNDER1 only): "game live" is the first moneyline poll pair no more than 45 s apart, i.e. the recorder's hot cadence, which starts on a 2c move; never the result or the final price. IGFADE1 uses no tip-off.
- Results: job IG_RESULTS (settled listing, closes 1794096000 to 1794527999 only), dispatched by Main.

## Amendment 2 (2026-11-15 ~21:55Z): Auditor B's hold map (21:26Z), before any read
- Clear: KXNBATOTAL and KXNFLTOTAL closes Nov 8 to Nov 12. IGUNDER1 runs on NBA and NFL only.
- Held: KXNBAGAME and KXNFLGAME closes from Nov 1 (SPORTS-PRE outcome set, until 2027-01-01, unless the Head rules a bare result listing is not a read of its test); NHL (NHLOT's held-out unknown, Desk B to state). IGFADE1 waits on both rulings and is not run tonight.
- IG_RESULTS cut to the two totals series (max 6 requests). The reader is unchanged: a market not in the listing is dropped.
- Head's ruling (21:27Z): a settled-result listing IS a read of SPORTS-PRE's outcome set, so KXNBAGAME and KXNFLGAME stay out until 2027-01-01 or SPORTS-PRE closes. IGFADE1 is PARKED (not killed); NHL waits on Desk B's NHLOT date. Main dispatches the 2-series IG_RESULTS (sha ad7d5391).
