# Two cards that need Kalshi's relayed sports live data, written not registered (Idea Desk B, Nov 13, 2026, 14:21Z by this desk's clock)

Written on the Head of R&D's order of 14:18Z (the owner: "max some out", the two feeds he accepted on Nov 13 as a recorded terms risk). **Nothing is registered, nothing is counted as a try, no Kalshi request was made, no data was opened.** PAPER ONLY. [research]

**What was checked first, and what is NOT here.** The History Miner's warning (14:26Z): the two obvious uses of the new feeds are versions of HOURLYTEMP and INPLAY1. Agreed, and so there is **no temperature-index card.** Every use of the index I can derive is a nowcast of an hourly strike against its quote (WXNEW1 FALSIFIED at Miami; HOURLYTEMP is the cost measurement), which is the same mechanism on a better reference. One idea waits for probe A instead of being written: Kalshi's calibration timeline (`/live_data/weather/{city}/calibrations`). If calibration changes are dated events that move the index against its member stations, that is a calendar-event mechanism (EVENT830's family), not a nowcast; it cannot be shaped until the probe shows whether the timeline has any entries. In-play score totals priced by pace is INPLAY1/ESPN1's family and is avoided. What is left are two mechanisms that need a state the feed gives and no other permitted source does.

Held-out line for both, from `HELDOUT_REGISTRY.md` (rnd-queue, ad42ec54): cards that hold or held out NHL series: NHLG1 (frozen cut 2026-10-03T16:00Z, goal-scorer and game series, READ spent), FAMSPORTS (spent), ESPN1 (spent, hockey absent), W-CAT-SPORTS1 (released 06:51Z), W-SPREAD-CELL1 (spent), TIE3 (KXNHL1P to KXNHL3P and KXNHLOT held-out from 2026-11-13, closed unread), NHLOT (closed, finished, sample ended 2026-11-12). **None holds a result of KXNHLGAME or KXNHLTOTAL on or after 2026-11-13 for the use below.** NBA: NBA series appear in ESPN1, FAMSPORTS, W-CAT-SPORTS1 (released), none after 2026-11-13 for player props. The registry lists no card on any player-statistic ladder.

---

## CARD 1. ENDNET: the goalie-pull regime in the last minutes of an NHL game

`ENDNET | family: rule-change regime near the end of a game (a known change of scoring rates at a known game state), taker entry on a total-goals strike that needs exactly one more goal, held to settlement | risk class: mid price (ask 15c to 45c), 1 contract | stage Idea | prior about 4%`

**The fact (arithmetic and common knowledge, not measured here).** In the last 2 to 3 minutes of an NHL game that is within one goal, the trailing team replaces its goalie with a sixth skater. That changes the scoring rate of BOTH teams: the trailing team shoots more, and the other team gets empty-net chances. A flat model, a constant goal rate for the whole game, leaves the rate at about 6 goals per 60 minutes (about 0.1 a minute, about 26% for at least one more goal in three minutes). By my arithmetic from rates I recall from hockey analytics and have NOT checked (empty-net goals in roughly a third of pulled-goalie minutes), the true chance of at least one more goal in the last three minutes of a one-goal game is nearer 40% to 48%. Whether Kalshi's maker prices the strike off a flat rate or off the state is the whole question.

**The claim.** In the last 3:00 of the third period with the score one goal apart, the total-goals strike that needs exactly one more goal is priced below the state-aware chance by more than the fee and half the spread.

- **Other side:** a maker who quotes a total-goals ladder from the running total and a pace, not from the end-game state.
- **Why they would lose:** the rate change is a published tactic, not news; it is exactly the same each game and shows up in the clock, which a pace model does not read.
- **Honest caution:** this is the first thing a sharp hockey bettor looks at. The same hockey cards of the old research team (NHLG1, FAMSPORTS) found only that the market's total mid beat a box-score model; nobody tested the late state. Prior 4%.

**The state needs the feed.** The period, the clock and the score are not in any permitted outside source (every score site is banned by `test/noSportsScoreSitesGates.test.js`). Kalshi's live data (`/live_data/milestone/{id}`, and play-by-play for "Pro Hockey" in `game_stats`) is the one permitted source, under the owner's recorded exception.

**Entry, management, exit (for a later registration, not registered here).**
- Entry: the first one-minute candle at which the game clock reads 3:00 or less in the third period, the score is one goal apart, and a KXNHLTOTAL strike exists whose `floor_strike` is the current total goals (so one goal makes it YES). Buy YES at the ask plus 1c if the ask is 15c to 45c and the spread is 4c or less. One contract. One entry a game.
- Management: none. Exit: held to settlement (the market closes minutes later), no resting order.
- It is a MID-price buy, not a favourite-and-hold: the favourite-and-hold ban (Charter checklist item 5) does not apply. It is not a favourite at 88c to 97c in any way.

**The four uniqueness checks.**
1. **Signal:** a game state (period, clock, score) from a feed, applied to a known tactic. Not a price pattern, jump, base rate, count pace or outside forecast.
2. **Entry and exit:** a taker at a mid price, held minutes to settlement. No live or shadow rule trades hockey.
3. **Correlation with live strategies:** no shared market with gold L1, OICORE or EVENT830; expected near 0 (not measured).
4. **Declined list (STRATEGY_LIFECYCLE.md 7e), rows compared:** favourite-and-hold (this buys 15c to 45c); two-sided market making (taker, one side); weather forecasts; order-flow signals on the 15 minute tape (no flow field, no 15 minute market); lock and parity scans (one position, no relation); cheap-side price/regime/grammar rules on the 15 minute series (this reads a game state, on game markets); the tie premium (not a 15 minute market). None matches.

**Closest existing mechanisms, said plainly.** NHLOT (closed tonight on its price measurement): the same sport and the same family of a state change in a hockey market, but its state was a tied late game read by the market's own prices, and it bought an overtime rate. ENDNET reads the clock and the score from the feed and a different tactic. INGAMELAG and SWING1 are price-lag cards (closed). INPLAY1 is a win-probability ratio on winner markets. A reader may call ENDNET a version of NHLOT; the answer is the state source (feed against the market's own prices) and the rate change (a tactic against a tie). The Verification Analyst is asked to score the four checks.

**Numeric prediction and kill lines, written before any data.**
- Define, for each qualifying game, p_state = whether at least one more goal was scored before the final buzzer (reading the result of the market itself, only at stage 2) and ask = the strike's ask at entry.
- **Stage 0 (the probe, zero tries):** DEAD if the live data for an NHL game has no clock or no period field, or if a FINISHED game's play-by-play is not retrievable AND forward recording of the state is not something the owner will allow (see below).
- **Stage 1 (zero-try measurement, no result read):** count qualifying entries per game night and the median ask. **CLOSED if the median ask is above 45c** (the market already prices the regime) or **fewer than 6 qualifying entries a week**.
- **Stage 2 (one try, its own registration before any scored file):** 150 filled entries; cash PF 1.5 on development and on the held-out block, halves at 1.0, deflated z at the then-current bar. **Prediction:** the median ask at the qualifying minute is 30c to 40c and the win rate 35% to 45%; cash PF 0.7 to 1.3; a pass has a chance of about 4%.
- **Held-out, as date constants (fixed now, before any recorded state is read):** development = games closing from 2026-11-17 00:00Z to 2026-12-14 23:59Z; HELD-OUT = games closing from 2026-12-15 00:00Z to 2027-01-31 23:59Z, not pulled, not recorded into any file a scorer can read before the stage 2 registration. The NHL calendar has a short break around the holidays; this is stated, not hidden.

**Data and cost.** If a finished game's play-by-play stays retrievable (probe B2), the history exists and the test needs no recorder: one batch of live-data reads per game, about 1,300 games a season at one request each, but a probe of 8 requests comes first. If it does NOT stay, the state has to be RECORDED forward (a poll every 30 seconds in the last 10 minutes of third periods only, 8 to 12 games a night): that is a NEW recorder and needs the Charter's runner-minute check and the owner's approval; it is not requested here. **Events:** about 80 to 100 NHL games a week; roughly a quarter are within one goal at 3:00 left; so about 20 a week, about 150 in 8 weeks.

**Weakness, stated.** The prior is low because hockey markets are heavily traded and this is a well-known tactic. A second weakness: the feed "is not guaranteed to be current", so a state read a minute late can sit after a goal.

---

## CARD 2. PROPPACE: cost first, then a pace read on live player-statistic ladders

`PROPPACE | family: count so far plus remaining-time model on LIVE player-statistic ladders (the count is observable mid-game from play-by-play), cheap side only, held to settlement | risk class: cheap tail (ask 3c to 30c), 1 contract | stage Idea, conditional on a cost measurement | prior about 2%`

**What is new.** COUNT1 and EXECSUM died for one structural reason: "count so far" was not observable mid-period (a publication lag of days, or no archive). A live game's play-by-play gives the count so far to the second. That is the one thing the new feed supplies for a count ladder, and no registered card used it.

**The claim.** A player-statistic ladder in a live game (points, rebounds, assists) is a count with a known remaining-minutes structure: the count so far is known; what remains is a rate times the minutes the player will still play (starters sit in blowouts; a player in foul trouble sits). A thin ladder maker who prices off pre-game lines may not update the minutes: the cheap strikes are priced too low or too high by minutes the play-by-play shows.

- **Other side:** the slow or thin-book maker on a prop ladder.
- **Honest caution:** prop ladders on Kalshi may have almost no liquidity: the cost (a wide spread on a thin book) probably kills it before any model matters. This is why the card is cost first.

**Entry (for a later registration).** Cheap side only (ask 3c to 30c, hard limit 30c), at fixed game-clock looks (start of the 4th quarter and 6:00 left), only if the pace model's probability for that side is at least 3 times the ask, one entry per player and game, held to settlement. (The 3x rule and the cheap-side limit are the standing rules of COUNT1; this card does not invent new ones.)

**The four uniqueness checks.**
1. **Signal:** a live count so far plus minutes from a feed. Not a price pattern, an outside forecast or a flow.
2. **Entry and exit:** a taker at a cheap price, held to settlement.
3. **Correlation with live strategies:** none expected; unmeasured.
4. **Declined list rows compared:** cheap-side price/regime/grammar rules on the 15 minute series (different market and a different information source); no counts or props row exists on the declined list. The favourite-and-hold ban does not apply (cheap side).

**Closest existing mechanisms, said plainly.** COUNT1 (same pace model shape, NOT_ENOUGH_DATA, different count source); INPLAY1 (cheap side with a ratio rule on winner markets from ESPN's probability); BOOKNCAA1 (pre-game cheap side). PROPPACE differs by the count source (observed so far in a live game) and the market (a player ladder).

**Numeric prediction and kill lines, written before any data.**
- **Stage 0 (the probe):** DEAD if `game_stats` returns null for NBA (the documentation says it supports "Pro Basketball"; for games "without a Sportradar ID" it returns null) or if player statistics are not in it. DEAD if no player-statistic series exists in the open NBA events (it is not known that one does).
- **Stage 1 (zero-try measurement, no result read):** the median spread and the share of cheap strikes with any two-sided quote at the 4th-quarter look. **CLOSED if the median spread of cheap strikes is above 6c** or fewer than 40% are two-sided.
- **Stage 2:** one try, registered before any scored file; 150 filled entries; cash PF 1.5 development and held-out, halves 1.0.
- **Prediction:** it closes at stage 1 (spread too wide), probability about 70%; if it reaches stage 2, cash PF 0.4 to 1.0; a pass about 2%.
- **Held-out, as date constants (fixed now):** development = games closing from 2026-11-17 to 2026-12-14; HELD-OUT = games closing from 2026-12-15 to 2027-01-31, not pulled.

**Data and cost.** The same probe B2 (does a finished game's play-by-play stay), then at most 8 requests to read one live game's play-by-play fields; then 60 to 100 requests of candles for the player ladders of one night. **Events:** about 10 NBA games a night; a few cheap-tail entries a game at best.

---

## For the Head's read

- Two cards, neither registered. If the probe shows hockey clock fields and a retrievable finished game, ENDNET is registerable the same day; PROPPACE waits for its cost stage. Both held-out blocks are constants today.
- **Nothing here is padded:** I did not write a temperature card, an in-play-total card or a settlement-lag card, for the reasons given above.
- Probe B (`desk_b_jobs/LIVEDATA_PROBE_B.json`, 80b2fa4f) answers stage 0 only in part: it lists current milestones and the doubles events. **A step B2 is needed for these two cards** (the live data of one NHL and one NBA milestone, the game_stats of the same two, and one finished game of each): about 8 requests, written once B's answers show milestone ids.

## ENDNET: three readings pinned, Nov 13, 2026, 15:12Z by this desk's clock (the Head of R&D's ruling stamped 15:12Z by the Head's clock). Written before any state, price or result of this card was read; the scorer was built on invented rows only.

Dated lines, to be carried into the registration when ENDNET is registered (it counts as a registered rule only once its state source is shown to exist):
1. **The strike.** The strike bought is the one whose `floor_strike` f satisfies 0 <= f - total < 1, where total = home goals + away goals at the entry minute, so exactly one more goal makes YES (YES = final total above f). This replaces the card's wording "a strike whose floor_strike is the current total": a half line such as 5.5 against a total of 5 is the usual case, and an integer line equal to the total also qualifies.
2. **One look only.** The entry minute is the FIRST third-period minute with 180 seconds or less left and the score exactly one goal apart. If that minute has no usable quote, the game is counted and not entered; no later minute is tried.
3. **Nothing carried.** The quote is the candle whose end time equals the entry minute's end time, two-sided (0 < bid < ask < 100). No candle from another minute is used.

The scorer is `endnet/endnet.py` (sha256 84ecad6a91af8621a37c99ac8955726b7e26506d8e5fcc640f4565d0541544d9, commit e6a09275), the first build; the second build waits for the real feed layout (probe B2). The development and held-out dates are the constants in the card and in the scorer. The measurement job is a draft on this branch (`desk_b_jobs/ENDNET_LISTS_DRAFT.json`, e895b103), undispatched: it goes to Auditor B and Main only after B2 shows whether a finished game's play-by-play is retrievable, and not before 2026-12-15. No pilot on games of Nov 1 to Nov 12 (prices without a state source answer nothing).
