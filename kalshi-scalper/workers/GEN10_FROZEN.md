# GEN10 frozen discovery results (pushed before any validation row is built)

## Gold (KXGOLD15M), frozen 2026-10-30 14:15 UTC

Rows: 1,704 discovery windows on 23 days, 125,972 rows (signal bar and side pairs in the 15c to 85c band with a fill). 21,219 draws to 5,000 distinct (rejected: 3,472 without a signed condition, 1,167 under 30 trades, 11,580 duplicates). Median discovery PF 0.86, 95th percentile 1.08; 4,274 distinct at screen size (100+ trades, 15+ days), 311 with PF 1.0 or more, 10 with 1.3 or more, best 1.97. **3 survivors** (PF 1.5+, at size), listed with the best 10 in `workers/GEN10_frozen.json`:

1. `no 600..600s, tbig <= 0 & dpw > 25, held` (discovery PF 1.97, n 100, 18 days, mean +8.7c, win rate 89%, mean fill 79c)
2. `both 600..600s, dp30 <= 0 & dpw > 25 & f30 > -2306, held` (PF 1.88, n 111, 21 days, +7.9c, 89%, fill 80c)
3. `no 660..600s, bigdir30 > -1 & f60 > 476.7 & dpw > 17, held` (PF 1.50, n 143, 19 days, +6.7c, 81%, fill 73c)

All three buy the side priced about 73c to 80c at 10 to 11 minutes left after the price has moved 17c to 25c toward it since the open (`dpw`); the side-shuffle control in validation is what decides whether that is the tape or the band.

- `workers/GEN10_frozen.json` (3 survivors, best 10): sha256 f73d61d655ef3d3d46ae8660c1dabe1d10f49d6ae2cca8ba2fe0a2c6b4282b76
- `data/gen10/controls.json` (4,271 controls, not committed): sha256 a0076494ad2961f1e3ed8e425ece5714a662c8fc6fef0332f81f4a57e8e1e4ab
- `data/gen10/distinct.json` (not committed): sha256 254d354073b9c8482eb8d5e049a5fb87049b1ba96f4372e1e77c8e035813a815

Validation (Sep 21 to Oct 27, sampled days) is read once after this file is pushed.
