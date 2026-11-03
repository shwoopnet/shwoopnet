# PUB20 registration: 20 published rules, 10 tested (Strategy Research V2, worker PUB20, research only)

Written 2026-11-03 BEFORE any win, loss, profit factor or result of any PUB20 trade was computed. Only metadata was read to choose
the universe (window counts, date ranges, median quote spread at 180 s before the close, share of quotes with volume; the `result`
column was not read). Code: `src/scalper/pub20.py`, tests
`tests/test_pub20.py`. Nothing here means trade, touches live code, `functions/`, L1 or OICORE, or has a promote verb.
Commit order: this file and the README ledger entry first (pushed), then the code, then one run.

**Plain statement.** The likeliest outcome is that all ten are FALSIFIED or NOT_ENOUGH_DATA. About 728,700 variants have been tried;
published effects mostly come from equity and sportsbook markets with other counterparties, and the Kalshi fee (7% x C x p x (1-p),
rounded up, C = 10) is 1.75c a contract at 50c and 0.4c at 5c. A rule is only interesting if it has a named counterparty who loses.

## Exclusions and universe
- EXCLUDED from every universe: the 15 minute crypto series (Bitcoin, Ethereum, XRP, Dogecoin, Solana, HYPE, NEAR, Zcash, BNB) and gold
  (L1, OICORE and banned areas), and the hourly crypto ladders (KXBTCD, KXETHD, KXGOLDH).
- **Universe A (15 minute, chosen on metadata only: at least 2,500 settled windows on file and median quote spread at 180 s of 0.02 or
  less):** KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXSILVER15M, KXCOPPER15M, KXWTI15M, KXNATGAS15M, KXPLATINUM15M, KXPALLADIUM15M.
  Left out as too thin on file: KXAUDUSD15M and KXUSDCAD15M (1,008 windows each, p90 spread 0.13 and 0.16), KXBRENT15M (71), the four Treasury
  rate series (158 each). Coverage on file: silver and WTI from 2026-08-06, copper and gas from 08-27, platinum and palladium from 09-17,
  the three FX pairs from 09-23. Median spread: 0.01 (silver, copper, WTI, gas), 0.02 (FX, platinum, palladium).
- **Universe B (hourly index ladders, "above K"):** KXINXU (S&P 500) and KXNASDAQ100U (Nasdaq 100), `data/inx1.sqlite` and
  `data/ladders.sqlite`, 2026-08-24 to the end of the file. Chosen as the only held index series.
- Windows by close time (UTC), the same cuts as EVENT1: **W1 2026-08-06 to 09-04, W2 09-05 to 10-04, W3 (frozen holdout) 10-05 to the end of the
  data.** W3 is NOT read unless a rule passes W1 and W2 (below). All thirds are reported by date.

## Common trade and fee
- Cheap-side rules: the cheaper side (YES first on a tie) whose ask is 0.05 to 0.50 at the candle ending 180 s before the close, quote
  spread at most 0.10, fill at that side's ask on the candle ending 120 s before the close with a HARD LIMIT of 0.50, held to settlement
  (`event1.window_trade`, not re-implemented). Directional rules (P04, P05, P08) state their own band below; all hold to settlement.
- C = 10 contracts, fee 7% x C x p x (1-p) rounded up per order (`gen6.fee`), taker at the ask, no sell fee. Also reported at fee x1.2.
- PF = gross wins over gross losses in net cents per contract. z = day-clustered mean (`calibration.cluster_mean_z`). Deflated bar:
  N +2 per rule tried (10 rules = +20), **N about 728,755, z bar about 5.27** (the bar is reported; clearing PF 1.5 in three windows is the
  pass criterion, the z bar is the "would you believe it" check).
- **Excess** (calendar and event rules P03, P06, P07, P09, P10): mean net cents of the rule's trades minus the mean net of the control
  trades in the same series (control defined per rule below, at least 10 control trades or the trade is dropped from the difference).
  For P01, P02, P04, P05, P08 excess = mean net cents (the price is the control: a fair price nets minus the fee).

## Kill rule (fixed now)
1. Pooled W1 + W2 trades under 150: **NOT_ENOUGH_DATA** (nothing else is claimed; counts and windows are still reported).
2. Else FALSIFIED if PF is below 1.5 in W1 or in W2, or excess is negative in W1 or in W2.
3. Else W3 is read once: PF below 1.5 or negative excess in W3 = FALSIFIED; otherwise NOT_YET_FALSIFIED (never "validated").
4. Reported for every rule whatever the verdict: n, window, win rate, implied win (mean fill), payoff, PF (fee x1, x1.2), mean net cents, z.
5. Run once; the runner refuses a second run (`data/pub20_score.json`). No parameter, universe or rule is changed after the first outcome.
6. Anything with a stated mechanism and positive mean net after the fee in BOTH W1 and W2 is flagged in the result with a capped-probe spec
   (1 contract, hard limit, kill rule, named worst-day loss, date by which 40 fills would exist) even if it fails the PF bar. That flag
   is information for the owner and a brief, never a recommendation to trade.

## The 20 rules (one line each: rule | mechanism | counterparty | data | held-data only? | status)

Status key: TRIED = already run, one line verdict, not re-scored here (sources: README.md and workers/OICORE_SHAPE_INVENTORY.md);
TEST = registered below and run once; NEEDS = needs data we do not hold.

### Already tried (10), not re-scored
1. **Favourite-longshot bias** (Snowberg and Wolfers 2010): sell longshots / buy favourites at 24 h to 168 h. | Retail overpays for lottery payoffs. | Retail bettors. | ladder candles. | held | **TRIED: FLB1 (24 h, 168 h), CAL1, scout FLB cells: FALSIFIED; "favourites in the rest of Kalshi do not beat their price" (README ~3539).**
2. **Late-resolution drift / settlement convergence** (buy the 88c to 97c favourite shortly before the close). | Takers who sell early at a discount. | Impatient sellers. | 15 min candles. | held | **TRIED: it is L1, live; owner stopped further work 2026-10-28.**
3. **Sports heavy favourite** (Levitt 2004; Forrest and Simmons 2008). | Bettors back underdogs. | Retail. | sports candles. | held | **TRIED: SP1, -4.2c, FALSIFIED (2026-10-13); F6 tennis favourites FALSIFIED.**
4. **Overs bias, buy the Under in game totals** (Paul and Weinbach 2005; Gandar et al.). | Public bets overs. | Retail overs. | totals ladders. | held | **TRIED: F7 (2026-10-27), FALSIFIED.**
5. **Post-news overreaction fade** (Chan 2003; De Bondt and Thaler 1985). | Momentum chasers. | Chasers. | 1 min candles. | held | **TRIED: SCALP2 PF 0.57, LADFADE, GEN8/GEN9, BOUNCE1: FALSIFIED (gold, Bitcoin, Ethereum only; FX and metals not run, but a fade of a window's own first-minute move is the same rule; not re-scored).**
6. **Volume-surge reversion / high-volume return premium** (Gervais, Kaniel and Mingelgrin 2001). | Liquidity demanders. | Impatient takers. | volume candles. | held | **TRIED: IDEAS20 volume-surge cells within noise of zero (README ~5923, ~6000); "following and fading, breakouts and volume spikes all do the same".**
7. **Round-number clustering** (Harris 1991 price clustering; Osler 2003 stops at round figures). | Orders cluster at round levels. | Stop and take-profit placers. | strikes. | held | **TRIED: NEWH1 round-number barriers ($500, $1,000) FALSIFIED; strikes are full-cent settlement values.**
8. **Market-maker inventory skew** (Avellaneda and Stoikov 2008; Ho and Stoll 1981). | Makers skew quotes against inventory. | Makers. | order books. | needs books | **TRIED: MAKER4 PF 0.00 FALSIFIED, MM1 NOT_ENOUGH_DATA, BOOKCH1 forward only.**
9. **Wide-spread / stale-quote fade** (Easley and O'Hara 1992 informed-trade spreads). | Quote providers who stopped updating. | Slow makers. | quotes. | held | **TRIED: SS2, QSTALE1 FALSIFIED (2026-11-03).**
10. **Overnight gap / weekend gap** (Lou, Polk and Skouras 2019 tug of war). | Day traders and makers who must be flat. | Intraday flow. | opening quotes. | held | **TRIED: NEWH11 (CME weekend gap, gold opening vs COMEX) FALSIFIED; equity overnight drift "gone after costs" (README, SPY).**

### Registered and tested now (10), all on held data only
Duplicate check for each ran `grep -n -i` on README.md and workers/OICORE_SHAPE_INVENTORY.md for the rule's name and mechanism
(NR7, narrow range, compression, volatility clustering, Friday, fix, month-end, settlement, reopen, cross-sectional reversal,
smile, interpolat, Nasdaq lead); zero hits for the rule as stated on these universes. Neighbours and how they differ are named.

**P01 NR7 (volatility compression breakout; Crabel 1990, "Day Trading with Short Term Price Patterns").** Trigger: the previous
window's absolute log move (from consecutive strikes: strike of window t over strike of window t-1, strike is the spot at the
window's open) is strictly smaller than each of the 6 moves before it (7 contiguous windows needed, any gap = not eligible). Trade:
cheap side (common trade). Mechanism: ranges expand after compression; makers pricing from trailing realised volatility quote the
tails too cheaply. Counterparty: makers who sell cheap-side tails off a trailing volatility. Differs from TSLM1 (shock then calm
INSIDE one window, Bitcoin and alts) and REGIME1 (L1 stand-down). Prediction: win rate 11% to 15%, PF 0.80 to 0.95, FALSIFIED.

**P02 VOLEXP (volatility clustering; Engle 1982 ARCH).** Trigger: mean of the previous 4 windows' absolute moves is at least 1.5
times the median absolute move of that series in the trailing 24 hours (at least 48 observations). Trade: cheap side. Mechanism:
volatility persists but the quotes lag it. Counterparty: slow vol updaters. Differs from PRIORMOVE (a skip filter on L1 entries).
Prediction: PF 0.80 to 0.95, FALSIFIED.

**P03 DOWFRI (Friday afternoon liquidity withdrawal / pre-weekend de-risking; Cross 1973, French 1980 weekend effect lineage).**
Trigger: window closes on a Friday between 12:00 and 17:00 US Eastern (exclusive of 12:00, inclusive of 17:00). Trade: cheap side. Control: the
same series' windows in the same Eastern 15 minute slot on Tuesday to Thursday. Mechanism: makers cut size before the weekend, so tails
are priced wider than they run. Counterparty: makers. Prediction: excess between -1.0c and +0.5c, PF 0.85, FALSIFIED.

**P04 XSREV (cross-sectional short-term reversal; Jegadeesh 1990, Lehmann 1990, Campbell, Grossman and Wang 1993 volume-driven
price pressure).** Trigger: in a close time with at least 5 universe-A series having a valid previous move, z = previous window's log
move / standard deviation of that series' window moves over the trailing 24 hours (at least 48 observations); the series with the most
negative z (z at most -1.5) is bought YES, the series with the most positive z (at least +1.5) is bought NO. Trade: ask 0.20 to 0.80 at the
fill candle and spread at most 0.10 at the look, 180 s look, 120 s fill, held. Counterparty: liquidity demanders who pushed a price away.
Prediction: win rate near the price paid, mean net -1.5c to -2.0c (fee dominated), FALSIFIED. Differs from XMET1/XCRY1 (a trigger in
one asset, a cheap side in another) and S06/BTC1 (Bitcoin window persistence).

**P05 NDXLEAD (cross-index lead-lag; Hasbrouck 1995 price discovery).** Trigger: for one close of the hourly ladders, at 60 minutes
and 30 minutes before the close, pick each index's strike whose YES mid is closest to 0.50 at the 30 minute look (two-sided spread at most 0.10,
volume above zero); move = probit(mid at 30) minus probit(mid at 60) on that strike (a spot move in standard deviations). If one
index's move is at least 0.50 in absolute value and the other's move, signed in the same direction, is at most 0.15, buy the lagging index's
ATM strike in the direction of the leader (YES if up, NO if down) at ask 0.20 to 0.80 on the next candle, held to the close. Counterparty: slower
quoters on the less traded ladder. Prediction: n under 150 (about 60 to 120 triggers in 60 days), NOT_ENOUGH_DATA; if n is enough, PF 0.9.
Differs from INX1 (index plus VIX fair value, FALSIFIED) and NEWH13 (gold and Bitcoin).

**P06 FIXES (benchmark fix windows; Evans 2018 and Melvin and Prins 2015 on the WM/Reuters 4 pm London fix, LBMA Silver Price).**
Trigger: windows closing at 16:00 London time (the WM/R 4 pm fix) or at 10:00 US Eastern (the New York option cut) on weekdays for EURUSD,
GBPUSD, USDJPY, and at 12:00 London time (the LBMA silver price) for silver; times converted with the zone rules (UK and US changes
included). Trade: cheap side. Control: the same series' windows 2 hours earlier and 2 hours later on the same day. Mechanism: benchmark
order flow is price insensitive and gets reversed afterwards. Counterparty: dealers filling fix orders / benchmark-order placers.
Prediction: n under 150 (about 80 to 140), NOT_ENOUGH_DATA; else excess within +-1c. Differs from EVENT1 (London open, not the fix).

**P07 MONTHEND (month-end hedging and rebalancing flows; Melvin and Prins 2015, Etula, Rinne, Suominen and Vaittinen 2020).** Trigger:
windows whose US Eastern date is one of the last two US business days of a calendar month (2026-08-28 and 08-31, 09-29 and 09-30, 10-29 and 10-30).
Trade: cheap side. Control: the same series' windows in the same Eastern 15 minute slot on the other weekdays. Mechanism: end-of-month
dollar-demand flows that the quoters do not price. Counterparty: makers facing price-insensitive hedgers. Prediction: PF 0.85, FALSIFIED;
only 6 independent days, so z is reported but no claim rests on it.

**P08 SMILE (strike-ladder interpolation residual; Breeden and Litzenberger 1978, Carr and Madan).** For one index close at 30
minutes before the close, take all strikes with a two-sided spread at most 0.06 and a YES mid from 0.05 to 0.95 (at least 7 strikes); fit
probit(mid) on strike with a quadratic by least squares WITHOUT the strike being priced (leave one out). Buy YES if the YES ask is at least
0.04 below the fitted probability, buy NO if the NO ask (1 - bid) is at least 0.04 below the fitted NO probability; require the same inequality at
least 0.02 on the next candle's ask (fill); ask 0.10 to 0.90; held. Counterparty: the quoter of one thinly traded strike. Prediction: win rate
vs price excess between -2c and +1c, PF 0.9, FALSIFIED. Differs from ARB1 to ARB5 / RULES1 (exact monotonicity and bracket locks),
LAD1 and NEWH14 (hourly Bitcoin ladder against a vol model) and INX1 (a vol model, not neighbours).

**P09 SETTLE (futures settlement windows; Hillion and Suominen 2004 "marking the close", Kuserk and Locke 1993).** Trigger: windows
closing at 13:30 US Eastern for silver, at 13:00 for copper, at 14:30 for WTI and for natural gas (CME settlement periods as I recall
them: COMEX silver 13:25 to 13:30, copper 13:00, NYMEX crude and gas 14:28 to 14:30 Eastern; not re-checked against the CME site). Trade: cheap side.
Control: the same series' windows 2 hours earlier and later the same day. Mechanism: settlement-period trading is price insensitive and
partly reverses. Counterparty: benchmark-order placers. Prediction: n under 150, NOT_ENOUGH_DATA. Differs from EVENT1 (NYSE close, EIA).

**P10 REOPEN (first hour after a trading halt; Madhavan, Richardson and Roomans 1997 on opening uncertainty).** Trigger: a window whose
open is within 60 minutes after a gap of at least 90 minutes in that series' windows on file (the weekend reopen; a daily 60 minute
maintenance break is shorter than 90 minutes and is NOT a trigger). Trade: cheap side. Control: windows of the same series, same US Central
15 minute slot, Monday to Thursday that are not within 60 minutes of such a gap. Mechanism: price discovery after a halt is noisy and
quoters are wide. Counterparty: makers quoting stale. Prediction: about 40 to 150 trades, NOT_ENOUGH_DATA; else excess within +-1c.
Differs from NEWH11 (gold and Bitcoin weekend gap vs an external price) and the "Gold, forex ... not checked Friday 17:00 to Sunday 18:00" site note.

## Registered parameters are final
Cheap-side band 0.05 to 0.50, hard fill limit 0.50, directional band 0.20 to 0.80 (P04, P05) or 0.10 to 0.90 (P08), look 180 s, fill
120 s, spread at most 0.10 at the look (0.06 for P08 ladder strikes), thresholds exactly as written above. Any zero-volume rule: none.
If a rule fires on fewer than 150 W1 + W2 trades the verdict is NOT_ENOUGH_DATA and nothing is widened to rescue it.

## Counts and N
10 rules tried, 2 counted each: N rises from about 728,735 to about 728,755; z bar about 5.27.

## Not tested, and why (the ten TRIED above are in the table; no rule needed other data except as noted)
- Inventory skew (rule 8) needs order books (R6 recorder is forward only).
- Turn-of-year, day-of-week and turn-of-month effects on the S&P itself (Ariel 1987, French 1980) cannot be tested as a Kalshi price
  question with 47 index days; P07 and P03 are the part testable on 15 minute markets.
