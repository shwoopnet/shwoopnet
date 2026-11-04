# BOOKNCAA1: is Kalshi's cheap side (ask 3c-30c) on D1 men's college basketball underpriced against the DraftKings closing moneyline? Held to settlement.

Registered 2026-11-04 BEFORE any Kalshi candle or outcome of KXNCAAMBGAME was fetched or joined. Worker ID BOOKNCAA1, session "Strategy Research V2". 1 try. **N: +2** (coordinator keeps the total, about 730,365; z bar 5.27). Cheap side only (owner rule): no favourite-side result is computed or printed. No 15 minute crypto or gold trigger. Discovery only.

## Duplicate check (done first)
BOOKS1 (CFB, MLB, NFL, NBA vs DK close: 0 treated of 258 cheap sides), BOOKS2 (totals and spreads, football and baseball), SOCCER1, INPLAY1, SP1, SPORTCONS1, FAMSPORTS, SPORTSPRE (football, NBA, MLB), ESPN1/SWING1, CALIB1 Sports row (5-10c +1.81c [-2.14, +6.24], 186 events, category level, no outside price) and OICORE_SHAPE_INVENTORY were read or grepped for NCAAMB / college basketball: none tests KXNCAAMBGAME or KXNCAAWBGAME against a sportsbook (KXNCAAMBTEAMTOTAL appears only in a PROPS1 census). **Not a duplicate.** What is new: the league (many mismatched games, so extreme cheap sides exist in volume), not the mechanism.

## Census (done before this registration; listings, close times and ESPN odds metadata only, no candle, no outcome)
- Kalshi `/historical/markets`: KXNCAAMBGAME 10,566 markets / **5,283 events**, closes 2025-11-03 to 2026-04-05 (all before the frozen cut); KXNCAAWBGAME 8,156 / 4,078 events (women's: DK odds not checked, **not run here**; a separate registration). The live settled list holds 288 markets from 2026-11-01 onward: those are the frozen last third and are never fetched or joined.
- ESPN odds coverage on a registered random sample, the first 100 events by md5(event_ticker): ESPN scoreboard (site.web.api.espn.com, groups=50, one request per date, 1 per second, UA "research-bot BOOKNCAA1 (kalshi research)") matched **61 of 100** by exact team-code concatenation; **60 of those 61 have a DraftKings/ESPN BET close moneyline for both teams**. Projected about 3,200 games with odds (above the 300 floor). A fallback match (below) is expected to lift the match rate.
- Expected treated trades: cannot be known from odds alone; BOOKS1's 3x condition produced 0 of 258. Prediction: 10 to 120 here, so NOT_ENOUGH_DATA is the likely verdict; the run is cheap enough (below) to measure it rather than assume it.

## Universe and joins (fixed now)
- Games: Kalshi KXNCAAMBGAME events with close time before 2026-10-03T16:00Z (all 5,283; no frozen game exists in development). Frozen third (games from 2026-10-03T16:00Z) never fetched or joined.
- Game match: event suffix `YYMONDD` + team codes; ESPN scoreboard for that date. Primary match: code == away_abbrev + home_abbrev. Fallback (unique per date only): code starts with away_abbrev or ends with home_abbrev, and exactly one game on that date satisfies it; the other side's code is the rest. A ticker is the away market if its suffix equals the away code, else the home market. Unmatched games are dropped and counted.
- Odds: ESPN core `.../events/{id}/competitions/{id}/odds`, first item with `homeTeamOdds.close.moneyLine.american` and `awayTeamOdds...`. Start time = ESPN scoreboard event `date`. Proportional de-vig as in BOOKS1.
- Book-side prefilter (book only, no Kalshi price or outcome): the book underdog is the team with the lower de-vigged q; **only the underdog's ticker is fetched** (candidate = book underdog; a game whose ask-cheaper side is the other team is not seen: stated deviation from BOOKS1's "lower ask of two", it halves the requests). Games with underdog q above 0.45 are dropped before any candle fetch (cannot have an ask in 3c to 30c with a gap of interest; this also drops pick-ems, which are not cheap sides).
- Candles: historical single-ticker 1 minute candlesticks `/historical/markets/{ticker}/candlesticks`, window start minus 4 h to start plus 10 min (public, 1-2 threads, backoff, cache in /tmp/bookncaa1 and a copy under the scratchpad, tracked background fetch, ordered by md5(event_ticker) with a 2 hour time box; unfetched games are reported as a prefix and not read in).
- Look: last candle ending at or before start minus 120 s with 0 <= yes_bid < yes_ask <= 1 and ask minus bid <= 0.10 (the ask is the close of yes_ask). Candidate valid only if ask in [0.03, 0.30]. Games without such a candle are counted ("no look").
- Outcomes (`result` yes/no from the historical market list) are read ONLY after the entries file (ticker, ask, q, start) is written and its sha256 recorded in the README ledger.

## Rule (ONE, no tuning)
**Treated:** buy the book-underdog's YES at the ask, C = 10 contracts, hard limit 0.30, held to settlement, one per game, when q (de-vigged DK close probability) >= 3 x ask and ask in [0.03, 0.30]. **Control:** every candidate in the same band, one per game, no ratio condition. Fee 7% x C x p x (1-p) rounded up to the cent, per contract divided by C; fees x1.2 check. Taker at the ask. Cluster = game (one per game, so event-level).
Information only (cheap sides): gap q minus ask, median and p90; win rate vs mean ask vs mean q by ask bucket (3-5, 5-10, 10-15, 15-20, 20-30c); control net and PF.

## Halves
Development games sorted by ESPN start time are split into thirds (counts only); nothing is fitted. Halves D1/D2 = first and second half of the treated trades by start time.

## Numeric prediction (stated before)
Match rate after fallback 60 to 75%; games with odds 3,000 to 3,700; candidates (book underdog with an ask in the band) 1,000 to 1,800; gap median +0.5c to +2c, p90 under 8c (larger than BOOKS1 because small-school books are thinner); control win rate 1 to 3 points under mean ask and control mean net -3c to -6c; **treated n 10 to 120** (probability treated n < 150: 90%). Verdict probabilities: NOT_ENOUGH_DATA 85%, FALSIFIED 12%, pass under 3%.

## Kill rules
- **FALSIFIED** if treated mean net after fees is not above 0 in both halves, or PF under 1.5, with at least 150 treated trades.
- **NOT_ENOUGH_DATA** if under 150 treated trades: report n, months-to-go at the observed rate (the season runs November to April, so the file is a full season: months-to-go is a season-count, about the same n per season), and a forward plan (record the DK close at each Kalshi pre-game look in the 2026-27 season; a first read after about 150 treated trades or the season's end).
- A pass also needs the game-clustered z of the treated mean at the deflated bar (about 5.27), treated minus control positive, and fees x1.2 positive; the frozen games stay closed otherwise.

## Capped-probe spec (only if positive in both halves and passes the bar)
1 contract, hard limit 0.30, one per game, KXNCAAMBGAME only, no overlap with L1 (different series), kill at 3 losses in the first 10 fills or net under zero after 40 fills.

## Hygiene
ESPN 1 request per second, honest User-Agent, no spoofing. Kalshi polite. Code `src/scalper/bookncaa1.py`, tests `tests/test_bookncaa1.py`; result `workers/BOOKNCAA1_RESULT.md` and README.

## Entries fixed before any outcome was read (2026-11-04)
Scoreboards 5,283 events processed, 4,976 matched (3,442 exact, 1,534 unique-per-date fallback), odds cached for 4,963. Candles fetched for 2,252 events in md5 order (two workers, one from each end of the md5 order, time box about 2.5 hours; 3,031 events not fetched, a random md5 subset not read in; 99 candle errors, 429 exhausted, left out). Entries file `entries.json`: **1,081 candidates** (book underdog, valid look, ask in [0.03, 0.30]); **0 with q >= 3 x ask** (largest q/ask 2.01), computed from prices and book only. sha256 `65630494b3402f4ab8d82640cf87082f124c2784a5ecfda62e50b682aedffb15`. Outcomes read only after this commit.
