# TAPECLOCK1 result: the tape says the quote is the old side (2026-11-12)

Registration: `TAPECLOCK1_REGISTRATION.md` (commit d972bca, before anything was computed). Script `tapeclock1.py`, raw output `results/TAPECLOCK1.json`. A measurement: no rule scored, no settlement result loaded, zero tries. Public recorded data, zero Kalshi requests, nothing about the live account.

**The answer in one sentence.** The quote recorder is the old side: the R6 order book matches the price takers actually paid when it is read within about a second of the trade, and the quote recorder's ask only matches that price when it is read 7 to 8 seconds AFTER the trade.

**Sample.** `KXBTC15M`, closes 2026-10-29 22:15Z to before 2026-11-05. Trades where the taker bought a side at 5c to 30c (the cheap side by the trade's own price), 150 to 30 seconds before the close, in windows that have both sources: 412,603 trades with a row from each source at the trade's time, in 161 windows. gap = trade price minus the source's ask for the side bought. A positive shift means the source is read AFTER the trade.

| | R6 order book | Quote recorder (market list) |
|---|---|---|
| **150 to 120 s before the close** (93,982 trades, 134 windows) | | |
| Within 1c of the trade price, read at the trade's time | 70.2% (67.1 to 73.4) | 33.0% (28.1 to 37.8) |
| Mean absolute gap, read at the trade's time | 1.5c (1.2 to 1.9) | 5.0c (4.2 to 5.9) |
| Shift at which it matches the tape best | **+1 s** | **+7 to +8 s** |
| Within 1c / mean absolute gap at that shift | 81.5% / 0.9c | 53.0% / 2.4c |
| **120 to 30 s before the close** (318,626 trades, 137 windows) | | |
| Within 1c, read at the trade's time | 52.9% (50.1 to 55.5) | 20.0% (18.1 to 22.2) |
| Mean absolute gap, read at the trade's time | 2.6c (2.3 to 2.9) | 8.8c (7.6 to 10.3) |
| Shift at which it matches best | **+1 s** | **+7 s** |
| Within 1c / mean absolute gap at that shift | 65.8% / 1.7c | 36.4% / 4.4c |

Share within 1c of the trade price by shift, 150 to 120 s:

| Shift (s) | -6 | -4 | -2 | -1 | 0 | +1 | +2 | +3 | +4 | +6 | +7 | +8 | +10 | +12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Book | 27% | 34% | 46% | 55% | 70% | **82%** | 75% | 61% | 52% | 40% | 35% | 30% | 25% | 23% |
| Quote | 17% | 21% | 26% | 29% | 33% | 39% | 44% | 48% | 50% | 53% | **54%** | 53% | 50% | 42% |

**Reading, by the registered rule.**
- **The book is current.** Its agreement with the tape peaks at +1 second and falls away steeply on both sides. The peak sits at +1 rather than 0 because "the last 2 second poll before a trade" is about a second old on average; a poll taken just after the trade is the nearest one in time.
- **The quote is old by about 7 seconds.** Its agreement rises slowly, peaks at +7 to +8 seconds and stays low throughout: a copy refreshed every 11 seconds never lines up sharply with anything. At the trade's own time only a third of quote rows are within a cent of what the taker paid.
- The two peaks are 6 to 7 seconds apart, which is the 5 to 6 second shift QUOTEVSBOOK1 found between the quote and the book (the two measures match "nearest" and "last before" slightly differently).
- So QUOTEVSBOOK1's reading stands with the missing clock supplied: the order book R6 records is the market as it is; the market-list quote is the market as it was several seconds earlier.

**Both sources are worse nearer the close**, because the price moves faster: the book is within 1c of the tape on 53% of trades at the trade's time in the last two minutes (66% at its best shift), the quote on 20% (36%). The headline 57% agreement between quote and book in QUOTEVSBOOK1 is for 150 to 120 seconds; in the last two minutes it is 42%, as that file's secondary span says.

## Sizes (the one line registered, and it is weak)

Of 105,976 cheap-side taker buys that printed within half a second after a book poll, only 28.7% printed at that poll's ask at all: in 71.3% the ask had already moved within half a second. Among the 30,414 that did print at the poll's ask, 94.1% were at or under the size displayed there (median trade 1.5% of the displayed size), and 5.9% were LARGER than the displayed size, some by hundreds of times.

What that supports: the size displayed at the touch is not an upper limit on what trades there (one print in seventeen at the touch is bigger than the size shown half a second earlier), and the touch itself is gone within half a second most of the time. What it cannot show: whether a displayed size is real resting interest. A size that is never hit leaves nothing on the tape, so the tape cannot confirm or refute sizes at levels 2 to 5. The Verification Analyst's point stands: R6's sizes change at every level every 2 seconds and should not be read as depth that would still be there.

## Caveats

Six days, one series. Trades are matched to the last source row before them, so each source's own polling gap (2 s for the book, 0.6 s for the quote) is inside the comparison; that favours the quote slightly and it still loses. Not yet re-checked by the Verification Analyst.
