# W-POL-APPR1 registration (Nov 11, 2026; written BEFORE any candle was scored; pull of candles had just started)

Question: are Kalshi's presidential-approval and generic-ballot brackets mispriced on Kalshi's own prices and settlements (calibration test)? No Yahoo, no Open-Meteo, no outside poll data. Owner rules: hold to settlement, max hold 14 days, entry 10c to 90c on the bought side, either side, 3 contracts, first strategy in holds a market.

## UNIVERSE (settled markets, result yes or no; counts from the market lists pulled before scoring)
- APPR_DAILY: KXTRUMPAPPROVE (70 events, 630 markets, 2026-09-02 to 2026-11-10; one event per day, open about 27 hours, so only the 1d and 6h looks exist)
- APPR_RCP: KXAPRPOTUS (RCP approval, weekly, 263 events, 2025 markets, 2021 to 2026-11)
- APPR_538: KX538APPROVE (143 events, 1278 markets, 2022-05 to 2025-03; the 538 approval of the then president)
- [live figure removed, ask Main]
- GCB (generic ballot): KXVHGCB (41 events, 367 markets, 2026-09-25 to 2026-11-04), KXGENERICBALLOTVOTEHUB (9 events). KXGENERICBALLOT has 0 listed markets. KXMIDTERMMOV is a one-off (1 event) and cannot be calibrated, so it is out; KXTRUMPPOLLDAILY, KXAPRPOTUSD, KXTRUMPFAV, KXSILVERAPPROVE, KXTRUMPGALLUP50/30 list 0 markets.
- [live figure removed, ask Main] The pull is stopped when the session must report; the events actually pulled define the universe, and the report states coverage per family. Which events were pulled is decided by date order only, never by price or result.
- POOLED family ALL_APPR = the four approval families together (same observations, so not independent of its parts).

## LOOKS (time from the quote to the market's close_time)
7d, 3d, 1d, 6h. Quote = the last hourly candle whose end time is at or before close minus the look, and at most 6 hours before that moment for 7d and 3d, at most 3 hours before it for 1d and 6h. A market not open at that moment has no observation for that look.

## PRICES AND SIDES
[live figure removed, ask Main] Bought side price 0.10 to 0.90. Buckets of the price of the side bought: [0.10,0.25), [0.25,0.40), [0.40,0.60), [0.60,0.75), [0.75,0.90]. Sides YES and NO. A YES ask of 1.00 or 0, a NO with bid 0, is not a valid quote. Cell = (family, look, price bucket, side). One observation per event per cell: if several markets of an event land in the cell, the one whose yes mid at that quote is nearest 0.5.

## GRID SIZE (counted in the shared deflation)
6 families (APPR_DAILY, APPR_RCP, APPR_538, APPR_OTHER, GCB, ALL_APPR) x 4 looks x 5 buckets x 2 sides = 240 cells (many empty). Shared deflation ledger was about 7,950 tries; with these it is about 8,190. Bonferroni z bar about 4.5 as in the sibling registration; naive z 2 is reported as exploratory only.

## BASIS
[live figure removed, ask Main] PF = gross gain over gross loss across observations; mean in cents per contract.

## SPLITS
Chronological thirds of event close dates per family (over the events with usable candles): TRAIN, VALIDATE, HELD-OUT. HELD-OUT is NOT scored; heldout.py is written for the session lead for any frozen survivor and is not run. ALL_APPR thirds are by close date over its pooled events.

## BOOTSTRAP
2,000 resamples of events in a cell (each observation is its own event), 90 percent interval of mean cents at +1c in VALIDATE. Events in the same week are correlated (daily approval brackets move together, weekly series share one poll); for any candidate I also report a block bootstrap by calendar week of close, and that interval is the one that counts if it is wider.

## PASS BAR (registered now)
A cell advances only if: n >= 30 events in TRAIN and n >= 30 in VALIDATE (n stated; if the universe is too small for 30 the cell is reported as underpowered, not passed); PF >= 1.3 at +1c in TRAIN and in VALIDATE; VALIDATE event-clustered 90 percent lower bound of mean cents at +1c above 0. At most two cells advance (best validation lower bound). Anything that passes is also checked against the Bonferroni z (TRAIN+VALIDATE pooled, +1c); below it is stated as exploratory.

## KILL BAR
No survivor if no cell meets the pass bar. Also killed: any advancing cell whose as-if-live replay at 3 contracts fires the kill rule (net under -15 dollars after 20 fills, or 5 losses in a row) in TRAIN+VALIDATE, or whose validation mean at +1c is not above 0, or whose week-block interval includes 0.

## AS IF LIVE (every cell reported)
3 contracts per fill, bought-side price 0.10 to 0.90, fill at the ask as above, +1c slip, fee rounded up to the cent per order (0.07*3*p*(1-p)), fills ordered by close time (TRAIN+VALIDATE), net in dollars after 20 fills, longest loss streak, kill rule fired yes or no, and the maximum number of simultaneously open positions (entry quote time to close; cap 10), per cell. Conflicts: the first strategy in holds a market, so a second observation in the same market is skipped (one observation per event per cell already limits this).

## CALIBRATION CURVE (reported regardless)
For the approval series, by look and price bucket (all sides folded to the YES price of the market): realized YES frequency against the mean YES ask (and mean mid), with n. Reported even if no cell survives.

## CAVEATS (stated in advance)
(1) Hourly candles give the quote at the end of an hour, up to a few hours before or after a tight look. (2) Settlement source is the series rule (RCP, 538, VoteHub averages); no outside data is read. (3) 538 closed in 2025, so APPR_538 is an old regime and is reported separately. (4) The candle pull is a subset for RCP and 538; dates, not prices, decide which events are in.

## AMENDMENT 1 (Nov 11, coordinator data correction, before any scoring; no rule changed)
[live figure removed, ask Main] The market lists were merged from /markets and /historical/markets by ticker. True counts: KXAPRPOTUS 263 events (was 8 from /markets alone), KX538APPROVE 143, KXVHGCB 41, KXGENERICBALLOTVOTEHUB 31 events (was 9), KXGENERICBALLOT 1, KXTRUMPVH 22 (was 10), KXVOTEHUBTRUMPUPDOWN 38, KXAPRPOTUSD 10 events (Aug 2026), KXTRUMPFAV 2, KXSILVERAPPROVE 1, KXTRUMPPOLLDAILY 1, KXVOTEHUBVANCEAPPROVE 1, KXTRUMPAPPROVE 70. GCB is now 73 events, APPR_OTHER about 76. Candles for markets settled before the cutoff come from the historical candlestick endpoint (one request per market); the same coverage-by-date rule applies.

## AMENDMENT 2 (2026-11-12T01:11Z, Desk A held-out audit; no rule changed, no result changed)
The thirds above were defined "over the events with usable candles", i.e. from the data present when the script ran. They are now constants. The cut close-timestamps (unix seconds) and the fixed list of events with the third each belongs to are in `POL_APPR1_CUTS.json`, computed from the local event list exactly as used in the existing results (rerun of report.py with the constants reproduces the earlier report byte for byte). Per family (cut1, cut2): APPR_DAILY 1790614740, 1792515540; GCB 1791493440, 1792703040; ALL_APPR 1790701140, 1792515540; APPR_OTHER 1790344740, 1792159140; APPR_RCP 1790953200, 1792767600. TRAIN = close before cut1, VALIDATE = cut1 up to cut2, HELD-OUT = cut2 or later. The cuts are constants and later pulls may not move them. Events not in the list are in no third. Event counts per third (TRAIN/VALIDATE/HELD-OUT): APPR_DAILY 21/22/22, GCB 16/16/16, APPR_OTHER 3/4/4, APPR_RCP 2/3/3, ALL_APPR 28/28/28. (An earlier thirds.json in the scratch directory was written before the last pull and differs; the final report used the cuts above.)
HELD-OUT NOT READ as of 2026-11-12T01:11Z.
