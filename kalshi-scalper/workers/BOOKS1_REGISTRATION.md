# BOOKS1: is Kalshi's cheap side (ask 3c-30c) underpriced against the sportsbook closing line? Held to settlement.

Registered 2026-11-03 BEFORE any sportsbook line was fetched into a statistic and before any outcome was joined to a line. Worker ID BOOKS1, session "Strategy Research V2". 1 try. **N: +2** (coordinator keeps the total, about 730,130; z bar 5.27).

## Duplicate check (done first)
FAMSPORTS (points model, no book line reachable), FAMXV (Polymarket pre-game: median gap 0.5c), SP1, ESPN1 (ESPN win probability vs ask, favourite and gap), SWING1 (in-play swing), SPORTCONS1, SPORTSPRE, OICORE_SHAPE_INVENTORY: none uses a real sportsbook moneyline as the outside price. ESPN1 used ESPN's own win-probability model, not a book. Not a duplicate. Owner rule (Nov 3): cheap side only; no favourite-side result is computed or printed.

## Reachability findings (metadata only, 12 spot checks, no outcome joined)
`https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/odds` is keyless and returns for past games one provider, **DraftKings** (ESPN BET on some 2025 games), with `awayTeamOdds` / `homeTeamOdds` carrying `moneyLine` and `open` and `close` moneylines (American). So both the opening and the CLOSING pre-game line exist for past games (2026-08 onward checked in all four leagues; one NBA game had no odds item). Scoreboard-embedded odds not needed. Lines are the book's final pre-game line (time of close is about kickoff, not stamped), so the sportsbook side is slightly LATER than the Kalshi look; this favours the book and is stated as a bias.
**Earliest Kalshi quote** in `data/espn1.sqlite` (first valid two-sided candle vs ESPN start): median 6 to 7 minutes before the start (p10 -9 to -16, p90 -1 to +5); none 30 or 60 minutes ahead. So no 60 minute look is possible; the look is the last pre-game candle.
Leagues by matched game count (file 2026-08-29 to 2026-10-28): college football 963, MLB 426, NBA 123, NFL 107. All four are read (pooled and per league, information only, since this is a price comparison not a swing).

## Mechanism and counterparty
If the sportsbook's de-vigged chance is far above Kalshi's ask on the underdog, Kalshi retail is underpricing it; the counterparty is the Kalshi seller of YES (retail and market makers not tracking the books). Honest prior: market makers on Kalshi sports copy the books, so the two are one price within the spread.

## Rule (ONE, no tuning)
Look: for each game with a DraftKings moneyline for both teams, the **last candle ending at or before start minus 120 s** where both tickers are valid (0 <= bid < ask <= 1, ask minus bid at most 0.10). Sportsbook probability: **proportional de-vig**, q_team = implied(ml_team) / (implied(home) + implied(away)), implied(+x) = 100/(x+100), implied(-x) = x/(x+100). Candidate: the ticker with the lower ask (ties skipped) if its ask is in [0.03, 0.30] (cheap side). **Treated trade: buy that ticker's YES at the ask, C = 10, hard limit 0.30, held to settlement, one per game, when q >= 3 x ask.** Control: every cheap side in the band, one per game (same look, same candidate), no ratio condition.
**Fee:** 7% x C x p x (1-p) rounded up to the cent, per contract divided by C; fees x1.2 check. Taker at the ask.
Information only (cheap sides): gap q minus ask, median and p90, and the signed gap by league; calibration of q in the band for the control (win rate vs q vs ask).

## Windows
Windows by game start, fixed by date (same cut dates as SWING1): W1 start before 2026-09-13T01:00Z, W2 up to 2026-10-03T16:00Z, **W3 from 2026-10-03T16:00Z FROZEN: its odds are not fetched, its outcomes not joined, not opened unless W1 and W2 both pass.** Halves: first and second half of W1+W2 treated trades by date.

## Numeric prediction (stated before)
Median gap q minus ask for cheap sides: +0.5c to +2c (the ask carries the spread), p90 under 6c. Treated trades (q >= 3 x ask) in W1+W2: **0 to 15**, because a 3x ratio on a 3c to 30c price needs the book to say 9c to 90c, i.e. a 6c or larger gap at the bottom of the band and much more higher up. Control win rate within 1.5 points of mean ask, control net about -1c to -2.5c after fees. Verdict probability: NOT_ENOUGH_DATA about 95%, FALSIFIED about 4%, pass under 1%.

## Kill rules
- **FALSIFIED** if treated mean net after fees is not above 0 in both halves, or PF under 1.5 (pooled W1+W2), with at least 150 trades.
- **NOT_ENOUGH_DATA** if under 150 treated trades: report n, the months-to-go at the observed rate (file spans 2 months of football and baseball; NFL and NBA seasons run on), and a forward freeze: a fetch of the closing line at each Kalshi pre-game look going forward (needs a recorder; none built here).
- A pass also needs day-clustered z of the treated mean at the deflated bar (about 5.27) and fees x1.2 positive. W3 stays closed otherwise.

## Capped-probe spec (only if positive in both halves with this mechanism)
1 contract, hard limit 0.30, one per game, the four game-winner series, no overlap with L1 (different series), kill at 3 losses in the first 10 fills or net under zero after 40 fills.

## Hygiene
ESPN requests: 1 per second, User-Agent "research-bot BOOKS1 (kalshi research)", cache in the scratchpad outside the repo. Kalshi API not called (local sqlite only). The line is fetched before outcomes are joined; the outcome of a ticker is read only after the entry is fixed. Code `src/scalper/books1.py`, tests `tests/test_books1.py`; results `workers/BOOKS1_RESULT.md` and README.
