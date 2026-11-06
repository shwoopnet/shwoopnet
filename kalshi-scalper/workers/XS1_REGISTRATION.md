# XS1 registration: cross-sectional 24 hour momentum across the spread-filtered perps (2026-11-06, before scoring). Shared rules: workers/LEAD_COMMON.md

Counterparty: slow-to-update books and holders chasing yesterday's winners (momentum) or liquidity providers repaid for reversal. Direction registered: MOMENTUM (long top, short bottom); control = reversal.
Definition (fixed): once per UTC date, the first sample at or after 14:00 UTC is the entry t. The lookback sample is the one nearest t minus 24 h within +-3 h; the exit sample the one nearest t plus 24 h within +-3 h; else the date is skipped (counted). Rank the universe U (quotes present at all three samples) by the mid log return over (lookback, t). Long the top 2 and short the bottom 2, equal weight $1 per side in total ($0.5 a leg), enter t at ask/bid, exit at bid/ask. Cost: fee 0.12% per side on every leg, so 0.24% round trip on $2 gross, plus spread and funding.
Prediction: NOT_ENOUGH_DATA (at most 11 trades). Information: gross under 30 bp per day, net about -25 bp.
Kill: LEAD only under the common rules.
