# NEWH11 registration (Strategy Research V2 worker NEWH11, 2026-10-30, research only)

Written and pushed BEFORE any NEWH11 rule was joined to a Kalshi quote after its signal or to any outcome. Code
`src/scalper/newh11.py` (committed with this file); result `workers/NEWH11_RESULT.md`. Markets: Kalshi gold `KXGOLD15M` and
Bitcoin `KXBTC15M`; outside prices are public and keyless (Yahoo `GC=F` 1 minute COMEX gold future bars, `data/gc1m.json`, fetched
2026-10-29; Binance spot `BTCUSDT` 1 minute klines from data.binance.vision, local to 2026-10-26 plus daily files for 10-27 to 10-29
fetched 2026-10-30 into the scratchpad). Times are UTC in the code and US Central (CDT, UTC-5, the whole sample) in words.

## Step 1: which of the brief's families are untested (ledger grep, README to NEWH10)

| Family in the brief | Ledger | Status |
|---|---|---|
| Settlement-source mechanics (the partly locked 60 s BRTI average in the last minute, a Coinbase/Kraken/Bitstamp proxy, either side, by proxy distance) | **BTCAVG** (exactly this: median of the three venues, P(YES) from the observed part of the average plus a random walk, either side; NOT_ENOUGH_DATA, 7 to 16 trades, "Kalshi's last-minute quotes already price the averaging"), **L9** (FALSIFIED), **LATECAL**, NEWH2 decline | TESTED, no try spent |
| Strike placement (a strike grid, round strikes at the open) | 15 minute strikes are the settlement source's own value at the open, not a chosen level: the information look below shows 8,158 Bitcoin and 6,723 gold strikes with all 100 cent endings and 0.0% on a $10 grid, so there is no grid to be biased; the lagging-average strike at the open is **L8** (FALSIFIED, -2.38c); round dollar levels ($500, $1,000) as barriers are **NEWH1** (FALSIFIED both); hourly ladder strikes on a $100 grid against the curve are **KINK**, **LAD1** | TESTED or not applicable |
| Window-to-window persistence (outcome or open-price momentum between consecutive 15 minute windows) | **S06** (side = previous outcome), **BTC1 CONT** (buy the prior result at the open), **S07**, **BK2** (streak fade and continue), **STREAK3**, **OPENLEAN** (NEWH6), **XLEAD1**, NEWH1 flip reversal at the next open | TESTED, no try spent |
| Gold 15 minute against public gold futures or spot moves around the open (lead-lag at the open) | **GOLDFV1** is the same input (GC=F) at 10 and 6 minutes left (FALSIFIED, holdout unread); S14, GREOPEN, GBREAK use Kalshi's own gold price across the daily break; NEWH9 ASIAGOLD and NYGOLD are clock drifts at the open; no test of the FIRST minute of a gold window against COMEX | UNTESTED at the open (disclosed as adjacent to GOLDFV1): H1 |
| Other family with a named counterparty | **CME gap fill** (N6 in the needs list, "CME futures closes", never run; EVT1's CME_BTC_CLOSE cell is the window AT the Friday close, not the weekend distance from it) | UNTESTED: H2, H3 |
| Declined from the director's never-tried list | Upbit (Korean) premium: the rule shape "a venue premium change picks a side" is **COINPREM** (FALSIFIED), a variant; Pyth gold: NOT_RUNNABLE (GOLDPYTH-H, 401 without a key); spot depth: no history; Deribit liquidations: LIQ1-INFO decided no outcome test | Not spent |

## What this is NOT

No 88c to 97c favourite (L1), no L1 exit, size, filter, hour or throttle test; no side bought late (every entry is the second
minute of a window, 13 minutes before the close); no price-band selection of a cheap side (GOLDOPEN's side is chosen by a model
from COMEX and may be either side at any price 10c to 90c; CMEGAP's side is chosen by where Bitcoin sits against the CME Friday
close and is bought at 30c to 70c). Not a variant of BTCAVG (last minute), L8 (spot against the lagging strike, any time), or the
persistence family (no previous outcome is read).

## What was looked at before this was written (disclosure)

The ledger sections above; NEWH9 and NEWH10 code; `python -m scalper.newh11 counts`, which reads clocks, data coverage and strike
values only (no Kalshi quote, no result):

| Arm | discovery | validation | holdout |
|---|---|---|---|
| GOLDOPEN windows (KXGOLD15M, closes 10-01 to 10-29 15:00) | 615 | 544 | 681 |
| CMEGAP-W windows (KXBTC15M, open in the CME weekend) | 1,372 | 695 | 285 |
| CMEGAP-R windows (KXBTC15M, open Sunday reopen to Monday close) | 559 | 361 | 184 |

Spot minutes 2026-08-01 to 10-29 (129,600); GC=F bars 2026-09-30 15:30 to 10-29 15:18 (28,802). GOLDFV1 read GC=F against gold
quotes at 10 and 6 minutes left on Oct 1 to about Oct 20 (its holdout unread); no rule has read the first minute of a gold window
against GC=F.

## Common to every rule (fixed now)

- **Signal candle:** the Kalshi 1 minute candle ending 840 s before the close (the first minute after the open). **Fill:** the
  held side's ask on the NEXT candle (ending 780 s before the close), never the signal candle's quote; missing, "no fill", and
  outside the rule's band, "band", both counted. One trade per window, held to settlement, nothing sold.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle had volume 0.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, net positive at fees x1.2 in each, at least 100 / 50
  / 30 trades (discovery / validation / holdout), a named counterparty, and pooled day-clustered z at least the deflated bar.

## H1 GOLDOPEN (1 try): gold's opening quote lags COMEX in the first minute

- **Universe (close time only):** every settled KXGOLD15M window closing 2026-10-01 00:00 to 2026-10-29 15:00 UTC (the GC=F file's
  span). Kalshi candles from `l1b`, `book`, `fresh`, `five` (first file wins per close).
- **Windows:** DISCOVERY closes 10-01 to 10-11; VALIDATION 10-11 to 10-20; HOLDOUT 10-20 to 10-29 15:00 (frozen; read once, only
  after a pass in both, after that result is pushed).
- **Model:** O = open (close - 900 s). d = close of the GC=F bar starting at O (it ends at the signal time) minus close of the bar
  starting O - 60 (the minute Pyth's strike candle covers; the future-to-spot basis cancels in the difference). sigma = population
  standard deviation of the 1 minute close changes between consecutive bars starting O - 3,660 to O - 60 (at least 45 changes).
  p(YES) = Phi(d / (sigma x sqrt(14))). Skipped before any quote: either bar missing, fewer than 45 changes, any 1 minute change
  above 0.5% (roll or bad print).
- **Rule:** at the signal candle (0 < bid < ask < 1), edge YES = p - ask; edge NO = bid - p (NO's ask is 1 - bid). Take the larger;
  trade if at least 0.05. Fill band [0.10, 0.90].
- **Counterparty:** the quoters who open each gold window (the book opens empty) and post near the previous window's close level
  in the first minute, before a COMEX move in that minute is in their price; and takers who lift those quotes.
- **Honest alternative:** GOLDFV1 found Kalshi gold already prices the latest COMEX minute at 10 and 6 minutes left; quoters at the
  open use the same feeds; a 1 minute COMEX change is mostly noise against Pyth spot.
- **Prediction:** FALSIFIED; discovery PF 0.80 to 1.10 at C = 10, win rate within 3 points of price.

## H2 CMEGAP-W (1 try): weekend Bitcoin drifts back toward the CME Friday close

- **Clock:** CME Bitcoin futures close for the week Friday 16:00 CT (21:00 UTC) and reopen Sunday 17:00 CT (22:00 UTC). F = Binance
  spot BTCUSDT close of the 1 minute candle ending Friday 21:00 UTC (a proxy for the CME close; the futures basis is not modelled).
- **Universe:** KXBTC15M windows opening Friday 21:00 to Sunday 22:00 UTC, closes 2026-08-06 to 2026-10-30. Candles `l1b`, `book`,
  `fresh`. **Windows** (as NEWH9 and NEWH10): DISCOVERY to 2026-09-21; VALIDATION to 10-18; HOLDOUT 10-18 to 10-30 (frozen).
- **Rule:** x = spot close of the 1 minute candle ending at the signal time. g = F / x - 1. If |g| at least 0.5%: buy the side
  toward F (YES if F > x, NO if F < x). Fill band [0.30, 0.70].
- **Counterparty:** Kalshi quoters who price each weekend window as driftless while CME-referenced desks and "the gap must fill"
  traders lean the price back toward the level their futures will reopen against.
- **Honest alternative:** the gap story is chart folklore; spot is a martingale at 15 minutes and Kalshi's opening price is about
  50c; at least 58% wins would be needed for PF 1.5.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.10, win rate within 3 points of price.

## H3 CMEGAP-R (1 try): after the Sunday reopen, an unfilled CME gap fills

- **Universe:** KXBTC15M windows opening Sunday 22:00 to Monday 21:00 UTC (the first CME session after the weekend), same dates and
  windows as H2.
- **Rule:** as H2 (|g| at least 0.5%, buy toward F, band [0.30, 0.70]), and only while the gap is unfilled: no spot 1 minute high
  (when F > x) or low (when F < x) since Sunday 22:00 UTC up to the signal time has reached F.
- **Counterparty:** as H2, plus CME traders whose reopen sits at a gap to Friday and who trade it shut on CME; Kalshi quoters at 50c
  do not price it.
- **Prediction:** FALSIFIED; discovery PF 0.80 to 1.10.

## Information look (counted in N, not a rule)

- **I1 strike structure** (already printed by `counts`, strikes only): KXBTC15M and KXGOLD15M strikes are full-cent values with no
  grid (whole dollars about 1%, the base rate); KXBTCD ladder strikes are $100 apart. This is why the strike-grid family is not
  applicable to the 15 minute markets.

## Kill criteria (each try, no parameter changes after any score)

- Discovery: fewer than 100 trades NOT_ENOUGH_DATA (validation printed for the record). PF at C = 10 under 1.5, or net at fees x1.2
  at or below 0: FALSIFIED.
- Validation (after a discovery pass): fewer than 50 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
- Holdout (after both passes, read once): fewer than 30 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
  All PF gates met but pooled day z under the deflated bar: NOT_ENOUGH_DATA. All gates met: NOT_YET_FALSIFIED (forward registration
  only).

## Count

N tried: **3** (GOLDOPEN, CMEGAP-W, CMEGAP-R) + 1 information look (I1) = **4**. Running count about 627,852 (after NEWH10) + 4 =
**about 627,856**. One-sided Bonferroni z bar at 0.05: **5.24**.
