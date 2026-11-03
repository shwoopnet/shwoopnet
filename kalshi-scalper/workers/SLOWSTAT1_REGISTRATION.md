# SLOWSTAT1 registration: cheap-side brackets on slow public statistics against an outside reference (written 2026-11-03, before any outcome was joined)

Worker for "Strategy Research V2". Research only: public keyless data, no order, no live code, no promote verb. Owner rule held strictly: cheap side only (ask 3c to 30c), no favourite-side result computed or printed, no 15 minute crypto or gold trigger.

## Duplicate check (done first, from README and workers/, no outcome read)
Already tested with a reference, carried and not re-scored: CALIB1 (Economics cheap side 20c to 30c, -17.9c on 1,309 entries), GAS1 and ECONNEW2 (AAA daily and weekly gas, RBOB), ECONNEW1 (weekly jobless claims vs persistence, FALSIFIED), MORTGAGE1 (KX30YMORTW vs 10y yield, NOT_ENOUGH_DATA), TSA1, SPOTD1, EQUAKE1, CPI1 rerun pending, FEDIMPL1 and the Atlanta Fed tracker (NOT_ENOUGH_DATA), USWEEP1/2/3 (every non-15-minute series with 8+ events and volume, both tails, no reference), NEWLIST1, EVENT1, PUBINDEX1, WXLOCK1, XLADDER1, COMDAY1, OICORE_SHAPE_INVENTORY. Ten year Treasury daily: no settled series (NOT_RUNNABLE, earlier).

## What is new
Series on the public series list (Economics, Financials, Climate and Weather, Science and Technology, 3,553 series) that no file in the repo names and that have settled markets since 2026-07-01: 556 unmentioned daily to monthly series, about 90 with settled markets. Candidates with a free keyless reference and a known update rule:
- KXADP (ADP employment change, monthly; reference: the earlier ADP prints), KXTEMPHELP (FRED TEMPHELPS), KXEGGS (BLS egg price, FRED APU0000708111), KXPOWERKWH (FRED APU000072610), KXUSHOME and KXEXUSHOME (Census, FRED MSPNHSUS), KXNFCI (FRED NFCI), KXCFNAI, KXDATACENTCON, KX10YRDIRHM / DIRLM / 2YRDIRHM / 2YRDIRLM (monthly high or low of the Treasury par yield; FRED DGS10, DGS2), KXUSDINRAW, KXUSDNOKAD (FX), menu prices (KXCHIPBURRITO, KXDDCOLDBREW, KXTBCRUNCHWRAP, KXSBUXSAR, KXCFACHICKSAND; reference: the previous settled value).

## Rule (fixed now; would have been run only if the cap below allowed 150 trades)
Look: one fixed time per series, 24 hours before the close. Reference R: the latest published value known at the look (outside source, or the previous settled value for menu prices). Prediction: persistence, sd of the change estimated ONLY from the first two thirds of events (by close time); probability of each strike bracket from a normal at R; for the monthly yield extremes the running extreme so far plus the remaining business days. Trade: the side with ask between 3c and 30c whose model probability is at least 3 times the ask, 1 contract, held to settlement, fee 7% x p x (1-p) rounded up per order (C = 10 and x1.2 shown). Pooled, one cluster per event. Data window: events closing before 2026-10-03T16:00Z only; the last third (from that instant) is never fetched or joined.

## Feasibility cap (computed from the listings only: market counts and volumes, no result, price or candle)
The trade count cannot exceed the number of settled markets that traded at all. Pre-cutoff, with 20 or more contracts traded: KXADP 120 markets on 18 events, KXEGGS 18 on 18 (one market per event), KXTEMPHELP 13 on 3, KXDATACENTCON 12 on 2, menu prices 66 on 11 events, KXUSDINRAW 121 on 6 events, the monthly yield extremes 0 to 60 on 2 events, KXPOWERKWH, KXUSHOME, KXNFCI, KXCFNAI 0 to 24 on 1 to 3 events. Even if every one of them were an eligible cheap-side trade (a share of perhaps a fifth to a third is realistic), the total is below 150 and the event count is far below the 25 an event-clustered test needs for the first two thirds alone. No series other than ADP has more than 6 events with a reference.

## Numeric prediction (before any join)
If run, the pooled cheap-side mean net would be near the CALIB1 Economics figure (negative), win rate at or under the ask, PF under 1.0 against a control of the same brackets at random. Prior of a pass: under 1%.

## Kill rules
FALSIFIED if mean net after fees is not above 0 in both halves, or PF under 1.5. NOT_ENOUGH_DATA under 150 trades with months to go. NOT_RUNNABLE if the cap above is below 150 trades in total (it is), which means the rule is not scored and consumes no more than its registration. N: +2 for the one registered rule (running count about 730,287 if the coordinator's 730,285 is current; z bar 5.27).

## Forward plan
Re-run the census (`python -m scalper.slowstat1 census`) on 2027-02-01. The rule becomes runnable only if one reference-backed series shows 40 or more events with trading (monthly releases: KXADP reaches that around 2028), or the pooled cap exceeds 400. No recorder is needed: Kalshi keeps settled candles.
