# POLITICS_CARDS_V2B: three Idea cards (2026-11-11, V2, politics program sub-families h, j, l)
Declined list (docs/STRATEGY_LIFECYCLE.md 7e) checked for all three, rows compared: favourite-and-hold, GOLDHOLD, XRP, probe markets, Bitcoin, Ethereum, Dogecoin, gold band and ladder rows, maker or resting entries on gold, gold 94.5c floor. None matches: (h) and (l) are structure and screening, (j) is rule reading. Fee: unrounded 0.07 p(1-p), cash basis. Sample bars: N shared about 1,100,000 (z about 5.34); a single-test N of 8,795 needs z about 4.39.

## POLPARITY1 | family: structural lock, buy-all or paired legs held to settlement (entry = hit every leg of an exhaustive set or a deadline pair at once, exit = settlement pays a fixed $1) | risk class: no outcome risk if exhaustive; loss shape = leg not filled or set not exhaustive; dollars about $0.90 a set at 1 contract | stage: Idea
- Data: ARB2/ARB3 stored scans (0 of 7,628 politics rows positive) and held hourly candles (211 testable event-timestamps, 1 unconfirmed buy-all lead, KXFLPRIMARY-02D26 +5.3c).
- Terms: need each event's "mutually exclusive" flag and rules text; settled-single-YES is not proof.
- Cheapest test: a forward book read (public, GET, no key) of full-field politics events 7 to 14 days from close, a few snapshots a day, counting sets with ask sum below 1 minus fees and displayed size of at least 10.
- Sample size: events with 3+ exclusive legs: 293 in 74 days (about 28 a week), so 100 events in about 4 weeks; fills per week about 0.1 to 1.
- Recorder need: a small politics-only book poller (not built); a recorder is needed only if the owner wants to proceed.
- Declined-list check: no row. Uniqueness: structural, no signal; correlation with L1 expected about 0.
- Prior: 3%, since 0 of 7,628 live rows were positive and makers price these sets.

## POLRULES1 | family: rule reading, no signal (entry = buy the side a naive reading mis-prices, exit = settlement) | risk class: win rate unknown, loss = the price paid, under $0.30 an order if cheap side only | stage: Idea
- Data: 76 favourite reversals (90c or more on one side, lost) and 34 odd-count exclusive events held in theta1, flb1, newlist1; 0 of 82 date-ladder pairs inverted.
- Terms: Kalshi contract-terms PDFs and each market's rules text (public, one plain read each).
- Cheapest test: read the rules of the 110 flagged markets, classify cause (tie, by or before, certification, recount, source change), count confirmed cases; dead if under 20.
- Sample size: 110 markets now; 20 confirmed is the bar to even register a rule.
- Recorder need: none for the count; a rules-text snapshot if cases appear.
- Declined-list check: no row (not a favourite rule, it is a rule reading); overlaps card RULES1 (Nov 11 cards, item 6) which covers ties and halts on 15 minute and ladder markets; this one is politics only and must not be run twice.
- Prior: 5%.

## LOCKRANK1 | family: portfolio screen, no position (ranks ideas by days to verdict times days of lock-up) | risk class: none | stage: Idea
- Data: `workers/LOCKUP_RANK_V2.md` (21 rows; top 5 STALE1, LADBFLY1, MMHOUR1, LIQ1, AVG1 by the score, all minutes to hours of lock-up).
- Terms: none. Cheapest test: re-run the table when fills per week for the estimated rows become held counts.
- Sample size: n/a. Recorder need: none. Declined-list check: no row; this is a ranking, not a strategy (7g rule 10 style cost input).
- Finding: politics itself offers short lock-up (757 settled markets with life of 7 days or less, 1,875 with 14 days or less, in 74 days) but only cheap-tail or favourite rules use it, and both are parked or declined; a 1c lock on a 7 to 14 day set would annualize at about 40% to 60% but fills are about 0.1 a week.
- Prior: n/a.
