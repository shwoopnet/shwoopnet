# SINGLELEG1 (registered Nov 9, 2026, before any outcome is read): are there mispriced SINGLE legs?
Owner/main directive: find any series and price band where the realized hit rate beats the price paid by 2c or more after the fee, with a held-out third and the deflation counter. Research only; no order, no key, no network (local sqlite caches).
## Data (held, listed only)
21,036 settled markets with a usable decision quote, 22 series, from `data/sports.sqlite` (tennis ATP/WTI/challengers, NCAAF, MLB, NHL, UFC, NFL, NBA, WNBA, esports game winners), `data/sports1.sqlite` (NBA/NHL/NFL totals and first-half totals ladders), `data/nflcombo1.sqlite` (NFL moneyline, passing/rushing/receiving yards, anytime TD, one season) and `data/nflpc1.sqlite` (NFL spread, total, passing yards). A market in two caches is counted once (first cache wins).
## Decision quote (fixed, one lead, no search)
The last candle ending at least 4 hours before the market's close time, with both sides quoted (bid > 0, ask < 1) and ask minus bid at most 0.05. Markets without one are dropped and counted. Price paid: YES at the ask; NO at 1 - bid. Fee: ceil(0.07 x 10 x p x (1-p) x 100) cents for 10 contracts, per contract (taker, C = 10).
## Cells
series x side (YES or NO) x price band, bands 0.05 to 0.10, 0.10 to 0.20, ..., 0.80 to 0.90, 0.90 to 0.97 (10 bands). Potential cells 22 x 2 x 10 = 440; N = 160 (futures and prior sports ledgers) + 440 = 600 (conservative: all potential cells counted, only 92 have 100 development markets). Edge = mean of (win - price - fee) per contract, in dollars.
## Cuts
Per series, the first two thirds of markets by close time are development; the last third is held out and read ONCE, only for a shortlisted cell. Events (the ticker without its last segment) are clusters: ladders and both sides of a game are not independent; z is the cluster-robust t-statistic of the mean.
## Shortlist rule (set now)
A cell is shortlisted only if development has at least 100 markets in at least 30 events, mean net edge at least +0.02 dollars per contract, and cluster-robust z at least the one-sided normal quantile for alpha 0.05/600 (3.88). The holdout is then read once for those cells: a cell passes only with a positive net edge on at least 20 held-out markets; below 20 it is NOT_ENOUGH_DATA. A pass would only mean "worth a forward test", never "tradeable".
## Prediction (before reading anything)
Zero shortlisted cells (about 90%). The favourite-longshot bias in Kalshi sports is documented as a cost on the longshot side and nearly flat on favourites before fees; the fee on 50c tickets is about 1.75c per contract, so 2c net needs a 4c gross gap. If anything, cheap NO sides of totals ladders (a known Kalshi ladder pattern) or tennis challenger favourites may show up; those would be hypotheses, not findings.
## Output
Ranked list (series, side, band, n, events, net edge, z, holdout result) for main.
