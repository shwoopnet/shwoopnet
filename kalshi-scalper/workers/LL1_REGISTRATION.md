# LL1 registration: BTC/ETH perp return leads the US Tech 100 and US 500 perps (risk-on/risk-off flow) (2026-11-06, before scoring). Shared rules: workers/LEAD_COMMON.md

Counterparty: slower index-perp books and their makers, who update after crypto has already moved (crypto trades 24/7 and risk appetite shows there first). Honest alternative: no lead; any hit is noise.
Definition (fixed): for consecutive samples (t0, t1) with gap 2 to 8 h, s = mean of the mid log returns of BTC and ETH perps over (t0, t1). If |s| >= 0.5%, then for EACH of US Tech 100 and US 500 (each a separate trade) trade in the sign of s from the quotes at t1 to the next sample t2 with gap (t1, t2) 2 to 8 h. No overlap issue (one trade per index per interval). Control: opposite sign.
Prediction: NOT_ENOUGH_DATA (certain: 11 dates). Information figures: gross per trade under 10 bp, cost about 25 to 30 bp, net negative; hit rate near 50 percent.
Kill: LEAD only under the common rules.
