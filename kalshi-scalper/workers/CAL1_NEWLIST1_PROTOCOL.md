# CAL1 (calendar consistency) and NEWLIST1B (new listing, mid and exit variants): registration (V2 workers, Nov 11, 2026, BEFORE any score is computed)
Research only. No live change, no Kalshi call (everything is read from held sqlite files), no Polymarket, ESPN, NHL, MLB, NBA.com or Rotten Tomatoes. Fee: unrounded 0.07 p (1-p) per contract per fill, cash basis, 1 contract. Card source: workers/IDEA_CARDS_NOV11B.md rows 7 and 8. Declined list (7e) checked: neither is favourite-late (88c to 97c) or favourite-and-hold; CAL1 is a paired lock, NEWLIST1B is cheap-side and mid-price with a time or target exit. Name note: `data/cal1_result.txt` is the older CAL calibration test (FALSIFIED); this CAL1 is the Idea card 7 and shares only the name. NEWLIST1 (Nov 3, 2026, cheap side 0.05 to 0.30, hold to settlement, 1, 3, 6 h looks) was FALSIFIED (PF 0.36 to 0.64); this registration is NEWLIST1B, which adds the mid band and exits, so it is not a rerun of that rule. NEWLIST1's frozen third H was never read.

## CAL1: what is held (inspected before registering, no price or result read)
- S&P 500: KXINXU (hourly "above K", inx1.sqlite, 47 close times, H1600 closes Aug 24 to Oct) and KXINX (daily bracket ladder, xladder1.sqlite, 20 closes, Aug 28 to Sep 25, 30 markets per close: greater, less, 28 between), same underlying and same 16:00 ET instant. KXINX candles are sparse (3 or 4 per market).
- Gold: KXGOLDD (daily) and KXGOLDW (weekly) quotes at 10 and 6 minutes before the close for 40 weekly markets (ladl1.sqlite `q`), 21:00 UTC close on the Friday both settle.
- NOT held (so NOT_ENOUGH_DATA, no test counted): Nasdaq 100 daily and weekly candles (KXNASDAQ100 has listings only), silver (KXSILVERD has 23 markets with candles, KXSILVERH/KXSILVERMON none), oil and natural gas. Enough would exist only after a candle crawl of those ladders (about 1,200 requests at 1 per 2 seconds, not run now: shared budget).
## CAL1 rules
Same-instant assumption: markets of two series with the same close_ts and the same underlying settle on the same value. Reported, not assumed silently: the count of identical-strike pairs whose settled results disagree (if any, that pair is excluded and counted).
Quote at look L minutes before close (L = 60, 30, 10 for the index; the held 10 and 6 for gold): each leg uses its latest candle ending in (close - L min - 15 min, close - L min]. A leg bought YES needs 0.01 <= ask <= 0.99; a leg bought NO needs bid >= 0.01 (cost 1 - bid). Any leg missing = pair unscored (counted).
- I2 (index two leg): KXINX "greater" market and KXINXU market with the identical numeric strike (7974.9999 style). Lock: YES of A at ask + NO of B at 1 - bid_B, payoff exactly 1; both directions, best one counted. Locked profit = bid_B - ask_A - fee(ask_A) - fee(1 - bid_B).
- I3 (index three leg): KXINX between bracket [lo, hi] and KXINXU strikes at lo - 0.0001 and hi (the exact edges of the bracket). With x = above(lo), h = above(hi), b = bracket, x = b + h. D1: YES b + YES h + NO x, payoff 1. D2: YES x + NO b + NO h, payoff 2. Best direction counted; fee on all three legs.
- G2 (gold two leg): KXGOLDD and KXGOLDW with the same close_ts and the same strike number, looks 10 and 6, same lock as I2.
Tests counted: I2 x 3 looks + I3 x 3 looks + G2 x 2 looks = **8**.
Development = the earlier two thirds of close dates (by distinct close_ts) of that structure; held-out = the last third, read ONCE and only for a test that survives development. Survive = at least 100 scored pairs in development, a locked profit above 0 after fees in at least 30 pairs on at least 10 dates, and a mean locked profit over those pairs of at least 1.0c. (No outcome enters a lock, so cash PF is infinite by construction; the order's PF >= 1.5 and z bars are met only if the counts are met, and z is not defined. The held-out read confirms the count and the mean.) Fewer than 100 scored pairs in development = NOT_ENOUGH_DATA with the date more would exist (the next close date of that series times the recorded rate), else FALSIFIED.
Prediction: FALSIFIED, prior 4%, as AAASPREAD1: the same makers quote both ladders and the spread plus two or three fees exceeds any gap. Sparse KXINX candles make most pairs unscored, so I2 and I3 may be NOT_ENOUGH_DATA.

## NEWLIST1B rules (data: newlist1.sqlite `mk`, `cd` hourly candles, `res`; universe = the 3,785 markets that have candles and a settled result, life (close - open) >= 12 hours, same as NEWLIST1)
Look at age T hours (T = 1, 3, 6): the first priced candle (bid >= 0.01, ask <= 0.99, ask > bid) whose end is in [open + T h, open + T h + 1 h); no such candle = no entry. NO ask = 1 - yes bid.
Side C (cheap): the side with ask 0.04 to 0.30 (cheaper if both). Side M (mid): the side with ask above 0.30 and up to 0.88 (cheaper if both). Hard limit: the band edge.
Exit X1 (time): sell at the bid of the first candle ending 3 h or more after the entry candle (priced; fee on the sale), if none before the close then settlement. Exit X2 (target): sell at the first later candle within 6 h whose bid is at least entry ask + 0.10 (fee on the sale); if none, the bid of the candle at 6 h; if none, settlement (no fee, pays 1 or 0). Net per contract = proceeds - ask - entry fee - exit fee.
Tests counted: 2 sides x 3 looks x 2 exits = **12**.
Development = markets closing before 2026-10-19 03:59 UTC (NEWLIST1's D plus V, the earlier two thirds by close time); held-out H = closing at or after that, read ONCE and only for a survivor. Survive in development = n >= 100, mean net > 0, cash PF >= 1.5, day-clustered (open date) z at or above the bar below. Per-category cells are information, never tests.
Prediction: FALSIFIED, prior 2%; the cheap side overpays at every age (NEWLIST1) and the mid band should show no gap larger than the two fees of a round trip.

## Bar for z (shared)
Shared N about 1,100,000 + 20 registered here: z about 5.34; on the N 8,795 + 20 basis: about 4.39. A cell must meet 5.34 to be called more than a flag.

## Procedure
Code `scripts/cal1_newlist1_score.py`, one run, refuses a second (`data/cal1_newlist1_score.json`). Nothing in this file changes after the first outcome; later changes are amendments appended below with their reason. Registered in git before the script is written or run.

## RESULT (scored once, Nov 11, 2026; `scripts/cal1_newlist1_score.py`, output `data/cal1_newlist1_score.json`; held-out not read for any test, no survivor)
**CAL1: NOT_ENOUGH_DATA for the index structure, 0 pairs for I2 and G2, no survivor, no lock found.**
- I2 (identical strike KXINX greater vs KXINXU): 0 pairs. The 20 KXINX "greater" markets sit at one extreme strike per day and none matches a KXINXU strike at the same close. Not testable on held data.
- G2 (gold daily vs weekly): 0 pairs. The held gold daily and weekly ladders never share a close date (weekly closes on Fridays, the held daily markets skip those Fridays). Not testable.
- I3 (bracket = above(lo) - above(hi), 3 legs, index): 230 listed bracket triples, 147 in development over 13 dates. Scored (all three legs quoted within 15 minutes before the look) in development: 42 at 60 min, 36 at 30 min, 29 at 10 min; locks with profit above 0 after three fees: 1, 1, 2 (best 1.72c, 0.96c, 0.51c). Far under 100 scored pairs, so NOT_ENOUGH_DATA, and the signs say FALSIFIED if more existed (3 of 107 scored lock; two of the three under 1c). The sparse KXINX candles (3 to 4 per market) are the limit; a 1 minute read of the KXINX ladder would be needed, about 600 markets x 1 request, not run. Settlement consistency check: 0 mismatches (index), so the same-instant assumption held. Silver, Nasdaq 100, oil, natural gas: not held (NOT_ENOUGH_DATA, nothing counted). Counted tests: 8 registered, 3 scored.
**NEWLIST1B: FALSIFIED, all 12 tests, development only (held-out count only: 272 to 509 entries, unread).** Development n 733 to 902 per cell, net per contract:
| side | look | X1 time exit mean, PF | X2 target exit mean, PF |
|---|---|---|---|
| cheap 0.04 to 0.30 | 1 h | -7.85c, 0.04 | -7.92c, 0.06 |
| cheap | 3 h | -7.61c, 0.03 | -6.99c, 0.11 |
| cheap | 6 h | -8.58c, 0.04 | -8.50c, 0.07 |
| mid 0.30 to 0.88 | 1 h | -34.80c, 0.02 | -33.72c, 0.03 |
| mid | 3 h | -29.06c, 0.02 | -28.30c, 0.03 |
| mid | 6 h | -24.35c, 0.02 | -24.92c, 0.03 |
All z between -10 and -23. The cause is the spread: in a market's first hours the average quoted spread is 57c in the mid band (bid 0.26, ask 0.61 on average, hourly candle closes), so a taker pays the ask of a book with no maker yet. Win rate in the mid band (44.7% at mid 50.6%) is only about 6 points under the mid, but crossing the spread costs far more. Best cell by category was not flagged (no cell near the bar); category cells are in the JSON as information. Prediction held in direction (FALSIFIED), but PF is far below the predicted band. A resting (maker) entry in a new book would be a different, untested rule and is NOT registered here. Disclosure: hourly candles only, so the first 10 minutes of a listing are not tested.
