# GEN11 frozen discovery results (pushed before any validation row is built)

## Bitcoin (KXBTC15M), frozen 2026-10-30 14:41 UTC

Rows: 558 discovery windows on 23 days (the 1,004 fetched markets of GEN9's seeded half of days), 42,954 rows (signal bar and side pairs in the 15c to 85c band with a fill). 28,442 draws to 5,000 distinct (rejected: 4,661 without a signed condition, 3,066 under 30 trades, 15,715 duplicates). Median discovery PF 0.87, 95th percentile 1.26; 2,923 distinct at screen size (100+ trades, 15+ days), 471 with PF 1.0 or more, 23 with 1.3 or more, best 1.63. Unconditioned base (first in-band bar from 840 s down, held, C = 10): YES PF 0.85 (n 558, -3.8c, win rate 49%, fill 51c), NO 0.90 (n 558, -2.5c, 51%, fill 52c). **5 survivors** (PF 1.5+, at size), listed with the best 10 in `workers/GEN11_frozen.json`:

1. `no 480..480s, c30 > 877 & f10 > -5124, held` (discovery PF 1.63, n 102, 23 days, mean +9.6c, win rate 59%, mean fill 48c)
2. `both 780..720s, c10 <= 365 & f60 <= -5738 & big30 > 3753, held` (PF 1.59, n 110, 23 days, +9.4c, 70%, fill 59c)
3. `both 720..720s, big30 > 2000 & iw <= 0.09205 & dp30 > 3, held` (PF 1.58, n 100, 23 days, +8.4c, 75%, fill 65c)
4. `both 660..660s, i30 > -0.07715 & iw <= -0.09205 & c30 > 451, held` (PF 1.55, n 102, 23 days, +8.9c, 70%, fill 59c)
5. `both 600..600s, dp10 <= -5, held` (PF 1.53, n 108, 23 days, +8.8c, 57%, fill 47c)

Unlike gold's three, these are five different bets (a busy 30 s at 8 minutes left; a big print with flow against the side at 12 to 13 minutes; a big print with the price moving toward the side at 12 minutes; flow against the side since the open at 11 minutes; a 5c drop against the side in the last 10 s at 10 minutes), each at exactly its discovery PF edge of 1.5 to 1.63 on 100 to 110 trades, which is what the best of 2,923 at size looks like under the null. The side-shuffle control in validation is what decides whether any of it is the tape.

- `workers/GEN11_frozen.json` (5 survivors, best 10): sha256 e2c960eff0ada0e93a47607c4829644e4c96a11165474256548e6707789b1c5c
- `data/gen11/controls.json` (2,918 controls, not committed): sha256 39c9e6dc4f1e476d744b2b236c407dd0c80e84f3cb5e2a93a52e796a77b9e6e7
- `data/gen11/distinct.json` (not committed): sha256 ef54bcc559e75e71f8d82d86b15ffdfad84aceefc7e8f1bf7ff3f7a2c2e92f7e

Validation (Sep 21 to Oct 27, sampled days, fetched markets) is read once after this file is pushed.
