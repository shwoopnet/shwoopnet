# VOLGAP1 registration (Strategy Research V2 worker, 2026-11-03, research only)

Written and pushed BEFORE any Kalshi candle, OKX kline or settled result of this rule was fetched or read. Code `src/scalper/volgap1.py` and
tests `tests/test_volgap1.py` (synthetic data, plain python runner) are committed with this file; result `workers/VOLGAP1_RESULT.md`. Owner's
brief: the mechanism test with an INDEPENDENT price (the vol of the last minutes of spot against the vol the ladder implies). Nothing live is
touched (no `functions/`, no L1, no OICORE). Times are UTC. No promote verb.

## 1. Duplicate check (README citations)

**Not a duplicate. Close relatives, none of which ran this trigger:**
- **LAD1 / LADL (README ~6498, "Model (fixed)"):** hourly Bitcoin ladder fair value with sigma from DVOL (implied, 30 day) or from the last 60 minutes
  of perpetual returns (realised), buying where the model disagrees with the ladder by 3c; FALSIFIED (45/30/15 minutes, implied -1.5c to -2.1c). It
  used the model's disagreement itself as the trigger, with the centre from the perpetual's price, and never compared the ladder's own implied sigma
  with a short realised sigma. No ratio trigger, no tail restriction.
- **HOURLY1 (README ~8189, `workers/HOURLY1_RESULT.md`):** SOL/XRP/DOGE/HYPE hourly, spot-lognormal with trailing 60 minute realised vol, 10 minute
  look, edge 0.08: FALSIFIED on Brier (model 0.1197 vs mid 0.1045). BTC and ETH hourly were excluded there as DERIBIT-IMPLIED. Different assets, a
  level model (no ratio), a 10 minute look.
- **NEWH7 IVGAP (README ~7792):** cheap side of the 15 MINUTE markets when Deribit DVOL / CBOE GVZ sits well ABOVE realised vol: gold 0.85 / 0.81,
  Bitcoin 0.84 / 0.81, FALSIFIED. The opposite sign (implied above realised, not below), the 15 minute product, an outside implied index and the
  cheap SIDE, not a far strike of a ladder.
- **TAIL / NEWH4 H3 and LADLONG1 (README ~8053):** buying the 2c to 6c longshot of the hourly Bitcoin ladder at 30 minutes loses (win 2.9% / 3.3% against
  4.2% paid, PF 0.64 / 0.72). This is the prior: unconditional cheap tails lose. VOLGAP1 asks whether the loss disappears when realised vol is 1.5x
  the ladder's implied vol.
- **DERIBIT-IMPLIED (README ~8122):** forward-only recorder, Deribit mark_iv vs the ladder at the 45 minute look; no realised-vol ratio.
- **NEWH14 I2 / L13 (README ~692, listed OPEN as a likely duplicate of H7):** "makers' volatility estimates lag after a jump in realised vol", never run
  as such on the ladder's wings; its text says "calibration error doubles in the top volatility decile" using the 15 minute market, not a ladder fit.

**What is different here (and why a pass is still unlikely):** the trigger is a RELATIVE ratio of realised to the ladder's OWN implied sigma (fitted
from all strikes at the look), the centre of the model is the ladder's own fitted median (so no spot level, basis or index difference enters), spot is
used only for the volatility estimate, the trade is restricted to cheap far strikes (ask 0.03 to 0.30) where a vol error matters most, and it is run on
Bitcoin, Ethereum AND gold hourly. **Honest prior:** HOURLY1 died on Brier; the quote usually knows the vol (the same quoters read the same tape); a
15 minute realised-vol estimate from 15 returns has a relative standard error near 18% (more with fat tails) so many "ratio >= 1.5" hours are noise;
and the ladder fits a smile with ONE sigma, so tails may already be quoted above the fitted lognormal. Prior of a survivor 3%.

## 2. Universe (fixed now; no outcome has been read)

- **Series (public series list, checked 2026-11-03):** KXBTCD "Bitcoin price Above/below hourly", KXETHD "Ethereum price Above/below hourly",
  KXGOLDH "Gold Hourly". Settled hourly events on the list: KXETHD and KXBTCD thousands; KXGOLDH 1,827 events since 2026-07-07. Only markets with
  `strike_type = greater`, result yes/no, closing 2026-08-27 00:00 UTC through 2026-11-02 23:59 UTC (68 dates; the HOURLY1 sample window). The
  800-close rule: a series with fewer than 800 closes that have a fit is reported NOT_RUNNABLE. Gold closes are counted at the run; if under 800 gold is
  NOT_ENOUGH_DATA by that rule, not tested.
- **Spot for the realised vol only:** OKX 1 minute klines (`BTC-USDT`, `ETH-USDT`, and `XAU-USDT-SWAP` for gold; `history-candles`, keyless,
  reachable from the sandbox, depth checked back to 2026-01; Binance is blocked, Yahoo `GC=F` 1 minute holds only 7 days). **Gold caveat (disclosed
  now):** the swap is a USDT perpetual, trades while COMEX is shut, and Kalshi's gold hourly settles on a gold candle ("1-minute candlestick close for
  gold at 7:00 AM EST" in the rules text), a different source; only its 1 minute RETURNS enter, never its level.
- **Strikes fetched (spot only, chosen before any quote):** those within |ln(K / spot at the look)| of 1.5% (BTC), 2% (ETH), 1.0% (gold), spot = the
  OKX close at the look. Kalshi candles are fetched for [look - 300 s, look + 60 s] only (1 minute, bid and ask close). Nothing after the fill minute.

## 3. Quantities (all fixed)

- **Look:** the candle ending 25 minutes (1,500 s) before the close. One value.
- **Quote at the look:** the latest candle ending at or before the look and at most 120 s old, two sided (0 < bid < ask < 1), ask - bid <= **0.05**
  (the registered maximum spread, used for fit strikes, trade strikes and the fill candle).
- **Implied vol (the fit):** for strikes with a quote and YES mid in [0.03, 0.97], z_i = Phi^-1(1 - mid_i) is regressed (ordinary least squares, equal
  weights) on ln K_i. One lognormal: P(S_T > K) = 1 - Phi((ln K - m) / s). Slope b = 1/s, intercept a = -m/b. Required: at least **6** fit strikes,
  b > 0 and R^2 >= **0.90**, else the hour is "no fit" (counted, dropped). s is the total standard deviation of ln S_T over the horizon.
- **Realised vol:** root mean square (drift ignored) of the **15** one minute log returns of the OKX closes from 15 minutes before the look up to the look
  (16 closes; the kline opening one minute before the look ends AT the look), per minute: sr. ONE window (15 minutes). A second window (10 or 30
  minutes) would be a separately counted try and is not run. Missing kline, or sr = 0: "no vol" (counted, dropped).
- **Horizon:** the final settlement averages the last 60 s, so the variance horizon at the look is 24 + 1/3 = **24.333 minutes** (TAU). Realised total
  s_r = sr x sqrt(TAU). **Ratio = s_r / s.**
- **Model with realised vol:** the same median m (from the ladder fit) with s_r: p(K) = 1 - Phi((ln K - m) / s_r).
- **Trigger (relative, fixed now): ratio >= 1.5.** Control hours: ratio <= 0.67.
- **Trade (treated):** among strikes quoted at the look, the YES tail (YES ask in [0.03, 0.30]) and the NO tail (price = 1 - YES bid in [0.03, 0.30]),
  edge = model probability of that side - price - exact fee 0.07 x p x (1 - p). Take the side/strike with the largest edge if edge >= **0.08**; ONE
  trade per hour per asset. Fill at the NEXT candle (ending 24 minutes before the close): the YES ask (NO: 1 - YES bid), two sided and tight. **Hard
  limit:** no trade if the fill price is above **0.30**, or more than 0.03 above the price at the look, or there is no tight fill candle (counted
  "no fill", no replacement trade). Held to settlement. Cost: fee 7% x C x p x (1 - p), rounded up to the cent per order, **C = 10** headline, fees x1.2
  reported. Volume is not filtered; filling 10 contracts at a far-strike ask is MODELLED, not observed (candles carry no sizes).
- **Comparator and control rule (no model; same fill rules):** the tail (either side, price 0.03 to 0.30) whose price is nearest 0.10 (ties: lower),
  one per hour. **TREATED-ALT** = this rule in hours with ratio >= 1.5; **CONTROL** = this rule in hours with ratio <= 0.67. The model-edge rule in the
  control hours is also printed (it will rarely fire; information).
- **Calibration (information):** all cheap tails (every strike and side with price 0.03 to 0.30 at the look) in three ratio buckets: n, mean price paid,
  win rate, mean model probability, windows W1 and W2 only.

## 4. Counterparty

Retail buyers of the ladder, who take far strikes off a stale implied vol (the quote), and the makers who sell the tail: **the tail seller loses when
vol expands intra-hour** (the 25 minute estimate says it already did). The edge source would be that makers quote the wings off a slower volatility
than the last 15 minutes show. Why it should fail: the same firms quote the ladder and read the same tape, and the quote moves with the spot within
seconds (RECORD1-style lag is the thing the 15 minute tests already looked for and did not find at this size).

## 5. Numeric prediction (fixed now)

- **Fits:** 85% to 97% of hours have a fit (BTC, ETH); gold 60% to 90% (stale ladder in closed hours drops fits).
- **Trigger rate (ratio >= 1.5 among fit hours):** 7% (range 3% to 15%) for BTC and ETH, 9% (range 3% to 20%) for gold. Control rate (ratio <= 0.67): 12% (6% to 25%).
- **Trades (outcome-free count, all windows):** about half the trigger hours reach an 8c edge and a fill: BTC about 60, ETH about 60, gold about 70; **BTC + ETH
  pooled about 120 (range 60 to 250), so NOT_ENOUGH_DATA (under 150) is the most likely result, about 60% likely.**
- **If trades are scored:** win rate **11%** (range 6% to 18%) against an average price paid near 0.12; payoff ratio (mean win / mean loss) about **6.5**
  (range 4 to 9); **PF 0.85 (range 0.55 to 1.25)**. P(PF >= 1.5 in W1 and in W2) = 2%.
- **Control (TREATED-ALT, CONTROL nearest 0.10):** PF **0.75** for the control (cheap tails lose, as TAIL's 0.64 / 0.72); treated-alt PF 0.85 to 0.95.
  The vol ratio does not matter much: treated-alt minus control PF about +0.1 (range -0.2 to +0.5).
- **Brier / calibration:** the model with realised vol is worse than the ladder mid at ratio >= 1.5 (the mid wins 70%). Cheap-tail win rate below the mean price paid in all three buckets.

## 6. Kill rules (fixed)

1. **NOT_ENOUGH_DATA** if the trades of the TREATED rule number fewer than **150** pooled over the group (counted over all three windows: whether a
   trade exists never depends on its outcome, so counting W3 does not read it). Checked first; the W1/W2 lines are still printed for information. Groups:
   CRYPTO = BTC + ETH pooled (primary), GOLD alone. A series with fewer than 800 closes with a fit is NOT_RUNNABLE.
2. **FALSIFIED** if any of: profit factor < **1.5** in W1 or W2 (equal thirds of the dates, by `lag15.thirds`) at C = 10 after fee; W1 or W2 mean not
   positive at fees x1.2; **the control behaves like the treated group**: CONTROL PF >= 1.0 (cheap tails do not lose in calm hours) OR TREATED-ALT
   PF minus CONTROL PF < 0.25 (the ratio makes no difference); or, if W3 is read, W3 PF < 1.5 or W3 not positive at fees x1.2.
3. **NOT_YET_FALSIFIED** only if none of the above and the pooled z (day-clustered) is below the deflated bar of **5.27** (N about 728,740): "not a
   finding", never "proven". If z is at or above 5.27, NOT_YET_FALSIFIED with the forward window as the next step.
4. **Frozen holdout:** W3 (the last third of the dates, about 2026-10-12 to 2026-11-02) is read only if W1, W2 and the control all pass; it is never read
   a second time, and no parameter above is changed after the first read. One run; the program refuses a second.
5. Overlap: the tail trade is on the hourly ladder (different ticker from L1 and OICORE, which trade 15 minute markets); a tail position can coexist with
   a live L1 or OICORE position at the same close. Paper only; nothing to build on a pass without a new owner decision.

## 7. Tries, risk, streaks

- **N tried:** +2 per asset (Try A = the treated model-edge rule; Try B = the comparator / control rule), 3 assets = **+6**. Running count 728,734
  (after EVENT1) + 6 = **728,740**, z bar about 5.27. Windows (a 10 or 30 minute realised window), other looks, other ratio cut-offs: none run, each
  would be a separately counted try. TREATED-ALT, the model rule in control hours and the calibration are printed as information, not tries (they are the
  control's definition).
- **Worst single loss** (price at the 0.30 hard cap, fee rounded up): **$3.15 at 10 contracts, $1.58 at 5**; at the typical 0.10 price $1.07 at 10,
  $0.54 at 5. One trade per hour per asset, so up to three at once at a close (worst $9.45 at 10 contracts).
- **Streaks (`src/scalper/streaks.py`, independence assumed):** at win rate 11%: longest losing run in 100 trades mean 25, median 23, p95 42, p99 54;
  in 250 trades mean 33, median 31, p95 52, p99 65; 96.6% chance of a 20-loss run in 250 trades, one 20-loss run expected every 84 trades. At 20%
  (if the model were right): 250 trades mean 20, p95 30.

## 8. Read dates

The scored read is the historical run, once, **2026-11-03** (today); W3 only on the conditions above. There is no forward recorder for 25 minute
hourly looks (the ladder recorder covers the last 150 seconds). A forward window, 60 days from the first new close after 2026-11-03, is the next step
only on NOT_YET_FALSIFIED with z >= 5.27 (earliest read 2027-01-03). Otherwise none.

## 9. Disclosure of what was looked at before writing

Series titles and the settled-event counts on the public list; the head of one KXGOLDH event (strike spacing $2, rules text); counts of markets per event
(BTC 188, ETH 300+, gold 100+); two OKX rows to confirm field order and that `XAU-USDT-SWAP` history reaches back to 2026-01; the ledger texts cited above
and the lag15 / hourly1 code. No candle was fetched for this rule, no ratio, fit or outcome was computed, and the synthetic tests do not touch real data.
