# NEWLIST1 registration: cheap sides in the first hours after a market is listed (Strategy Research V2, research only)

Written 2026-11-03 BEFORE any candle was downloaded and before any win or loss of any NEWLIST1 trade was computed. Code `src/scalper/newlist1.py`,
tests `tests/test_newlist1.py`. Nothing here means trade, touches live code, `functions/`, L1 or OICORE, or has a promote verb.

## Duplicate check (done first)
grep of README.md, workers/*.md and scout/FLB1/CAL1 for new listing, first hours, market age, NEWMKT, LISTING, `open_time`: **no test of market age exists.**
Only neighbours: README idea table row N6 ("new series, first weeks", never run, "merge with N3"), FLB1 and CAL1 and scout (cheap and favourite sides by
category at fixed LEAD times before the close: 24 h, 72 h, 168 h, never time since listing), PUB20 P10 REOPEN (first hour after a trading halt, 15 minute
series, FALSIFIED), OP1 to OP3 and OPENLEAN (first minutes of 15 minute crypto windows, falsified). None conditions on how old the market is. Not a reword.

## What was read before this registration (disclosure)
Listing metadata only, from the public keyless `/series` and `/markets` (status settled, closing 2026-09-04 or later): ticker, series, event, created time,
open time, close time. The `result` field comes in the same listing and was stored in a separate table (`res`) that the universe code never reads; no
outcome was counted, printed or looked at. Not read: any candle, price, volume or win rate.
Scan list (fixed by metadata, `scan_wanted`): every series Kalshi labels daily, weekly or hourly; monthly Economics, Financials and Commodities; Sports
series of a named league whose ticker ends in GAME, MATCH, TOTAL, SPREAD or FIGHT. KXMVE, anything with 15M, and gold (KXGOLD*) are excluded; so are
all 15 minute crypto and the hourly crypto ladders by the life filter below. The full list of 4,957 recurring series was too many calls for the shared
rate limit, so the other 3,600 custom series (politics, entertainment, one-offs) are NOT scanned: stated, not hidden.

## Universe, frozen (metadata only)
Rule: every scanned series with at least 200 settled markets closing 2026-09-04 or later whose life (close - open) is at least 12 hours. The metadata scan is still running (rate limited), so the family list and counts are committed as **Amendment 1 (metadata only, before any candle download)**; the rule above is what is frozen now.

## Mechanism and counterparty
When a market lists, its book opens EMPTY (bid 0, ask 0.99; seen on a fresh ATP game spread) and the first quotes are wide and set by a maker who has
not yet converged on fair value, or by a retail first mover. Two opposite stories: (a) **cheap sides overpriced** (the favourite-longshot bias at its
worst, because a thin new book has no one to arbitrage a 12c quote on a 3c event), so the cheap side loses more than the fee; (b) **cheap sides
underpriced** (a maker quoting a conservative wide spread leaves value on the tail). The counterparty of a taker buying a cheap side is the maker or the first
trader who posted that ask. I expect (a), which is the usual finding, and the test is whether the early-life gap is different from the same family's gap
later in life; only a **different** gap is a new-listing effect. Prior that any family-look is a net-positive survivor after the fee: 2%.

## The two rules (each is one rule family; look at ages 1, 3 and 6 hours are three claims of the same rule)
Data: hourly candles (`period_interval` 60) from `open_time` to `close_time` for each market; fields yes_bid close and yes_ask close. NO ask = 1 - yes bid.
A **priced** candle has bid >= 0.01, ask <= 0.99 and ask > bid; an empty book is never a look.
**Look at age T hours (T = 1, 3, 6):** the first candle whose end time is at least open + T hours and less than open + (T+1) hours (so age T to T+1 hours;
the quote is that candle's close, known when it ends). No priced candle in the slot = no look, counted as unpriced and reported.
**Late-life control look:** the last candle ending at or before close - 3 hours (needs life >= 12 hours, so it is always after the 6 hour look).
**A (cheap side):** the side whose ask is 0.05 to 0.30; if both qualify the cheaper. Taker at that ask, HARD LIMIT 0.30, hold to settlement.
**B (tail favourite, one separate counted try):** the side whose ask is 0.85 to 0.97, HARD LIMIT 0.97, hold to settlement.
Fee: 7% x C x p x (1-p) rounded up per order, C = 10, as everywhere (x1.2 shown). Net per contract = win - ask - fee. PF = gross win / gross loss of net per contract.
z = day-clustered (by the market's open date) mean net per contract, `calibration.cluster_mean_z`. Calibration gap = win rate minus price paid.

## Sample (frozen before download)
Per family, the 400 markets (or all if fewer) with the smallest md5(ticker) among those with life >= 12 hours: a hash with no outcome in it. Cluster key: open date.
Thirds by market close time over the picked set (rule fixed now; the two cut dates go in Amendment 1 with the family list, from metadata, before any candle): **discovery D** closes before the first-third cut; **validation V** the first-third cut to before the second-third cut;
**holdout H** the second-third cut on, **NOT READ unless a rule passes D and V** (the scorer prints only its count until then).

## Claims and kill rules (decided now)
Claims: A1, A3, A6, B1, B3, B6, each pooled over the whole universe, `ALL`. Per-family cells are INFORMATION (each family x look is a cell; a family cell that
passes is only flagged, because it was picked from many); the family count is stated in the result and a family cell must reach z 5.27 to be called more than a flag.
1. A claim with fewer than 150 entries in D+V or fewer than 50 in D or in V: **NOT_ENOUGH_DATA**.
2. **FALSIFIED** if PF < 1.5 in D or in V, or net mean per contract is not positive in both, or the early-minus-late difference in calibration gap (same families, the
   late-life look of the same rule) is not positive in both D and V. The last condition separates a new-listing effect from the family's general bias.
3. Otherwise H is read once: PF < 1.5 or negative net in H = FALSIFIED, else NOT_YET_FALSIFIED (never "validated").
4. Reported for every cell whatever the verdict: n, win rate vs price paid, gap, PF, mean net (c), z, spread of the quote, unpriced share.
5. The scorer refuses a second run (`data/newlist1_score.json`). No parameter, family, look or band is changed after the first outcome.
6. A claim positive in net mean in BOTH D and V with a stated mechanism gets a capped-probe spec (1 contract, hard limit 0.30, kill rule, named worst-day dollars,
   when 40 fills would exist) even if it fails PF 1.5; information, never a recommendation.
**Prediction (numeric):** A: win rate 1 to 3 points BELOW price paid in every look (gap -1 to -3 points), PF 0.70 to 0.95, mean net -2c to -4c; early gap more negative than
late gap by 0 to 2 points; entries: unknown until candles exist, expected a few hundred per look pooled. B: win rate 0.5 to 1.5 points below price, PF 0.85 to 1.0 (a payoff ratio near 0.07, so PF is hostage to 2 or 3 losses).
Likeliest verdict: all FALSIFIED. N: +4 (two rule families, +2 each); the per-family cells are not separate tries.

## Disclosures
Hourly candles give one quote per hour (the close), so "first priced candle" is coarse; a faster 1 minute read of the first 10 minutes of life is NOT tested.
Markets on one event (strikes of one ladder, two sides of one game) are correlated; the day cluster does not remove that, so z is optimistic.
Sports and election markets list a day or more before the event: age is not time to the event. Family and age are confounded with lead time to the close; the
late-life control exists to hold that fixed within a family.

## Outcome status at registration
No outcome seen. Candles: none downloaded. `res` table holds settled results from the listing, unread. Expected read date: the day candles finish (2026-11-04 or earlier), one scored run.
