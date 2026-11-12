# In-game lag between related markets: one card for the Head of R&D (Idea Desk B, Nov 12, 2026)

**Status: a CARD, not a registration. Nothing was scored.** No trade result, no lag measurement and no profit figure was computed. The counts below are an inventory of what the recorder holds (games, polls, gaps, how often the trigger event occurs, how wide the side markets are). The Head of R&D decides whether it is registered.

`INGAMELAG1-M | family: cross-market lag inside one game, entry on a stale side market, time exit | risk class: mid price, 1 contract, many small trades on game nights, uncorrelated with the gold and Bitcoin strategies by construction (to be measured) | stage Idea`

It is V2's orphaned INGAMELAG1 (`workers/INGAMELAG1_PROTOCOL.md` on `claude/epic-ptolemy-0amjd9`, registered Nov 8, forward, never read) rewritten for a bot that looks once a minute. It is a version of that card, not a second card.

## 1. What V2 registered, and what happened to it

- **INGAMELAG1 (Nov 8, Kalshi data only):** inside one NBA game, when the moneyline mid moves 8c or more in 3 minutes, buy the moving team's spread YES if it has moved under half of what a fitted slope says it should, ask 3c to 30c, exit at the bid 10 minutes later. Fit on the first 40% of events, development the next 30%, held-out the last 30%. NOT_ENOUGH_DATA under 150 development trades or 60 games. V2's own prediction: makers re-quote within seconds, 96% that it fails. **Never read.**
- **A different idea under the same name (Nov 11):** lag of Kalshi quotes behind a live SCORE feed. Blocked on source terms (no free licensed score feed) and parked by the owner. This card does not touch it and uses no score feed.
- **SERIESLAG1 (Nov 8 to 9, Kalshi history):** lag of playoff SERIES markets after a game ends. Measurement on 25 clean events: the series market had made half of its jump one minute after the game ended, 62% at three minutes, 73% at five, 90% at ten. The one registered rule (cheap side, held to the series result): 44 trades, mean -12.97c, cash PF 0.21, NOT_ENOUGH_DATA. So a lag of minutes was seen once, on series markets, and the trade built on it lost.
- **Same family, already falsified:** SWING1 (in-play swing, cheap side: PF 0.99 and 1.06) and ESPN1. If "in-play sports" is counted as one family, it has two falsified tests and a third closes it for good. That is the Head's ruling to make before this is registered.

## 2. What the recorder actually holds (branch `sports-data`, read Nov 12, 15:30Z)

| Item | Count |
|---|---|
| Recording span | Nov 8, 23:55Z to Nov 12, 12:00Z: 84.1 hours |
| Hours with no polling at all (gaps over 10 minutes) | 15.8 hours (19%) in 8 gaps, every one at a 4 hour job boundary; the two largest were 6.2 and 4.8 hours on Nov 9 |
| Rows | 727,364 |
| Games listed and polled | 161 (NHL 68, NBA 60, NFL 33), including games up to 11 days ahead |
| Games that finished inside the recording (moneyline reached 97c or 3c) | 35 (NBA 22, NHL 11, NFL 2) |
| Of those, games with 90% or more of the last hours covered | 24 (NBA 16, NHL 7, NFL 1) |
| **Time between polls of one game while it was being played** | **median 128 seconds** (NBA 128, NHL 128, NFL 132) |
| Share of in-play time polled every 45 seconds or faster | about 0% (median game), 1% to 4% overall |
| Trigger events as V2 defined them (moneyline mid moved 8c or more against 3 to 4 minutes earlier), in the 35 finished games | 25 events in 11 games (NBA 15 in 5 games, NHL 10 in 6, NFL 0) |
| Side markets with a two-sided quote at least half the time in play | all four (two spread, two total) in the median NBA game |
| Width of the side markets in play (ask minus bid, median) | NBA spread 1c, NBA total 1c, NHL spread 4c, NHL total 3c |
| Games a week on the schedule (the recorder's own event dates, Nov 9 to 15) | 113 (NBA 51, NHL 48, NFL 14) |

**The recorder is not doing what it was built for.** It was specified at one poll every 20 seconds for a game that is "hot" and every 2 minutes otherwise, at most 8 hot games. In the data every listed game is polled at the same pace of about 130 seconds, whether it is being played now or is five days away (about 107 games were being polled at one instant on Nov 10). The request budget is spread evenly over the whole schedule, so a live game gets no priority. The result is a 2 minute picture of live games, which is COARSER than Kalshi's own 1 minute candles. This is an engineering matter for Main (for example: poll only games dated today, or raise the bar for "hot" so that a pre-game flicker does not count). Until it is fixed the recorder adds nothing that 1 minute candles do not give.

## 3. The rule a one-minute bot could follow (proposed, not registered)

The bot looks once a minute. A lag that is gone in under a minute cannot be traded by it, so every time in the rule is a whole minute.

- **Markets:** NBA and NHL games (NFL has about 14 games a week and no trigger event so far). The home team's moneyline, and the two spread markets nearest 50c fixed before the game starts.
- **Signal, at minute t:** the moneyline mid has moved 8c or more against its mid three minutes earlier, and was between 10c and 90c three minutes ago.
- **Expected move of the spread:** slope times the moneyline move, the slope fitted per sport on games before a pinned date and never re-fitted.
- **Entry, at minute t+1** (one full minute after the signal minute, so the bot has seen the move and acts on its next look): buy the moving team's spread YES at the ask if the part still owed (expected move minus the move already made) is 6c or more, the ask is 10c to 80c and the spread is 3c wide or less. One contract, one entry per game per 10 minutes.
- **Exit:** sell at the bid ten minutes after entry, or take the settlement if the game ends first. A time exit, the strategy's own.
- **Costs:** fee on both legs and 1c slip on both legs. At these prices the round trip costs about 4c in NBA (1c of width plus about 1.5c of fee a leg) and 6c to 7c in NHL. That is why the rule asks for 6c still owed, and why NHL may not clear its own costs.

## 4. Power line

- **Bar:** cash PF 1.5 on development and held-out and a one-sided z of 5.46 at about 2,113,000 tries. The unit is the game, not the trade.
- **Trades needed** for a time-exit trade with a spread of results near 6c: about 360 at a true 2c net a trade, about 160 at 3c (80% power).
- **Supply:** the trigger fires about 0.7 times a game (25 events in 35 games). Only a fraction of those can have 6c still owed one minute later. If that fraction is a tenth, it is about 8 trades a week from 113 games, and 360 trades take about 45 weeks. If it is a half, about 9 weeks. If makers re-quote in seconds, as V2 expected, it is zero and the card is dead.
- **So the fraction decides everything, and it can be measured without spending a try.** See the next section.
- From the recorder alone, at today's coverage (24 well-covered games in 3.5 days, about 48 a week), V2's own minimum of 150 development trades is not reachable before the recorder ends on 2027-01-31 unless most trigger events turn out to be tradable.

## 5. The cheapest test: a measurement first, with its kill rule written now

**Step 1, zero tries, about 60 requests through kalshi-pull.** One-minute candles (bid and ask closes) for the six markets the recorder followed in each finished game: two moneylines, two spreads, two totals. The tickers are already in the recorder's files, so no listing is needed. 35 games today; about 110 by Nov 19. Batched candle requests, roughly 9 games a request if the batch endpoint serves them (not verified for sports markets; if it does not, about 6 requests a game).

What is measured, and only this: for each trigger event, the share of the spread market's move over the following ten minutes that is already in its price at the end of the first full minute after the signal minute, and at minutes 2, 3 and 5. No entry, no exit, no profit.

**Kill rule for the card, fixed before the measurement:** if on 80% or more of trigger events the spread has already made 75% or more of its ten-minute move by the end of the first full minute, the lag is shorter than the bot's clock and the card is CLOSED with no try spent. Fewer than 40 trigger events in the sample: NOT_ENOUGH_DATA, wait a week and measure once more (two such results close the source).

**Step 2, only if step 1 survives: 1 try.** Register the rule of section 3 with date constants (slope fitted on games before the first constant, development to the second, held-out after it, read once). History is available from candles for every game already played this season, so the test does not have to wait for the recorder: lists of the settled spread markets (about 40 pages), a pre-game hourly candle to fix the two strikes nearest 50c, then the one-minute candles. About 400 to 500 requests, an estimate that depends on the batch endpoint's limits.

The recorder data already held could give a first look at no cost, but at 2 minutes a poll it cannot tell "gone in under a minute" from "still there after one minute", which is the only question that matters for this bot. So it is not the test.

## 6. Checks

- **Declined list.** "Lock and parity scans", which names the in-play twin-book LOCK (TWINLOCK1): not this. A lag rule takes a directional position and can lose; nothing is locked. "Cheap-side price, regime and grammar rules on the 15 minute series", which names lead-lag sweeps on those series: a different market type; this is one fixed rule on sports games, not a sweep. Favourite-and-hold: not this (mid prices, ten minute exit). The score-feed version: parked by the owner, not this.
- **Uniqueness (to be scored by the Verification Analyst, not by me).** Signal: the price of a DIFFERENT market in the same game, on a market type the bot does not trade. Exit: a time exit. Entry: after a move in another market, not a price band at a clock time. Correlation with the live strategies: not measured; game nights and the gold market share no driver I can name.
- **Who is on the other side, and why they might lose.** The maker of the spread market, if they update it more slowly than the moneyline. The honest counter: on Kalshi the same few makers quote all three markets of a game from one model, and V2 put 96% on "re-quoted within seconds". The SERIESLAG1 profile is the only evidence of a lag of minutes, and it is on series markets, which are quoted less closely.
- **What the bot would need (engineering, not research).** Quotes for the day's games every minute during games: about 3 public reads a game a minute, up to roughly 45 a minute on a busy night. Which exchange shard sports markets sit on, and the fee schedule of the sports series, have not been read.
- **Honest probability:** 3% that it reaches the bar; about 60% that step 1 closes it in a week at a cost of about 60 requests and no try.

## 7. The earlier in-play and sports-lag tests, for the family ruling (added Nov 12 at the Head's request)

Under lifecycle 7f a family is the entry mechanism plus the exit style. What each earlier test was, from V2's own registrations and results (branch `claude/epic-ptolemy-0amjd9`, `kalshi-scalper/`):

| Test | Entry mechanism | Exit style | Verdict and n | Source |
|---|---|---|---|---|
| SC1 (Oct 26 to 27) | In play, tennis match winner. A 5c jump in the market's OWN one-minute mid; four rules: follow it or fade it. Kalshi prices only, entry at the next minute's quote | Time exit: sell at the bid 2 or 5 minutes later | FALSIFIED, all four. 62,747 jump events; net -4.2c to -4.5c a contract, the same for follow and fade, so the loss is cost (two fees and two spread crossings), not direction | `README.md` "Pre-registration: SC1" and "Result: SC1" |
| ESPN1 (Oct 29 to 30) | In play, game winner (NFL, college football, NBA, MLB). Buy the side an OUTSIDE win-probability feed rates 8c or 15c above its ask, 180 seconds after the play | Hold to settlement | FALSIFIED, 4 of 4 variants. 1,613 games; PF 0.76 to 1.20, under 1.0 in the last two windows; Kalshi's mid was the better forecast | `workers/ESPN1_REGISTRATION.md`, `ESPN1_RESULT.md` |
| SWING1 (Nov 3) | In play, game winner (college football, MLB). Buy the faller after its own mid fell 25c in 5 minutes, ask 5c to 30c. Kalshi prices only | Hold to settlement | FALSIFIED. 302 trades; PF 0.99 and 1.06 | `workers/SWING1_REGISTRATION.md`, `SWING1_RESULT.md` |
| INPLAY1 (Nov 3) | In play, cheap side when the outside feed's probability is 3 times the ask, at fixed looks | Hold to settlement | NOT_ENOUGH_DATA. 30 trades, 0 wins | `workers/INPLAY1_REGISTRATION.md`, `INPLAY1_RESULT.md` |
| SERIESLAG1, the rule (Nov 8 to 9) | AFTER a game ends: buy the cheap side of the playoff SERIES market when a fixed coin-flip series model beats the ask by 5c, three minutes after the game market closed. Kalshi prices and a fixed model | Hold to the series settlement | NOT_ENOUGH_DATA. 44 trades, mean -12.97c, PF 0.21 | `workers/SERIESLAG1_PROTOCOL.md`, `README.md` "SERIESLAG1 result" |
| INGAMELAG1 as V2 registered it (Nov 8) | In play, NBA. After the moneyline moved 8c in 3 minutes, buy the moving team's spread YES if it moved under half the fitted amount, ask 3c to 30c. The signal is a DIFFERENT market of the same game | Time exit: sell at the bid 10 minutes later | Never read. n 0 | `workers/INGAMELAG1_PROTOCOL.md` |

What that says, without ruling:

- **Same entry mechanism and exit style as this card (a sibling market's move, a time exit): none before.** INGAMELAG1 is this card's parent and was never read.
- **In play, Kalshi prices, time exit: SC1 only**, one falsified test (four rules). Its signal was the market's own jump, not a sibling's. Its finding matters here all the same: a one-minute round trip at mid prices cost about 4.3c in tennis, measured. This card's estimate of about 4c for NBA spreads agrees with it, so the lag must be worth more than that.
- **In play, Kalshi prices, held to settlement: SWING1**, one falsified test.
- **In play, an outside probability feed, held: ESPN1** (falsified) and INPLAY1 (not enough data). A different signal source; that source is no longer permitted in any case.
- **After the game, series markets, held: SERIESLAG1**, not enough data and negative.

If the family is drawn as "in play on Kalshi prices" whatever the exit, it has two falsified tests (SC1, SWING1) and this card would be the third and last. If it is drawn by entry mechanism plus exit style, as 7f words it, this card's cell is empty. The Head rules after step 1.

## 8. Step 1 as approved, rebuilt ONCE on a longer fixed list (Nov 12, before any candle was pulled)

- **Approved by the Head of R&D:** the measurement only, zero tries. Step 2 is not approved. **One run, one answer:** the first version of the job (35 games from the recorder's files) was withdrawn before it ran, because it was expected to end as NOT_ENOUGH_DATA and a measurement must not be run twice on a growing list.
- **The fixed list: 215 games** (NBA 61, NHL 130, NFL 24): every NBA, NHL and NFL event in Refinement's committed list (`refine_tools/SPREAD_CELL1_EVENTS.json` on `claude/refine-live`) whose market closed from 2026-10-20 00:00 UTC to 2026-11-11 23:59 UTC. That file was used for tickers and close times only; no price and no result was read from it. The list is `workers/ingame_m1/games.json`, committed with this section. At the recorder's rate of about 0.7 triggers a game this should give well over the 40 clean events the measurement needs (about 100 to 150 triggers).
- **Markets, chosen without any price:** both moneyline markets of each game (tickers derived from the team codes in the spread tickers, and checked equal to the recorder's on the 14 games both hold), and for each team its two lowest spread strikes in the list. This replaces "the two spread markets nearest 50c fixed before the game": picking by price would need a pre-game candle, which the guard below forbids, and the low strikes are the ones that are live when a game is close, which is when the trigger fires.
- **Job:** `workers/desk_b_jobs/INGAMELAG_M1.json`, built by `workers/ingame_m1/build_job.py`: **215 requests**, one batched one-minute candle request a game (3 to 6 tickers, about 4 to 5 hours ending at the market's close), cap 235. It passes the pull script's own check.
- **Guard (Head of R&D): in-play candles only.** These spread markets are also the unread sample of Refinement's W-SPREAD-CELL1, whose look is 48 hours before the game. `workers/ingame_m1/measure.py` finds the minute the moneyline was decided and keeps only the candles of the 120 (NBA), 135 (NHL) or 170 (NFL) minutes before it, shorter than any game of that sport; everything else is dropped before anything is computed. It reads no result field and prints no price, no pre-game figure and no outcome, only counts and shares of a move. A trigger whose ten-minute horizon would run past the decided minute is not used.
- **Constants, unchanged:** a trigger is a moneyline mid move of 8c or more against three minutes earlier, from a mid of 10c to 90c, at most one a game per ten minutes; the spread's full move is its move to ten minutes after the trigger minute, in the direction the moneyline implies; an event counts only if that move is 3c or more ("a clean move"); of the followed spread markets, the one that moved most is used.
- **Kill rule, unchanged:** the card is CLOSED if 75% or more of the move is in by the end of the first full minute on 80% or more of the events. Under 40 events with a clean move: NOT_ENOUGH_DATA, and that is then the answer for this source; the list is not extended.
- **Not known:** whether the batched candle endpoint answers for sports markets, and whether a market that closed weeks ago still serves one-minute candles there. If the first three requests fail, the run stops by the script's own rule.

## 9. The cost to beat, and the two readings of the family (Head of R&D, Nov 12)

- **The cost to beat is SC1's.** SC1 is this card's nearest relative: in play, Kalshi prices only, follow a jump, time exit. It lost about 4.3c a trade over 62,747 events, the same whether it followed or faded, so the whole loss was the cost of the round trip. A lag has to be worth more than about 4.3c a trade, after it has been seen and acted on a minute late, before this card earns anything.
- **By entry mechanism plus exit style (lifecycle 7f), this card's cell is empty:** a sibling market's move as the signal, with a time exit. It is not barred.
- **On the broader reading, "in play on Kalshi prices", this would be the THIRD try** after SC1 and SWING1, both FALSIFIED, and the last one the three-falsified rule allows.
- If step 1 survives, the Head of R&D puts both readings to the owner before anything is registered.
