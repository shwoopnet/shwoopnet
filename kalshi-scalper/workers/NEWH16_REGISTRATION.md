# NEWH16 registration (Strategy Research V2 worker NEWH16, 2026-10-30, research only)

Written and pushed BEFORE any NEWH16 signal was joined to any Kalshi quote after its signal time or to any outcome. Code will be
`src/scalper/newh16.py`; result `workers/NEWH16_RESULT.md`; sources in `workers/NEWH16_DIGEST.md`. The owner asked directly on
2026-10-30: "research new kalshi 15 min prediction market strategies". Scope: no L1 variant, no buy-the-favourite-and-hold, no cheap side
late, no short round trip. Every rule below buys a side whose ask is between 35c and 65c (a coin flip, not a favourite) and holds it to
settlement. Nothing is sent to anyone; no order, no key.

Looked at before registering (all counted below): the table layouts; the number of settled markets and the day coverage per series; the YES
share of settled markets per series in `data/fresh.sqlite` (45% to 54%, nothing used); the time span and cadence of `data/pm1.sqlite`
and `data/pm2.sqlite` (Polymarket "Up" price, about every 60 s, Aug 6 to Oct 12). No signal, quote or outcome was joined.

## Ledger check (grep of README.md, workers/CENSUS_2026-10-30.md, studies/)

- **T1 TREND4H** (multi hour trend of the strike, followed and faded, as an entry at the open). Nearest: BTC1 CONT/FADE (the previous window's
  result only, a coin flip), IDEAS20 TREND4 and STREAK3 (these are L1 favourite filters, not entries), PERPFLOW1 FLOW30 (30 minute signed
  perpetual flow), S06, QUIRK1 (no condition). A trend over 16 windows used as a coin flip entry has not been run. New by condition, not a
  reworded test.
- **T2 BIGMOVE** (fade the side of an extreme previous window move, top 5 percent). Nearest: BTC1 FADE (no size condition), S10 (an upset in the
  previous window, on the cheap side, NOT_ENOUGH_DATA), IDEAS20C PRIORMOVE (strike move 0.15 percent or more, L1 filter only), PERPFLOW1.
  The size of the previous move as the only condition on a coin flip entry is not in the ledger.
- **T3 PMGAP** (Polymarket price gap against the Kalshi ask as the only reason to enter). Nearest: PM1 (Oct 13), PM2, PM3 (L1 entries skipped when
  Polymarket disagrees; all FALSIFIED), PM1 Oct 27 (noon ladder, NOT_ENOUGH_DATA). As an entry rule on its own it was never scored; PM1's
  Brier result (Polymarket blend worse than Kalshi alone, z about -3.8) is a strong prior against it.
- **Declined, no try spent:** turn of the candle (digest source 4): expected shift about one point against a 3.6 percent fee, and QUIRK1
  already scored Bitcoin YES at the first candle. Chainlink TWAP against CF index disagreement: needs both venues' settlement values per
  window, a recorder proposal in the result file, not a test. Reversal after taker flow (arXiv 2608.21888): PERPFLOW1 faded 5, 15 and 30
  minute signed flow and failed.

## Common to every rule (fixed now)

- **Markets:** KXBTC15M and KXGOLD15M (T1, T2); KXBTC15M and KXETH15M (T3). Candles and strikes via `scalper.newh2.load`
  (first file wins per close): Bitcoin and Ethereum `l1b`, `book`, `fresh`; gold `l1b`, `book`, `fresh`, `five`. Every settled window with a
  usable quote on the candles named below, chosen by date only. Strike = the market's stored `strike` column.
- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00 (T3: to 2026-09-14 00:00); VALIDATION 2026-09-21 00:00
  to 2026-10-18 00:00 (T3: 2026-09-14 00:00 to 2026-10-13 00:00, where the Polymarket files end); FROZEN HOLDOUT 2026-10-18 00:00 to the
  last settled window on file (2026-10-30 about 14:15 UTC, the latest 12 days), read ONLY if both earlier windows pass. For T3 the
  holdout needs a Polymarket fetch that is made only if discovery and validation both pass.
- **Candle names:** offsets are seconds relative to the close; the candle ending open + 60 s has offset -840, then -780, ..., -600, -540.
- **Fill:** the bought side's CLOSING ask on the candle AFTER the signal candle (YES `ask_c`, NO 1 - `bid_c`), accepted only if it is in
  [0.35, 0.65]; otherwise no trade (counted). A missing signal or fill candle, or a missing outside input, is a data gap (counted).
  Held to settlement, no sale. One trade per window per rule.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order (`scalper.newh2.fee`), headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose fill candle had volume 0 (reported, not the screen).
- **Cut points** are computed once from OUTSIDE-the-outcome quantities on discovery windows only (no result, no quote) and applied unchanged to
  validation and holdout. A threshold that gives fewer trades than the minimum is NOT relaxed: the verdict is NOT_ENOUGH_DATA.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades with net > 0 at fees x1.2; VALIDATION PF >= 1.5 on >= 50 trades with
  net > 0 at fees x1.2; HOLDOUT (only if both pass) PF >= 1.5 on >= 30 trades with net > 0 at fees x1.2. A failed PF with enough trades is
  FALSIFIED; too few trades is NOT_ENOUGH_DATA. Pass of all three plus a pooled day clustered z of at least 5.27 (deflated bar for N about
  728,660) is NOT_YET_FALSIFIED, which earns only a forward registration. Pass of the three PF bars with z below 5.27 is NOT_YET_FALSIFIED
  at the PF bar only and is reported as "not deflated": it still earns nothing but a forward registration.

## T1 TREND4H: the last four hours of the strike predict the next window, as a coin flip entry (4 tries)

- **Signal (known at the open):** m4 = ln(strike_k / strike_(k-16)), where window k-16 is the window closing exactly 14,400 s before window k. If that
  window is missing, data gap. Signal windows: |m4| above the 80th percentile of |m4| over discovery windows of that series. Sign up: the follow
  rule buys YES, the fade rule buys NO; sign down: the reverse.
- **Timing:** signal candle offset -840 (no quote needed to form the signal; the candle must exist), fill candle offset -780.
- **Tries:** (1) Bitcoin follow, (2) Bitcoin fade, (3) gold follow, (4) gold fade.
- **Counterparty:** Kalshi makers who open each fresh window near 50/50 whatever the last four hours did, and the retail takers on the other
  side of a drifting asset. Follow: trend persistence in crypto and gold at hours (time series momentum). Fade: liquidity providers paid for
  absorbing a trend (the 15 minute reversal preprint).
- **Numeric prediction:** hit rate of either direction between 49% and 52% (an edge of 0 to 2 points), mean net per contract between -3c and
  -1.5c, profit factor about 0.5 to 0.7 in every window. All four FALSIFIED (about 90%). Break even needs about 53.5 percent.
- **Kill:** any try below the screen in discovery or validation is FALSIFIED; no cut point is changed.

## T2 BIGMOVE: fade the side of an extreme previous window (2 tries)

- **Signal (known at the open):** m1 = ln(strike_k / strike_(k-1)), where window k-1 closes exactly 900 s before window k (else data gap; this is the
  previous window's realised move). Signal windows: |m1| above the 95th percentile of |m1| over discovery windows of that series. After a
  rise buy NO, after a fall buy YES.
- **Timing, fill:** as T1.
- **Tries:** (1) Bitcoin, (2) gold. The follow direction is reported as information, not screened and not counted as a try.
- **Counterparty:** takers who chased the big move into the next window's open and the makers who then quote it near 50/50; the literature's
  reversal after aggressive flow (arXiv 2608.21888) says the opposite side is paid for absorbing it.
- **Numeric prediction:** hit rate 49% to 52%; PF about 0.6; both FALSIFIED (about 90%). A hit rate above 56% with at least 100 discovery trades
  would be an audit trigger first (a universe or timing leak is the first suspect).
- **Kill:** as T1.

## T3 PMGAP: Polymarket's price is higher than Kalshi's ask for the same side (2 tries)

- **Data:** Kalshi candles as above; Polymarket "Up" price history from `data/pm1.sqlite` and `data/pm2.sqlite` (slug
  `btc-updown-15m-<close - 900>` and `eth-updown-15m-<close - 900>`, 1 minute fidelity, a midpoint or last trade, not a quote we could hit).
- **Signal (decision candle offset -600):** p_pm = the latest Polymarket point at or before close - 600 s and no more than 120 s earlier (else gap).
  g_yes = p_pm - Kalshi YES `ask_c` at offset -600; g_no = (1 - p_pm) - Kalshi NO ask (1 - YES `bid_c`) at offset -600. Buy YES if g_yes >= 0.06,
  NO if g_no >= 0.06 (both cannot hold). Both asks at the decision candle must be inside [0.30, 0.70].
- **Fill:** the bought side's closing ask at offset -540, in [0.35, 0.65], held to settlement; fees as above.
- **Tries:** (1) Bitcoin, (2) Ethereum. The threshold 0.06 is fixed (the Kalshi spread plus a fee round trip is about 3 to 5 points); no other
  threshold is run or reported.
- **Counterparty:** a stale or thin Kalshi quote while the other venue has already moved; the other venue's makers would be the losers if the
  gap were the other way round, and a stale Polymarket quote works against this rule (its history shows quotes parked for minutes).
- **Numeric prediction:** the gap is noise, hit rate near the Kalshi price paid, PF about 0.5 to 0.8; both FALSIFIED (about 85%). PM1's Brier
  difference (Polymarket worse) says the rule buys the wrong side as often as the right one.
- **Windows:** see above; the holdout fetch (Polymarket history for the Kalshi windows closing 2026-10-18 to 2026-10-30) is made only after
  discovery and validation both pass.

## Counts

- **Tries registered:** T1 4, T2 2, T3 2 = 8. **Looks already taken:** the YES share per series (1), the Polymarket file span and
  cadence (1) = 2. Running count before this file: about 728,648. **After registration: about 728,658.** If a holdout is read, no try is added
  (it is part of the same try); information lines (T2 follow, zero volume split, C = 1) add none.
- **Not run:** nothing else. If a rule above is changed after this commit, the change is an amendment with its own commit and its own try.
