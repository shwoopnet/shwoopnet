# IDXFUT1 registration: S&P 500 and Nasdaq 100 4 pm ladders (KXINXU, KXNASDAQ100U) against an outside real-time reference and its short realised volatility; cheap asks only

Worker IDXFUT1, Strategy Research V2, 2026-11-03. Research only, no promote verb. Written and pushed before any OKX index-linked price was compared with any Kalshi quote, model probability or outcome. N +8 (4 tries).

## Reference found (disclosed; only listings and a 2-row sample of the candle history were looked at)

Reachable keyless from this sandbox: **OKX public** `GET /api/v5/market/history-candles` for the equity-index perpetuals `SPY-USDT-SWAP` (SPY ETF, about 1/10 of the S&P 500) and `QQQ-USDT-SWAP` (QQQ, about 1/40 of the Nasdaq 100), 1 minute bars, listed 2026-03-04, so they cover every Kalshi 4 pm close on file (2026-08-24 to 10-28). `US500-USDT-SWAP` and `US100-USDT-SWAP` (the index itself) were listed only on 2026-09-10 and cover about half the window, so they are NOT used (disclosed so nobody reads a choice into it). Also reachable: FRED daily `SP500` (daily only, no use intraday), Hyperliquid `xyz:SP500`/`xyz:XYZ100` mids (live only, no history fetched), Kraken `SPXUSD` (this is the SPX6900 token, not the index). Refused or unusable: Yahoo (429 now; its 5 minute bars from INX1 are on disk), Stooq (JS wall), CNBC (403), Binance (451). The OKX equity perps are a 24/7 perpetual that tracks the ETF through the cash session (volume is thin: the sample candles show 0.05 to 2 contracts a minute), so basis noise between the perp and the true index is a known error source and is part of the test.

## Ledger check (done first)

- **INX1** (README ~7630, FALSIFIED): the same two ladders against Yahoo 5 minute index + VIX/VXN implied vol, buy when ask at least 5c under the model, both sides, 60/30/10. PF 0.29 to 3.18 at 25 to 32 orders; 354 of 360 orders were a side under 50c and 85% lost; Kalshi's mid beat the model on Brier at every look. IDXFUT1 changes three things and is therefore a counted variant, not a repeat: (1) the reference is a real-time OKX equity-index perp (1 minute) instead of a delayed 5 minute Yahoo bar, (2) the vol is the realised vol of that same reference over the last 60 minutes instead of VIX/VXN, (3) the entry is only an ask of 3c to 30c with reference probability at least 3x the ask (a ratio rule, not a 5c edge), hard limit 0.30.
- **PUB20 P05** (NDXLEAD S&P/Nasdaq lead-lag between the two ladders): NOT_ENOUGH_DATA, carried, not re-scored. **PUB20 P08** (SMILE residual within the ladder): FALSIFIED, carried. **E4** (L1 band rule on KXINXU): -2.78c, FALSIFIED, carried. **XMET1**: macro-metadata lead, FALSIFIED, carried. **VOLGAP1** (2026-11-03): ladder-implied vol vs realised vol on Bitcoin/Ethereum/gold hourly ladders, tails lose 1 to 3 points everywhere; the S&P/Nasdaq ladders and an outside price are the new part. **TAIL/LADLONG1**: unconditional cheap tails lose (PF 0.64 / 0.72), carried: cheap asks are the population here, so the control is the nearest-to-10c ask with no model.
- The daily range series (`KXINX`, `KXNASDAQ100`, 25 point buckets) have no candle history on disk and fetching them is a new data pull; they are NOT in this registration (a follow-up only if this one shows a lead).

## The rule (exact)

- **Markets:** KXINXU and KXNASDAQ100U events with the 4 pm ET close (`H1600`), "above K" (`strike`, `result` as in `data/inx1.sqlite`), 47 closes 2026-08-24 to 10-28. Reference: SPY perp for KXINXU, QQQ perp for KXNASDAQ100U.
- **Looks:** L = 30 and 10 minutes before the close. D = close - L minutes. Two indices x two looks = **4 tries**.
- **Reference price at D:** R = close of the OKX 1 minute bar that ends at D (bar start D - 60 s). Index scale: r = (Yahoo 5 minute index close of the bar ending at close - 75 minutes) / (OKX close of the 1 minute bar ending at that same time), from `data/inx1_yahoo` (the scale is one number a day measured 45 to 75 minutes before the look; it is not updated afterwards). S = R x r.
- **Short vol:** sigma = RMS of the 1 minute log returns of the OKX closes over the 60 minutes ending at D (zero mean), needs at least 40 returns; horizon H = L minutes. Fair value p = Phi( ln(S/K) / (sigma x sqrt(H)) ). No drift, no VIX, no tuning.
- **Quote and fill:** the Kalshi 1 minute candle ending at D + 60 (first minute after the signal), closing bid and ask, must be two-sided (yes_bid > 0, yes_ask < 1). Candidates: YES at yes_ask a where 0.03 <= a <= 0.30 and p >= 3a; NO at b = 1 - yes_bid where 0.03 <= b <= 0.30 and (1 - p) >= 3b. **Hard limit 0.30.** Fill at that ask (taker), held to settlement, no stop. One trade per index per look per day: the candidate with the largest model edge (p - a, or (1-p) - b).
- **Size and fees:** C = 10 for scoring, 7% x C x price x (1 - price) rounded up to the cent per order; check at fees x1.2 and with +1c slippage on the fill.
- **Control (no model):** per index-look-day, the strike-side whose ask is nearest 0.10 inside 0.03 to 0.30, same candle, same hold. **Calibration (information, not a try):** every strike-side with an ask 0.03 to 0.30 in the windows, bucketed by model ratio p/a (under 1, 1 to 3, at least 3): n, mean price, win rate, mean model p.
- **Windows:** the 47 closing days sorted, equal thirds: W1 discovery, W2 validation, **W3 holdout frozen and unread** (not loaded into any print) unless W1 and W2 both pass for the pooled treated set and treated beats control; then read once.

## Counterparty

Kalshi takers and quoters who leave an index-ladder strike's cheap side stale against the live index (a round-number or last-print quoter), selling a 3c to 30c contract at less than a third of its probability. **Honest alternative (expected):** Kalshi's quoters price off futures in real time (as for gold, GOLDFV1, oil and FX, DAILY2, and INX1 on this very ladder), the model is a thin-volume ETF perp with basis noise and a 60 minute vol, and the far strikes carry the longshot bias; so the ratio rule buys the strikes where the model is most wrong.

## Numeric prediction (before any outcome)

Signals fire (ratio at least 3 with an ask 3c to 30c) in about 30% of index-look-days: about 14 trades per variant over 47 days, about 55 in total in W1 + W2 pooled across the four variants (NOT_ENOUGH_DATA, under 150, about 70% likely). Win rate about 9% against a mean price about 0.12 (model p about 0.30); payoff about 7; **PF 0.6 per window (range 0.2 to 1.3)**; control PF 0.7. Calibration: the win rate in the "ratio at least 3" bucket is under the model p by 10 points or more, and about 2 points under the price.

## Kill criteria and verdicts

- Pooled treated trades in W1 + W2 under 150: **NOT_ENOUGH_DATA** (informational lines still printed). Per variant fewer than 8 days with a trade in W1 or W2: that variant NOT_ENOUGH_DATA.
- **FALSIFIED** if PF under 1.5 in W1 or in W2 (pooled or per variant) after fees, or fees x1.2 mean is not positive, or treated minus control mean per trade is not positive in both windows.
- Only if PF at least 1.5 in W1 and W2 and positive at fees x1.2 and +1c and above control, with day-clustered z of the net per trade at least 5.27 (N about 728,763, flagged because 47 days cannot reach it unless the edge is huge): NOT_YET_FALSIFIED, which earns a W3 read and a forward-recorder registration only.
- No parameter changes after this commit. Any later variant (a third look, another vol window, US500/US100 perps, the daily range series) is a new counted try with its own registration.

## Capped-probe spec (only written to be filled in if a lead appears; not a recommendation)

1 contract per order, hard limit 0.30 (and a model ratio of at least 3 at the look), YES or NO whichever the rule picks, max 1 order per index per look per day (so at most 4 orders a day, worst day 4 x (30c + fee 1.5c) = about $1.26 at one contract, worst single loss about 31.5c), held to settlement. Kill: 3 straight probe losses beyond the expected run, or net under -$3 after 40 fills, or PF under 1 after 40 fills. Fills expected: about 0.3 a day per variant means 40 fills in about 100 trading days; to be updated with the measured rate. Runs in a separate research module with an outside price feed, which does not exist in the bot; a probe would need the owner's approval and a new feed (not built).

## Expected read date

Scored once on the data on file: 2026-11-03 (today), after the OKX fetch finishes. No forward read unless a lead shows.
