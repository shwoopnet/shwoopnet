# NEWH7 registration (Strategy Research V2 worker NEWH7, 2026-10-30, research only)

Written and pushed BEFORE any NEWH7 signal was joined to any Kalshi quote after its signal time or to any outcome. Code will be
`src/scalper/newh7.py`; result `workers/NEWH7_RESULT.md`. Scope (owner, 2026-10-28): no buy-the-favourite-and-hold idea and no L1
filter, exit, size, hour or throttle. Every rule below buys a side priced at 50c or less (a cheap side or a coin flip), or is a round
trip. Markets: Kalshi KXGOLD15M and KXBTC15M only.

Nothing has been looked at except: the candle table layout (as NEWH6), that the outside sources answer (CBOE GVZ daily CSV, Yahoo
GC=F daily chart, Deribit DVOL and BTC-PERPETUAL 1 minute chart data, Coinbase BTC-USD 1 minute candles, Binance spot BTCUSDT 1 minute
zips), and the first rows of each to learn their layout. No signal was computed and no quote or result was read.

## Ledger check (what is new, what was declined without a try)

Read: `workers/RULES.md`, README headings, IV1, LAD1, SEARCH5K, FIX1, VRP2, UNDER1, S12, GOLDFV1, INX1, EVT1, PM1, FAM2 and the
results of NEWH1 to NEWH6, GEN1, GEN4 to GEN7, FALS3, FALS4, MECH1, SLOTEX.

**Declined, no try spent:**
- **DVOL against the Kalshi book's implied move (fair value):** IV1 (15 minute Bitcoin, DVOL as sigma) and LAD1 (hourly ladder) ran
  exactly this; the market's mid beat the DVOL model. Reworded.
- **GVZ against the gold book's implied move at minute resolution:** needs a gold spot path inside each window; the only keyless
  minute gold series (Yahoo GC=F 1 minute) covers the last 30 days only (GOLDFV1), so no discovery window. NOT_RUNNABLE, not spent.
- **The window holding the US equity open (13:30 UTC) or close (20:00 UTC):** Bitcoin's open is S12 (NOT_ENOUGH_DATA), Bitcoin's
  close is the same instant as EVT1's CME_BTC_CLOSE (16:00 ET). For gold it is one window a day, at most about 33 discovery windows
  against the 100 the screen needs: NOT_ENOUGH_DATA by construction, so not spent. Same for the LBMA gold auctions (FIX1 read them as
  an L1 filter; a cheap-side version is one or two windows a day).
- **Kalshi's own metadata:** listing time against open is empty information (the book opens empty, NEWH6); open interest is GEN6,
  GEN7, MECH1; per-window volume as an attention measure has no signed counterparty I can name that is not the longshot buyer, whose
  exploitation means holding the favourite (closed by the owner).

**What is new below:** (1) the gap between implied and realised volatility as a regime for the CHEAP side (SEARCH5K used the DVOL
gap only on L1's favourite entries; nobody used GVZ); (2) the Coinbase over Binance spot premium, a cross-venue spread that maps to
the US venues that make up BRTI (NEWH1's basis was perpetual against index, not venue against venue); (3) a vega round trip after an
options-market volatility bid (a change in DVOL, held 3 minutes, never to settlement).

## Common to every rule (fixed now)

- **Kalshi data:** 1 minute candles exactly as NEWH6 (`scalper.newh6.load`): Bitcoin `l1b`, `book`, `fresh`; gold `l1b`, `book`,
  `fresh`, `five`; first file wins per close. Universe: every settled window in those files, chosen by date only.
- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00; VALIDATION 2026-09-21 00:00 to 2026-10-28 00:00.
  Nothing closing on or after 2026-10-28 00:00 is loaded or fetched. The third window is the FORWARD record (a validation survivor
  goes to `workers/candidates/` with a freeze time after its commit; evaluator `scalper.newh7:forward_eval`; parity check against
  this file's code).
- **Outside data timing:** an outside bar stamped with its START time T is usable only from T + 60 s. A daily close dated D is usable
  only for Kalshi windows closing on a later UTC date.
- **Fill:** the bought side's closing ask on the candle AFTER the signal candle (YES `ask_c`, NO 1 - `bid_c`), inside the stated band
  and strictly inside (0, 1); else no trade (counted). A missing signal or fill candle, or a missing outside input, is a data gap
  (counted), never a no-trade.
- **Held rules (H1, H2):** held to settlement; there is no sale, so no bid is used. **Round trip (H3):** sold at the held side's
  closing bid (YES `bid_c`, NO 1 - `ask_c`) at the stated candle; a zero bid or missing candle moves the sale to the next candle, at
  most to the candle ending 120 s before the close; still none: booked at 0 (whole entry lost), counted as "no sale"
  (`scalper.newh6.round_trip`, unchanged).
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, on every buy and every sell. Headline C = 10; C = 1 reported; fees
  x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades, and without trades whose fill (or sale) candle had volume 0.
- **One trade per window per rule.**
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on >= 50
  trades and net > 0 at fees x1.2. Fewer trades than the minimum: NOT_ENOUGH_DATA. Day-clustered z reported; the deflated bar for N
  about 592,000 is z about 5.2, so a survivor earns only a forward ledger entry.
- **Cut points** (terciles, deciles, percentiles) are computed once from the OUTSIDE series on discovery dates only, never from
  trades or outcomes, and applied unchanged to validation.

## H1 IVGAP: implied volatility far above realised, buy the cheap side and hold (2 tries: gold, Bitcoin)

- **Gold input (daily):** R = (GVZ / 100) / RV20, where GVZ is the CBOE Gold ETF Volatility Index close (`cdn.cboe.com` GVZ_History.csv)
  and RV20 = sqrt(252) x standard deviation of the last 20 daily log returns of Yahoo `GC=F` daily closes; both from the latest
  dates strictly before the window's UTC close date (and RV20 ends on the same date as the GVZ close used, or the latest earlier GC=F
  date). Signal day: R above the 2/3 quantile of the daily R values on discovery dates (UTC dates 2026-08-06 to 2026-09-20).
- **Bitcoin input (per window):** at decision time D = close - 600 s, R = (DVOL / 100) / RV24, DVOL = close of the last Deribit BTC DVOL
  1 minute bar usable at D; RV24 = sqrt(525,600) x standard deviation of the 1 minute log returns of Deribit `BTC-PERPETUAL` closes over
  the 1,440 bars usable at D (at least 1,300 present, else gap). Signal: R above the 2/3 quantile of R over all discovery windows' D.
- **Trade:** at the candle ending 600 s before the close, the side whose closing ask is in [0.10, 0.40] (YES checked first); bought at
  the next candle's (540 s) ask, in [0.05, 0.50]; held to settlement.
- **Counterparty:** Kalshi makers whose quotes scale with recently realised movement while the options market pays for more movement
  ahead; when implied is far above realised, the side that needs a move is quoted too cheap.
- **Honest alternative:** implied volatility carries a risk premium and usually overstates what follows (VRP2's +3.7 points), so a high
  ratio is often just a high premium; the cheap side is overpriced in general (UNDER1, TAIL), and a regime gate rarely flips that.
- **Information (not counted, not screened):** the same trade on the bottom third and on all windows.
- **Prediction:** FALSIFIED on both; discovery PF gold about 0.8, Bitcoin about 0.9 (n several hundred each).

## H2 COINPREM: US spot buying shows first as a Coinbase premium; follow it with the not-yet-favoured side (1 try: Bitcoin)

- **Input:** prem(t) = ln(Coinbase BTC-USD 1 minute close / Binance spot BTCUSDT 1 minute close) for the minute starting t. At D = close
  - 600 s: dprem = prem of the last minute usable at D minus prem of the minute 15 minutes earlier (both must exist, else gap).
- **Signal:** dprem above the 0.90 quantile of dprem over all discovery windows' D: side YES; below the 0.10 quantile: side NO.
- **Trade:** that side's closing ask at the candle ending 600 s before the close in [0.20, 0.50] (the side is not yet the favourite);
  bought at the next candle's ask in [0.15, 0.55]; held to settlement.
- **Counterparty:** Kalshi makers who price BRTI's distance from the strike off the offshore price (Binance, the perpetuals); BRTI is
  built from US venues, and slow US spot demand (ETF creation buying sliced over hours) lifts those venues relative to offshore and keeps
  going for minutes.
- **Honest alternative:** makers quote from Coinbase itself (BRTI's largest constituent), so the premium is already in the price, and
  cross-venue premia are arbitraged back within minutes (the sign could even reverse). USDT/USD drift is in the premium level but cancels
  in a 15 minute change.
- **Prediction:** FALSIFIED; discovery PF about 0.9 (n about 200 to 400).

## H3 VEGALAG: buy the cheap side after an options-market volatility bid, sell 3 minutes later (1 try: Bitcoin)

- **Input:** dvol5(t) = DVOL close of the last 1 minute bar usable at t minus the DVOL close usable at t - 300 s.
- **Signal:** scanning candles ending 780 s to 420 s before the close in order, the first whose end time t has dvol5(t) at or above the
  0.99 quantile of dvol5 over every minute of the discovery dates (computed on the DVOL series alone).
- **Trade:** at that candle, the side whose closing ask is in [0.10, 0.40] (YES first); bought at the next candle's ask in [0.05,
  0.45]; sold at its bid on the candle ending 180 s after the fill candle (latest sale 180 s before the close, zero-bid rule above).
- **Counterparty:** Kalshi makers who set the cheap side from trailing realised movement and update their volatility slowly: an
  out-of-the-money binary gains value when volatility rises, and an options-desk bid for volatility should reach the Kalshi quote
  late.
- **Honest alternative:** DVOL is a 30 day index; a 5 minute jump says little about the next 10 minutes, and it usually follows a spot
  drop that Kalshi already priced. Two fees and the spread on a 10c to 40c contract held 3 minutes cost about 3c to 4c.
- **Prediction:** FALSIFIED; discovery PF about 0.6 (n about 150 to 300).

## Kill criteria (each try)

Discovery PF < 1.5 on >= 100 trades, or net <= 0 at fees x1.2: FALSIFIED (validation printed for the record only). Discovery pass and
validation PF < 1.3 on >= 50 trades, or net <= 0 at x1.2: FALSIFIED. Fewer than 100 discovery or 50 validation trades:
NOT_ENOUGH_DATA. Both passes: NOT_YET_FALSIFIED, a candidate file and a parity check, forward read only. No parameter is changed after
any score; a zero-trade run of a rule is reported as NOT_RUNNABLE or amended once before any trade of that rule is scored, as in
CONF1 and NEWH6.

## Count

N tried: **4** (IVGAP gold, IVGAP Bitcoin, COINPREM, VEGALAG). Information lines are not counted. Running count about 592,082
(after NEWH6) plus other workers' additions, plus 4.
