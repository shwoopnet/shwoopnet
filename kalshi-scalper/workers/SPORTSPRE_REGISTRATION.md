# SPORTS-PRE registration: pre-game moneylines against ESPN's pre-game win probability
Written 2026-10-31, about 2:50 PM CT (19:50 UTC), BEFORE any SPORTS-PRE row has been recorded and before the recorder exists. Research only. Owner approved the proposal at 2:45 PM CT. Nothing places an order; no live code changes. Recorder (review branch, owner merges): `claude/v2-recorder-sportspre`.

## Question and counterparty
Is the Kalshi pre-game moneyline for a US team sport wrong in a way ESPN's pre-game win probability can see? **Loser:** retail traders who over-bet YES (Bartlett and O'Hara, NBER, "Adverse Selection in Prediction Markets: Evidence from Kalshi", 41.6 million trades; see `NEWH16_DIGEST.md` source 2, hourly resolution, not measured on sports moneylines specifically). The cheap side of a mispriced favourite is the candidate.
**Honest prior, stated now:** sharp sportsbooks are far better forecasters than ESPN's BPI/FPI, and Kalshi quoters follow them. The market probably has the better Brier score. The most likely result is FALSIFIED (Brier), and ESPN1 already found the same ordering in play (Kalshi's mid beat ESPN's probability in NFL, college football and NBA). Prior of a pass: 3%.

## Ledger check: what is NOT repeated
| Earlier test | What it used | Why SPORTS-PRE differs |
|---|---|---|
| SP1 (2026-10-13) | Kalshi hourly ask 12 hours before, 88c to 97c favourites, 12 series. FALSIFIED, -4.19c | Kalshi price only, no outside forecast, favourites. This one compares to ESPN and buys the CHEAP side |
| F6 (2026-10-26, tennis favourites 0.75 to 0.95) and F7 (game totals under) | Kalshi quote only. FALSIFIED | no outside forecast; tennis and totals |
| FP3, MAKER1 | tape footprints and resting orders on tennis | execution and order flow, not a forecast |
| ARB5, SPORTCONS1 | internal consistency locks (totals ladders, winner complement). FALSIFIED / NOT_ENOUGH_DATA | no forecast; SPORTCONS1 showed the two team markets stay inside the arithmetic |
| ESPN1 (2026-10-30) | ESPN IN-PLAY win probability against the in-play ask, lag D = 180 s. FALSIFIED 4 of 4 | in-play lag; ESPN1's own README text says nothing tested a PRE-GAME calibration gap. Same data family (ESPN), different object (the pre-game BPI/FPI figure), different time (60 minutes before the start, no play data) |
| NEWH16 digest | literature on short horizon binaries | source of the counterparty only; no tested edge |
| L1 | 15 minute crypto and gold | **no overlap: no 15 minute ticker is ever touched** |
Not a reword of any of them. What is shared with ESPN1: the matching of a Kalshi event to an ESPN game by teams and date.

## Universe (cost rule fixed now)
Kalshi series `KXNFLGAME` (NFL), `KXNCAAFGAME` (college football), `KXNBAGAME` (NBA), `KXMLBGAME` (MLB). A game enters the universe only if, at the look, BOTH team markets are two-sided (yes bid at least 0.01, yes ask at most 0.99, ask not below bid), the spread of each (ask minus bid) is at most 2c, and the ask size of the market bought is at least 10 contracts (so C = 10 is real). Games failing this are counted and dropped, not tried at another time.
**MLB is in the registration but out of season:** the World Series is over, there is no MLB game before the stop date, and `KXMLBGAME` has 0 open markets today. It adds nothing to the count; it is kept so the recorder does not need a change in spring. NHL is out (not one of the four sports). Games with a start before 2026-11-01 00:00 UTC are excluded from the read (today's games were looked at, see the disclosure).

## Market structure (read from Kalshi's public API on 2026-10-31)
- One Kalshi **event** per game, ticker `<SERIES>-<yyMONdd><AWAY><HOME>` (for example `KXNBAGAME-26OCT31PHICHA`, `KXNFLGAME-26NOV09BUFMIN`, `KXNCAAFGAME-26NOV14UNAUWGA`), `mutually_exclusive: true`. The event holds **two binary markets, one per team**, tickers `<event>-<TEAM>` (for example `...-CHA`, `...-PHI`). `yes_sub_title` is the team's Kalshi name ("Charlotte", "Los Angeles L"); the YES market of team X pays $1 if X wins. A tie in the NFL resolves to $0.50 for each team.
- Pairing: `GET /markets?event_ticker=<event>` returns both team markets in one request. Quote fields: `yes_bid_dollars`, `yes_ask_dollars`, `yes_bid_size_fp`, `yes_ask_size_fp`, `status` (`active`), `result` (empty until settled; `yes` or `no`).
- **Start time:** Kalshi has no start field. `occurrence_datetime` and `expected_expiration_time` are an END estimate (3 hours after the ESPN start for the NBA and NFL games checked: PHI@CHA ESPN start 22:00Z, Kalshi 01:00Z), and `close_time` is days later (a latest-settlement bound). **The start time is ESPN's `events[].date`** (scoreboard), and the Kalshi event is matched to the ESPN game by league, the date in the event ticker (ESPN start in US Eastern time, plus or minus one day) and the two team names (`yes_sub_title` against ESPN displayName, shortDisplayName, location, abbreviation). Unmatched games are counted and dropped.
- Kalshi markets are open for days before the game; the 60 minute look is an hour-old-at-most quote near the start, not the 12 hour early candle SP1 used.

## The look
**T-60 minutes before the ESPN start time.** The recorder polls each tracked game every 5 minutes from 120 down to 30 minutes before the start. The look is the LAST poll received (recorder clock) at or before T-60 min and no earlier than T-75 min; a game with no such poll is dropped and counted. Both Kalshi markets and the ESPN predictor are taken from that one poll (the ESPN response must have been received within 5 minutes of the Kalshi read, both stored with their own receive times). Nothing after the look is used to choose the trade.

## Rule (2 tries)
Let pE(team) be ESPN's pre-game win probability for the team (defined below), ask(team) the YES ask at the look.
- **Try A (the proposal):** buy the **cheaper side**: the team with the lower YES ask (a tie: the larger gap). Signal if pE(cheaper) - ask(cheaper) is **at least 6c (0.06)**. Buy 1 order of C = 10 YES contracts of that team at the quoted ask, hold to settlement. At most one trade per game.
- **Try B (the companion, defined here because the proposal fixed one rule and "2 tries"):** the same threshold of 6c, but the side is **either** team (the larger pE - ask gap of the two, if at least 0.06). Purpose: show whether any gap, not only the underdog's, is paid. The numbers (0.06, C = 10, T-60) are the proposal's; only the side restriction is dropped.
Fill: the quoted ask at the look, no price improvement, no fee waiver. **Fees:** 7% x C x p x (1 - p), rounded up to the cent per order, at C = 10 (p = the ask paid), and the whole check again with fees x 1.2. Net per contract = (payout - ask) - fee / 10. NFL tie payout 0.50.

## ESPN's probability: what it is, and the look-ahead check (done 2026-10-31, the owner asked for it)
**Fields found** (all public, keyless; `site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={id}` and `sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/predictor`; fetched at 19:43 UTC on Oct 31 for games in all three states, college football, NFL, NBA, and a finished MLB game):

| Endpoint | Not started (`pre`) | In progress (`in`) | Finished (`post`) |
|---|---|---|---|
| `summary.predictor` | present: `homeTeam.gameProjection`, `awayTeam.gameProjection` (e.g. FLA vs UGA 81.8 / 18.2; NFL BAL@BUF 61.4 / 38.3; NBA PHI@CHA 40.6 / 59.4) | **absent (null)** | **absent (null)** |
| `summary.winprobability` | empty list | per play rows | per play rows |
| `core .../predictor` | present, `lastModified` present | still present, same `lastModified` as before the start | still present, same `lastModified` (MLB: `lastModified` 2026-10-28T11:04Z for a game that started 2026-10-29T00:00Z) |
| `core .../probabilities` | HTTP 400 "not supported" (football) / empty | per play (25 per page) | per play |
| scoreboard `events[]` | no probability field at all | none | none |
| HTTP headers | `Date` only, `Cache-Control: max-age=6 to 10`; no `Last-Modified`, no `ETag` | same | same |

**What this means, plainly:**
1. **The summary's pre-game `predictor` is removed once the game starts.** It exists only in the `pre` state, so it cannot be read after the fact and a post-start reader cannot see a different number there. It also means it is **not backtestable from ESPN's side**: it can only be recorded forward, which is why this is a recorder and not a download.
2. **The core `predictor` stays after the game and carries a `lastModified`.** For college football and NFL the stamp is a BPI/FPI run time **hours before the kickoff** (2026-10-31T11:00Z for the 16:00Z to 19:30Z college games, 09:00Z for the NFL games) and **was identical for games already in progress and already finished**, so the football figure was not changed after the start in the samples seen. Its description reads "Team's predicted win percentage in this game at time of given BPI run". The values agree between the two endpoints (UGA 81.76 core, 81.8 summary).
3. **NBA: the `lastModified` is not a usable clock.** It read 22:00Z both for PHI@CHA (not started; 22:00Z is its start) and for POR@UTAH (in progress since 19:00Z), a time in the future at the moment of fetching. NBA also has only the AWAY team's statistics populated (`gameProjection` and `teamChanceLoss`); the home figure is the away team's `teamChanceLoss` (matches the summary: CHA 40.6 = PHI's chance of loss 40.577). I could not show from one day whether the NBA figure moves after the start. **NBA is kept, with the audit moved to our own clock** (below), and the verdict does not rest on `lastModified` for NBA.
4. **No timestamp on the HTTP response that proves when the value was generated**; `lastModified` (football, MLB) is the only generation time, and the in-play probability series (not used here) is known to be rewritten after the game (ESPN1 check: core `lastModified` on those rows is a post-game batch rewrite).
5. **Not shown, and not claimable from one day:** whether the BPI/FPI run for a given game is re-run between 120 and 30 minutes before the start (injury news). The recorder stores every poll, so the first change is visible.

**Look-ahead design (the audit).** The recorder stores the **raw ESPN response** (core `predictor`, and the summary's `predictor` block while the game is `pre`) for every poll with the **recorder's own receive time** and the Kalshi server `Date` header. Because every figure used is a forward recording received before the start, a post-start or retroactively edited value cannot enter the look (it would carry a receive time after T-60 and be excluded by the look rule). Audits at the read, none a try: (a) every game's look has an ESPN receive time at or before its T-60 and before the ESPN start; (b) for football and MLB the stored `lastModified` is before the start; (c) the results step re-reads the core predictor after the game and the read reports how often it differs from the look value (it should be 0 for football and MLB; any other rate for NBA is reported and a rate above 5% drops NBA from the verdict as post-start-updated); (d) no value whose receive time is later than the look is used.
**Sports dropped:** none dropped at registration. **If the (c) NBA check exceeds 5%, NBA is dropped from the verdict and the read says so.** MLB cannot be audited in season before the stop date (no games) and is therefore out of the read by construction.

**pE(team)** = that team's `gameProjection` / 100 from the core `predictor` (for NBA the home figure is the away team's `teamChanceLoss` / 100). For the Brier comparison both ESPN and Kalshi are normalised to sum to 1 over the two teams (the NFL pair sums to about 0.997 because of ties).

## Data and results
- Quotes and ESPN raw: forward recorder (workflow + script, `quote-data` branch, folder `sportspre/`, see the recorder header). 
- **Outcome:** Kalshi `result` on the market after settlement (public `GET /markets/{ticker}`), the primary; ESPN's final status and scores (scoreboard `events` by date, `status.type.completed`) as a cross-check. A game where they disagree, or that is postponed, voided or not settled by the read, is counted and left out.
- **Stop date: 2026-12-31 (UTC).** Games with an ESPN start before 2026-12-31 00:00 UTC are tracked; the recorder tracks nothing that starts later and finishes recording results by 2027-01-01 06:00 UTC.
- **Read date: 2027-01-01, once, after 12:00 UTC (6 AM CT).** The verdict is not looked at earlier; an information look before is allowed only for counts and coverage, never for a PF or a Brier.

## Window, halves, unit
The tracking window is about 60 days from the day the recorder is merged and started (the owner merges). Halves: the games of the first and the second 30 days (by ESPN start date, split at whole days). Independent unit: the game; the clustering unit for z is the UTC calendar day of the start (same-day games in one sport are correlated).

## Numeric prediction (before any row)
Try A: profit factor **0.95** (range 0.80 to 1.10), **400 to 600 trades in 60 days** in season (NFL, college football, NBA; no MLB). Market Brier lower than ESPN's. Try B: PF 0.95 (0.8 to 1.1), more trades.

## Kill rules (numeric, any one is FALSIFIED)
1. **The market's Brier score at or below ESPN's Brier score** over all universe games with a look (the likeliest outcome).
2. **PF under 1.2 in either 30 day half** (after fees at C = 10).
3. **Fewer than 200 trades** in the tried rule: NOT_ENOUGH_DATA (for Try A and Try B separately).
4. **Day-clustered z of net per trade under 3** at the read.
5. **Deflated bar:** running N about 728,696 (728,694 after DERIBIT-IMPLIED, plus these 2 tries), one-sided z bar **about 5.27**; a try with day-clustered z under 5.27 is FALSIFIED at the bar even if rules 1 to 4 are passed.
6. Positive PF is also required at fees x 1.2. 
Result words: FALSIFIED / NOT_ENOUGH_DATA / NOT_YET_FALSIFIED (all of the above passed; earns only a registered forward test, never a live rule). A mean above +3c per contract is an audit trigger first: check the look, the receive times, the outcome source.

## Disclosure: what was looked at before writing this
On 2026-10-31 between about 19:40 and 19:50 UTC: the ESPN scoreboards of the four leagues (statuses, start times, team names); ESPN `summary` and core `predictor`/`probabilities` responses for 8 games (3 college football, 2 NFL, 2 NBA, 1 finished MLB) to see which fields exist; the open Kalshi market lists of the four series (field names, a few quotes: MIA/LAL 0.51 to 0.54, PHI/CHA 0.49 to 0.52 with PHI's ESPN figure 59.4, BUF/MIN about 0.42 to 0.45 YES for MIN). **No outcome, no settled price, no historical gap and no Brier score was computed.** The PHI@CHA gap was visible by eye while checking field names; for that reason games that start before 2026-11-01 00:00 UTC are excluded from the read. No threshold was chosen after seeing anything: 6c, C = 10, T-60, spread 2c are the proposal's.

## Count
2 tries (Try A, Try B). Running count about 728,696.
