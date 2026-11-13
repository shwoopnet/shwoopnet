# Idea Desk B, short second wave in fast families (Nov 12, 2026)

Asked for by the Head of R&D: at most 4 cards, only in families with 300 or more independent events a year, with the request count each needs. **Result: 1 card.** The other candidates were duplicates of tests already run or sit in families already closed, and they are listed at the end so nobody repeats them. Nothing was scored and no Kalshi request was made for this file.

## A rule of thumb that removed most candidates before any data

At the research bar (cash PF 1.5), a bet held to settlement has to win much more often than its price says:

| Price paid | Win rate the price implies | Win rate needed for PF 1.5 after the fee |
|---|---|---|
| 10c | 10% | 15% |
| 30c | 30% | 41% |
| 50c | 50% | 62% |
| 70c | 70% | 79% |

So a mid-priced bet needs about 9 to 12 points of error in the market's price, every time. A crowd bias (overs, popular teams, round numbers) is worth 1 to 3 points and cannot get there. Only two kinds of idea can: the market has not yet priced a public fact, or the market is using the wrong model after the situation changed. The card below is of the second kind.

## Card 17. NHLOT: overtime resets a hockey game to a coin flip

`NHLOT | family: state reset, the pre-game favourite is still priced as a favourite after the game has become close to a coin flip; entry on the underdog at the start of overtime, hold to settlement (minutes) | risk class: mid price (about 35c to 46c), 1 contract, about 290 events a year, no link to the gold or Bitcoin strategies | stage Idea`

- **Mechanism in one line.** A regular-season NHL game tied after 60 minutes is decided by five minutes of three-on-three sudden death and then a shootout, which is far closer to a coin flip than the full game was; if the moneyline still leans on the pre-game favourite, the underdog is cheap.
- **Who is on the other side, and why they might lose.** Holders and makers who carry the pre-game strength of the favourite into overtime. Honest counter: this is well known to anyone who prices hockey, and the makers on these markets are professionals. I expect the price to be within a few cents of even.
- **How overtime is seen without a score feed (the new part).** No outside sports data is allowed. But when regulation ends tied, the game's total-goals markets stop being uncertain: either the total is final, or exactly one more goal will be added, depending on the rules text. So every total strike goes to about 0c or 100c while the moneyline is still near the middle. In regulation that combination cannot happen until the last seconds. **Detection rule:** every listed total strike of the game is at 4c or lower or 96c or higher, and both moneyline mids are between 30c and 70c. It uses Kalshi's own sibling markets, a different field with different logic, not the same price at another time.
- **Rule a one-minute bot could follow (proposed, not registered).** At the first minute the detection rule holds, and again one minute later if not filled: buy the pre-game underdog (the team whose moneyline mid was lower at the scheduled start) at its ask if the ask is 43c or lower and the spread is 3c or less. One contract, one entry a game, hold to settlement. Regular season only (playoff overtime is full-strength hockey and is not a coin flip).
- **Closest existing, and why this differs.** SWING1 (buy the faller after a 25c in-play drop: a price swing, no state change, FALSIFIED), ESPN1 (an outside win probability, FALSIFIED), the in-game lag card (a stale sibling quote, a time exit). This one buys on a change of game state that sibling markets reveal, at a mid price, and holds for minutes. Not favourite-late (it buys the underdog), not a lock (it can lose), not on the declined list. If "in-play sports" is ruled one family with two falsified tests, this would be its third and last test; the Head should rule on that first.
- **Data and terms.** Kalshi's own public data only (settled market lists, one-minute candles), through kalshi-pull. No outside host. Rules text of the NHL total series to be read first (does the total include overtime and the shootout goal): it does not change the detection rule, only its explanation.
- **Cheapest test: a price measurement first, zero tries, about 60 requests.** This season's settled NHL games (about 270 so far; about 60 should have gone to overtime): the settled lists of the game and total series (about 6 pages), then one-minute candles of the two moneylines and every total strike for the last 45 minutes before each game closed (about 10 markets a game, batched, about 50 requests if the batch endpoint serves them). Measured: how often the detection rule fires, and the underdog's ask at that minute. No outcome is read.
- **Kill rule for the card, fixed now:** if the underdog's ask is 43c or lower in fewer than 30% of detected overtimes, the market already prices overtime as close to even, there is nothing to buy, and the card is CLOSED with no try spent. Also closed if the detection rule fires in fewer than 12% or more than 35% of games (it is then not detecting overtime; about 20% to 23% of games go to overtime).
- **If it survives: 1 try,** on date constants: development = games of the 2025 to 2026 season if Kalshi's history holds one-minute candles for them (about 1,300 games, about 290 overtimes; request count not known until the historical endpoint is probed, at worst about 3,000 single requests, three runs), held-out = this season's games from a pinned date.
- **Power line.** About 290 independent events a year. At a price of 43c the bar needs the underdog to win about 55% of overtimes; published hockey results put the weaker team near 46% to 48%. A true PF of 1.5 would need about 960 bets (over three seasons); a true PF of 2 about 320 (one season plus history). **Honest reading: even if the price measurement survives, the bar is reachable only if the market misprices overtime by 10 points or more, and I do not expect that.**
- **Time to settlement:** under 20 minutes. **Time to a verdict:** about 2 days for the price measurement after the pull runs. **Probability:** 2% that it reaches the bar; about 75% that the price measurement closes it at once.
- **A later version, not a separate card:** extra innings in baseball (the runner-on-second rule), in season from April, if a detection rule from Kalshi's own markets can be found.

### Card 17, added Nov 12 after the Head of R&D's rulings (before any NHL data was pulled)

**Ruling (Head of R&D, Nov 12):** in-play sports is NOT one family; a family is the entry mechanism plus the exit style (lifecycle 7f). The two falsified in-play tests are still a prior against this card. Daily weather "forecast against market" IS closed under the three-falsified rule.

**The earlier in-play tests, one line each** (full table with sources: section 7 of `IDEA_DESK_B_INGAME_CARD.md`):

| Test | Entry mechanism | Exit style | Verdict and n |
|---|---|---|---|
| SC1 | the market's own 5c jump in play, follow or fade (tennis) | time exit, 2 or 5 minutes | FALSIFIED, four rules, 62,747 events, about -4.3c a trade |
| ESPN1 | an outside win-probability feed against the ask, in play | hold to settlement | FALSIFIED, 4 of 4, 1,613 games |
| SWING1 | buy the faller after its own 25c drop in play | hold to settlement | FALSIFIED, 302 trades, PF 0.99 and 1.06 |
| INPLAY1 | the outside feed at 3 times the ask, cheap side | hold to settlement | NOT_ENOUGH_DATA, 30 trades, 0 wins |
| SERIESLAG1 rule | series market after a game ends, fixed coin-flip model | hold to the series result | NOT_ENOUGH_DATA, 44 trades, PF 0.21 |
| NHLOT (this card) | a change of game STATE read from sibling markets, buy the cheaper side | hold to settlement, minutes | not read |

**The price measurement is APPROVED; nothing beyond it is.** Zero tries, no outcome read.

- **Script:** `workers/nhlot/measure_prices.py`, committed with this section and self-tested on made-up data. **Jobs:** `workers/desk_b_jobs/NHLOT_LISTS.json` (4 requests, at most 9 pages, cap 10, passes the pull script's check) and `NHLOT_CANDLES.json` (not runnable until built from the lists by `workers/nhlot/build_candles_job.py`). Requests: 4 for the lists, then about 40 to 150 for the candles, depending on how the games' close times cluster (changed Nov 12 from a cap of 50: with requests no longer scarce, the 150 game sample is never cut to save them). The whole chain was run end to end on made-up data before any pull.
- **Three details fixed now, each a small change from the card text above:**
  1. **The underdog is the side with the lower ask at the detection minute,** not the pre-game underdog. It is the market's own lean in overtime, which is the thing being measured, and it needs no pre-game price.
  2. **A total strike counts as decided** when its YES bid is 93c or higher or its YES ask is 7c or lower (the card said 96c and 4c; a decided market often shows only one side of its quote, so one side is tested and the line is a little wider). At least 4 strikes must have a quote that minute, none undecided, at least one decided each way, and both moneyline mids between 30c and 70c. Only the last 45 minutes before the game market closed are searched.
  3. **Sample:** the 150 most recently settled regular-season games, never extended. **Under 30 detections is NOT_ENOUGH_DATA.**
- **Kill rules, unchanged:** CLOSED if the cheaper side can be bought at 43c or lower (spread 3c or less, at the detection minute or the next) in fewer than 30% of detections; CLOSED if the rule fires in fewer than 12% or more than 35% of games.
- **What the script never does:** it reads no result field and no minute later than one minute after detection.
- **Amendment, Nov 12 at 17:30Z, before any NHL list or candle was pulled (a cross-check only).** The Nov 10 census listing showed a market this card did not know about: "game goes to overtime" (`KXNHLOT`, one market a game). The candle job now also asks for that market's candles (one more ticker a game, built by name from the game's own ticker), and the reader prints, for games the detection rule flags and for games it does not, what that market showed at those minutes (says overtime, says no overtime, undecided, no quote). **Detection, the price that is measured and both kill rules are unchanged.** The cross-check only says whether the rule built from total-goals strikes is really finding overtime. If that market did not exist for older games, its line reads "no quote" and nothing else changes. The reader also prints the candle freshness line the Head of R&D required. Chain re-run on made-up data after the change; the built job still passes the pull script's own check.

## Not cards: two pointers for the queue

1. **COMBOPRICE1 is an orphan too.** V2 designed a test of a combo's price against the prices of its own legs (`workers/COMBOPRICE1_DESIGN.md` on V2's branch). It needs the leg tickers the combo recorder does not store yet. When Main adds them it can run on `combo-data` with zero reads. It is V2's design, not a new card of mine.
2. **One more line to read on Nov 26, as description only.** The combo recorder stores printed trades with the taker's side. Where the taker bought YES, the maker took the house side at that price. The settled result of those prints measures the house's real margin where the volume actually is, which says whether S3's premise (parlay buyers overpay) holds on Kalshi at all. It is not a strategy we can run (it is the maker's seat), it is not a try, and it is read only on or after Nov 26, with the recorder's own stop rule.

3. **RAINCAL is RETIRED, unread (Head of R&D, Nov 12). Do not revive it.** V2 registered it on Oct 31: daily rain markets against the NWS probability of precipitation, buy when the price is 8c or more away from the forecast, hold to settlement. By its own mechanism it sits inside the closed forecast-against-market family. Its recorder (`record-rain.yml`, still running on Nov 12) caught 163 of about 385 possible city-days from Nov 2 to Nov 12, about 42%, so its own minimum of 150 trades was in doubt; V2 itself predicted a profit factor of about 1.05; and whatever it read, it could not have opened a card. Its 2 tries stay counted and its data stays on `quote-data` under `raincal/`. The Head has recommended to Main, for the owner's word, that the recorder be deleted. It was never read.

## Examined and dropped (so nobody repeats them)

| Family the Head named | What I looked for | Why there is no card |
|---|---|---|
| Daily weather city-days | forecast against bracket, neighbouring city's forecast miss, the evening low | The family has four falsified tests already (WX1 twice, WX3, WXDEAD1) plus RAINFACT1, and WXLOW1, RAINCAL, WXPRIOR, WXREVISE and WXDAYEND are registered by others. Every idea I had was a forecast-against-market rule again. Under the three-falsified rule the family looks closed; the Head should rule |
| Daily approval | the daily settled value against the bracket prices | ROLLOFF was killed today. Calibration (APPROVAL1, Refinement's approval calibration) and the NO side (S1, W-NO-ARM1) are owned and running. A persistence rule is the closed persistence-against-ladder mechanism, and a late entry is favourite-late |
| Sports games, before the game | over and under bias, popular teams, moneyline against spread | Calibration is done (SPORTS_CAL), consistency is done (SPORTCONS1), the spread cell is registered (S2). A bias of 1 to 3 points cannot reach PF 1.5 at a mid price (table above) |
| Sports games, in play | lag (card sent today), overtime (card 17) | two cards in all |
| Hourly and 15 minute ladders on recorded books | anything with a new input | Price, time, regime, flow, depth, lead-lag and lock rules are closed without a new data source. The new sources that exist (options, liquidations, spot feeds, perps) are each already registered by V2 or Refinement. A news-count signal (GDELT, updated every 15 minutes) would be new, but news follows price at this horizon and I would be padding to card it |

## Request counts, in one place

| Item | Requests through kalshi-pull | Tries |
|---|---|---|
| In-game lag, step 1 (measurement) | 215 used (two runs) | 0. CARD CLOSED Nov 12: no drift after the first minute |
| In-game lag, step 2 | not run | 0 (its try was not spent) |
| NHLOT price measurement | about 60 | 0 |
| NHLOT test (only if the measurement survives) | not known until the historical endpoint is probed; at worst about 3,000 | 1 |
| ECONLAG (already registered) | 10, then at most 380 with stop rules | 1 against the paper screen |

## NHLOT: dated amendment, Nov 13, 2026, 00:09Z, before any NHL candle was read (Auditor B's three findings on the reader)

1. **Hindsight in the search window, labelled, not hidden.** The reader looks for the overtime state only in the last 45 minutes before the game market closed, and the close is known only afterwards. Inside that window it scans forward and takes the first qualifying minute. The candles already pulled are anchored on the close, so this cannot be changed for this measurement; the reader now prints the label and the number of detections that fall in the window's first 5 minutes (where the state may have begun earlier). This stays a zero-try price measurement with no bet and no outcome. **A rule registration would need candles anchored on the scheduled start, and that is written here as a condition.**
2. **"Buyable" is no longer the best of two minutes.** The registered verdict now reads: the cheaper side's ask is 43c or lower with a spread of 3c or less at the detection minute, AND a limit one cent above that ask is filled the next minute (the SAME contract's ask one minute later is at or under the limit). The earlier "at the detection minute or the next" figure is printed beside it, labelled optimistic. The 30% line and every other number are unchanged.
3. **The reader refuses a HELDOUT_ folder** (the shared guard of this desk, added the same night).

## NHLOT: second dated amendment, Nov 13, 2026, 00:10Z, before any NHL candle was read (Head of R&D's ruling of 00:09Z on Auditor B's findings). It replaces point 2 of the amendment above.

1. **One price, one chance.** "Buyable" is the cheaper side's OWN contract (the side that was cheaper at the detection minute) at its ask ONE MINUTE AFTER the detection minute: 43c or lower with a spread of 3c or less at that minute. Not the detection minute's price, and not the better of two. The earlier best-of-two figure is still printed, labelled optimistic.
2. **Every line the reader prints carries the label "hindsight window: detection uses the close time; upper bound, not a live rule".** The fire rate and every price are from a window that ends at the game's close, which a live bot cannot know.
3. **No rule is registered from this measurement** without a detector that scans forward from the game's scheduled start with no close time, on games the measurement did not use. The 150 most recent games are its whole sample, so it has no held-out.
4. Its pull is moved behind the WHEEL0 files and the INPLAYJUMP candles (the Head's order), because as built it cannot produce a candidate.
5. **Said plainly for the owner's count:** NHLOT and MAPBREAK are one candidate. MAPBREAK is out on CS2 and short of its minimum elsewhere until the rest of its candles are read; NHLOT has no live detector. That candidate stands at "no evidence".

## NHLOT: clarifying line, Nov 13, 2026, 00:16Z, before any NHL candle was read (Auditor B's grep; Head of R&D's order)

Every comparison against a registered line in the reader carries a tolerance of 1e-9, with a value exactly on the line kept on the registered side: the moneyline band edges are inclusive, a strike at exactly 0.93 or 0.07 counts as decided, the 12% and 35% fire-rate edges are inclusive, and a share of exactly 30% is NOT closed. No number and no rule changed.


## NHLOT: third dated amendment, Nov 13, 2026, 05:33Z, before any NHL candle was read (the second build's findings; the Head of R&D's ruling, seq 9, 05:31Z)

The History Miner built a second reader from this card's text alone (commit 25e1c43e on `claude/history-miner`) and printed it on nine made-up cases before comparing. Games, usable games, detections, the median and lowest ask and all nine verdicts agreed. Three points differed, and one of them reached a registered figure: on one case the buyable share was 19 of 33 in the second build and 20 of 33 in the first. **Here the CODE moves to the TEXT, not the text to the code: the difference reaches a registered figure and the text's words favour the second build.** The first reader (sha256 ff3e4811...) is changed to what follows; the readings are the History Miner's.

1. **"The last 45 minutes before the game market closed"** is the candles whose end time is after the close minus 2,700 seconds and at or before the close: 45 one-minute candles. (The first reader searched 46: it also took the candle ending exactly 45 minutes before the close.) The scan runs forward and takes the first qualifying minute.
2. **"The first 5 minutes of the window"** is a detection at a candle ending at or before the close minus 2,400 seconds.
3. **The overtime market cross-check (information only; no line reads it).** For a game the rule detects: the overtime market's candle at the detection minute. For a game it does not detect: that market's last candle inside the window. It "says overtime" at a YES bid of 0.93 or more, "says no overtime" at a YES ask of 0.07 or less, is "undecided" with a quote that is neither, and has "no quote" with no candle or a candle showing neither side. (The first reader used 0.90 and 0.10, the detection minute and the next, and every minute of the window.)
4. **The median and the quartiles** of the cheaper side's ask are by linear interpolation at (n minus 1) times p on the sorted asks (the median of an even count is the mean of the two middle values). Information only.
5. **The cheaper side** is the moneyline ticker with the lower ask at the detection minute; with equal asks, the ticker that sorts first as a plain string.
6. **A side missing from a candle is never carried from another minute.** A total strike with no candle that minute, or a candle with neither side, has no quote that minute and does not count toward the four; a strike showing one side counts and is decided only by the side it shows. A moneyline mid needs both sides that minute. "Buyable" needs both sides at the candle one minute after the detection minute.
7. **A usable game** is one where both moneyline tickers have at least one candle anywhere in the answers.
8. **The run is read by its manifest, whole or refused:** the run must be complete, every request of its job must have an answered row (status 200, not cut short), each stored answer is unpacked and checked against the manifest's sha256 and length where the manifest gives them, and every file must lie inside the run folder. A file that cannot be read stops the reader; it is never skipped.
9. **Order of the verdict:** fewer than 30 detections is NOT_ENOUGH_DATA first; then the fire rate (12% and 35% inclusive); then the buyable share (exactly 30% is not closed). The shares are printed only with 30 detections or more and the fire rate in range.

No kill number changed. The measurement is still a hindsight measurement with zero tries, and as built it cannot produce a candidate (second amendment, point 4).

## NHLOT: fourth dated amendment, Nov 13, 2026, 05:37Z, before any NHL candle was read (Auditor B's finding; the Head of R&D's ruling, seq 11, 05:40Z)

Kalshi's candles do not leave an empty side out: they show a bid of 0.00 or an ask of 1.00. The reader and the third amendment's words "a candle with neither side" took those numbers as sides that are present. **Ruling: a bid of 0.00 is NO bid and an ask of 1.00 is NO ask, everywhere in this measurement. A side exists only when its bid is above 0 or its ask is below 1; a mid needs both sides, with the bid not above the ask.** This is the same reading the other texts of this desk use for a two-sided quote (0 < bid < ask < 1). Comparisons carry the 1e-9 tolerance. Points 3 and 6 of the third amendment are read with it. The auditor's three worked cases:

1. **A total strike whose candle shows 0.00 and 1.00** has no quote that minute. It is not an undecided strike and does not block the detection; it also does not count toward the four. (Before: it counted as undecided, and a detection due 44 minutes before the close moved to 43.)
2. **A moneyline side showing a bid of 0.30 and an ask of 1.00** has no ask, so no mid, and the moneyline condition fails at that minute. (Before: its "mid" of 0.65 sat inside the band and the game was detected on a side nobody was offering.)
3. **The overtime market's candle showing 0.00 and 1.00** reads "no quote", not "undecided".

"Buyable" needs a bid above 0 and an ask below 1 at the candle one minute after the detection minute, as before. Also said here, not a change: the pull runner writes the sha256 and the length of every stored answer, the reader checks them when the manifest carries them, and Auditor B's structure check of the landed run checks them in any case. No kill number changed.

## NHLOT: held-out line, Nov 13, 2026, 07:06Z, before any NHL candle was read (the Head of R&D's order of 06:53Z). No rule, figure or reading changes.

The sample is unchanged: the 150 games of `nhlot/games.json` (closes 2026-10-21T04:35Z to 2026-11-12T06:01Z), series KXNHLGAME, KXNHLTOTAL and KXNHLOT. It is a price measurement: no result is read and no rule is scored. Every card found that ever held out these series, with its state:

- **W-CAT-SPORTS1 (Refinement):** KXNHLGAME and KXNHLTOTAL among its 27 series, held-out closes at or after 2026-10-30T02:53:19Z, never read. **Released by the Head of R&D 2026-11-13 (dated line in its registration on `claude/refine-live`, 06:51Z). Development here.**
- **TIE3 (Testing Desk; closed on two builds):** KXNHLOT held-out from 2026-11-13T00:00Z, never listed or requested. This sample ends 2026-11-12: no overlap.
- **FAMSPORTS (research chat, run once 2026-11-03; both tries FALSIFIED, closed):** KXNHLTOTAL, 91 eligible hockey games to 2026-11-02; its last third by game date (W3) is unread and nothing can read it now (W3 opens only if the first two windows pass, and they failed). **W3's dates are not printed; it is the latest third of 190 games that end on 2026-11-02, so it lies partly or wholly inside this sample's first days (Oct 21 to Nov 2).** A closed card; named here so the Head of R&D can see it before releasing the job.
- **USWEEP2 (research chat, generic cheap-tail sweep, run once 2026-11-03, "no lead"; closed):** KXNHLGAME is on its frozen series list (not among its scored results); for each series the last third of its anchor dates was frozen and never fetched. The dates are not printed; for a sweep run on Nov 3 they most likely fall inside this sample. A closed card, named for the same reason.
- **SERIESLAG1 (research chat, registered 2026-11-08, no result on its branch):** uses KXNHLGAME for playoff games of April to June 2026 only. No overlap in dates.
- **HISTDEPTH (History Miner plan):** KXNHLOT on the historical endpoint, closes before about 2026-09-07. No overlap.
- Named these series but hold nothing out on them: ESPN1 (hockey absent from its data), NHLG1 (its frozen third is on the goal-scorer series only), SP1 and SPORTS1 F7 (October tests with no held-out window), W-SPREAD-CELL1 (spread series only).

No OPEN card holds any of the three series inside the sample dates. Two CLOSED research-chat cards (FAMSPORTS, USWEEP2) have unread held-out that overlaps it.

**What was swept:** as in the hourly temperature note of the same minute (whole-word names over main, `rnd-queue`, the desk branches, `claude/refine-live` and the research chat's whole tree at 79724f00; the research chat's sports registrations read by hand because it writes series as patterns). The same limit applies.

**NHLOT: cross-check against the held-out registry, Nov 13, 2026, 07:10Z** (`HELDOUT_REGISTRY.md` on `rnd-queue` at ad42ec54, Desk A's lookup; its states are conservative and mostly taken from file names). Its table of series gives KXNHLGAME: ESPN1, NHLG1; KXNHLTOTAL: FAMSPORTS, NHLG1; KXNHLOT: TIE3. Its states: ESPN1 READ (spent); NHLG1 READ (spent), frozen cut 2026-10-03T16:00Z (on the goal-scorer series, as the line above says); FAMSPORTS READ (spent), which does not contradict the line above (its own result says W3 is unread); TIE3 CLOSED UNREAD; W-CAT-SPORTS1 RELEASED; W-SPREAD-CELL1 READ (spent). **One disagreement for the Head of R&D to rule: the registry marks USWEEP2 OPEN, and does not list any series for it.** My reading of the card itself: its frozen series list holds KXNHLGAME; its rule says "run once" and "FALSIFIED as a family if no cell clears the bar"; its result says 0 cells meet the lead rule and the frozen last thirds were never fetched. I called it closed in the line above; whether it counts as closed is the Head's call, and the candle job is not released until they say. SPORTCONS1 (registry: OPEN) covers football and basketball only and holds none of these three series.

**NHLOT, Nov 13, 2026, 07:11Z: FAMSPORTS and USWEEP2: reservations released by the Head of R&D, 2026-11-13 07:09Z; development here.** (The Head's message of 07:11Z; the dated line is in `RND_QUEUE.md` on `rnd-queue` at 0f7bfccb, where it is stamped 07:08Z: FAMSPORTS, its last third by game date; USWEEP2, the frozen last third of every series on its list. Both are closed with nothing that could read their held-out.) The disagreement noted above is settled by that line. The sample and the reader are unchanged.

## NHLOT: CLOSED at the price measurement on two builds (Nov 13, 2026, 08:17Z; the Head of R&D's ruling and record of 08:19Z by their clock). No bet, no outcome, no try spent.

**The dated line that pins two information-only lines (no code moves, no registered figure is touched).** The read is made; the two builds differ on two lines that the card's text did not settle, so both readings are written here side by side:
1. **Detection minute, minutes before the game market closed:** 9.5, range 3 to 19, in whole candle minutes (my reader); 9.87, range 3.58 to 19.83, by the clock in seconds (the second build), which is the truer distance, every close in this run being 17 to 29 seconds past the minute.
2. **Optimistic best-of-two share:** 6 of 34 = 18%, re-choosing the cheaper side at the next minute (my reader, as the first reader did); 4 of 34 = 12%, keeping the side chosen at the detection minute (the second build), which is the stricter reading.
Under either reading the share is under the card's 30%. If this card is ever registered again, the stricter readings go into the new text.

**The record.**
- Run: `pull/NHLOT_CANDLES/2026-11-13T0802Z_43390050891/` on `kalshi-pull-data` (86 requests, 1,988 tickers, 90,000 candles; job sha256 a019a029d1c94f0e79f794ca424b987352aa7de49cc2d72a529b6ca6e406d8d9), structure-checked by Auditor B before it was opened. Games: `nhlot/games.json` (2b403841), 150 games closing 2026-10-21 to 2026-11-12.
- Two builds on that one run: `nhlot/measure_prices.py`, sha256 7d3b67310ba1e05653b0f725451abf55f106e475f6e1d3ba0c7f5a8266918e31, audited CLEAN (printed lines `nhlot/real_read/desk_b_printed_lines_2026-11-13T0802Z.txt`, sha256 d78f2fd7); and the History Miner's `nhlot2.py` (649f8aad), built from this card's text only, run blind, its printed lines committed first at 954214a5 on `claude/history-miner` (output sha256 56ee6eed).
- The same in both: 150 games, all with moneyline candles. A tied late game is detected in 34 of them, 22.7%, inside the card's 12% to 35%. The cheaper side's ask at the detection minute: median 0.49, quartiles 0.47 to 0.50, lowest 0.42; at 0.43 or lower in 2 of 34. **The registered line: the cheaper side's own contract buyable at 0.43 or lower (spread 0.03 or less) one minute after the detection in 4 of 34 = 12%, against the card's 30%.** The overtime market's cross-check agrees with the detections (it says overtime in 6 of the 34 and in none of the 116 others; the rest undecided or no overtime).
- **Verdict: CARD CLOSED.** When a tied late game is visible in the prices, the underdog is already quoted near even, so the state the card hoped to buy below its worth is not on offer. All of it sits inside the hindsight window the card states (the search is anchored on the close time, an upper bound, not a live rule), and it is a price measurement: no result was read, nothing was bet, no try was spent.
- Requests used by this card: the lists (through TESTING_LISTS_BUNDLE and NHLOT_LISTS) and 86 candle requests.
