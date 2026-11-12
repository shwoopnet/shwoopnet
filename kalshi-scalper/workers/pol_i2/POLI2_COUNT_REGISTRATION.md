# POL-i2, overnight gaps in politics markets: COUNT registration (zero tries)

**Registered Nov 12, 2026, before any price of these markets was read by this desk.** Card: Refinement's POL-i2 (`refine_tools/POLITICS_CARDS_NOV11.md` on `claude/refine-live`, row POL-i2), never run and with no reason recorded. Re-opened by the Head of R&D's ruling on `REOPEN_RANKING_NOV12.md` (the count step only, after the census first cut). Written by Idea Desk B.

`POL-i2 | family: follow an overnight price gap in a politics market at the US morning; time exit 24 hours later | risk class: mid price, 1 contract, round-trip cost paid | stage Idea, count only`

**This stage COUNTS. No trade is scored, no price after the entry hour of a gap day is read, no result field is read, nothing is traded.** It answers two things: are there enough overnight gaps to test at all, and what does it cost to get in and out.

## What the card says, and three things in it that had to be pinned before data

The card: at 22:00 ET take the YES mid of each liquid politics market; at 07:00 ET, if the price moved 5c or more overnight, buy the direction, only if the ask is still within 1c of the 06:30 ET quote, side priced 10c to 90c, one per market a day; exit 24 hours later at the bid. Kill: profit factor under 1.0, or fewer than 40 qualifying gaps per half.

1. **"06:30 ET" does not exist in hourly candles.** Pinned: the YES ask (or NO ask, for a down gap) at the 07:00 ET candle close must be within 1c of the same ask at the 06:00 ET close. Read plainly, that says the price was steady for the last hour, so 07:00 is a price one could have paid. It does NOT show that "the quote has not yet followed", which is what the card wanted; hourly data cannot show that.
2. **"Liquid"** is pinned as the card has it: at least 200 contracts traded in that market over the 7 days before the gap day, summed from the candles' own volume (known at the entry hour).
3. **Eastern time** is America/New_York clock time, so the two hours shift in UTC when the clocks change on Nov 1, 2026.

## Universe, fixed now

The 61 series in `kalshi-scalper/workers/POLREC_SERIES.json` on `main` at commit `be0b6dbb`: the 45 the politics recorder reads and the 16 it leaves out as long-dated (`later_only`). That list was reviewed and merged before this registration and was not chosen from any price. Every market of those series that was open at any time from 2026-09-12 on.

**Window:** gap days (the morning's date, Eastern) from **2026-09-13 to 2026-11-12**. **Halves:** before and from **2026-10-13** (Eastern date). **Held-out:** gap days from 2026-11-13, not pulled.

## What a qualifying gap is (all from candle closes)

For a market and a morning D:

1. the hourly candle ending 22:00 ET on D-1 and the ones ending 06:00 and 07:00 ET on D all have a two-sided quote (0 < bid < ask < 1);
2. the YES mid at 07:00 differs from the YES mid at 22:00 by 5c or more; the direction is its sign;
3. the ask of the direction's side at 07:00 is between 10c and 90c and within 1c of the same ask at 06:00;
4. the market traded 200 or more contracts in the 7 days ending 22:00 ET on D-1;
5. the market does not close within 24 hours after 07:00 ET on D (the exit must exist).

One gap per market a morning. **For independence, gaps are also counted per series and morning** (several markets of one event moving together are one event).

## What is reported (counts first)

1. Series asked for, series with any market, markets pulled, markets with any two-sided hourly candle.
2. Qualifying gaps: all, per half; distinct markets, distinct series, distinct mornings; **series-mornings per half** (the independent count).
3. How the count falls at each condition (how many market-mornings pass 1, then 2, then 3, then 4, then 5), so the binding condition is visible.
4. At the entry hour of qualifying gaps: median spread, and median round trip = spread plus two fees of 0.07 x p x (1 - p) on the price paid.
5. The median size of the gap.

## Kill rules, fixed now

- **CLOSED, "not enough to test":** fewer than 40 series-mornings with a qualifying gap in either half. (The card says 40 gaps a half; counting by series and morning is stricter, on purpose.)
- **CLOSED on cost:** the median round trip at the entry hour is above 5c. The Forensics desk already measured politics markets priced 20c to 80c at a round trip of 6.3c (three snapshots of the recorder), so I expect this line to bind: a rule that pays 6c to get in and out has to find more than 6c of follow-through in a gap whose own size is about 5c to 8c.
- Neither fires: the card goes to a scored test under its own registration, before any price after an entry hour is read: the follow arm is the card, the fade arm is a scored control, **2 tries**, the count window as development read once, held-out from 2026-11-13.

## Power, stated before the count

About 360 trades are needed at the shared bar (z 5.46) if the rule nets 2c a trade after costs with a 6c spread of results, about 160 at 3c. My guess before counting is 150 to 400 gaps a year on these series. So even if the count survives, one year of history is the least that could decide it, and the history endpoint would have to hold the older markets.

## Requests

- **Lists:** two reads a series (open, and settled with a close time from 2026-09-12): 122 requests, about 130 pages.
- **Hourly candles:** 62 days x 24 hours is about 1,490 candles a market, so 6 markets a batched request. Markets are taken in order of total contracts traded as the list shows it, most traded first, **at most 600 markets: at most 100 requests.** (The list's volume is a total to date, so it uses the future to choose which markets to pull; it is a pull limit only. Condition 4 is computed from candles up to the entry hour.) If more than 600 markets exist the cut is reported.
- **Total: about 220 requests, two runs. Tries: 0.**

## Honest limits

1. Hourly closes are one instant an hour; a quote that is one-sided at that instant drops the morning, and those are counted at step 3, not filled in.
2. Candle freshness was measured on the Bitcoin 15 minute series only.
3. This is a price-only rule on Kalshi's own history, the kind that has failed many times here on other markets. What is different is the market type (politics, thin overnight) and the 24 hour exit. My probability that the count survives both kill lines: about 25%. That a survivor reaches the bar: about 1 in 12.
4. A politics gap is often news. Following news a night late at a 6c cost is the null I expect to see.
