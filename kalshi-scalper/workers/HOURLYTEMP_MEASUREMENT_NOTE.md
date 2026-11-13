# Hourly city temperature: a cost and timing measurement note (Idea Desk B, Nov 12, 2026)

**A note, not a card.** Asked for by the Head of R&D (ruling of Nov 12, 17:15Z): a rule driven by a forecast is inside the closed weather family; a rule driven by the latest observed reading is the WXDAYEND mechanism on another venue and waits for WXDAYEND's count and a ruling under the declined list, because a reading-against-bracket rule mostly buys the near-certain side, the favourite-and-hold shape the owner banned. What is allowed now is one zero-try cost and timing measurement, because this is the largest event count anywhere outside the 15 minute series. **Nothing here is a rule, a try or a request to trade.**

## What the family is (from the Nov 10 listing's market objects: titles, rules text and time fields only)

- Four series: `KXTEMPNYCHS` (New York City), `KXTEMPMIAH` (Miami), `KXTEMPLAXHS` (Coastal Los Angeles), `KXTEMPCHIHS` (Chicago Metro Area).
- One event per clock hour, 21 to 22 events a day a city in the listing: about 32,000 events a year across the four.
- About 10 markets an event, each "will the temperature be above X.99 degrees at that hour", strikes one degree apart.
- **Each market lives one hour:** it opens 60 minutes before the hour and closes on the hour. So "60 minutes before" is the open; the looks below are 55, 30 and 10 minutes before the hour.
- **It does not settle on the National Weather Service.** The rules text names Synoptic Data, "calculated in accordance with the Kalshi Weather Index Methodology", and says other sources "may serve as references, but are not authoritative". Synoptic's terms have NOT been read and no read of Synoptic is proposed. A weather service reading is therefore a proxy for the settling value, not the value.
- Settles a median 71 minutes after the close (listing). About 800 contracts a market that day (a lower bound). No recorder holds it; spread and depth are unknown.

## The measurement (zero tries, no result read)

**Sample, fixed now:** the seven most recent full UTC days before the pull, all four cities. Seven days because the weather service's public station history goes back about a week; it is never extended.

**From Kalshi (through kalshi-pull):** the settled lists of the four series for those days (for tickers, strikes and times; the result field is not read), then one-minute candles of every strike for the 60 minutes each market lived.

**From the weather service (a permitted source, read by this desk, not through kalshi-pull):** the station observations of the same seven days for one airport station a city (New York Central Park, Miami International, Los Angeles International, Chicago O'Hare). The index may blend stations; that is why this is a proxy.

**Reported, at 55, 30 and 10 minutes before the hour, per city:**

1. Strikes with a two-sided quote, as a share; median spread; round trip (spread plus two fees).
2. For each strike, the distance between it and the last weather service reading published before that look, in degrees. By distance band (under 1, 1 to 2, 2 to 3, over 3 degrees, above and below): the median YES mid and the median ask of the nearer-certain side.
3. How many minutes old that last reading was at the look.
4. Minutes with no trade, as a share (from candle volume).

That answers three things without a result: what it costs to trade here, whether there is anything two-sided near the money at all, and how tightly the market already hugs the latest reading. If strikes 2 degrees from the reading already sit at 95c or more by the 30 minute look, the only thing left to buy is the near-certain side, and the family is closed for this desk on the owner's favourite-and-hold ban without waiting for WXDAYEND.

**What it cannot say:** whether any rule makes money (no result is read); how the proxy differs from the settling value (Synoptic is not read); depth (a candle has no size).

## Requests

| Part | Requests |
|---|---|
| Kalshi, settled lists: 4 series, about 1,540 markets each over 7 days | 4 requests, about 8 pages |
| Kalshi, candles: 4 cities x about 10 strikes x 60 minutes, two clock hours a request (80 tickers, 9,600 candles), 7 days | about 80 |
| Weather service, station history: 4 stations, a week | about 8 (not Kalshi requests) |
| **Kalshi total** | **about 85, one run** |
| Tries | 0 |

Order: after TIE3 and SOCDERIV, and only if the Head wants it run; the job file and reader would go to the Testing Desk in the same way.

## Ruling and final shape (Head of R&D, Nov 12, 17:25Z): Kalshi's own data only

**Approved: the Kalshi-only part, zero tries, LAST in the dispatch order (behind TIE3, POL-i2 and SOCDERIV).** Not approved: any use of an outside reading. The family settles on Synoptic Data, whose terms are unread; a weather service reading would be a proxy for the settling value, and a proxy that did not match the settled value is exactly what closed ROLLOFF on the same day. So the weather service part above is DROPPED, there is no read of Synoptic, and there is no reading-driven card.

**What is measured now**, per city, at 55, 30 and 10 minutes before the hour (the market opens 60 minutes before it):

1. strikes with a two-sided quote, the median spread and the median round trip (spread plus two fees);
2. the same round trip for strikes within two ranks of the money, where "the money" is the strike whose YES mid is nearest 50c at that look (taken from the quotes alone);
3. the ask of the nearer-certain side one, two and three or more strikes away from the money, and the share of strikes already priced at 95c or 5c and beyond;
4. the share of market-minutes with a trade;
5. the size at the touch on the markets open at the time of the pull (from one open-market list a series: a copy up to about 11 seconds old, a level only).

**Rule fixed now (the Head's line):** the family is CLOSED as too costly, with no need to settle the source question, if the median round trip near the money is above 5c at every look in every city.

**Fixed sample:** the seven UTC days Nov 5 to Nov 11, 2026, never extended.

| File | What |
|---|---|
| `desk_b_jobs/HOURLYTEMP_LISTS.json` | 9 requests, at most 17 pages: the settled markets of the four series for the seven days, one open-market list a series, one fee-field read. Passes the pull script's own check |
| `hourlytemp/build_candles_job.py` | builds `HOURLYTEMP_CANDLES.json` from the lists: two clock hours a request, about 84 requests (cap 110) |
| `hourlytemp/measure.py` | the reader. Never reads a result field. Prints the candle freshness line |

The whole chain (lists, builder, candle job check, reader) was run end to end on made-up data before any pull. Kalshi requests in all: about 93. Tries: 0.

## Dated amendment, Nov 12, 2026, 19:39Z, before any list or candle of these series was pulled (Head of R&D, 19:38Z: UN-PAUSED as a cost and settlement-source measurement, 0 tries, behind tonight's built reads and REMATCH stage 1)

1. **Step one is the settlement source, quoted.** The reader prints `rules_primary` and `rules_secondary` of each series from the lists answer before anything else. What this desk has already read, in the Nov 10 census listing: the rules text names Synoptic Data, "calculated in accordance with the Kalshi Weather Index Methodology". Idea Desk C reports a Kalshi help page naming The Weather Company. The series' own rules text decides; if the two differ the file says so.
2. **If it settles on a source we may not read,** a card may still exist with the NWS station reading (permitted) as a PROXY signal, but it must say so, and the gap between the proxy and Kalshi's settled strike becomes the first thing measured, before any rule.
3. **The cost line is one-way** (the rule would buy and hold for under an hour): half the spread plus the entry fee as charged at the ask plus 1c, rounded up. The family is CLOSED as too costly if the median one-way entry cost near the money is above 4c at every look in every city (it was: round trip above 5c). The round trip is still printed as information. Changed before any price was read, for the reason given in the Head's 19:02Z ruling for every hold-to-settlement rule.
4. **The Head's ruling on the declined list:** a rule driven by the last station READING on an HOURLY market is outside the row "weather forecast against market on daily temperature brackets" (a different market and different information), and the owner's weather rule allows singles on NWS data.
5. Only after the source and the cost line: a card, registered before any outcome. Standing rule (h) applies to its held-out from the start: the seven days the lists job covers already carry results in the landed file, so the held-out will be later dates.


## Dated amendment, Nov 13, 2026, 01:59Z: the reader's pins, written before any list or candle of these series was pulled (Head of R&D, 01:56Z: build the reader from this text, freeze it, audit it, second build, then the pull)

Nothing of these series has landed. The earlier reader and builder (`hourlytemp/measure.py`, `hourlytemp/build_candles_job.py`) are replaced by one file, `hourlytemp/hourlytemp.py` (commands `job` and `measure`), built from this text. Where an earlier section is less exact than this one, this one is right. Still zero tries, still a measurement, still no result read and no outside reading.

1. **Sample.** Every settled market of the four series in the `settled_` answers of the lists run, closing from 2026-11-05 00:00:00Z to 2026-11-11 23:59:59Z, with a ticker, an event, a strike (`floor_strike`), an open time and a close time. A market outside those dates stops the run. The builder never cuts the sample: over its request cap it writes no job and prints the count. It also writes no job if the settled list of any of the four series is missing, was refused, was cut short by the runner, or ends on a page that still carries a cursor (the lists job allows three pages of 1,000 a series).
2. **Step one, the settlement source.** Before any figure the reader prints `rules_primary` and `rules_secondary` of one market of each series, as listed.
3. **A look** is the minute 55, 30 or 10 minutes before a market's close time.
4. **The quote at a look, two readings, both printed.** "Carried": the 1-minute candle ending exactly at the look; if there is none, the last candle ending before it and after the market's open time (Kalshi omits a minute in which nothing changed; a market lives 60 minutes, so no carried quote is older than that). If the candle found shows 0.00 and 1.00, or lacks a side, there is no quote; the search does not go further back. "Exact": only the candle ending exactly at the look. A quote is two-sided when 0 < bid < ask < 1.
5. **The money, from quotes alone.** In one event at one look, take its strikes that have a two-sided quote, in strike order. Rank 0 is the strike whose YES mid is nearest 50c; on a tie the lower strike. A strike's rank is its distance from rank 0 in that order. "Near the money" is rank 0, 1 or 2.
6. **Costs.** Round trip of a strike (information): its spread plus 2 x 0.07 x mid x (1 minus mid). **One-way entry cost of a strike: half its spread plus the fee as charged at the YES ask plus 1c** (0.07 x p x (1 minus p), rounded up to the next cent; p is held at 99c at most).
7. **Per city and look, over the seven days:** strikes with a quote; two-sided strikes and their share; the median spread; the median round trip; near the money: the count, the median round trip and the median one-way entry cost; the share of two-sided strikes whose mid is 95c or more or 5c or less; the median ask of the nearer-certain side at rank 1, rank 2 and rank 3 or more (the YES ask for a strike below the rank 0 strike, 1 minus the YES bid for a strike above it). A median of an even count is the mean of the two middle values.
8. **Per city:** the share of market-minutes with a trade: candles with volume above zero, over 60 minutes for each market.
9. **Size at the touch (a level only):** from the `open_` answers, the median of the YES bid and YES ask sizes above zero, per series.
10. **The line (unchanged): the family is CLOSED as too costly if the median one-way entry cost near the money is above 4c at every look in every city.** Read exactly: under one reading of the quote, the family is "closed" if all twelve city-and-look medians exist and each is above 4c; "not closed" if at least one of them is 4c or less; and "cannot say" otherwise (none is 4c or less but one is missing). **The verdict is CLOSED only if both readings say closed, NOT closed only if both say not closed, and otherwise "depends on the reading of a missing minute: not decided".** If the candle run did not finish, or any request of its job was refused, cut short or not answered, the verdict is "the candle pull is not whole: not decided" whatever the figures say. Nobody picks a reading after seeing the figures (the Head's ruling on VOIDSNAP's carry, applied here from the start).
11. Every comparison against a line carries a tolerance of 1e-9. A printed figure rounds a half up (cents to two places, shares to one). The held-out folder guard runs on every path. Every printed figure line is labelled "measurement, not a rule".
12. **What it cannot show:** whether any rule makes money (no result is read); how any outside reading relates to the settled value (none is read); depth beyond one level on markets open at the pull; and whether a carried quote could have been paid (a carried ask is a quote last seen).

## Dated amendment 2, Nov 13, 2026, 02:18Z: two rulings and the audit's hardening, still before any list or candle of these series was pulled

Auditor B read the first frozen reader (commit 3bceb4bc) and found pin 6 could be read two ways, plus gaps the text did not close. The Head of R&D ruled on the two open points (seq 3, 02:17Z). Nothing has landed. Where this amendment and an earlier line differ, this amendment is right.

1. **Pin 6, the one-way entry cost (the Head: reading 1, the rule (d) template).** It is half the spread, plus the fee computed AT THE PRICE of the YES ask plus 1c (that price held at 99c at most). Only the fee is rounded up to the next cent. The sum is not rounded. No flat 1c is added. Worked: bid 48c, ask 50c: 1.00c plus the fee at 51c (1.7493c, charged as 2c) = 3.00c. Bid 47c, ask 50c: 1.50c + 2c = 3.50c. (The other reading, the fee at the ask plus a flat 1c, would give 4.00c and 4.50c; it is NOT the rule.)
2. **Pin 1, a listed market lacking a strike, an event or a time (the Head: stop).** The builder writes no job and the reader refuses; the count goes to the Head of R&D. No market is skipped.
3. **A market's life.** If any sampled market's close time minus its open time is not exactly 3,600 seconds, the builder writes no job and the reader refuses (pin 4's carry and the job's time ranges assume the 60 minute life).
4. **The strikes must be one ladder of "above" thresholds.** If the settled lists carry more than one `strike_type`, or one that is not `greater` or `greater_or_equal`, the builder writes no job and prints the types and their counts; the reader refuses. Pin 5's strike order and pin 7's nearer-certain side assume a lower strike is the likelier YES. If these markets are range brackets, the note needs re-pinning and the Head is sent what the list says.
5. **The reader ties its three inputs together and refuses otherwise:** `markets.json` must equal the sample re-read from the lists run; the candle run's manifest must carry its job; and the tickers that job asked for must equal the sample's tickers.
6. **Files.** Every file opened inside a run is tested by the held-out guard and must lie inside that run folder (a link or a `..` that leads elsewhere is refused).
7. **Printed with the figures:** the number of candles that carry no volume field at all (each counts as a minute with no trade), and the number of candle requests answered whole out of those asked. The size median rounds a half up like every other printed figure.

## Dated amendment 3, Nov 13, 2026, 02:28Z: three wordings fixed after the second build, text only (the Head of R&D, seq 5, 02:24Z)

The Testing Desk built a second reader from this note alone (commit a7b2a5fc on `claude/testing-desk`) and printed it on fifteen made-up cases before comparing: 1,848 figures were compared across the seven measured cases and 2 differed, both one point; every twelve-median line and every verdict agreed. **All three points below were found by that second build, and in each case the TEXT was moved to what the first, audited reader does, because none of them touches a cost, a median or a verdict.** The reader (sha256 f443ae60...) is unchanged. Nothing has landed.

1. **Pin 7, "strikes with a quote".** What is counted and printed is the **strikes with a candle found** under the reading (the candle ending at the look, or the carried one), **an empty book included**. Pin 4 still holds for everything else: a candle showing 0.00 and 1.00, or lacking a side, gives no quote, and the strike is not two-sided. This count is printed beside the figures and feeds no line.
2. **Pin 7, the two-sided share** is the two-sided strikes over the strikes with a candle found. The number of sampled markets is printed, so the share over all sampled strikes can be worked by hand.
3. **The candle job's requests (pin 1's builder).** One request holds one time range, at most 100 tickers and at most 9,800 candles (tickers times the minutes of the range, both ends counted). Clock hours are taken in time order; an hour shares a request with the next hour only if that hour closes at most 3,600 seconds later and both limits still hold; otherwise it has its own request. A request's range runs from 60 minutes before its first close to its last close. The cap is 110 requests; over the cap, or with an hour that breaks a limit by itself, no job is written and the count goes to the Head of R&D.
4. **Pin 9, the size at the touch** is the one pooled median of the YES bid and YES ask sizes above zero per series (the second build printed the same pooled figure, with the two sides beside it).

## Held-out line, Nov 13, 2026, 07:06Z, before any list or candle of these series was pulled (the Head of R&D's order of 06:53Z). No pin, figure or reading changes.

The sample is unchanged: the four series KXTEMPNYCHS, KXTEMPMIAH, KXTEMPLAXHS and KXTEMPCHIHS, closes 2026-11-05T00:00:00Z to 2026-11-11T23:59:59Z. Every card found that ever held out these series, with its state:

- **W-CAT-CAL1 weather (Refinement):** held-out closes at or after 2026-10-20T06:00:00Z, never read. **Released by the Head of R&D 2026-11-13 (dated line in its registration on `claude/refine-live`, 06:51Z): the held-out will never be scored under that card. Development here.**
- **WXNEW1 (research chat, run once 2026-10-31):** frozen holdout 2026-10-19 to 2026-10-31, not read. Miami FALSIFIED; Chicago, New York and coastal Los Angeles not tested (NOT_ENOUGH_DATA), no forward plan. Its dates end before this sample starts: no overlap.
- **WXOTHER1 (research chat, 2026-11-04):** declares the hourly family a DUPLICATE of WXNEW1 and does not score it. It holds nothing out on these series.
- **This note's own later card, if one is ever written:** the seven sample days already carry result fields, so they could only be development for it (pin 5, as written).

No OPEN card holds any of the four series inside the sample dates.

**What was swept:** by whole-word series name, every text file of main, `rnd-queue`, the desk branches (testing, history miner, idea desks A and C, forensics, probe, stocks, research audit), `claude/refine-live` and the research chat's whole tree (`claude/epic-ptolemy-0amjd9` at 79724f00). Because the research chat and Refinement often write series as a pattern or a category, their weather registrations (WXNEW1, WXOTHER1, WXENS1, WXLOW1, FAMWX) and Refinement's category cards were also read by hand. Not swept: the website's feature branches, which hold no research card. A card that names these series only by a pattern in a file not read by hand could have been missed.

**Cross-check against the held-out registry, Nov 13, 2026, 07:10Z** (`HELDOUT_REGISTRY.md` on `rnd-queue` at ad42ec54, Desk A's lookup; its states are conservative and mostly taken from file names). Its rows for these series: W-CAT-CAL1 weather RELEASED; WXNEW1 **OPEN** (its frozen holdout is 2026-10-19 to 2026-10-31, which ends before this sample starts, so open or closed it does not overlap); WXOTHER1 CLOSED UNREAD (frozen cut 2026-10-03T16:00Z, never fetched; it scored nothing and calls the hourly family a duplicate); this note itself, state unknown there. The registry's table of series lists KXTEMPCHIHS and KXTEMPMIAH under WXNEW1 and does not list KXTEMPNYCHS or KXTEMPLAXHS; WXNEW1's amendment names all four, as the line above says. Nothing in the registry adds a card to the line above, and the conclusion stands: no OPEN card holds any of the four series inside 2026-11-05 to 2026-11-11.

## AMENDMENT 4, Nov 13, 2026, 08:14Z: strikes added after their hour opened are KEPT, each read from its own open (the Head of R&D's ruling of 08:09Z). Written after the lists landed and before any candle was pulled.

**What was read before this was written, and what was not.** The lists run `pull/HOURLYTEMP_LISTS/2026-11-13T0756Z_43389350994/` passed Auditor B's structure check and was read for tickers, strikes' presence and times only: by the audited builder (which stopped, as Amendment 2, item 3 required), by Auditor B's independent count, and by `hourlytemp/lives_breakdown.py` (three fields: ticker, open_time, close_time; read by Auditor B before it ran). No candle exists, and no price, strike value, volume or result has been read. The counts that led to the ruling: 6,720 settled markets in 658 series-hours; 140 markets with a life under 3,600 seconds (540 to 2,940), all inside 43 series-hours, and in each of those the hour's other 10 markets lived the full 60 minutes; none longer than 3,600 seconds; no close off the clock hour.

**The ruling, in the Head's terms. It replaces Amendment 2, item 3; no other pin changes except where a line below says so.**

(a) **A market that opened after its hour's ladder (a life above 0 and under 3,600 seconds) is kept.** At a look whose time is at or before the market's own open time it is **"not yet open"**: it is not an empty book, it is not a strike with a quote candle, and it is never a candidate for the money (pin 5 ranks only strikes with a two-sided quote, and a strike that is not yet open has none). The count of not-yet-open strikes is printed on every line. Its carried quote looks back only to its own open, as pin 4 already says. In the candle job it is asked for in a request whose range starts at its own open and ends at its close; late markets share a request only when they have the same open time and the same close time.

(b) **The builder's stop on a life other than 3,600 seconds becomes a printed count with the table of lives** (seconds, count, per series). The builder and the reader still STOP on any life LONGER than 3,600 seconds, on any close that is not on the clock hour, and on a market whose open is at or after its close: none exists in the sample, and one would mean something else is wrong.

(c) **Every reported figure is printed twice, one line under the other: on ALL series-hours, and without the series-hours that gained strikes** (a series-hour "gained strikes" if at least one of its markets has a life under 3,600 seconds). The series-hours that gained strikes are listed (series, close hour in UTC, strikes added). **The headline, and the only figure the cost line and the verdict read, is the all-hours figure**, as "the sample is never cut" requires. The same line worked on the hours that gained none is printed as information only.

(d) **The missing clock hours are printed as they are, per series, and are not filled** (in the lists: 2026-11-05T09 and T10 in all four series, and six more in New York).

**Three consequences, stated so that nobody has to infer them:**
1. **Pin 8, the share of market-minutes with a trade,** is taken over each market's own minutes of life (60 for a full market, fewer for a late one), not over 60 minutes for every market.
2. **The request cap of the candle job is 140 (it was 110).** Late markets cannot share the full-hour requests under (a), so they add at most one request per distinct opening time per hour: at most 47 from the counts above, on top of about 84 full-hour requests (two clock hours a request, as before). The builder prints the exact count, and over the cap it writes no job; the count and the held-out line go to the Head of R&D before any dispatch. Full-hour requests keep ids `h001` onward; late-strike requests are `l001` onward.
3. **The job's held-out line** names every card found that ever held out these series, with its state (the dated held-out line above).

**What stays an inference.** That the added strikes are the ones nearest the money is my reading of why a ladder is extended; no strike value has been read, and it stays an inference until the read. The twin lines of (c) exist so that the reader can see how much the hours that gained strikes carry.

**Process from here (the Head's order):** the reader's new hash; Auditor B's diff against this amendment; the Testing Desk's re-run of its own build on made-up fixtures that include a strike opening 21 minutes before the close, one opening 9 minutes before, and an hour with two opening times (`hourlytemp/fixture_inputs_MADE_UP_DATA/case_16` and `case_17`; cases 18 and 19 are the two new stops); only then the candle job, which goes to the Head first with its request count and held-out line.
