# XMET1 registration (Strategy Research V2, written 2026-11-03 BEFORE any Kalshi candle was downloaded and before any outcome, result flag, price or PnL was computed; research only)

Owner direction relayed by the main session: more strategies in the OICORE shape (cheap side or underdog, ask 5c to 50c, held to settlement, low win rate, large payoff per win, trigger from public data published before the quote reprices). Family XMET1 is a CROSS-SERIES test that needs no outside spot feed: the signal is the move of a LEADING Kalshi market (gold 15 minute) read from Kalshi's own 1 minute candles. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
Read `workers/OICORE_SHAPE_INVENTORY.md` section D and grepped README.md for XMET, KXSILVER15M, KXCOPPER15M, KXPLATINUM15M, KXPALLADIUM15M, "gold lead", "partner". Findings: NEWH1/2/6/9/11 included a "silver lead" test on GOLD and Bitcoin (silver leading gold; the opposite direction, FALSIFIED, best discovery PF 0.99); NEWH12 is Bitcoin/Ethereum/Dogecoin lag (FALSIFIED, control equals hypothesis); NEWH15 is Coin Race; XLEAD1 is a Bitcoin flip on coins; OICOREX1 moved the Bitcoin open interest core to silver (PF 0.55/0.80) but that is a different trigger; LAG15 listed silver/copper/platinum/palladium as NOT_RUNNABLE (spot-based) and ran nothing. **No prior run of "gold's Kalshi mid move, trade the same direction in silver, copper, platinum or palladium, cheap side, held". Not a duplicate.** The GEN2 "partner and market-wide move" features (README line 7468, exits before settlement, 229 exits) are the nearest relative and are a different trade (an exit, not a held cheap side).

## What was looked at before this registration (disclosure)
Only counts already printed in LAG15's registration (settled markets: KXSILVER15M 4,476; KXCOPPER15M 4,401; KXPALLADIUM15M and KXPLATINUM15M 2,839 each, to 2026-11-02; gold about 5,900) and the inventory depth table. No candle, bid, ask, result, outcome or price for any of these five series was read for this test.

## Counterparty and mechanism
The metal markets (silver, copper, platinum, palladium 15 minute, settled on a single Pyth print) are quoted by makers and retail from their own flow and are thinner than gold, the most liquid and the L1-traded metal. If gold has moved in the last 3 minutes and the metal market has not yet repriced, the buyer of the cheap side in the gold direction is paid when the metal follows gold after the look (settlement on one print). **Honest prior:** gold and silver are highly correlated intraday, but the same makers probably watch gold, NEWH12/NEWH15/BK1 to BK7 found cross-book leads and lags priced inside one minute, and the control (the other side) often equalled the hypothesis. What could still make it work: platinum, palladium and copper are newer and less watched, a 3 minute gold move is a 3 minute-old public fact, and a cheap side pays 2 to 5 times its stake so only a small shift in the follow-through rate matters. Prior of a pass: 3%.

## Data sources
Kalshi public market listing (settled markets: ticker, close_time, result, volume) and Kalshi 1 minute candles with `yes_bid` and `yes_ask` (historical endpoint field `close`, live `close_dollars`; the shared parser reads both) for KXGOLD15M (the leader, never traded), KXSILVER15M, KXCOPPER15M, KXPLATINUM15M, KXPALLADIUM15M. No outside feed, no key.

## Universe (fixed now)
Traded markets: KXSILVER15M, KXCOPPER15M, KXPLATINUM15M, KXPALLADIUM15M. Liquidity (decided on the listing before any outcome): at least 1,000 settled markets and mean listed volume at least 1,000 contracts (the four pass on LAG15's listing numbers; platinum and palladium start on or after Sep 17 and are reported with their own n). **Never traded: gold, Bitcoin, Ethereum, Dogecoin** (L1/OICORE markets; a cheap-side trade there would hedge L1). Gold is read only as the signal. XRP, probes, and everything else are not in the test. Per-metal quote rule (uses only candles ending at or before the look): latest two-sided candle (0 < bid < ask < 1) ending at or before the look and not older than 120 s, quoted spread at most 0.10, and candle volume summed over the 5 minutes ending at the look at least 10 contracts.

## Exact trigger and trade rule (fixed now, frozen by this file)
Windows are matched by the 15 minute close time T (gold and the metal share it).
1. **Signal window** is the 3 minutes from T-360 s to T-180 s. For gold's market closing at T, `mid(t)` is (yes_bid.close + yes_ask.close) / 2 of the latest two-sided candle ending at or before t and not older than 120 s; both `mid(T-360)` and `mid(T-180)` must exist. `chg(T) = mid(T-180) - mid(T-360)`.
2. **Relative trigger:** `sd(T)` is the population standard deviation of `chg` over the previous 96 gold windows (the 24 hours before T, only windows whose close is before T and at least 48 of the 96 must have a `chg`; a missing one is skipped). `sd(T)` must be at least 0.005. Trigger if `abs(chg(T)) >= 1.0 * sd(T)`. The factor 1.0 is fixed now and not tuned. Direction = sign of `chg` (up or down).
3. **Trade (hypothesis H):** at the look `T-180 s`, for each metal market closing at T that passes the quote rule: gold up -> buy YES at the ask if `ask` is in [0.05, 0.50]; gold down -> buy NO at `1 - bid` if that price is in [0.05, 0.50]. If the gold-direction side is not the cheap side, no trade. One order of C = 10 contracts per metal per window, taker at the ask, held to settlement, no exit. No look-ahead: only candles ending at or before the look.
4. **Control (M, mirror, descriptive, not a try for the verdict):** the cheaper side AGAINST gold's move, same price band, same quote rule, same windows.

## Cost
Fee 7% x C x p x (1-p) rounded up to the cent per order, C = 10 (`lag15.fee`), taker at the ask; stress x1.2. PnL per contract in cents: (win - price - fee) x 100.

## Windows, holdout
Eligible dates = dates with at least one triggered gold window that has a metal market passing the quote rule (decided with no outcome). Sorted dates cut into three equal thirds W1, W2, W3 by number of dates; **W3 is the frozen holdout, read only if W1 and W2 both pass profit factor >= 1.5**. Pooling: the four metals are pooled for the verdict (registered); each metal's n, win rate and PF are also printed separately (descriptive only; no per-metal verdict). Date-clustered z (all metal trades of one day are one cluster, since metals move together).

## Numeric prediction (written before scoring)
Trades pooled 300 to 900 (silver and copper about 100 to 300 each, platinum and palladium about 50 to 150 each). Win rate **0.27 to 0.33 (point 0.30)**. Payoff ratio (average win in cents / average loss in cents) **1.8 to 2.8 (point 2.2)**, which follows from the price band alone (a 0.30 ask pays 70c less fee and risks 30c plus fee). Profit factor **0.7 to 1.1 per window (point 0.9)**, pooled mean per contract **-3c to +1c**. The control M lands within 1c of H. The claim under test is the opposite: PF >= 1.5 in each of three windows.

## Kill rules
- `FALSIFIED`: PF under 1.5 after fees in ANY read window (W3 read only if W1 and W2 pass), or not positive at fees x1.2, or pooled mean under +2.0c, or the pooled date-clustered z below the deflated bar. Also FALSIFIED in spirit if H does not beat the control M by at least 2.0c on the pooled mean (reported; if M is as good as H the signal is not gold's direction).
- `NOT_ENOUGH_DATA`: fewer than 150 pooled H trades (PFs still printed).
- A pooled z below the deflated bar of about 5.27 at N about 728,722 (see Tries) with PF over 1.5 in every window is `NOT_YET_FALSIFIED`, never a pass; it would permit a forward re-read only.
- Windows, trigger factor, band, look, universe and bans are not changed after the result; no variant is run.

## Tries
N + 2 (H and its control M counted; no other variant). Running count about 728,722 (README tail shows HOURLY1 at about 728,720; the brief quoted about 728,702, an older figure). Deflated z bar about 5.27 (unchanged at this scale).

## Streak report (the numbers the result must give)
`src/scalper/streaks.py` at the observed win rate and observed n: longest losing run (empirical, in the chronological sequence of H trades), 95th and 99th percentile of the longest losing run in 100 trades, chance of at least one 10 loss run in 100 trades. For reference, computed now from the predicted win rates (independence assumed, a floor since metal losses cluster by day): win rate 0.30 -> median longest losing run in 100 trades 10, p95 17, p99 21, chance of at least one 10-loss run 58%; win rate 0.25 -> 12 / 20 / 26 / 79%; win rate 0.35 -> 9 / 14 / 18 / 37%.

## Overlap with L1 and OICORE
None by construction. No gold, Bitcoin, Ethereum or Dogecoin trade, entry prices 0.05 to 0.50 (L1 buys 0.88 to 0.97), different markets. Gold is a signal only. No code under `functions/`, L1 or OICORE is touched; no order is placed.

## Forward read (not built)
Candles and results are retrievable after the fact, so no recorder is needed. If the history is NOT_YET_FALSIFIED a forward re-read would need at least 150 fresh H trades after 2026-11-03; at the predicted rate (about 5 to 10 trades a day) that is about 3 to 4 weeks, earliest read **2026-12-01**. If the history is NOT_ENOUGH_DATA the same rate gives the date at which pooled n reaches 150.
