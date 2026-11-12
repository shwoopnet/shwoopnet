# Idea Desk A: tonight's cards (Nov 12, 2026; ordered by the Head of R&D for the owner's "find more ideas and strategies to bring"; no padding)

**Honest number: ONE card (PREDRIFT), registered below as a rule before any price is read. The other four seeds fail the Head's own test (a different state from INPLAYJUMP, a named other side that differs, outside a closed row) and are reported with the reason, not padded into cards.** Nothing here was run; no price or result of these series was read; zero tries spent until a go.

## The seeds that did not become cards
| Seed | Why it is not a card |
|---|---|
| Two jumps the same way (a second jump after the first) | The other side is the same one as INPLAYJUMP's (stale resting orders). A second jump is a later look at the same mechanism: a **venue/state of INPLAYJUMP's family**, not a new one. If INPLAYJUMP's first jump is falsified this is dead too; if it survives, ask for this as its second state. |
| A jump half given back within three minutes | It is the fade of a jump once the market has partly faded it: SWING1 and SC1 (fade, hold) were FALSIFIED. The other side would be "late over-reacting buyers", which nothing recorded can name. Inside the own-in-play-price-path family the Head counted. |
| A match market pinned near 50c late in a match | Needs "late in match": only the clock families have a start. There the TIE contract and the cheap side are the tradeable parts, and both are closed rows (cheap-side; favourite-late on the Tie's NO). No separate other side. |
| Quotes that go one-sided in play (bid or ask missing) | When the bid is pulled the only buyable side is the stale offer, and the NO side costs 1.00: the state offers nothing to take on the side that matters, and at the extremes it is a cheap-side or favourite row. Also rare outside the extremes (a count the candles of INPLAYJUMP will give for free; if the count is under 1,200 it is dead). |
| The CFRTI-K "ran rows" idea as a rule (a rising ask over the PREVIOUS minute, entered at the current ask) | That is momentum on the cheap side of a 15 minute market: inside the declined grammar rows ("cheap-side price, regime and grammar rules on the 15 minute series"). Dropped before writing. |

## PREDRIFT, the pre-match drift: rule registration (a state INPLAYJUMP does not look at: BEFORE play)

`PREDRIFT | family: a single market's own pre-match price drift, followed; buy the contract that rose in the 30 minutes before the start, hold to settlement | risk class: mid price (20c to 85c), 1 contract, hundreds of matches a day, no link to any live strategy | stage Idea, registered as a rule`

**Nothing here permits an order.** One development read (and, on the Head's go, one held-out read); tries: 3, one per clock family (e-soccer, table tennis, e-basketball). Built on the same engine and files as INPLAYJUMP (`desk_a_verify/inplayjump.py`, Desk B's `INPLAYJUMP_SERIES.json` families, windows and constants).

**Why it is not INPLAYJUMP:** INPLAYJUMP reads a jump DURING play (a match event). PREDRIFT reads the slow pre-match drift (team news, a withdrawal, a late market move) and buys at the start. Different time, different signal (a 30 minute drift, not a one minute jump), a different other side.

**The named other side, and why it may not lose:** resting limit orders left by makers who do not reprice a low-tier pre-match market while information arrives (a lineup, a player's warm-up). **Why it may well fail, said first:** a pre-match drift is usually informed money arriving; by the start the price is theirs. This is the pre-match mirror of the mirror: I expect FALSIFIED near the cost.

**The rule, every number pinned:**
1. **Clock families only** (e-soccer, table tennis, e-basketball): the ticker key gives S (US Eastern, as INPLAYJUMP); guard: the market closed 4 to 90 minutes after S, else dropped and counted. Tennis has no clock and is out.
2. **Candles:** one-minute, a minute counts only if 0 < bid < ask < 1. Mid = (bid + ask) / 2. The Tie contract is never the drifter and never bought.
3. **The drift (the state):** at the candle ending 60 s before S (minute S-1), a team contract's mid is 6c or more above its mid at the candle ending 31 minutes before S; both candles two-sided; its mid 31 minutes before S was between 25c and 75c. Exactly one contract can qualify in a two-team market (they mirror); in e-soccer a double qualification is dropped and counted.
4. **Entry:** at the close of the minute ending at S, if the drifter is two-sided there, its ask is 20c to 85c and its spread 4c or less: buy 1 contract at that ask plus 1c. If not, no bet, counted; no second chance.
5. **Fee** 0.07 x price x (1 - price) rounded up to the cent. **Hold** to settlement; the result is read only for matches with a bet.
6. **Cost kill before any result:** the INPLAYJUMP line (median round trip of spread plus two fees at the mid above 5c closes the family). By the arithmetic I sent Desk B, this kills any family with a median spread of 2c or more at mids from 20c to 80c.
7. **Placebo:** in every development match, the same entry at S when the higher-mid contract's drift over the same 30 minutes was under 2c in size, buying the higher-mid contract at ask plus 1c in the same band; grouped by price paid in 10c buckets and re-weighted to the rule's own mix.
8. **Windows are INPLAYJUMP's development windows** (e-soccer 2026-10-15 to before 10-23; table tennis 10-01 to before 10-23; e-basketball 09-15 to before 10-23); held-out as in the series file, not pulled until the Head's go.
9. **Verdict, per family:** under 300 bets NOT_ENOUGH_DATA at n = x; 300 or more and cash PF under 1.0 overall or in either half FALSIFIED; cash PF 1.5 or better, both halves above 1.0 and net above the placebo's by two standard errors "development bar met"; else "bar not met". Research bar as INPLAYJUMP (cash PF 1.5 on development and held-out, one-sided z 5.46 on both). Every output line: "candle freshness measured on Bitcoin 15 minute only, not on these markets".

**Events and bets:** the clock families list about 450 (e-soccer), 147 (table tennis) and 84 (e-basketball) matches a day; a 6c drift over 30 minutes before the start is perhaps 10% to 20% of matches, so about 1,200 to 2,400 bets in e-soccer's eight development days if the markets are quoted that early (**unknown: whether they are two-sided 31 minutes before the start; the first count will say**), far fewer in the other two. Only e-soccer is likely to reach 300 bets.

**Requests:** lists: none beyond INPLAYJUMP's (the same matches). Candles: the clock families' window must start 45 minutes before S, not 40 minutes before the close, so the pull is wider; if the Head approves one shared candle pull from S minus 45 minutes to the close for the clock families, it serves INPLAYJUMP and PREDRIFT together. Estimate (not a count): about +200 requests over INPLAYJUMP's clock-family calls (e-soccer about 110 to 190, table tennis 60 to 100, e-basketball 60 to 105).

**Declined list / earlier tests:** not favourite-late (ask capped at 85c), not cheap-side, not tape flow, not market making, not a lock, not the in-game lag card. Closest earlier tests: SC1 and SWING1 (in-play jumps; time exit or fade). V2's rating rules on esports failed twice (a pre-match ratings model); this uses the market's own path, not a rating. **My odds: about 2% that any one family meets the development bar; below 1% the research bar.**
