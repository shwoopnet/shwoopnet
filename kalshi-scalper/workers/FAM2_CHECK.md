# FAM2 novelty check (Strategy Research V2, worker FAM2, 2026-10-29)

Line numbers are `kalshi-scalper/README.md` at commit 658a4e9 unless another file is named.

## Family A: volatility regime on the hourly Bitcoin and Ethereum ladders from Deribit DVOL

**Verdict: tested as LAD1 (with IV1 and SEARCH5K). Not run; no try spent.**

- LAD1 (pre-registration 6494, result 6550 to 6563) priced every near-money `KXBTCD` strike with sigma = DVOL and bought a side when the DVOL price beat the quote by more than 3c plus the fee, at 45, 30 and 15 minutes. For one strike, "the DVOL probability is above the YES ask" is the same statement as "the strike's own implied volatility is on the wrong side of DVOL": the condition is monotone in the gap between DVOL and the volatility backed out from that strike's price. So the proposed signal, DVOL minus the ladder's implied volatility, deciding which side of the ladder is overpriced, is LAD1's entry condition. Averaging the gap over near-money strikes into one "regime" number keeps the same sign on those strikes and only narrows the strike set; it is a filter on LAD1's own trades, not a different bet. All three implied-sigma tries lost (-2.07c, -2.02c, -1.65c, win rates under the price paid, 6550 to 6560).
- The regime version on the 15 minute contracts is also run: SEARCH5K's features included DVOL level, its 60 minute change and **DVOL minus realised volatility** (6292 to 6296), and "implied volatility ... produced no rule that survived" (6308 to 6316). IV1 (6250 to 6284): DVOL as fair value, market mid had the best Brier score, DVOL the worst. N7 "implied volatility regime gate" (1202) is the idea list entry that IV1 and SEARCH5K later covered.
- The one untested piece is LAD1 re-read on the look-ahead-free `lad2.sqlite` (CORR1, 7487 to 7489, notes LAD1's 45 minute universe had the look-ahead). That is a correction of LAD1, not a new family; it fails on LAD1's sign anyway (win rate below price in all six cells).
- Data check (information): Deribit `get_volatility_index_data` answers keyless at resolution 60 (checked 2026-10-29, BTC, last 24 hours, OHLC rows returned).

## Family B: cross-asset lead-lag at the minute level, E-mini S&P future, 10 year yield, dollar index onto the 15 minute Kalshi quotes

**Verdict: new. Registered in `workers/FAM2_REGISTRATION.md`.**

- GOLDFV1 (7495 to 7531) used the COMEX gold FUTURE, gold's own underlying, and found "Kalshi gold already prices the latest minute of COMEX" (7530). A non-gold asset leading gold is not in it.
- GEN2 (7372 to 7392) and the further-family check (7468) cover lead-lag between Kalshi series (a family partner and the market-wide Kalshi move), Kalshi-only inputs. CONF1 TAPE (7431) is also Kalshi-only.
- SEARCH5K's cross-asset feature is the other coin's move (Ethereum for Bitcoin and back, 6292 to 6296); LAG2 and LAG2B (5964 to 6020) test Kalshi against the same coin's spot. XM1 (3069, 3598) is the hourly ladder against the 15 minute market, both Kalshi.
- No equity future, Treasury yield or dollar index minute series appears anywhere in the ledger as an input to a 15 minute Kalshi decision (search of README.md, `studies/SCOREBOARD_2026-10-28.md` and `studies/NOVIEW_MECHANISMS_2026-10-28.md` for ES=F, E-mini, TNX, DX-Y, dollar index, yield, lead-lag: only daily ETF studies such as SLOW1 4195 and IDX1 3714, which are not Kalshi and not minute level). The scoreboard's "Underlying markets" row (SCOREBOARD line 19) is the same coin's perpetual and spot, not another asset.
