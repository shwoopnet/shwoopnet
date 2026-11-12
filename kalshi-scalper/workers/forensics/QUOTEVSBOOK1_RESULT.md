# QUOTEVSBOOK1 result, Part 1: the quote recorder's ask is a cached quote about 5 to 6 seconds behind the order book (2026-11-12)

Registration: `QUOTEVSBOOK1_REGISTRATION.md` (commit 1539121, before any quote file was fetched). Script `quotevsbook1.py`, raw output `results/QUOTEVSBOOK1.json`. A measurement: no rule scored, no settlement result loaded (the quote recorder's results files were not fetched), zero tries. Public recorded data, zero Kalshi requests, nothing about the live account. **Part 2 (the model's edge rows against its other rows) is at the end of this file.**

**Sample.** `KXBTC15M`, closes 2026-10-29 22:15Z to before 2026-11-05. 415 windows have an R6 book; 153 of them also have quote-recorder rows on the cheaper side at 5c to 30c. Primary span (150 to 120 s before the close): 4,506 quote rows in 130 windows. Secondary span (120 to 30 s): 8,197 rows in 132 windows. d = the quote's ask minus the book's ask; negative means the quote shows a cheaper ask than the book. Intervals 95%, resampling windows.

## The finding

**The quote recorder does not see the market at the time it stamps. It sees a copy that is refreshed about every 11 seconds.**

1. **The same quote is returned for about 11 seconds at a time.** The quote recorder polls every 0.6 seconds, but the market list it reads (`/markets?tickers=...`) returned only 4,360 distinct states in 72,012 polls: 16.5 polls per state. The time between changes is 10.4 to 11.5 seconds for the middle half of changes (median 10.96 s; 85% are between 10 and 12 s). The order book R6 reads is never the same from one 2 second poll to the next on Bitcoin (0.0% of a sample of 61,014 polls from ten runs; 0.4% on gold). So the list quote is between 0 and about 11 seconds old when read, about 5.5 on average.
2. **The time-shift curve says the same thing.** Comparing each quote row with the book k seconds away, the disagreement is smallest when the book is taken 5 to 6 seconds EARLIER than the quote row's time stamp, in both spans and on every one of the six days (best shift -6, -5, -6, -6, -5, -6 by day on a mid-against-mid check). The registered search was -3 to +3 seconds; the minimum sat on the -3 edge, so the curve was extended to -20 (said here as a step beyond the registration).
3. **It is not a clock offset between the two recorders.** R6's clock against the exchange's own Date header: median -18 ms. The quote recorder's network time checks: median +3 ms (range -8 to +18 ms). Its requests take 0.11 s. Both clocks are right; the data is old.

| Primary span, 150 to 120 s | As stamped (shift 0) | Book taken 5 s earlier |
|---|---|---|
| Mean absolute difference, nearest poll | 2.9c | 1.9c |
| Bracket measure: within 1c | 57.0% (52.6 to 61.1) | 76.0% (72.8 to 79.1) |
| Quote 2c or more BELOW the book | 12.8% (9.6 to 16.4) | 9.6% (7.4 to 12.0) |
| Quote 4c or more below | 7.7% | 5.1% |
| Quote 10c or more below | 3.1% | 1.4% |
| Quote 2c or more ABOVE the book | 23.8% (20.0 to 27.7) | 10.8% (8.6 to 13.1) |
| Quote 4c / 10c or more above | 10.5% / 2.2% | 3.6% / 0.9% |

Against the single poll before the quote row (as stamped): within 1c 50.3%, quote lower by 2c / 4c / 10c or more 15.4% / 9.0% / 3.6%, higher by the same 27.0% / 11.7% / 2.4%. Against the poll after: within 1c 39.7%, lower 18.4% / 11.2% / 4.5%, higher 33.3% / 15.5% / 3.5%. ("Bracket" counts a quote as agreeing when it lies between the book ask just before and just after it.)

Secondary span, 120 to 30 s, as stamped: within 1c 42.4% on the bracket measure, mean absolute difference 5.2c; with the book taken 6 s earlier, 67.2% and 3.1c. Closer to the close the price moves faster, so an 11 second old quote is further off.

By price, primary span, bracket measure as stamped: 5c to 10c within 1c 64.7%; 10c to 20c 54.2%; 20c to 30c 48.8%.

Shift curve, primary span (mean absolute difference to the nearest poll): -10 s 2.54c, -8 s 2.13c, -6 s 1.93c, -5 s 1.93c, -4 s 1.98c, -3 s 2.09c, -2 s 2.29c, -1 s 2.57c, 0 s 2.91c, +1 s 3.23c, +2 s 3.50c, +3 s 3.79c.

## Reading against the registered rule

- (a) "the recorders agree and the 4 of 16 was chance": **NO.** As stamped, only 57% of rows agree within 1c.
- (b) "a clock offset explains it": **NOT AS WORDED.** A shift of 5 to 6 seconds lowers the mean absolute difference by 34%, but both clocks check out and only 76% agree within 1c after it (the bar was 90%). It is not an offset; it is a quote served from an 11 second copy, so each row is stale by a different amount between 0 and 11 seconds.
- (c) "the quote shows asks the book does not, concentrated on edge rows": **the first half is established for ALL rows** (about one row in eight shows an ask 2c or more below the book at that moment, one in thirteen 4c or more, one in thirty 10c or more). The second half, concentration on the model's edge rows, is Part 2 below: the direction is as (c) says and the interval is above zero, on 16 and 12 edge rows.

**What follows without waiting for Part 2.** A rule that compares live spot prices with this quote compares "now" with "up to 11 seconds ago". Whatever part of its signal is "the quote has not caught up with spot" is the copy's age, not the market's. Any figure priced at the quote recorder's ask is not a tradable figure; only a replay at the book means anything. That applies to every test built on the `quotes/` files (the 15 minute quotes and, by the same endpoint, the `ladder.csv` strikes), not only CFRTI.

## Two things for engineering (Main), not decided here

1. **The bot decides on the market object too**, but through the single-market read (`/markets/{ticker}`), not the list. This measurement cannot say whether that read is served from the same kind of copy. It can be settled with no new request from the live order rows since Nov 11, which hold both the quote the bot saw and a book snapshot read about a second later; or with a few dozen paired public reads of the two endpoints. If the single-market read is also a copy several seconds old, then the bot's "ask seen" is stale before it sends, which would be a mechanical cause of unfilled limits, and reading the order book for the decision price would remove it. This desk has no live rows and makes no claim about the bot.
2. **Recorders that read the market list** (quotes, ladder, daily, politics, combo) record a quote up to about 11 seconds old. For slow markets that is harmless. For anything timed to seconds it is not; R6 and NC15 read the order book and are not affected.

## Caveats

Six days, one series, public unauthenticated reads from GitHub's runners; the copy's refresh time may differ by endpoint, by series, by authentication or over time. The 2 second book polls limit how well any single row can be matched, which is part of why agreement tops out at 76%. Not checked by the Verification Analyst.

## Part 2: the rows the CFRTI model picked against the rows it did not (added 2026-11-12, after Desk A's rows arrived)

Input: `kalshi-scalper/workers/desk_a_verify/cfrti_dev_allcheap.csv` on `claude/idea-desk-a` (437 rows: form, t0_utc, ticker, side, ask_seen, quote_t_send_ms, edge; closes before 2026-11-05; no outcome column, and the script refuses a file that has one). The quote's own send time is used as its time. 105 three-venue rows and 101 Kraken-only rows have an R6 book (the rest are before the recorder began or in its gaps). Every row is its own window. d = ask_seen minus the book ask; negative = the quote the model saw was cheaper than the book.

| | Three-venue: edge rows (16) | not edge (89) | Kraken-only: edge rows (12) | not edge (89) |
|---|---|---|---|---|
| Mean d, bracket measure | -2.3c (-5.7 to 0.0) | +1.5c (+0.5 to +2.4) | -0.6c (-2.2 to +1.2) | +1.4c (+0.5 to +2.3) |
| Quote 2c or more BELOW the book | 31.2% (12.5 to 56.2) | 5.6% (1.1 to 11.2) | 33.3% (8.3 to 58.3) | 5.6% (1.1 to 11.2) |
| Quote 4c or more below | 25.0% | 2.2% | 25.0% | 2.2% |
| Quote 2c or more ABOVE the book | 0.0% | 33.7% | 8.3% | 31.5% |
| Within 1c | 68.8% | 53.9% | 58.3% | 56.2% |
| Mean d against the poll AFTER the quote | -4.8c (-10.0 to 0.0) | +1.6c | -3.6c (-9.8 to +1.0) | +1.5c |

Edge rows minus the others:

| | Three-venue | Kraken-only |
|---|---|---|
| Mean d, bracket | -3.7c (-7.5 to -1.2) | -2.0c (-3.9 to +0.1) |
| Share with the quote 2c or more below the book | +25.6 points (+3.5 to +50.6) | +27.7 points (+1.6 to +55.0) |
| Share 4c or more below | +22.8 points (+4.0 to +43.8) | +22.8 points (0.0 to +48.9) |
| Mean d against the poll after | -6.4c (-12.1 to -1.6) | -5.1c (-11.1 to -0.3) |

**Reading.** On the rows the model did NOT pick, the quote is on average 1.5c ABOVE the book and is 2c or more above it a third of the time: the ordinary effect of an old quote on a side whose price is drifting down. On the rows the model picked it is the other way round: the quote is below the book on average, and 2c or more below it in about a third of them, five to six times as often as on the other rows. That is what a rule that hunts for an underpriced ask does when the ask it reads is up to 11 seconds old: it picks the rows where the old ask is lowest against the present.

**Label.** By this desk's rule, 16 and 12 edge rows are "no evidence at n = 16 and n = 12" as a rate. Said plainly beside that: the direction is the one reading (c) predicts in both forms, the interval of the difference is above zero for the three-venue form and touches zero for the Kraken-only form, and the mechanism that produces it (Part 1, 72,012 polls) is not in doubt.

**What this supports.** Reading (c): the quote recorder shows asks the book does not, more often on the rows the model picked. The registered CFRTI development figure is priced at those asks and is not a tradable figure. The book replay is the line that means something: of the 16 three-venue edge rows with a book, 9 fill at the ask seen about 2 to 4 seconds later (`results/CFRTI_DEV_REPLAY_GRID.csv`).

**For the held-out read.** Price every held-out row from the R6 book at arrival, never from the quote recorder's ask; and form the signal from the book too if that is possible, because a signal formed on an 11 second old quote and then filled at the book is a different rule from the one registered: it selects rows on a stale price and then pays the real one. Whether that changed rule has any edge is exactly what the held-out read would then measure, once, and it should be registered as such before Nov 20.

### Band note (added 2026-11-12, after Desk A said its cheap-side band is 3c to 30c)

The Part 2 tables above use every row in Desk A's file, which is its rule's own band, 3c to 30c (88 of the 437 rows are under 5c, 6 of them edge rows). Restricted to the 5c to 30c band this desk registered:

| | Three-venue | Kraken-only |
|---|---|---|
| Edge rows / other rows with a book | 15 / 71 | 10 / 72 |
| Quote 2c or more below the book (bracket): edge rows against the others | 26.7% against 7.0% | 30.0% against 6.9% |
| Difference in that share | +19.6 points (-1.8 to +43.9) | +23.1 points (-2.8 to +54.4) |
| Difference in the mean gap | -3.8c (-8.0 to -1.2) | -1.8c (-3.8 to +0.3) |

Same direction and nearly the same size, but with one or two fewer edge rows the interval of the share difference now includes zero in both forms; the mean-gap difference for the three-venue form still does not. So the edge-row concentration stays "no evidence at n = 15 and n = 10" as a rate, direction as predicted, and the conclusion rests on Part 1's mechanism rather than on these few rows. Counted on the same rows, "stale" in the earlier replay note (4 of 16 three-venue rows with the book 4c or more above the ask seen) and here (5 of 16 at 2c or more, 4 of 16 at 4c or more; Kraken-only 4 of 12 and 3 of 12) agree with Desk A's own count of 5 of 16 and 4 of 12.
