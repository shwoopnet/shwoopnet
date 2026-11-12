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
| In-game lag, step 1 (measurement) | about 60 | 0 |
| In-game lag, step 2 (only if step 1 survives) | about 400 to 500 | 1 |
| NHLOT price measurement | about 60 | 0 |
| NHLOT test (only if the measurement survives) | not known until the historical endpoint is probed; at worst about 3,000 | 1 |
| ECONLAG (already registered) | 10, then at most 380 with stop rules | 1 against the paper screen |
