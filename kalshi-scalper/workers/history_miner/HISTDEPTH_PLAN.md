# History Miner: which families have enough settled history to be read now (Nov 12, 2026)

Desk: R&D History Miner, reports to the Head of R&D. Research on public data only; no live account figure is in this file. Zero tries spent by anything here. [research]

## What sets the cost of history (measured, not assumed)

From the `CFRTI_K_LISTS` answer already on `kalshi-pull-data` (KXBTC15M):

- Kalshi's **live** list endpoint (`/markets`, status settled) holds markets that closed from about **2026-09-07** to now. Their candles come from the batched endpoint: up to about 9,000 candles a request, so one request can price many markets that close near the same time.
- Everything that closed **before about 2026-09-07** is on the **historical** endpoint (`/historical/markets`). Its lists page at 1,000 markets a request (about 2.2 KB a market), but its candles cost **one request a market** (`/historical/markets/{ticker}/candlesticks`).
- At 20 runs a day and 1,200 requests a run, history costs about 24,000 market candles a day if nothing else ran. So "fetchable now" means: the live window cheaply, and older history at one request a market.

## The table (sent to the Head of R&D)

Events a year and the Nov 10 count are Desk B's (`FAMILY_TABLE.md` on `claude/idea-desk-b`; Nov 10 is a lower bound, 23 of 24 hours hit the page cap). "Live window" is an estimate: the Nov 10 count times the days since about Sep 7 that the family was in season, labelled as such. "History before Sep 7" is NOT KNOWN for any sports series until the depth jobs below run, except where a test already counted it.

| Family | Events a year | Events fetchable now (live window, batched) | History before Sep 7 | Requests to price about 1,200 bets | Open to a new rule? |
|---|---|---|---|---|---|
| Tennis: ITF, Challenger, tour match winners | over 100,000 | estimate 20,000 or more matches (Nov 10: 408 ITF, 84 Challenger, about 110 tour, lower bounds) | not known | lists about 40 to 60 pages; candles a few hundred batched | Only as a rating or calibration rule; ratings FALSIFIED twice on esports, TENNIS1's source is barred. No card |
| Virtual sports: e-soccer, e-basketball, Liga Pro table tennis | over 200,000 | estimate 40,000 or more (Nov 10: 450, 84, 147) | not known | as tennis | VIRT1 every sign negative (n 15); a rating rule again. No card |
| 15 minute series (crypto, metals, forex) | about 35,000 a series | yes, and recorded books | back to at least April 2026 (KXBTC15M lists reach 2026-04-17 in 14 pages) | already held | CLOSED families (favourite, cheap side late, order flow, grammar sweeps) |
| Esports match and map winners (CS2, Dota 2, Valorant, LoL) | thousands of matches | MAPBREAK samples 1,500 matches from Sep 12 to Oct 22 (about 4,700 in 61 days) | from 2026-03-31 at least (ESPORTM1's census: 4,141 qualified matches to Oct 3) | about 1 request a market for the older part: about 2 to 3 markets a match needed, so about 10,000 to 20,000 requests for the March to September block | MAPBREAK (Desk B, Testing Desk) is the card; history would raise it from about 150 to 300 bets toward the about 950 it needs |
| NHL periods 1 to 3 and level after regulation (TIE3, NHLOT) | 3,936 period-events | about 630 Tie contracts priceable (Oct 27 to Nov 12, the Head's count) | **the question that decides TIE3**: if the series ran in the 2025-26 season, about 3,900 more | about 1 request a Tie market: about 4,000 requests, 4 runs, one day | TIE3 is the card (Desk B). Depth job A answers it |
| NFL quarters (TIE3 cell) | 1,140 quarter-events | about 600 (season from Sep 10) | the 2025 season if listed: about 1,100 | about 1,100 requests | TIE3 cell. Depth job A |
| Soccer first halves, 12 series (TIE3 cell) | about 2,800 big-league games | estimate 1,000 to 1,500 games | not known | about 1 request a game | TIE3 cell. Depth job B |
| Soccer extras against siblings (SOCDERIV) | about 2,800 big, about 9,000 small | estimate several thousand | not needed: the card uses the live window | 200 to 300 batched | SOCDERIV is the card (Desk B, Testing Desk). Not duplicated here |
| NBA and college basketball halves and quarters | 1,230 NBA, over 5,000 college games | NBA about 200 games (from Oct 21); college about 600 (from Nov 3) | last season not known; KXNCAAMBGAME has 5,283 events from 2025-11 to 2026-04 (V2's census) | about 1 request a market for last season: 10,000 or more | Ties under 10%: cheap tail, out. Spread and total ladders are a venue of SOCDERIV's card. No card here |
| Hourly city temperature | about 32,000 | live window, 4 cities | not known | batched | Forecast against bracket is a CLOSED family |
| Weather daily, approval, macro, politics, weekly counts | under 400 or slow | | | | closed or slow families (paper screen only) |

**Plain reading.** The families with 1,200 or more events that can be fetched cheaply are tennis, virtual sports, the 15 minute series and esports. The 15 minute series are closed families. For tennis and virtual sports the only rule a one-minute bot may write before the match is a rating or calibration rule, and a mid-priced bet held to settlement needs the price wrong by about 9 to 12 points to reach the bar (Desk B's arithmetic); ratings have failed twice. So history is NOT what is short there; a mechanism is. **Where history IS the binding constraint is the two Friday cards that died on it: TIE3 (about 630 contracts against about 1,200 needed) and MAPBREAK (150 to 300 bets against about 950).** Both depend on whether the same series existed before Sep 7. That is what the two depth jobs below answer, cheaply.

## The depth jobs (zero tries, listing only)

| Job | Requests (cap) | Series | Size |
|---|---|---|---|
| `HISTDEPTH_A` | 8 requests, at most 29 pages | KXNHL1P, KXNHL2P, KXNHL3P (6 pages each), KXNHLOT (3), KXNFL1Q to KXNFL4Q (2 each) | about 62 to 90 MB |
| `HISTDEPTH_B` | 16 requests, at most 40 pages | the 12 soccer first-half series of TIE3 (2 pages each), KXCS2GAME (6), KXDOTA2GAME (4), KXVALORANTGAME (2), KXLOLGAME (4) | about 90 to 130 MB |

- Historical endpoint only (`/historical/markets`, series_ticker, limit 1000, cursor). Pages are newest first: a short last page means the series' first market was reached and the count is exact; a full last page means a floor.
- Held-out: none touched. Everything on the historical endpoint closed before about 2026-09-07, before TIE3's held-out (2026-11-13), MAPBREAK's (2026-10-23) and any NHLOT date. The lists carry each market's `result`; only counts, close dates and event tickers are read from them in this step. A later bet-level registration decides how any of it is used, BEFORE any candle is pulled.
- Owner field `MAIN` (the runner's owner list has no History Miner). Both pass `python3 -I scripts/kalshi_pull.py <JOB> --dry-run`. The workflow's choice list needs the two names (Main's change).

## What I do with the answer

1. One line per series to the Head: settled events before Sep 7, first close date, exact or floor.
2. If NHL periods hold about 1,200 or more Tie contracts before Sep 7: a bet-level registration on that history, written with Desk B under TIE3's mechanism (one try, a date-constant development and held-out split by close date, base rate always from games earlier than the bet, the same 10c gap and 4c spread rule), sent to the Head BEFORE any candle job. The candle job is then about 1 request a Tie market.
3. If the series start in October 2026: TIE3 stays as the Head told the owner (a season forward), and the job cost about 1 minute.

## Rules not registered, and why

No own rule is registered from this table. Every family with enough fetchable events either sits in a closed family or would need a rating or calibration rule that has already failed or cannot reach a 9 to 12 point error. Padding the count with such a rule would spend a try for nothing. Deflation ledger: 0 tries added.
