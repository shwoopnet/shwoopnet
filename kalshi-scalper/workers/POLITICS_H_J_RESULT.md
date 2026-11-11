# POLITICS_H and POLITICS_J result (2026-11-11), protocol `workers/POLITICS_H_PROTOCOL.md` (commit 41153001, before counting)

Data held only, no API call. Politics = Politics and Elections categories in theta1, flb1, newlist1: 4,850 markets, 882 events (674 with 2 or more markets), 3,098 markets with candles. Script kept in the scratchpad (not committed); code is plain joins.

## H1, live scans (ARB2 and ARB3, 12 scans each, politics events only)
- ARB2: 232 politics rows (20 events); best lock -0.2c; 0 with lock above 0; 0 opportunities.
- ARB3: 7,396 politics deadline rows (63 events); best lock -1.4c; 0 above 0; 0 opportunities.

## H2, held hourly candles, exclusive sets (3+ markets, exactly one settled YES, every leg quoted at one end_ts)
293 sets, 211 testable event-timestamps. 38 had a lock above 0 after unrounded fee and spread, in 15 events. Reading them by hand:
- 34 of the 38 are SELL-all and all are cumulative threshold ladders (T175, A10, P51, 48 to 56 percent and similar), where several legs can pay together; selling every leg is not a lock. Rejected as ex-ante invalid (an observed single YES after the fact proves nothing).
- 4 are BUY-all: KXTRUTHSOCIAL-26OCT03 (brackets plus tails, valid, +0.1c, one timestamp, bids at 0c: thin), KXHORMUZPEAK-26SEP20 and KXTRUMPPHOTO-26SEP20 (cumulative thresholds, not exhaustive, rejected), KXFLPRIMARY-02D26 (5 candidates, ask sum 0.90, lock +5.3c, 168 hours before close, 7 days to settle; exhaustiveness unconfirmed, size unknown, the candle is a close not a book).
Verdict H2: one unconfirmed lead (FLPRIMARY), not CLOSED by the strict rule and not a result. Needs a forward book read of a candidate-field politics event (any full-field primary) to learn size and whether the set is complete.

## H3, monotone date ladders
Pairs of same-stem markets with date-like last segments and different closes: 82, all settled; settled inversions (earlier YES, later NO): 0 of 82. Executable pair-timestamps: 8 (4 pairs), 0 violations, best -24.3c. Under 20: NOT_ENOUGH_DATA for the executable test, but the live ARB3 scan (7,396 politics deadline rows, 0 positive) covers it.

## Combined verdict for (h): CLOSED on the live scans (0 of 7,628 politics rows positive), with ONE unconfirmed historical lead (FLPRIMARY +5.3c, 1 of 211 event-timestamps, size unknown).

## (j) resolution edge cases (no outside host read, so no terms PDF was opened and no POLITICS_TERMS_V2.md was written)
- Date-ladder inversions: 0 of 82 settled pairs.
- Name-style exclusive events (no digits in any leg, 3+ markets, all settled): 222. 188 had exactly one YES, 11 had zero YES, 23 had two or more (several are "advance", "combo" or count-style events that are not meant to be exclusive, e.g. KXAKSENADVANCE 4, KXTRUMPSTATES 11). Zero-YES examples: KXBRISRAELSENCOMBO-27OCT, KXACTBLUESECOND-26OCT23.
- Favourite proxy (YES ask at or above 90c, or bid at or below 10c, last candle within 48 hours of close): 2,020 markets, favourite lost 76 (3.76%) against an average price in the mid 90s: consistent with fair pricing. These 76 are NOT confirmed rule surprises; confirming one means reading its rules text and terms.
Verdict (j): NOT_ENOUGH_DATA. Confirmed rule-driven reversals counted: 0 (needs 20). The next cheap step is reading the rules text of the 76 reversals and the 34 odd-count events (outside host: Kalshi's contract-terms PDFs, one read each, record in POLITICS_TERMS_V2.md).
