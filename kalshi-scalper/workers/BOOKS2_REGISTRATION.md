# BOOKS2: Kalshi game TOTAL and SPREAD ladders, far (cheap-side) strikes vs a normal distribution around the DraftKings closing line. Held to settlement.

Registered 2026-11-03 BEFORE any total or spread line was read into a statistic, before any final score was fetched and before any Kalshi total or spread candle or result was fetched. Worker ID BOOKS2, session "Strategy Research V2". **N: +4** (two rules, T totals and S spreads, +2 each; coordinator keeps the total, about 730,245; z bar 5.27). 1 try each.

## Duplicate check (done first)
- FAMSPORTS: a points model from public scores for totals lost to the market (Brier 0.30 vs 0.27); it had no book line. BOOKS2 uses the book's own line as the centre, so the model is not a team average.
- F7 (README, 2026-10-26): the "under" at YES mid 0.40 to 0.60 on total ladders, hold; predicted about -2c. Near-the-middle strikes, no book line. Different strikes and a different information source; its middle-of-ladder result is not repeated here.
- BOOKS1: moneyline only; implied book probability vs the game-winner ask is one price (median gap +0.76c, treated n 0). Totals/spread ladders were never tested against the book line.
- SP1, SPORTCONS1 (ladder arithmetic locks, not NOT_RUNNABLE spread ladders by value), ESPN1, SWING1, OICORE_SHAPE_INVENTORY: no row uses a sportsbook total or spread line as the outside price on a ladder's far strikes. ARB5 (totals ladder locks) is arithmetic within Kalshi, not an outside price. Not a duplicate.
- Owner rule (Nov 3): CHEAP SIDE ONLY (ask 3c to 30c). No favourite-side result is computed or printed.

## Data (metadata only so far)
- Games: the BOOKS1 universe, `data/espn1.sqlite` table `match` joined to `egame`, start before **2026-10-03T16:00Z** (frozen third W3 never fetched or joined). Games with a DraftKings total in the BOOKS1 odds cache (ESPN core API `.../odds`, close line; field `overUnder` and `spread`, which is the HOME team spread, negative when home is favoured): NCAAF 501, MLB 396, NFL 50 (NBA 0 before W3). Leagues by game count: **college football, MLB, NFL**. NHL has no ESPN match file. Per league and pooled are read.
- Kalshi series (public series list): totals `KXNCAAFTOTAL`, `KXMLBTOTAL`, `KXNFLTOTAL`; spreads `KXNCAAFSPREAD`, `KXMLBSPREAD`, `KXNFLSPREAD`. Totals markets are "over K.5" per strike (YES = over); spread markets are "TEAM wins by over K.5" for each team. A total or spread event shares the suffix of its game-winner event (`KXNFLTOTAL-26NOV01NEMIA` and `KXNFLGAME-26NOV01NEMIA`), which is the join key.
- Final scores from ESPN's public scoreboard (one request per league per date, 1 per second, User-Agent "research-bot BOOKS2 (kalshi research)"), used ONLY for the sd fit.
- Kalshi: settled market lists per series (cursor), then the BATCHED candlestick request (8 markets per request), 1 to 2 threads, backoff, cache outside the repo.

## Look
For each strike market, the **last candle ending at or before start minus 120 s** (start = ESPN start; candles asked from start minus 6 h to start minus 60 s) with a valid quote: 0 <= bid < ask <= 1 and ask minus bid at most 0.10. No such candle means the strike is not available (counted, not imputed). YES ask = ask; NO ask = 1 minus bid. Cheap side of a strike = the side with ask in [0.03, 0.30] (at most one qualifies).

## Fetch economy (before any outcome)
Only strikes that could plausibly be cheap are fetched: strikes with distance |K.5 - mu| of at least 0.5 x PRIOR_SD, where PRIOR_SD is fixed here from general knowledge, not from data: totals NCAAF 14, NFL 10, MLB 3.2; margins NCAAF 16, NFL 13, MLB 3.3. mu is below. (A narrower fetch can only drop trades near the middle, which are not cheap anyway.)

## Probability rule (one, no tuning)
- **Totals:** total T ~ Normal(mu = L, sd), with L = DraftKings close overUnder. P(YES, "over K.5") = 1 - Phi((K.5 - L) / sd). (Strikes are half points, so no continuity correction; an integer L is used as is.)
- **Spreads:** home margin M = home score minus away score ~ Normal(mu = -S, sd), with S = DraftKings close home spread (home favoured by 7.5 has S = -7.5, mu = +7.5). P("home wins by over K.5") = 1 - Phi((K.5 - mu) / sd); P("away wins by over K.5") = Phi((-K.5 - mu) / sd).
- **sd estimation, written before use:** per league, the root mean square of (actual total - L) for T and of (actual margin - mu) for S over games in the **first two thirds** of that league's games with a line, ordered by start time (cut by game count, decided from line availability only). No other fitted number. The last third of each league (**the test third**) is never used to fit.
- The PRIMARY result is the **test third** (out of sample for the sd). The fit two thirds are reported as information (in sample for the sd, not a result).

## Trade (ONE rule per family, no tuning)
For each game and family, over all fetched strikes with a valid look and a cheap side: model probability p of the cheap side from the rule above. **Treated trade: buy the cheap side at its ask when p >= 3 x ask, C = 10, hard limit 0.30, held to settlement, at most 2 strikes per game per family (the two largest p / ask; ties lower ask).** **Control:** every cheap side (ask 3c to 30c) with a valid look, one per strike, no ratio condition, same sd rule. Fee 7% x C x p_ask x (1 - p_ask) rounded up to the cent (per contract divided by C), taker at the ask; fees x1.2 check. Outcome read only after the entry is fixed.
Events (a game within a family) are ONE cluster: z is computed on per-game net sums, also by day.
Information only: gap = model probability minus ask over cheap sides (median, p90, by league), calibration by ask bucket (win rate vs ask vs mean model p), the fitted sds, coverage (fraction of fetched strikes with a valid look).

## Mechanism and counterparty
Retail overpays for the long-shot over/under or big margin? or underprices it? A normal around the book's centre prices the far tail; if retail overweights centre-hugging, tails are underpriced. The counterparty is the Kalshi seller of the cheap side (retail and thin market makers). Honest prior: market makers copy the same book line and a normal tail is rough (football scores are lumpy: 3 and 7 point steps; MLB runs are skewed), so any gap is as likely to be my model's error as the market's.

## Numeric prediction (stated before)
Cheap sides are about calibrated to the model within the model's own error: median gap (model p minus ask) -0.5c to +1.5c, p90 under 6c. Treated trades in the test third: **0 to 40 per family** (a 3x ratio at 10c to 30c needs 30c to 90c). Control mean net about -1c to -3c per contract after fees. Win rate within 2 points of mean ask. Verdict: NOT_ENOUGH_DATA about 90%, FALSIFIED about 9%, pass under 1%. **Treated n small, one price again.**

## Kill rules (each family separately)
- **FALSIFIED** if, with at least 150 treated trades (test third), mean net after fees is not above 0 in BOTH halves (by date) or PF is under 1.5.
- **NOT_ENOUGH_DATA** if under 150 treated trades: report n, the months-to-go at the observed rate (the file spans Aug 29 to Oct 3 for fit and test; NFL and college football run to January, baseball ended), and a forward freeze (a recorder of the DK close at each pre-game look is needed; none built here).
- A pass also needs day-clustered z at the deflated bar (about 5.27), fees x1.2 positive and the frozen W3 stays closed otherwise.

## Hygiene
ESPN requests 1 per second. Kalshi shared API: 1 to 2 threads, backoff on 429, cache in the scratchpad outside the repo, tracked background fetches. Code `src/scalper/books2.py`, tests `tests/test_books2.py`; results `workers/BOOKS2_RESULT.md` and README.
