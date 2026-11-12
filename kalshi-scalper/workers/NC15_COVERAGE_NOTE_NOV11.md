# NC15COVER1: coverage read of the first NC15 file (2026-11-11, job 1932)

Zero-call, not a test, scores nothing. Read: book.csv, trades.csv (row counts only), coverage.csv (counts, gaps, note column; the `result` column was NOT read), clock.csv from `origin/nc-data:nc15/2026-11-11/1932/`. No outcome, price path or P/L was computed. Recorder: `scripts/record_nc_book.py` (PR 776): 11 non-crypto 15 minute series, WHOLE window of every market, book every 5 s (best 5 YES and 5 NO bids), tape swept 60 s after each close, stops 2026-12-31. (Not "last N minutes".) Frozen-window key (DATA_INVENTORY): none applies to NC15; it is new data after every freeze.

## (1) and (2) Series, windows, span
Job span: first poll 19:32:21Z, closes 19:45Z to 00:00Z (18 close times, 4.5 h). Tickers are `<SERIES>-26NOV11HHMM-MM`.

| Series | Windows with a book | Closes with "no open market" | Tape trades |
|---|---|---|---|
| KXSILVER15M | 8 | 10 | 18,195 |
| KXCOPPER15M | 11 | 7 | 17,819 |
| KXWTI15M | 13 | 5 | 51,070 |
| KXEURUSD15M | 13 | 5 | 4,647 |
| KXGBPUSD15M | 14 | 4 | 3,684 |
| KXUSDJPY15M | 15 | 3 | 4,429 |
| KXHYPE15M | 16 | 2 | 30,500 |
| KXBNB15M | 15 | 3 | 32,279 |
| KXAUDUSD15M | 15 | 3 | 5,110 |
| KXUSDCAD15M | 16 | 2 | 4,105 |
| KXNATGAS15M | 17 | 1 | 33,614 |

153 windows with a book of 198 close-by-series slots; 45 are "no open market" (the commodity and forex markets are closed or not listed at those hours; this is the evening US session, so it is NOT a day-average). The first close (19:45Z) is "joined late" for all 11.

## (3) Per window quality (all series alike)
- Book snapshots per window: median 174 to 177 (180 possible at 5 s). First snapshot median 868 to 883 s before the close, last median 3.3 to 3.4 s before it. Only 35 of 153 windows start at 880 s or more (the rest started a few seconds late, market open before the poll found it); none is missing the last minutes.
- Gaps: largest gap 5.2 s in every series (the 5 s poll plus 0.2 s); share of windows with a gap over 10 s: 0 of 153. n429 = 0, batch fallback = 0 everywhere, polls = ok_polls (152 of 152 in the late-joined window).
- Tape trades per window (median): WTI 2,890; Silver 2,096; BNB 2,068; HYPE 1,802; NatGas 1,516; Copper 1,332; EURUSD 358; AUDUSD 302; USDJPY 238; GBPUSD 231; USDCAD 211. Total 205,452.

## (4) Clock
5 hourly SNTP offsets: 6, 3, 4, 9, 1 ms. Skew is under 10 ms; ignorable against a 5 s poll.

## (5) Spread and touch depth at the looks (coverage only; both sides quoted at the nearest snapshot within 10 s)
Both sides quoted: 153 of 153 windows at both looks. Spread = 1 - best YES bid - best NO bid, in cents. Touch = the smaller of the two best-bid sizes, median (contracts).

| Series | Spread med 10m / 6m (c) | Share over 3c 10m / 6m | Touch med 10m / 6m |
|---|---|---|---|
| SILVER | 1 / 1 | 0.00 / 0.00 | 110 / 68 |
| COPPER | 3 / 3 | 0.27 / 0.27 | 5 / 11 |
| WTI | 1 / 1 | 0.00 / 0.00 | 145 / 54 |
| EURUSD | 2 / 2 | 0.31 / 0.08 | 216 / 275 |
| GBPUSD | 2 / 1.5 | 0.21 / 0.21 | 165 / 239 |
| USDJPY | 2 / 2 | 0.20 / 0.13 | 166 / 170 |
| HYPE | 1 / 0.8 | 0.00 / 0.00 | 10 / 6 |
| BNB | 1 / 1 | 0.00 / 0.00 | 6 / 2 |
| AUDUSD | 2 / 1 | 0.20 / 0.07 | 557 / 9 |
| USDCAD | 7 / 5.5 | 0.88 / 0.75 | 7 / 8 |
| NATGAS | 1 / 2 | 0.18 / 0.24 | 5 / 19 |

Small n (8 to 17 windows per series), one evening, so these are coverage facts, not a distribution estimate. BNB, HYPE, copper, natgas and USDCAD have a thin touch (median under 20 contracts), which matters for any depth-asymmetry cell.

## (6) Extrapolation
Assumptions: the recorder runs back to back in 4 to 4.5 h jobs (cron 5,35 and 20,50, one job at a time, 330 min timeout); observed uptime so far = one job fully pushed by 00:15Z with no gap inside it, and run 3 started by schedule at 23:43Z; hand-offs between jobs may lose up to one close. Windows per day per series = (windows with a book in this job / 18) x 96, which holds only if the evening share holds all day (it will NOT for the commodities and forex, which close for part of the day):

SILVER 43, COPPER 59, WTI 69, EURUSD 69, GBPUSD 75, USDJPY 80, AUDUSD 80, BNB 80, HYPE 85, USDCAD 85, NATGAS 91.

7 full days of coverage: data began 2026-11-11 19:32Z, so with no further lost job the NC15DEPTH1 start rule is met 2026-11-18 about 20:00Z. If a job is dropped (GitHub drops scheduled starts; the second cron pair is the cover), each dropped 4 h job pushes the date by 4 h. Treat 2026-11-19 to 2026-11-20 as the planning date.

NC15DEPTH1 (IDEA_CARDS_NOV11B card 12) states no cell definition, only "depth asymmetry at the 10 minute look vs outcome and next-minute drift; cheap side and mid". Windows needed for n >= 100 per cell: 100 x (number of cells). With a 2 x 2 split (cheap side by asymmetry high or low) that is 400 windows per series; at the per-day counts above, 400 windows takes about 4.4 (natgas) to 9.3 (silver) days of recording, so 7 days suffices for 9 of 11 series and falls short for silver (~300) and copper (~410, borderline) on this evening share. With a single pooled cell per series, 100 windows needs 1.2 to 2.3 days. Pooling across series is the alternative for thin ones.
