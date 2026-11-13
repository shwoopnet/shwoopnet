# Live spec sheets for the probation pool: REMATCH, MAPBREAK, INPLAYJUMP (Idea Desk B, Nov 12, 2026, 20:02Z)

Asked for by the Head of R&D at 19:59Z for the owner's "probation seats" decision. **This desk does research only: it places nothing and builds nothing live. These sheets describe the registered rules exactly; they change no registration.** A simplified version of any rule would be a NEW rule; none is proposed here.

## Said first, plainly

- **Evidence today: none, for any of the three.** No price of these markets has been read against an outcome. Author's odds that each has a real edge at the research bar: MAPBREAK about 2%, REMATCH about 1%, INPLAYJUMP about 1% a family. The likeliest result of each is that it loses its cost, about 2c to 4c a contract a bet.
- **The drawdown kill will fire by chance.** At 3 contracts and a price near 50c one loss is about $1.50, so an $18 drawdown is about 12 losses. A rule that bets 15 or more times a day at about even odds reaches that on luck alone within days. A kill is not evidence against the rule and survival is not evidence for it. Probation fills are never research evidence.
- **Shards (the `exchange_index` field in the list answers this desk holds):** e-soccer 0, CS2 0, Dota 2 0, table tennis 0, e-basketball 0, ITF tennis 3, challenger tennis 3. (Also NHL 0 and hourly temperature 0.) The notes on main say the bot's current markets sit on index 2, so index 0, and index 3 for tennis, would need money put there by hand.
- **Every one of these needs things the bot does not have today:** an entry timed from a ticker clock or a sibling market's close (not seconds before a 15 minute close), hold-to-settlement for a new strategy, new series and ticker shapes, and a quote reader for markets it does not read now.

## Rank by ease of a faithful live build: 1 REMATCH, 2 MAPBREAK, 3 INPLAYJUMP

## Sheet 1: REMATCH (e-soccer). Registration `rematch/REMATCH_REGISTRATION.md` with Amendments 1 to 4

1. **Order.** Series `KXESOCCERGAME`. Buy YES on the contract of the player who LOST the previous meeting of the same two players (never the Tie). Band: ask 20c to 80c, spread 4c or less. Decision: the minute ending 6 minutes before the later match's scheduled start (the clock in the ticker, US Eastern). Order in the following minute: limit at the ask plus 1c, 3 contracts, unfilled part cancelled at once (the registration books a fill at that price; a resting order is not in the rule). Exit: hold to settlement. One order a match.
2. **State the bot must hold at the decision, and where it reads it.**
   - The open e-soccer markets and their tickers (public market list): gives the later match B, its start S and its two player codes.
   - The earlier match A: same two codes in either order, B being the NEXT meeting of that pair, A's scheduled start 20 to 120 minutes before B's (tickers only).
   - A's markets' close times: the latest plus 300 seconds must be at or before the decision minute (public market read).
   - A's result: exactly one team contract "yes" and the Tie "no" (public market read; in the Nov 10 listing results were posted 4.0 minutes after the close, so they are present by then).
   - The loser's contract in B, mid at the candle ending at A's start minus 2 minutes, and at the decision minute; each from the exact minute or the last present candle at most 5 minutes earlier, never later (public candle read at the decision, or the bot's own minute log). Fall of 5c or more between the two.
   - The entry quote in the next minute.
   - **Any piece missing, unreadable or one-sided: no order, reason logged.**
3. **Orders a day (counts only):** 297 qualifying pairs on the one day seen (a lower bound, around the clock). The share with a 5c fall is not known until stage 1. At 5% to 15%: about 15 to 45 orders a day.
4. **Evidence:** none. Odds about 1%. Published work (Idea Desk C): no study of head-to-head recency; general recent-form overreaction points the same way but by a few percent, at the extremes only. **Read:** stage 1 (counts and cost, about 110 requests) runs once the e-soccer lists land; stage 2 (about 490 requests), its scorer and the Forensics audit follow on the Head's go. If everything merges tonight: stage 1 tonight, the development read Friday at the earliest, more likely Saturday.
5. **Hard to build by Sunday:** the pairing must match the scorer exactly (next meeting, either order, the 20 to 120 minute gap); a market list read every minute, day and night, and a memory of recently closed matches; if the ticker clock is wrong for some matches the bot would be buying in play (the registration prints that as a diagnostic; a live bot cannot see it).

## Sheet 2: MAPBREAK (CS2 and Dota 2). Registration `mapbreak/MAPBREAK_REGISTRATION.md` with Amendments 1 to 6

1. **Order.** Orders go in the match series `KXCS2GAME` and `KXDOTA2GAME`. Best-of-three only: the match's total-maps event (`KXCS2TOTALMAPS`, `KXDOTA2TOTALMAPS`) has a market at 2.5 and none higher, and map markets 1 and 2 are listed (`KXCS2MAP`, `KXDOTA2MAP`). Side: for each team, gap = model value minus the ask of its own match contract; buy YES on the team with the larger gap if that gap is 8c or more and that contract's spread is 4c or less. Limit at the ask plus 1c, 3 contracts, hold to settlement. Two possible orders a match, one per look.
   - First look: the first whole minute at or after the map-1 market's close plus 120 seconds, stepping forward to plus 5 minutes if both match contracts are not two-sided.
   - Second look, only when the match stands at one map each: the same from the map-2 market's close.
   - **There is no price band in the registration.** The team one map up will often be asked at 80c to 90c or more. Buying it there and holding meets the Charter's favourite-and-hold ban unless the owner excepts it; adding a cap would be a new rule.
2. **State.**
   - Start S from the ticker clock; map 1 must have closed 15 to 150 minutes after S, else no order.
   - Pre-match mids of both match contracts at the candle ending at S minus 10 minutes (step back to S minus 40).
   - **Changed Nov 13, 00:10Z by MAPBREAK Amendment 7:** who won a map is the OBSERVED winner, not the result field: at the look, the team whose map contract shows a YES bid of 0.90 or more in its last candle, or whose opponent's map contract shows a YES ask of 0.10 or less; exactly one team must qualify, else no order. (Amendment 8, 00:20Z: simplified to the winner's own map contract showing a YES best bid of 0.90 or more and the other team's not; and, by Amendment 9, the order is a limit at the decision candle's ask plus 1c that counts as filled only if the next minute's ask is at or under that limit, paying the limit.) The sentences that follow about waiting for the posted result are superseded.
   - (Superseded) Who won map 1: the map-1 market's result. In the listing a map's result is posted 3.0 minutes after its close, so a bot that waits for it looks at close plus 3 to plus 5 minutes: inside the registered window, sometimes a minute later than the scorer's look. The read also counts how often the winner's last quote was 90c or more, the only earlier signal.
   - The model: p = pre-match mid of the map-1 winner's match contract; q solves p = q x q x (3 minus 2q); value one map up = 1 minus (1 minus q) squared; at one map each the map-1 winner's value is q.
   - Second look: the map-2 market's result must name the team that lost map 1.
   - Which titles are "in" is decided by the development kill lines (cost, gap share, placebo). A title that is out cannot be traded faithfully.
   - **Any piece missing: no order.**
3. **Orders a day (counts only):** 1,912 best-of-three matches in 41 days (CS2 1,525, Dota 2 387), about 47 a day, about 68 looks a day with second looks. Firing share unknown; at 10% to 20%: about 7 to 14 orders a day, bunched in tournament hours.
4. **Evidence:** none. Odds about 2%. Published work: nothing on map breaks. **Read:** lists landed tonight; the candle job is the Testing Desk's (my estimate 250 to 450 requests, one run). If dispatched tonight, the kill lines and the development read can land tonight or Friday morning. On 450 to 675 bets over both blocks it can falsify or show a lead; it cannot reach the research bar.
5. **Hard to build by Sunday:** it is event-driven: the order must go within about three minutes of a sibling market closing, so the bot must poll the map markets of every live match each minute; the model arithmetic must match the scorer to the cent; the price-band question above.

## Sheet 3: INPLAYJUMP (five families). Registration `inplayjump/INPLAYJUMP_REGISTRATION.md` with Amendments 1 to 6

1. **Order.** Series: `KXESOCCERGAME`; `KXITFMATCH`, `KXITFWMATCH`; `KXLIGAPROMATCH`; `KXATPCHALLENGERMATCH`, `KXWTACHALLENGERMATCH`; `KXEBASKETBALLGAME`. Buy YES on the contract that just jumped (never the e-soccer Tie). The jump: at an in-play minute t the contract's mid is 10c or more above its mid at minute t minus 1, both minutes present and two-sided, volume above zero in minute t, and the mid at t minus 1 was 15c to 75c. Only the FIRST qualifying jump of a match, no second chance. Entry at the close of minute t plus 1: ask 20c to 85c, spread 4c or less, limit at the ask plus 1c, 3 contracts, hold to settlement.
2. **State.**
   - The minute-end bid and ask of every open match contract in the five families, every minute (about 1,075 matches a day on Nov 10: e-soccer 450, ITF 302, table tennis 147, challenger 92, e-basketball 84).
   - In play: clock families from the ticker clock plus 60 seconds; tennis has no clock, so a minute is in play only if 3 or more of the 20 one-minute steps before it moved the mid 2c or more, which needs a 21 minute history per contract.
   - Traded volume in the jump minute (a trade or candle read).
   - A per-match "already decided" memory.
   - A missing or one-sided minute means no step and no order; nothing is carried forward.
3. **Orders a day:** not known; every match is a candidate. If 10% to 30% of matches give an entry (a guess, not a count) that is roughly 100 to 300 orders a day.
4. **Evidence:** none. Odds about 1% a family. Published work: no drift after a goal on liquid exchange soccer; where continuation exists it is mostly gone in 2 to 6 minutes; thin markets showed more. This is the third and last look at the idea. **Read:** lists wait for their merge; then a 13 request pilot and validation; then up to 1,800 candle requests over two runs. Friday at the earliest for the clock families, later for tennis.
5. **Hard to build by Sunday, and I do not think it can be done faithfully:** it needs a reader of several hundred markets every minute with an order inside the next minute, on a function that today reads a handful; the volume condition needs a trade read; tennis sits on a different shard. At 100 or more orders a day the drawdown kill would fire on luck within a day or two.

## Could TIE3, NHLOT or the hourly temperature measurement give a simple price rule this weekend?

- **TIE3: yes, if its measurement finds a cell, and it would be the simplest live build of all.** The rule is pre-match and static: 30 minutes before the game (start = the market's `occurrence_datetime` minus 180 minutes), buy the Tie if its ask is 10c or more under a fixed base-rate table and the spread is 4c or less; hold to the end of the period. One quote read, one table. Its candle stage (50 requests) has the Head's go. My odds that a cell survives: about 15%. If one does I write the rule registration the same hour. Few orders: NHL about 7 games a day, NFL on Sunday. Shard 0.
- **NHLOT: possibly, but few bets and an event-driven build.** Its candles (86 requests) are with Main tonight. The state (level after regulation) has to be detected from Kalshi's own total-goals strikes inside the last minutes of a game. About one NHL game in five goes to overtime, so under 2 orders a day. Shard 0.
- **Hourly temperature: no.** The settlement source and the proxy gap have to be measured first, its lists job is last in the queue, and a card would be registered only after that. Not this weekend.
