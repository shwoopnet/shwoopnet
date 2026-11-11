# POLITICS_CARDS_V2 (Nov 11, 2026): four Idea cards, all stage Idea, none tested

Held facts (no new Kalshi calls made). Refinement's politics census is not on origin/claude/refine-live (no politics or census file under refine_tools/), so it was not reused. From data/newlist1_series.json and newlist1.sqlite (listing metadata, 34 Politics series, 658 listed markets): the settled-result table `res` holds ZERO of them (only 5,477 sampled markets, none Politics), and hourly candles exist for listed tickers only. data/ment1 holds 6,346 settled mention markets but ALL are KXEARNINGSMENTION (company earnings calls, not politics; transcripts copyrighted, so not public domain). Settled political history held: 0 markets. Declined-list check (STRATEGY_LIFECYCLE 7e, origin/main): none of these four is on it; they are cheap-side holds with a different entry, not favourite-and-hold (the favourite hold is banned by Charter item 5). Settled-history size must be fetched from Kalshi (public /historical/markets, a few hundred requests) before any test, which is only justified after the terms check clears.

Capital lock-up for all four: weekly or monthly ladders, 2 to 30 days; the annualised return is not computed because no price or result is held.

## d) EXECSUM
NAME EXECSUM | family: cheap-side entry (ask 3c to 30c) on a count ladder, held to settle | risk class: low win rate, small loss (price paid), $ per order small, group D (politics, uncorrelated with the 15 minute grid) | stage Idea.
- Series: KXEOWEEK (33 listed, executive orders per week), KXBILLSSIGNED 11, KXBILLSCOUNT 11, KXMAMDANIEO 9, KXJUDGECOUNT 7. Source: Federal Register API / govinfo (public domain content, access terms AMBIGUOUS, see POLITICS_TERMS_V2.md). Held: nothing.
- Cheapest test: negative-binomial or empirical weekly count of executive orders from the register vs the ladder's implied distribution, buy the cheap side where model probability beats price plus fee 0.07 p(1-p) by a margin. Prediction: thin edge, few dates.
- Sample: unknown until fetched; at most one weekly series, about 40 to 60 settled weeks, each with a ladder of strikes (strikes within a week are one cluster). Likely NOT_ENOUGH_DATA against N 1.1M (z 5.34) and N 8,795 (z 4.39). Recorder: not needed (register is archival). Fills per week 1 to 3.
- Uniqueness: signal = an official outside count, a different source from every live strategy. Passes check 1 by design.

## e) MENTPOL
NAME MENTPOL | family: cheap-side entry on "will X say word Y" in speeches and briefings, held | risk class as above | stage Idea.
- Series: political mention series exist in the full /series list (MENT1 saw 457 MENTION series) but none is in the held settled data; KXPRESSBRIEFINGCOUNT (10 listed) is the only political one in the held listing. Source: whitehouse.gov briefing transcripts (US government works, access terms AMBIGUOUS); debate and speech transcripts from other hosts not checked.
- Cheapest test: per-word frequency across past transcripts vs price of the cheap side. MENT1 already ran this design on earnings calls and was NOT_ENOUGH_DATA (71 of 100 events). Needs a political-series history fetch plus transcript scrape; likely hundreds of markets, event-clustered. Recorder: none needed, but transcript collection is per-event manual.
- Fills per week 3 to 10. Lock-up 1 day or less. Uniqueness: signal = a transcript base rate (different source); the earnings-call version is a related mechanism, not a duplicate of a live strategy.

## f) COURTTIME
NAME COURTTIME | family: cheap-side entry on decision-day or date-of-ruling ladders, held | risk class as above | stage Idea.
- Series: no SCOTUS or court series in the held 1,330-series listing (KXJUDGECOUNT only). Source: supremecourt.gov calendar (terms AMBIGUOUS, policy page errored). Held: nothing.
- Cheapest test: opinion days follow the published calendar and the end-of-term pattern; compare the date ladder to base rates. Sample: one term a year, at most about 10 to 20 decision-date markets per season: NOT_ENOUGH_DATA by construction. Recorder: not needed. Fills per week near zero off-season. Lock-up weeks to months. Uniqueness: official calendar, different source.

## g) PERSONNEL
NAME PERSONNEL | family: cheap-side entry on departure or nomination markets, held | risk class: rare large wins and total losses, group D | stage Idea.
- Series: KXLEAVECONGRESS 2, KXLEAVEHOUSECOMBO 1, KXTRUMPNOMNUM (listed, 0 markets held). Source: congress.gov / Federal Register nominations (terms AMBIGUOUS, congress.gov returned 403). Held: nothing.
- Cheapest test: historical departure base rate per role and year vs the ladder price. Sample: a handful of markets: NOT_ENOUGH_DATA. Recorder: not needed. Fills per week near zero. Lock-up months.

## Speed rank to a verdict (fastest first)
1. EXECSUM (one weekly series, archival count, clean model), 2. MENTPOL (more markets, but transcript work and a prior NOT_ENOUGH_DATA on the sibling), 3. COURTTIME, 4. PERSONNEL (both limited by season and rarity).

## Step 4 status
No test run: every host is AMBIGUOUS and held settled political history is 0 markets (the >= 100 bar is not met). Verdict for all four: NOT_ENOUGH_DATA. Needed first: owner-cleared terms, then a Kalshi history fetch of KXEOWEEK, KXPRESSBRIEFINGCOUNT and the political mention series, then a registration file committed before scoring.
