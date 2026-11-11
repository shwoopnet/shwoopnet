# MENTCOMBO1 (registered Nov 11, 2026, before any outcome is scored): mention combos simulated from singles
SIMULATION ONLY. No combo market was priced; this is never live evidence. Research only, held data, no Kalshi call.
Data: data/ment1/markets.json (6,346 settled earnings-call word markets, all EARN; no political mention series has candles in the held files, so none) and data/ment1/candles_*.json (hourly bid/ask candles). Event = the `ev` field (one call, several words).
Link stated in writing: legs are words in the SAME call, so they are linked on purpose (a long, topical call raises several words together). The test is whether that link makes the product price too cheap.
Look (ONE, fixed now): per leg, the last candle with end_ts <= close - 4h with bid and ask both present and 0 < bid < ask < 1. A leg with no such candle is dropped. Leg price = YES ask. Eligible leg = ask 0.10 to 0.90 inclusive.
Combos: events with >= 2 eligible legs; every combination of 2 and of 3 legs; if an event has more than 200 combos of a leg count, keep 200 chosen by smallest md5(seed "MC1" + event + sorted tickers). Leg counts 2 and 3 only (4 and 5 not run: too few eligible legs per event to fill).
Joint outcome = all legs result yes. Independence gap = observed joint YES rate minus mean product of leg asks, by leg count.
Paper trade: buy the combo YES at P = product x (1 - h), h in {0, 0.10, 0.20} (scenario, not evidence). Fee 0.07 P (1-P) unrounded per contract. Net per combo = win(1/0) - P - fee. Cash per dollar = sum net / sum P. Event-clustered z (clusters = events, ratio estimator se).
Paper-edge test (needs all): cash per dollar >= +0.10, both date halves of the development set also >= +0.10 each, n >= 100 combos, no single event over 30% of total net.
Split: events ordered by earliest market close; development = first two thirds; held-out last third read ONCE and only if some development scenario passes the test above (same test, same scenario).
Bars: z 5.34 (shared N about 1,100,000 plus this count) and 4.39 (N 9,009), reported next to z; a verdict above NOT_YET_FALSIFIED needs z over the bar too.
Prediction: words in one call are positively correlated, so the gap is positive for buyers at h = 0; but cheap-leg overpricing (MENT1: cheap sides lose) may offset it. Prior for passing at h = 10%: 15%.
