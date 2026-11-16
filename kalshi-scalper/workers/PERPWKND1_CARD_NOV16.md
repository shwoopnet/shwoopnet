# PERPWKND1: the stock and index perp weekend gap (Desk A, 2026-11-16). CARD ONLY, nothing read, nothing run. Not frozen until Auditor B signs the data, holds and look-ahead rows.

**Label on everything it will ever print: development, first weeks of stock perps (they began trading 2026-11-05 18:39Z), one regime; no evidence at n under 100.** The account size is never written; results are in price terms (basis points) and as percent of margin.

## The question (the Head's, Nov 16)
Kalshi stock and index perps keep trading while the cash market is shut. Does the move from the Friday 16:00 ET perp price to the Sunday 18:00 ET reopen (the CME-style Sunday 18:00 ET restart) **reverse or continue** by the Monday 10:00 ET perp price? Perp data only: no cash price source of any kind.

## The rule (pre-registered, one exit, no tuning)
- Price used: the mid (bid + ask) / 2 of the perp's 1 minute candle ending exactly at the clock time; a candle is usable only if 0 < bid < ask < 1,000 (the extract shows a placeholder ask of about 9.2e14 where there is no ask; that is NOT usable). A name-weekend is skipped (counted) if any of the three candles is missing or unusable.
- Gap G = ln(mid at the candle ending Sunday 18:00 ET / mid at the candle ending Friday 16:00 ET) of the same weekend. ET clocks with the DST offset read at the day's midday (as engine1_perps).
- Entry at the Sunday 18:00 ET candle's own quote (the candle ending 18:00): long at ask x (1 + h), short at bid x (1 - h). Exit at the candle ending Monday 10:00 ET: long at bid x (1 - h), short at ask x (1 + h). h = 0.0002 (primary) and 0.0005 (the 5 bp stress). Taker fee 12 bp a side (placeholder until the owner's screenshot); funding booked from the extract's own prints (a position pays or receives a print iff entry end < print < exit end; the POOL1 gap rules for a hold with no print ruled in).
- Rules: |G| >= T with T in {30, 60, 100} bp, mode FOLLOW (long if G > 0, short if G < 0) or FADE (the opposite) = **6 rules** (the same thresholds as POOL1's opening gap, no per-name tuning, one position per name per weekend). Indices and stocks are pooled; the split by class is display only (a class picked afterwards is a new try).
- Unit of count: a TRADE is one name in one weekend; a trading day is the Monday on which it exits (the POOL1 definition counts ET dates with a 09:31 candle, so the weekday denominator is 5 per week).

## Four uniqueness checks (docs/STRATEGY_LIFECYCLE.md 7d)
1. **Entry, management and exit:** entry Sunday 18:00 ET at the perp's own quote, one time exit Monday 10:00 ET, no stop or target; closest existing mechanism: POOL1's opening gap (entry Monday 09:31, previous close Friday or the day before 16:00) and the Testing Desk's OPENGAP1. **Difference:** this measures the whole weekend move inside the perp's own 24 hour market and enters at the SUNDAY reopen, about 15.5 hours before the cash open, so it trades the part POOL1 never sees. Where POOL1's Monday gap (Fri 16:00 to Mon 09:31) overlaps the weekend move, I will report the overlap by name and weekend.
2. **Signal source:** Kalshi's own perp prices at three clock times (a different field and time window from POOL1's weekday gap and from the 15 minute binaries); no outside source.
3. **Declined list (7e):** not Dogecoin, not favourite-and-hold, not gold L1 or its variants, not Bitcoin, Ethereum or XRP as L1; no row touched.
4. **Correlation:** with every live strategy (gold L1, OICORE, EVENT830) zero by construction (different markets and clock windows); with POOL1's gap rules to be computed by weekend if any rule passes (0.3 or more on the per-weekend returns is a duplicate, recorded on the declined list with the number).

## Counterparty guess
Weekend perp liquidity is thin and the cash market cannot absorb or correct it until Sunday 18:00 (futures) or Monday 09:30 (stocks). A weekend move that traders pushed through a wide, thin book is likely to be partly reversed by the time the cash market opens and arbitrage returns (FADE), unless the move carries real news (FOLLOW). The counterparty to a FADE is whoever sold or bought the weekend overshoot at a wide spread; **no counterparty is named beyond that guess, and this is a guess, not a measurement.**

## Numeric prediction (written before any read)
FADE at 60 bp or more: gross reversal by Monday 10:00 about 30% to 40% of the gap (mean gross +15 to +25 bp a trade); costs 24 bp taker plus 4 bp of haircut plus funding, so net about 0 or slightly negative. **Predicted outcome: no rule passes; the best rule is within 10 bp of zero after costs.** A pass would need a mean gross reversal above 30 bp at 60 bp or more.

## Kill criteria
- Pooled over all name-weekends: PF at h 0.0002 below 1.3, or at h 0.0005 below 1.0, or net at h 0.0005 not positive, or the top weekend carrying more than 30% of net: not a pass.
- n under 100 trades: NOT_ENOUGH_DATA, never FALSIFIED, and no pass can be named (the standing label).
- Forward: closed as FALSIFIED only after 100 forward trades (about 2 to 4 more weekends) at the same bar.

## Split (a date constant, fixed now)
The extract has two stock weekends (Fri Nov 6 to Mon Nov 9, and Fri Nov 13 to Mon Nov 16 once Monday's file lands) and index weekends from September, if those index perps traded then. **There is no honest SEARCH and VALIDATE split on stocks (two weekends): stocks are development only, `split.mode forward_only` from 2026-11-17.** For the index perps, the constant is: SEARCH = weekends whose Monday exit is on or before 2026-10-19; VALIDATE = every later weekend up to and including the Monday exit of 2026-11-09 (the pooled bar above applies to VALIDATE alone; SEARCH only picks nothing: with 6 rules nothing is selected, so SEARCH is printed for information). **A feasibility count comes FIRST and reads existence only, never a return:** for each name and weekend, are the three candles present and usable; print the counts by class and weekend. If fewer than 30 name-weekends are usable in total, the card is closed as NOT_ENOUGH_DATA before any price is read.

## Expected trades a week against the 3 a day gate (said plainly)
The 3 a day gate counts trades per trading day over the week's 5 trading days, so a weekend rule needs at least 15 trades a week. Stocks: up to about 94 names, of which perhaps 20 to 60 have |G| >= 30 bp (a guess, unmeasured), fewer at 60 and 100 bp. So the **30 bp rules can reach 3 a day from one weekend, the 60 and 100 bp rules probably cannot**. The harder limits are the others: with two stock weekends there are only two event days, so **the 30% top-day share limit cannot be met (each weekend is about half of the net), and n will be under 100 for the 60 and 100 bp rules**. So the rule cannot pass the gate on the data that exists today; it is a feasibility and development read. The forward read (a weekend a week from Nov 20, 21 on the live recorder and archive) reaches n of 100 for the 30 bp rules in about 2 to 4 weekends, so a first honest forward read is the weekend of Dec 4 to Dec 7.

## Margin view (the page-max table, sha256 5be707ec...e36, commit a67ac7f9 on forensics-desk; Forensics' own commit text)
Each result in price terms and as percent of margin at 10%, 25% and 50% of the name's leverage, the size-specific max where known (gold 17.4x at $800) else the page max (71 of 126 names have one; a name not in the paste reads "no page max, not shown" and a pass on it is printed but cannot be named for shadow or as a CANDIDATE), with liquidation distance 1 / leverage minus maintenance (4.47% gold, 4.5% elsewhere, assumed). **A weekend hold is 40 hours, so the liquidation distance matters more than for an intraday rule:** I print the worst weekend adverse move (low bid or high ask within the hold) for each trade against that distance, so a trade that would have been liquidated at the shown leverage is counted.

## Counts and m
6 new rules; m = the carried number 6,290,660 plus the rules registered since (batch C 1,201,824 and lanes 144 are already inside the 7,492,628 figure from Nov 17; use the Head's single carried number on the day of the print) + 6. Print the carried and own figures separately.

## Hand case (invented, not data)
Friday 16:00 ET mid 100.00; Sunday 18:00 ET mid 101.00 (G = +99.5 bp, above 60 and under 100). FADE (short at the Sunday bid x (1 - 0.0002)): bid 100.98, fill 100.9598. Monday 10:00 ET ask 100.30: exit 100.30 x 1.0002 = 100.3201; gross = (100.9598 - 100.3201) / 100.9598 = +63.4 bp; costs 24 bp; funding (one print, rate +0.01% a day, a short receives): +1 bp; net = 63.4 + 1 - 24 = +40.4 bp. FOLLOW on the same weekend (long at ask 101.02 x 1.0002 = 101.0402, exit bid 100.28 x 0.9998 = 100.2599): gross -77.2 bp, net about -101 bp. Margin at 4.5x (page max) and 50% of it (2.25x): +40.4 bp x 2.25 = +0.91% of margin; liquidation distance 1 / 2.25 = 44.4% minus 4.5% = 39.9%.

## Data and loaders
Perp-data branch kalshi1m and funding files (the same candle and print files as PERPSLANE4 and the perps passes), read through a loader with a wall, an allow line, Auditor B's CLEAN and a blind second build. The Sunday 10 second file (perps10) that the Head mentions is NOT yet on the branch (none exists for any Sunday as of this card), so the Sunday 18:00 ET price is read from the 1 minute candle only. No cash source. Nothing is read before the card is signed.
