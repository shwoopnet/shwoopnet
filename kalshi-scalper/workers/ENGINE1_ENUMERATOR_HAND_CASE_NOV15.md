# ENGINE1 enumerator hand case (Desk A, Nov 15, 2026). Worked by hand BEFORE the enumerator code. Invented market KXHAND15M, no real data.

## Frozen enumerator definitions (dated note to ENGINE1_SPEC_NOV15.md)
- A window is one market (one ticker). Candles sorted by end_ts; fields end_ts, yes_bid, yes_ask, last, volume (per candle, not cumulative), oi.
- Time-left bucket s = close_ts - end_ts of the ENTRY candle, in seconds, one of 120, 180, ..., 840 (13 buckets). The entry candle is the candle ending exactly at close_ts - s; none = no entry for that bucket (counted "no entry candle").
- Side asks in whole cents: YES ask = round(100 x yes_ask); NO ask = round(100 x (1 - yes_bid)). Side rules: yes, no, cheap (the lower ask; a tie is YES), favourite (the higher ask; a tie is YES). Band k = ask_cents // 5 for ask_cents 5 to 94, k in 1..18 (0.05 to 0.95); an ask outside is no entry. The entry price for scoring is the side's raw ask in dollars.
- Filters, at most one, from candles ending AT or BEFORE the entry candle end e, each needing the candles named (else no entry, counted by reason "missing feature candle"): oi3 = oi(e) - oi(e-180); oi6 = oi(e) - oi(e-360); vol3 = sum of volume over the candles ending e-120, e-60, e minus the sum over e-300, e-240, e-180; mom1, mom3, mom5 = side mid(e) - side mid(e-60, e-180, e-300), where side mid is the YES mid (bid+ask)/2 for a YES entry and 1 - that for a NO entry; spread = yes_ask(e) - yes_bid(e) in cents. oi3, oi6, vol3 and mom* take the classes up (> 0), flat (== 0), down (< 0); spread takes low, mid, high from SEARCH-only cut points (below). 22 filter options in all: none, 6 features x 3 classes, spread x 3.
- Spread cut points per (series, bucket): from the SEARCH-phase entry candles' spreads (all candles at that bucket before band, side or any other filter), sorted ascending: c1 = the ceil(n/3)-th value, c2 = the ceil(2n/3)-th; low <= c1, mid c1 < x <= c2, high > c2. Frozen from SEARCH and used unchanged in VALIDATE.
- Rules per series = 13 buckets x 18 bands x 4 side rules x 6 exits x 22 filters = 123,552, ALL counted as tried (dropped cells included) in the Benjamini-Hochberg denominator; only cells with n >= 100 (at n = 10 contracts) are scored for the gate.
- Gate scoring uses 10 contracts per order (1 contract shown beside it); SEARCH needs PF at 1c >= 1.3, PF at 2c >= 1.0, n >= 100. VALIDATE (SEARCH survivors): the same bar, plus BH at 5% on one-sided day-clustered p of the 1c mean cash, with m = total SEARCH cells tried; a survivor with the i-th smallest p passes if p <= 0.05 x i / m (the cells not scored in VALIDATE count as p = 1).

## Hand case (all values by hand)
Close C. Candles (end, bid, ask, volume, oi):
C-660 .40 .42 5 100 | C-600 .41 .43 4 102 | C-540 .42 .44 3 104 | C-480 .44 .46 2 105 | C-420 .46 .48 6 108 | C-360 .48 .50 1 110 | C-300 .50 .52 7 114 (entry candle, bucket s = 300).
- YES ask 52c, band 52 // 5 = 10. NO ask = round(100 x (1 - .50)) = 50c, band 10. cheap = NO (50c), favourite = YES (52c).
- oi3 = 114 - 105 (end C-480) = +9 up; oi6 = 114 - 100 (end C-660) = +14 up; vol3 = (6 + 1 + 7) - (4 + 3 + 2) = 14 - 9 = +5 up.
- YES mids: .51 (C-300), .49 (C-360), .45 (C-480), .42 (C-600): mom1 = +.02, mom3 = +.06, mom5 = +.09, all up for a YES entry; for a NO entry mid_no = 1 - mid: mom1 = -.02, mom3 = -.06, mom5 = -.09, all down.
- spread = 52 - 50 = 2 cents.
Expected, bucket 300, band 10, any exit:
1. side cheap, filter oi3 up: ENTRY (NO side, ask $0.50). side cheap, filter oi3 down: no entry.
2. side yes, filter mom1 up: ENTRY (YES, ask $0.52). side no, filter mom1 up: NO entry (NO's mom1 is down). side no, filter mom1 down: ENTRY.
3. side favourite, filter vol3 up: ENTRY (YES, $0.52). side favourite, filter oi6 flat: no entry.
4. band 9 (45c to 49c): no entry for any side (asks are 52c and 50c); band 10 only.
5. Spread terciles: SEARCH spreads at this bucket [1, 2, 2, 3, 4, 5] cents: n 6, c1 = the 2nd value = 2, c2 = the 4th value = 3; this window (spread 2) is "low"; a spread of 3 would be "mid" and 4 "high". Rule (cheap, spread low) ENTRY; (cheap, spread high) no entry.
6. Window W2, the same candles without the candle ending C-600: oi3, oi6, vol3 and mom1 and mom3 still computable; mom5 and vol3 (needs C-600) are not: rules with filter mom5 or vol3 are no entry, counted "missing feature candle" (6 of the 22 filter options: vol3 up, flat, down and mom5 up, flat, down; vol3 needs ends C-600, C-540, C-480 for its second sum and C-420, C-360, C-300 for the first, so it needs C-600).
7. Counting: 13 x 18 x 4 x 6 x 22 = 123,552 rules for this one series, all tried.
8. Buckets: with a candle ending at C-240 (bucket 240) there is a separate entry candle for the bucket 240 rules; bucket 300's features never use the C-240 candle (it ends after e).

## Dated notes, 2026-11-15 (after Auditor B's check; hand-case values above are all whole-cent quotes and do not change)
- The entry is scored at the RAW ask (YES: yes_ask; NO: 1 - yes_bid), never a rounded one. Whole cents are used only to pick the band and the cheap or favourite side, and are rounded UP (ceil(round(100 x ask, 6))), as the shadow logger does: 0.5249 is 53c, band 10. Each entry carries whole_cent (True or False) and the driver prints how many entry candles have a non-whole-cent ask.
- A NULL (None) volume or open interest in a feature candle makes that feature "missing feature candle", never an error.
- The spread cut points are computed on the SEARCH dates and also classify SEARCH entries, so SEARCH is in-sample for those cuts; VALIDATE uses them frozen.
- BH: m is the total number of cells tried over ALL series and sources in the run; a second run adds to the same m.
