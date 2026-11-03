# TSLM1 registration: time since the last big one-minute move, cheaper side held to settlement (2026-11-03, written and pushed BEFORE any outcome, win rate or PnL was computed)

Worker TSLM1, Strategy Research V2. Owner direction relayed by the main session: more strategies in the OICORE shape (cheap side held to settlement, low win rate, large payoff per win) with a trigger that is neither Bitcoin open interest nor price alone. Research only: no trading code, no deploy, no recorder, no promote verb. Nothing here means trade.

**Plain statement.** The likeliest outcome is FALSIFIED (prior of a pass about 3%). The nearest tested ideas (MOM_FADE, SURGE_FADE, S09) lost to cost; this one differs in trigger (a relative top 5% one-minute move, then required calm) but trades the same kind of price.

## Ledger check (stop-if-duplicate)
Grepped `README.md` and `workers/*.md` for shock, calm, time since, big move, late shock, jump then, top 5%. Hits and how this differs:
- **MOM_FADE / SURGE_FADE (IDEAS20)**: fade the side that moved 6c in 3 minutes (or 4c on a volume surge) at 7 or 8 minutes left, a fixed absolute size, no calm requirement, other side 0.15 to 0.45. FALSIFIED (-3.28c, PF 0.84). TSLM1 uses a size RELATIVE to the series' own trailing 24 h distribution, requires a quiet last 3 minutes (the market has settled after the shock), and trades the cheaper side whichever way the shock went (not a fade or follow rule).
- **S09 shock reversal** (previous market's move, twice the median of 24): move is across windows, not inside one. **S34 spread shock**, **GEN10 time since a big print** (tape, gold, 10 s bars): different data (spread, trade tape). **XMAC1 / FAM2** shocks are in outside assets. **ABSORB** (volume, favourite). None uses a within-window relative one-minute mid shock followed by calm, or its mirror.
**NOT a duplicate.** I could not find the same trigger. The family is, however, a price-path trigger (price alone in the sense of the owner's brief): it uses only the series' own one-minute quotes, and I treat that as the main reason for a low prior.

## Disclosure: what was read before this commit
Read: `workers/OICORE_SHAPE_INVENTORY.md`, `src/scalper/candlefield.py`, `src/scalper/streaks.py`, `workers/XOI1_REGISTRATION.md` and `XOI1_RESULT.md`, `src/scalper/xoi1.py` (loader, trade, fee and stats reused), `workers/candidates/REF_GEN6_OICORE.json`, the README tail. Data touched: none. I ran only the unit tests on hand-built candles (`tests/test_tslm1.py`). No count of trigger firings, no outcome, and no price of any real window has been read for TSLM1. The predictions below are priors, not read from the data.

## Counterparty and hypotheses
Two opposite stories, and the result decides nothing about which: (H-over) quote providers stay anchored to the pre-shock level after the shock settles and the cheaper side is under-priced (the loser is the maker who has not moved off the old price); predicts a win rate above the entry price (about 25% to 30% at a 22c fill). (H-null) a shock is priced in the same minute (every earlier lag test on these series found Kalshi's quote moves with spot in the same minute, FAM2 and LAG15), so a quiet price after a shock carries no information; predicts a win rate equal to the fill price and PF about 0.9 after fees. The cheaper side is favoured by neither story beyond the usual longshot bias (the cheap side wins slightly less than its price, a loss of about 1c to 3c a contract after fees across the history). A pass would still name no confirmed loser, which keeps it a capped probe.

## Data and alignment
Kalshi 1 minute candles (bid close, ask close, volume) from the local files via `scalper.oicorex1.load_series` (as XOI1). History 2026-08-06 to 2026-11-02 (windows closing). A window's open is its close minus 900 s. A one minute change is the change of the YES mid (bid close + ask close)/2 between the candle ending at e and the one ending at e - 60, both present and two sided (0 <= bid <= ask <= 1); a missing candle is a missing change, never a zero.

## Universe (fixed now, on liquidity and cost only)
KXBTC15M (OICORE's market; the cheaper side, so no hedge with OICORE) and the L1-free series KXHYPE15M, KXNEAR15M, KXZEC15M, KXBNB15M, KXXRP15M (XRP is paused by live L1; included as asked, reported by series). NOT traded: Ethereum, Dogecoin, gold (L1 buys the favourite there). Liquidity rule on quotes and volume known by the look: a two sided quote at the look (0 < bid < ask < 1), at least 10 contracts traded in the 5 one minute candles ending at the look, a quote at the fill candle (exactly XOI1's `alt_trade`).

## The trigger (ONE primary, fixed now; the numbers come from the trailing 24 hours, nothing is tuned)
- For each series, the trailing set = every one-minute absolute mid change of that series with end in (open - 24 h, open] (all earlier markets, nothing from the window itself). Fewer than 500 changes: window not eligible. **big** = |change| >= the 95th percentile of the set (numpy linear quantile) and > 0. **calm** = |change| <= the median of the set and not big.
- **Primary (SHOCK_CALM):** a big change among the nine changes ending 840, 780, ..., 360 s before the close (the first 9 minutes), AND the three changes ending 300, 240 and 180 s before the close are all available and all calm (no further big move, no change above the trailing median in the last 3 minutes up to the look). Plain float arithmetic.
- **Trade:** the cheaper side at the candle ending 180 s before the close: YES if its ask is 0.05 to 0.50, else NO if its ask (1 - yes bid) is 0.05 to 0.50, else no trade. Entry price = that side's ask on the next recorded candle (ending 120 s before the close), C = 10 contracts, taker at the ask, held to settlement (no sell fee). **Fee 7% x C x p x (1-p) rounded up to the cent per order** (`gen6.fee`). One order per series per window; windows of different series are correlated (handled by day-clustering). No look-ahead: nothing after the look candle is read for the decision.
- **At most one alternative (separately counted second try), LATE:** the mirror. No big change in the first 9 minutes (at least 7 of the 9 changes available) AND a big change among the three changes ending 300, 240, 180 s before the close (a late shock, visible in the look candle). Same trade, same universe. PRIMARY and LATE can never fire in the same window.
- No other variant, threshold, look time or band is run under this registration. A window counts as eligible (for the thirds below) if it has a threshold, the three late changes available, and a tradable cheaper side and volume, regardless of trigger or outcome.

## Windows, thirds, frozen holdout
Eligible dates sorted and split into **three equal thirds by number of dates** (W1, W2, W3; the dates are printed by `counts`, which reads no result). **W3 is the frozen holdout, untouched until this file is frozen (it is, by this commit), and is scored only if W1 and W2 both pass.** No second look. `score` refuses to run twice.

## NUMERIC PREDICTION (priors, written before any count or score)
- Trigger rate: PRIMARY about **4% to 8% of eligible windows**; with six series and a median 1.5 to 3 eligible windows in four, about **8 to 20 trades per day pooled**, so 600 to 1,700 trades over the history (about 200 to 600 per third). LATE similar, about 4 to 12 per day.
- Pooled over all PRIMARY trades: **win rate 20% to 27% (central 23%)**, average fill 20c to 28c, **payoff ratio (average win in cents / average loss in cents) 2.8 to 3.8 (central 3.2)**, **profit factor 0.80 to 1.15 pooled (central 0.93)**, in each third 0.6 to 1.4, mean per contract -2.5c to +1.0c. P(PF >= 1.5 in each of W1 and W2) = **3%**. P(pooled day-clustered z reaches 5.27) under 0.5%. LATE: central PF 0.90, P(pass W1 and W2) 2%.
- **OICORE overlap expectation:** an OICORE entry is a Bitcoin window where Bitcoin's 3 minute open interest rise exceeds the threshold (about 6 of the 96 Bitcoin windows a day fire). TSLM1's trigger is price shape only, so I expect it independent of that: about 5% to 10% of TSLM1's Bitcoin entries are also OICORE entries, i.e. about **1% to 2% of all TSLM1 entries** (Bitcoin is one of six series). A clearly higher share would mean the shock-then-calm shape is OICORE seen through its own price shape.

## KILL RULES (fixed now, no tuning)
- **NOT_ENOUGH_DATA**: fewer than 150 trades pooled in the windows scored.
- **FALSIFIED**: PF (C = 10, after fees) under 1.5 in W1 or W2 (or, if read, W3), or PF at fees x1.2 at or under 1.0 in any scored window.
- **NOT_YET_FALSIFIED**: PF at least 1.5 in each of W1, W2 and W3 and x1.2 PF above 1.0. History alone earns no more. **A pooled day-clustered z below the deflated bar 5.27 (N about 728,726) is reported as NOT_YET_FALSIFIED, never a pass.** No named counterparty, so no promotion path exists in any case.
- Headline is PRIMARY pooled over the six series. Bitcoin and the five others (as two groups) and each series are reports of that one try, not tries.

## STREAK REPORT (this registration, at the PREDICTED win rate; recomputed at the observed rate in the result)
`src/scalper/streaks.py`, independence assumed (a floor; losses cluster across series in one window). At a win rate of 22%, 100 trades: longest losing run mean 14.3, median 13, 95th percentile 23, 99th percentile 29; chance of at least one 10-loss run in 100 trades 89%, of a 15-loss run 40%; mean trades until a first run of 10 losses about 50. The same at the central 23% is a little shorter (p95 about 22).

## Worst single loss
A loss costs the fill plus the fee. At the cap of 0.50 (the cap applies to the look-candle ask; the fill candle's ask can be higher and the result will report the largest fill seen): fee 0.07 x C x 0.25 rounded up = 9c at C = 5 and 18c at C = 10, so **5 contracts: 2.50 + 0.09 = 2.59 dollars; 10 contracts: 5.00 + 0.18 = 5.18 dollars.** At the expected fill of about 0.22 the loss is about 1.15 dollars at 5 and 2.30 dollars at 10. A win at 0.22 pays about 3.9 dollars at 5 and 7.7 dollars at 10.

## Tries (N)
Two series groups (Bitcoin; HYPE, NEAR, Zcash, BNB, XRP) x two tries (PRIMARY, LATE) = **+4**: running count about 728,722 -> **728,726**, one-sided z bar **5.27** (0.05 / N). Every result is quoted with window, n, cost and N. Any code change after this commit will be disclosed in the result.

## Overlap with L1 and OICORE
None placed. Ethereum, Dogecoin and gold excluded; XRP flagged. Touches no code in `functions/`, L1 or OICORE. The result reports the share of TSLM1 entries that are OICORE entries (OICORE: Bitcoin cheaper side after a 3 minute open interest jump above 86,299.56, `REF_GEN6_OICORE.json`, via `oicorex1.stage_score`, matched on the Bitcoin ticker).

## Forward read (not built)
Stated in the result from the measured trades per day. Kalshi candles can be fetched after the fact for these series, so a forward read is a re-score of markets closing after 2026-11-02 with the same code; no recorder is needed unless the candle ingest stops.
