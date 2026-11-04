# SOCCER1: Kalshi soccer cheap side (draw, underdog, goals-total at the book line) vs the de-vigged DraftKings three-way price. Held to settlement.

Registered 2026-11-04 BEFORE any Kalshi soccer candle, price or result and any ESPN final score was fetched or joined. Worker ID SOCCER1, session "Strategy Research V2". **N: +2** (one rule, G game outcomes; the totals rule T is a second +2 only if it trades; stated +4 worst case). Owner rule: CHEAP SIDE ONLY (ask 3c to 30c, hard limit 0.30); no favourite-side result is computed or printed; no 15 minute crypto or gold candle trigger.

## Duplicate check (done first)
README, workers and docs searched for soccer, football, EPL, Premier League, La Liga, Bundesliga, Serie A, Champions League, MLS, draw/tie. **Not tested before.** Nearest: BOOKS1 (US moneylines, two-way, treated 0 of 150, gap median +0.76c), BOOKS2 (US totals/spreads vs a normal around the DK line, NOT_ENOUGH_DATA, control -2.7c), FAMSPORTS (sports totals without a book line), ESPN1/SPORTCONS1/SP1 (in-play and ladder arithmetic), INPLAY1, CALIB1 (Sports row, generic calibration, no outside price), USWEEP*, NEWLIST1 (listings), OICORE_SHAPE_INVENTORY (no soccer row). None uses a sportsbook price as the outside reference for a THREE-WAY market. Not a duplicate. Different from BOOKS1: a draw outcome exists and soccer is low scoring.

## Census (done first; listings and close times only, no candle, price or result kept)
`src/scalper/soccer1.py census` (cache outside the repo). Settled market listings, close before **2026-10-03T16:00Z**, series `KX<league>GAME/TOTAL/BTTS/SPREAD`. Match events with a GAME market: EPL 40, La Liga 50, Serie A 40, Bundesliga 36, Ligue 1 36, Champions League 18, Europa League 18, MLS 92, English Championship 71, Eredivisie 39, Primeira Liga 38, Liga MX 48 (Conference League 0). **Total 526 matches, each GAME event is 3 markets (home, tie, away), so 1,578 outcome markets** (TOTAL 3,826, BTTS 526, SPREAD 2,500 markets also listed). ESPN odds presence (registered sample: the first 8 events listed by ESPN for 1-30 Sep 2026 in eng.1, esp.1, ita.1, ger.1, fra.1, uefa.champions, usa.1, eng.2; 1 request per second; User-Agent "research-bot SOCCER1"): DraftKings moneyline present on **63 of 64 (98%)**, with a DRAW price and an over/under total on the same 63. The core API is used (site.api not used). Above the stop line of about 200 matches with odds (about 515 expected). Expected treated trades are far under 150 (BOOKS1 0, BOOKS2 11); the run is still done because the census cannot know the treated count without prices, and the answer is wanted either way.

## Universe
The 12 leagues above (ESPN slugs eng.1, esp.1, ita.1, ger.1, fra.1, uefa.champions, uefa.europa, usa.1, eng.2, ned.1, por.1, mex.1), matches with a DraftKings close three-way moneyline and a Kalshi GAME event. Join: ESPN event (league, start time, home and away team names) to the Kalshi event by UTC date within one day and team-name match on the markets' `yes_sub_title`; unmatched are counted and dropped. **Frozen W3: matches with ESPN start at or after 2026-10-03T16:00Z are never fetched or joined.** Windows by start date: W1 up to 2026-09-13T01:00Z, W2 up to the cut; halves are the first and second half of treated trades by date.
Out of scope, stated: BTTS and SPREAD ladders (no book price for them on the feed; NOT_RUNNABLE), strikes of TOTAL other than the book's own line (no tail model, BOOKS2 showed a normal is worse than the ask).

## Book probability (de-vig, one rule)
- G: DraftKings CLOSE moneylines (American) for home, draw, away; implied p_i = 100/(a+100) for a>0, -a/(-a+100) for a<0; proportional de-vig q_i = p_i / sum(p). The close is the book's final pre-game line (about kickoff, later than the Kalshi look; this favours the book, stated as a bias).
- T: the Kalshi total market whose strike equals the book's overUnder line (over K when the line is K.5): q(over) = pOver / (pOver + pUnder) from overOdds and underOdds. Other strikes not traded.

## Look
For each outcome market, the last 1 minute candle ending at least 120 s before ESPN kickoff (candles asked from kickoff minus 6 h to kickoff minus 60 s) with a valid quote: 0 <= bid < ask <= 1 and ask minus bid at most 0.10. None: not available (counted).

## Trade (one rule, no tuning)
Cheap side only: the outcome side (YES, or NO = 1 minus bid) whose ask is in [0.03, 0.30]. TREATED when q(side) >= 3 x ask. Buy one contract at the ask, hold to settlement, fee 0.07 x p x (1-p) per contract rounded up per 10 (C = 10), at most 2 per match (the two with the largest q/ask), win/lose from the market result (fetched only after this file is pushed). Control: every cheap outcome. Event (match) cluster for z. Also reported: gap q minus ask (median, p90), win rate vs mean ask vs mean q by ask bucket (3-10c, 10-20c, 20-30c), PF treated and control, halves, fees x1.2.
Result grade: the text of the result uses only cheap-side rows.

## Numeric prediction (before any data)
One price again: gap q minus ask median +0.5c to +2.0c, p90 under 6c (BOOKS1 +0.76c, BOOKS2 +1.1c). Draws (ask 20c to 30c, q about 0.25 to 0.30) never reach 3x, so treated are only long-shot sides (ask 3c to 10c). Treated n between 0 and 40 (point 10). Control (all cheap outcomes) win rate at or below its mean ask and mean net -1c to -3c, PF 0.7 to 0.95. Verdict NOT_ENOUGH_DATA 85%, FALSIFIED 12%, pass under 1%.

## Kill rules and verdicts
- FALSIFIED: treated n >= 150 and (mean net after fees not above 0 in both halves or PF under 1.5).
- NOT_ENOUGH_DATA: treated n < 150. Forward plan: months to go = (150 - n) / (n per month), rate from the in-window treated count over the window length (about 1.2 months of data, Aug 25 to Oct 3); the seasons run on, so a recorder of the DK close at each pre-game look would be needed; recommended only if the control gap is positive.
- A pass needs 150 treated trades, both halves positive, PF at least 1.5, z against the N-adjusted bar (running N about 730,335, z bar 5.27); nothing here promotes.
- Honesty: the control is the test of the idea, not the treated subset; a handful of treated trades decides nothing.

## Execution notes
Kalshi: 1 to 2 threads, backoff, batched candlesticks 8 markets per request, cache outside the repo (SOCCER1_CACHE), tracked background fetches. ESPN: core API, 1 request per second, honest User-Agent. Code `src/scalper/soccer1.py`, tests `tests/test_soccer1.py` (synthetic).
