# BTCAVG registration: second-by-second fair value of the Bitcoin 15 minute closing average (V2 worker, 2026-10-29)

Research only. Written and pushed **before** any quote price, spot price or result row of the recorder was read by me. What I read first: the files' headers and `coverage.csv` (to count Bitcoin windows per date). Nothing here changes a live rule.

## Disclosure of what has already been seen
- RECORD1 (README, 2026-10-22) is a close sibling: same recorder, a median-of-exchanges index, the partly fixed average, five assets, margin 3c, size at least 5, decision at 60/45/30/15 s, claim on mean and z over 300 trades and 10 dates. Its registered read is NOT duplicated here and is not run by me. Its information looks (pooled five assets; 2026-10-27: 79 trades, +12.4c, z 2.26, `clock_ok` False) were seen by the lead and are in the README; I have not seen a Bitcoin-only figure. This test differs in: Bitcoin only; the bar (PF at least 1.5 in each of three date windows at 1 and 10 contracts, fees rounded up per order); margin 5c; size at least 1 contract at the ask; one fixed decision second per variant (not the earliest of four); the exact sum-of-a-random-walk variance; and a report of the proxy's own error against settlement. It is still not blind to the pooled RECORD1 looks.
- L9 (minute candles, FALSIFIED -1.79c) and LAG2B (Kraken against Kalshi trades, FALSIFIED, model to last trade median gap 0.2c) are the prior evidence against.

## Data (frozen)
Branch `quote-data` at commit `b7dc9cbe823b2b9f734dc085ea03452a1aec3c1b` (2026-10-29T20:03Z); later commits are not read. `quotes/<date>/<HHMM>/{quotes,spot,results,coverage,clock}.csv.gz`. Universe: every `KXBTC15M-*` ticker in `results.csv` with result yes or no (chosen on time only, before any entry look). Counted from coverage (no outcome read): 257 Bitcoin windows with polls, by close date 10-22: 4, 10-23: 36, 10-24: 33, 10-25: 42, 10-26: 34, 10-27: 35, 10-28: 27, 10-29: 46.

**Three windows by UTC close date, fixed now:** W1 = 2026-10-22 to 2026-10-24, W2 = 2026-10-25 to 2026-10-26, W3 = 2026-10-27 to 2026-10-29 (holdout: read once, after W1 and W2 are written to the result file).

## The BRTI proxy (fixed)
From `spot.csv`, asset BTC, exchanges Coinbase (ticker = last match), Kraken (trades), Bitstamp (trades), timed by `t_recv_ms` (what a trader would have had; `exchange_time` is not used). For each integer second t, each exchange's value is its last price with `t_recv_ms < (t+1)*1000`, kept only if received within the last 5 s. Proxy X(t) = median of the live exchanges' values, defined only when at least 2 are live. (CF's BRTI is a volume-weighted median over order books of more venues; this is a three-venue last-trade median, so a basis is expected and is measured below.)

## The model (fixed, nothing fitted)
Settlement: YES iff the mean of BRTI over the 60 seconds before the close is at least the strike (`strike` column of `quotes.csv`). The final-minute seconds are t = C-60 ... C-1, C = close in unix seconds.
At a decision poll received at T ms: k = number of final-minute seconds with (t+1)*1000 <= T (complete), m = 60 - k remaining. A_obs = mean of X over the complete final-minute seconds that have a value (needs at least 80% of k present, else no decision; if k = 0 there is no observed part). S = X at the last complete second (needed). sigma = population standard deviation of one-second changes X(t+1) - X(t) over the 300 s before T (both ends present; at least 100 changes, else no decision). The remaining m seconds are S plus a driftless random walk: their sum has mean m*S and variance sigma^2 * m(m+1)(2m+1)/6. So the average A has mean (k*A_obs + m*S)/60 and sd sigma*sqrt(m(m+1)(2m+1)/6)/60, and P(YES) = 1 - Phi((strike - mean)/sd). (If sd is 0, P is 1 or 0.)

## The rule (fixed)
Decision poll: the first `quotes.csv` row for the ticker with status active, both yes_bid and yes_ask present (0 < bid <= ask < 1), and `t_recv_ms >= C*1000 - D*1000`; it must also have `t_recv_ms <= C*1000 - (D-5)*1000`, else that window has no decision for this variant. Fee per order f(p, n) = ceil(100 * 0.07 * n * p * (1-p)) / 100.
- Buy YES at the ask if P - ask - f(ask,1) >= 0.05 and ask_size >= 1.
- Else buy NO at 1 - yes_bid if (1 - P) - (1 - bid) - f(1-bid,1) >= 0.05 and bid_size >= 1.
- Held to settlement (results.csv). One trade per window per variant.
- At 10 contracts: filled count = min(10, floor(size at that price)); fee f(price, count) on that count. At 1 contract: 1 contract. Fees x1.2: each order's fee times 1.2, rounded up to the cent.

## Variants (N = 4 tried, each counted)
1. **D30**: decision at 30 s before the close (k about 30 observed seconds).
2. **D15**: decision at 15 s.
3. **D45**: decision at 45 s.
4. **D30L** (latency check, counted as a try, reported as information): D30's signal, but filled at the NEXT poll's quote for the same side (must still be at or below the model by any amount; if the next poll's price is worse than the signal price, that price is paid; no next poll before the close, no trade).

## Counterparty
Quoters who price the last minute as a point price at the close (or who reprice slowly as spot moves), so with part of the average already fixed the favourite is underpriced or the far side overpriced (L9's idea at the resolution where it bites). Honest alternative, which I expect: the book already prices the average and tracks spot (LAG2B: median model-to-trade gap 0.2c; market makers on these markets are fast).

## Prediction (numeric, now)
- D30 mean net at 1 contract between -2c and +3c per trade; PF below 1.5 in at least one window. Prior of passing the bar: about 3%.
- Most likely verdict: **NOT_ENOUGH_DATA**. With about 250 windows and a 5c margin, I expect 10 to 40 trades per variant in total, under the 30 per window needed.
- Proxy agreement (information): sign(A_proxy - strike) agrees with the settled result in about 95% or more of windows, failing mostly where |A_proxy - strike| is under about $10.

## Verdict rules (per variant; the strategy verdict is D30, D15 and D45 judged separately)
- **NOT_ENOUGH_DATA** if any of W1, W2, W3 has fewer than 30 trades.
- **FALSIFIED** if every window has at least 30 trades and any window's PF at 1 contract is below 1.0, or the pooled mean at fees x1.2 is at or below 0.
- **NOT_YET_FALSIFIED** only if every window has at least 30 trades, PF at least 1.5 in each window at both 1 and 10 contracts, pooled net positive at fees x1.2, and the pooled per-window (trade) z at least 5.17 (the deflated bar for N about 439,000). Otherwise NOT_ENOUGH_DATA. A pass earns only a forward test registration.
- PF = gross wins / gross losses in dollars of the trades in that window. Independent unit: the 15 minute window (one Bitcoin market each); a date-clustered z is also printed. Zero-volume candles do not apply (quote data, no candles); polls with a missing side are skipped and counted.

## Information only (decides nothing)
Proxy-outcome agreement: for every window with X present in at least 48 of the 60 final seconds, A_proxy = mean of those values; the share where sign(A_proxy - strike) matches the result, overall and by |A_proxy - strike| bucket (under $5, $5 to $20, $20 to $50, over $50). Model calibration of the D30 P against outcomes in five bins. The count of windows skipped at each step. The recorder clock offset per window where `clock.csv` has a value.

Tries: +4 (running count about 438,936 + 4 = about 438,940, plus other workers'). Code: `kalshi-scalper/workers/BTCAVG_score.py`, written after this file is pushed.
