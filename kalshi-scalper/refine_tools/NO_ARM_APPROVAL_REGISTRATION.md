# W-NO-ARM1 PLAN (Nov 11, 2026, written BEFORE any candle was pulled for it and before anything was scored)

Question: does the NO arm P4 flagged ("buy NO at 75 to 90c", the one lead in W-POL-APPR1, ALL_APPR 1d 0.75-0.90 N: validate +7.7c, train -11.3c, n 23/24, underpowered) have an edge on a larger, outcome-blind sample? Kalshi public API only (https://api.elections.kalshi.com/trade-api/v2, no key). No other source. Nothing here touches trading code.

## EXACT ARM DEFINITION
- Side: buy NO only. Entry price = the NO ask = 1 minus the YES bid close of the quote candle (cash at the ask, spread paid). Needs 0 < yes_bid < 1.
- Arm A (the P4 arm, the one under test): NO price paid in [0.75, 0.90]  (i.e. YES bid about 10c to 25c: the cheap-YES longshot bracket is sold). This is what P4 labelled "0.75-0.90 N", where the bucket is the price of the side bought.
- Arm B (mirror, registered because the brief's wording "yes-price 75 to 90c, NO cost 10 to 25c" reads the other way): NO price paid in [0.10, 0.25]  (i.e. YES bid about 75c to 90c). Reported separately, never merged into A. If the brief meant B, B is the answer; if A, A is. Both are counted in the deflation either way.
- Look: ENTRY ONE DAY BEFORE CLOSE: quote = the last hourly candle whose end_period_ts is <= close_time minus 86400 s and no more than 3 h older. A market with no such candle has no observation.
- One observation per event per arm: among the event's markets whose NO price lands in the arm's range, the one whose YES mid at that quote is nearest 0.5 (the P4 rule; ties by ticker). Not chosen by result.
- Hold to settlement; every universe market settles within about a week of its entry, so the 30 day cap never binds. 3 contracts live-sizing; 1 contract for PF and mean figures. Price band 10c to 90c is on the bought side (NO), so Arm A uses the 0.75-0.90 part and Arm B the 0.10-0.25 part. YES is allowed by the rulebook but is NOT part of this test.
- Fee: unrounded 0.07*p*(1-p) per contract (p = price paid), shown at +0c slip and at +1c harsher (1c added to the cost per contract). +1c is the basis for every pass test. As-if-live uses the per-order fee 0.07*3*p*(1-p) rounded UP to the cent plus 1c per contract.

## UNIVERSE (fixed from the merged market lists, live /markets plus /historical/markets, settled yes/no; counts known before any pull)
Series: KXAPRPOTUS, KXAPRPOTUSD, KXTRUMPAPPROVE (approval), KXGENERICBALLOTVOTEHUB, KXVOTEHUBTRUMPUPDOWN, KXGENERICBALLOT, KXVHGCB (generic ballot / Votehub). 454 events, 3,182 settled markets in the merged lists (script univ.py).
Families: APPR (the approval series plus KXVOTEHUBTRUMPUPDOWN), GCB (generic ballot series), ALL (both pooled; not independent of its parts).

## SPLITS (by event close date, event-count thirds over ALL 454 events, cut dates saved in cuts.json before any pull)
- TRAIN = earliest third (close before 2024-08-30), VALIDATE = middle third (2024-08-30 to 2026-07-23), HELD-OUT = last third (close on or after 2026-07-24, epoch 1784905200).
- The HELD-OUT third (151 events; it contains all of KXTRUMPAPPROVE, KXVHGCB, KXAPRPOTUSD and part of Votehub) is NOT pulled and NOT scored. Candles for it that exist in w_pol_appr/cand.jsonl from the earlier P4 pull are not used. No held-out script is written or run.
- Consequence stated in advance: the development third contains no live-endpoint events at all (all close before the 2026-09-12 historical cutoff), so every candle is one request per market from /historical/markets, and the development sample is mostly the weekly RCP approval series (247 events) plus Votehub updown (38) and Votehub generic ballot (17). The daily approval and VHGCB series that P4 saw sit in the held-out third. So this test cannot confirm P4's daily-series lead; it tests whether the NO arm exists on the older weekly series.

## CANDLE PULL (cap, rule, outcome-blind)
- AT MOST 1,200 historical candle requests in total (one request per market, 60 minute candles, window close minus 2 days to close). Counted in a ledger file (pulls.log); the puller refuses to go past 1,200.
- Development events (302: close before cut2) sorted by (close_time, event ticker), index 0..301. Pass 1: every even index event, all of its markets. Pass 2 (only if requests remain): odd indexes congruent to 1 mod 4, then 3 mod 4, all markets, until the cap. Chosen by close date and index only, never by price or result; so TRAIN and VALIDATE are covered evenly.
- Pacing: no request while any pull2.py process is running (poll pgrep); then 15 s between requests, 429 doubles the wait (max 60 s) and is not looped; 404 = no candles. Resumable jsonl, started with setsid nohup.

## SCORING (development only)
- Cells: Arm A, Arm B x families APPR, GCB, ALL = 6 cells, each in TRAIN and in VALIDATE (and pooled).
- Per cell: n events per third, PF and mean cents per contract at +0c and +1c, 2,000-resample event-clustered bootstrap 90 percent interval of the mean at +1c, a calendar-week block bootstrap where weeks repeat, and the as-if-live replay at 3 contracts (fills ordered by close time; net after 20 fills, longest loss streak, maximum open).
- Also reported: the calibration of the cheap-YES bracket (realized YES frequency against mean YES ask) for the dev markets, as a descriptive table.

## PASS BAR (fixed now)
A cell passes development only if: n >= 30 events in TRAIN and n >= 30 in VALIDATE; PF >= 1.5 at +1c in TRAIN and in VALIDATE (and pooled); VALIDATE event-clustered 90 percent lower bound of the mean at +1c above 0; AND the pooled TRAIN+VALIDATE t statistic at +1c clears the Bonferroni bar below ("after deflation"). A cell that meets everything except the Bonferroni bar is reported as EXPLORATORY, not a pass. n under 30 in either third is UNDERPOWERED, not failed and not passed. Nothing is relabelled afterwards.
KILL (as-if-live): net under -15 dollars after 20 fills, or 5 losses in a row, in TRAIN+VALIDATE at 3 contracts = the rule would have been stopped; such a cell cannot pass.

## DEFLATION LEDGER
N before this test 9,459 (Bonferroni z 4.55, two-sided alpha 0.05). This plan adds 6 cells -> N = 9,465, Bonferroni z = 4.55 (two-sided 0.05/9,465 gives 4.553; one-sided 4.41, quoted only for reference). The pooled-ALL cells overlap their parts, counted anyway.

## CAVEATS stated in advance
Hourly candles (quote up to 3 h before the look); settlement is the series' own source; 538 is not in this universe; the sample is a subset set by index, not the whole development third (up to 1,200 of 1,952 markets); weekly RCP brackets of one week share one poll, so events are correlated across neighbouring weeks (week-block interval applies). Data thin: failing to reach n 30 is a data limit, not evidence of no edge.

## AMENDMENT 1 (2026-11-11, before ANY candle was pulled; pulls.log did not exist and cand_no.jsonl did not exist when the pull was stopped; owner-side decision relayed by the coordinator)
Reason: the date-based event-count split above put every daily series (KXTRUMPAPPROVE, KXVHGCB, KXAPRPOTUSD) and part of Votehub in HELD-OUT, so the development third had no daily series and could not test the lead P4 saw.
New split (replaces the SPLITS section): PER-SERIES chronological thirds. Each of the 7 series is cut by event close date into its own oldest, middle and newest third (rank i of n: third = min(2, floor(3i/n))). TRAIN = oldest third of each series, VALIDATE = middle third of each series, HELD-OUT = newest third of each series: frozen, NOT pulled, NOT scored, no held-out script written. Cuts per series: W/thirds.json (event, close, third), rebuilt by univ.py before any pull. Counts T/V/H: KXAPRPOTUS 88/88/87, KXAPRPOTUSD 4/3/3, KXGENERICBALLOT 1/0/0, KXGENERICBALLOTVOTEHUB 11/10/10, KXTRUMPAPPROVE 24/23/23, KXVHGCB 14/14/13, KXVOTEHUBTRUMPUPDOWN 13/13/12. Development = 306 events, 2,167 markets.
PLAIN LABEL: P4 (W-POL-APPR1) already looked at the calibration and cells of the daily approval series and the generic ballot (and found this NO arm as its one lead). So TRAIN and VALIDATE for Arm A on those series are NOT fresh; the lead was seen in them. Only the HELD-OUT third (newest third of each series) is untouched. A development pass here is therefore weaker evidence than the pass bar suggests, and a development pass is a reason to ask for the held-out read, not a result.
Unchanged: arm definitions, looks, fee, cells, pass bar, kill rule, N = 9,465, Bonferroni z 4.553.
Pull rule (replaces the pull section's ordering): cap still 1,200 requests. Within each series, development events sorted by (close, ticker), selection order = even indexes, then 1 mod 4, then 3 mod 4. Series are then taken ROUND ROBIN one event at a time (series sorted by name; a series that runs out drops out), so the cap covers the daily series. Events closing after the 2026-09-12 cutoff are one live batch request each (all markets of the event, 55 per request at most); earlier events are one historical request per market. Pacing unchanged: no request while pull2.py runs, then 15 s, 429 doubles, never looped.
Queued after this pull (second job, same pacing, own ledger): the sports SPREAD live-range pull (274 candle requests, packing as step2b.py in w_cat_sports) and a rescore of the SPREAD 0.05 to 0.15 YES cell with the larger n; no held-out third.
