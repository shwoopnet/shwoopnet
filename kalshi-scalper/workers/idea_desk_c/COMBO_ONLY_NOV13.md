# Combo-only strategies: inventory and screen (Idea Desk C, Nov 13, 2026, about 21:35Z)

The owner, through the Head of R&D: "i want some new combo only strategies". This desk owns combo-only strategies. No price was read for scoring: only file names, columns and row counts on `combo-data`. Every idea goes to the Verification Analyst before any work. [research]

## 1. What the combo recorder captures (counts only, `combo-data` to Nov 13)

| File | Rows so far | Columns | What is NOT there |
|---|---|---|---|
| `combo/DATE/HHMM/quotes.csv` (42 runs) | 16,800 | ticker, event, open and close time, yes and no bid and ask, yes sizes, last price, volume, open interest, `legs`, `leg_tickers` (first 100 rows a run only) | Leg tickers for most rows; no leg prices; 30 minute cadence |
| `books.csv` (40 tightest a run) | 233 | top 5 YES and NO bids with sizes | Most books are empty (no depth) |
| `trades.csv` (15 most traded) | 705 | created time, yes price, count, taker side, trade id | No legs on the trade row (join by ticker to quotes) |
| `coverage.csv` | one a run | listed, pages, list_complete, selected, rows, books, trades, requests, 429s | n/a |
| Daily settled list | (written by the recorder once a day) | ticker and result | n/a |

**Missing for any combo-only rule:**
- the LEG markets' prices at the same minute as the combo quote (the recorder reads combos only);
- leg tickers beyond the first 100 quote rows a run;
- anything finer than 30 minutes.
Combos are created on demand (RFQ) and most settle within minutes to hours (MVE1's metadata note), so a 30 minute poll sees few of them twice.

## 2. The owner's four ideas, screened against existing combo work (before the VA)

| Idea | Closest existing | My reading | What it would need |
|---|---|---|---|
| (a) Combo price against the product of its single legs (correlation mispricing after fees) | **MVE1** (V2, registered Nov 5: combo cheap side against the product of its legs' mids), **COMBOPRICE1** (V2 design: independence product, Frechet bounds, copula sensitivity, edge per dollar) | A VERSION of MVE1 and COMBOPRICE1 unless the side or band differs; for the VA | Leg quotes at the same minute (1 + legs reads a combo) |
| (b) Legs that become near-certain mid-event | **COMBODONE** (this desk: combos with a leg already settled) | A near-certain leg is COMBODONE's mechanism before settlement; likely a version; for the VA | Leg prices or the in-game state over time |
| (c) Combo pricing right after one leg settles | **COMBODONE** (this desk; open card, waiting for a week of recording) | The SAME as COMBODONE | Leg settlement times (public results) and combo quotes soon after; the 30 minute cadence is coarse |
| (d) How combo makers price correlated legs | MVE1, COMBOPRICE1 (break-even rho) | Same as (a) | As (a) |

## 3. One mechanism of this desk's own, for the VA

**CROWDLEG: the RFQ maker's inventory on a crowded leg.**
- **The idea:** when many combos that share one leg trade in a short time, the maker that quotes combos carries a large one-sided exposure to that leg. It may then price new combos containing that leg dearer (YES costlier). The other side is the maker managing inventory, a named counterparty with a reason to skew.
- **The rule (sketch, frozen only at registration):** after at least K combo trades in an hour that share a leg (counted from the trades joined to their legs), buy NO on the next listed combo containing that leg, if its NO ask is 20c to 80c, and hold.
- **Closest existing:** MVE1 (price against legs, no flow signal) and S3, the combo house side (NO on high-priced combos, no flow signal).
- **Data needed:** legs for every traded combo (a market read per traded ticker, or the recorder widened to keep `leg_tickers` on all rows), and trades for more than the 15 most traded.

**Known guards on all of these:**
- the combo house side is an owner exception for paper only;
- the conditional tie premium is declined;
- parlay limits are $2 a parlay, a $40 total stop, 10c per dollar of paper edge first, 2 to 30 legs.
