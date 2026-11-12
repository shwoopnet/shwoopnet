# QUOTEVSBOOK1 result, Part 1: the quote recorder's ask is a cached quote about 5 to 6 seconds behind the order book (2026-11-12)

Registration: `QUOTEVSBOOK1_REGISTRATION.md` (commit 1539121, before any quote file was fetched). Script `quotevsbook1.py`, raw output `results/QUOTEVSBOOK1.json`. A measurement: no rule scored, no settlement result loaded (the quote recorder's results files were not fetched), zero tries. Public recorded data, zero Kalshi requests, nothing about the live account. **Part 2 (the model's edge rows against its other rows) waits for Desk A's rows and will be added here.**

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
- (c) "the quote shows asks the book does not, concentrated on edge rows": **the first half is established for ALL rows** (about one row in eight shows an ask 2c or more below the book at that moment, one in thirteen 4c or more, one in thirty 10c or more). The second half, concentration on the model's edge rows, is Part 2 and is not read yet.

**What follows without waiting for Part 2.** A rule that compares live spot prices with this quote compares "now" with "up to 11 seconds ago". Whatever part of its signal is "the quote has not caught up with spot" is the copy's age, not the market's. Any figure priced at the quote recorder's ask is not a tradable figure; only a replay at the book means anything. That applies to every test built on the `quotes/` files (the 15 minute quotes and, by the same endpoint, the `ladder.csv` strikes), not only CFRTI.

## Two things for engineering (Main), not decided here

1. **The bot decides on the market object too**, but through the single-market read (`/markets/{ticker}`), not the list. This measurement cannot say whether that read is served from the same kind of copy. It can be settled with no new request from the live order rows since Nov 11, which hold both the quote the bot saw and a book snapshot read about a second later; or with a few dozen paired public reads of the two endpoints. If the single-market read is also a copy several seconds old, then the bot's "ask seen" is stale before it sends, which would be a mechanical cause of unfilled limits, and reading the order book for the decision price would remove it. This desk has no live rows and makes no claim about the bot.
2. **Recorders that read the market list** (quotes, ladder, daily, politics, combo) record a quote up to about 11 seconds old. For slow markets that is harmless. For anything timed to seconds it is not; R6 and NC15 read the order book and are not affected.

## Caveats

Six days, one series, public unauthenticated reads from GitHub's runners; the copy's refresh time may differ by endpoint, by series, by authentication or over time. The 2 second book polls limit how well any single row can be matched, which is part of why agreement tops out at 76%. Not checked by the Verification Analyst.
