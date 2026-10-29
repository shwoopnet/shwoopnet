# GEN5 result (2026-10-29): NO_WINNER, FALSIFIED at validation. No forward candidate.

Registration: `workers/GEN5_REGISTRATION.md` (pushed first, commit e909056). Survivors frozen before validation: `workers/GEN5_FROZEN.md` (sha256 fc3a3259... gold, 7c414d6f... Bitcoin; commit e8af0ae). Validation read once.

**Data.** Yahoo 1 minute GC=F (28,864 bars), DX-Y.NYB (28,204), ^TNX (8,399, cash hours), 2026-09-30 to 10-29; Coinbase BTC-USD 1 minute (122,496 bars, 2026-08-05 22:00 to 10-29 23:36). Kalshi candles: gold 1,864 windows on 25 days (37,171 entry rows), Bitcoin 8,041 windows on 85 days (159,771 rows). Only outside bars with START at or before t - 120 were read (ended before the signal candle began); unfinished live bars dropped. ES=F not used (no 1 minute history before Sep 30, as registered).

## Funnel

| | Gold | Bitcoin |
|---|---|---|
| Generated (all in N) | 13,176 | 12,416 |
| Distinct (GEN1 dedupe, 30+ discovery trades) | 5,000 | 5,000 |
| Discovery PF over all distinct: median / 95th pct | 0.63 / 0.97 | 0.65 / 0.93 |
| Distinct at screen size (gold 60+ trades and 8+ days; Bitcoin 100+ and 10+) | 4,051 | 4,454 |
| Best discovery PF at screen size | 1.60 | 1.55 |
| Passed discovery (PF 1.5, size, zero-volume share 20% or less) | 3 | 1 |
| Passed validation (PF 1.3, 40+ trades, stress PF above 1.0) | **0** | **0** |

N added: **25,592** (running count about 464,600; Bonferroni z bar about 5.19). Fills: next candle's closing ask (gates); signal candle's ask reported. Fees: per-order rounded at C = 10 (C = 1 shown as pf1), stress x1.2. No fill fell on a zero-volume candle in any row below.

## Every survivor, then the best of the rest (validation is information only for the rest)

PF at C = 10, next-candle fill. Disc = discovery, Val = validation. Trades per week from the validation days.

| # | Strategy | Disc PF (n, days) | Val PF (n, days) | Val C=1 / stress | Val signal-fill PF | Val z | Trades/week |
|---|---|---|---|---|---|---|---|
| G1 survivor | gold NO, 13 to 11 min left, o_dz > 0 and TNX 5 min change > +0.2bp; TP +8c, out at 2 min or spread 3c | 1.51 (73, 11) | **1.25** (45, 9) | 1.14 / 1.18 | 1.17 | +0.60 | 29 |
| G2 survivor | gold both, 12 to 5 min, ask > 40c, DXY 15 min <= +0.1bp, vol ratio > 0.98, TNX 15 min <= -0.5bp; out at 2 min or spread 3c | 1.58 (69, 11) | **0.72** (54, 9) | 0.67 / 0.70 | 0.63 | -1.15 | 34 |
| G3 survivor | gold NO, 12 to 4 min, side bid fell 7c+ in 3 min, DXY 5 min > -0.29bp, TNX 5 min <= -0.2bp; stop -10c, out at 2 min or spread 3c | 1.60 (60, 11) | **0.77** (57, 9) | 0.69 / 0.74 | 0.51 | -0.85 | 36 |
| B1 survivor | Bitcoin both, 12 to 8 min, Coinbase 3 min return > +7.2bp toward the side and 60 min vol <= 2.67bp; out at 2 min | 1.55 (193, 36) | **0.88** (109, 24) | 0.80 / 0.86 | 0.85 | -0.49 | 26 |
| info | gold NO, DXY 15 min <= -1.2bp, hour > 9, gold 1 min <= -3.4bp, TNX 5 min <= 0.6bp; TP/stop 20c | 1.41 (64, 12) | 1.33 (50, 9) | 1.21 / 1.26 | 1.06 | +0.82 | 32 |
| info | gold NO, o_dz > -0.56, gold 1 min > +0.96bp, 15 min > -0.96bp, TNX 15 min <= -0.5bp | 1.48 (72, 11) | 0.70 (61, 9) | | 0.66 | -1.31 | |
| info | gold NO, DXY 15 min <= -3.7bp, o_fv > 0.10 | 1.47 (75, 12) | 0.49 (47, 9) | | 0.55 | -2.99 | |
| info | Bitcoin YES, o_fv <= -0.16 and 60 min vol > 7.3bp; stop -5c | 1.36 (291, 36) | 0.73 (102, 21) | | 0.74 | -1.44 | |
| info | Bitcoin NO, o_dz > 0, vol ratio <= 1.29, spread > 1c; TP 12 stop 10 | 1.33 (120, 38) | 1.28 (12, 11) | | 0.94 | +0.44 | |
| info | Bitcoin YES, hour <= 9, o_dz > 0.29, 1 min <= 1.3bp, 5 min <= -0.53bp; out at 4 min | 1.27 (192, 54) | 0.96 (93, 26) | | 0.96 | -0.14 | |

(All 20 validation rows, 10 per market, are in `data/gen5_<market>_validation.json`, not committed; all are below PF 1.3 except the two shown at 1.33 and 1.28, which were not survivors and have 50 and 12 trades.)

## Verdict

**FALSIFIED** for all four frozen survivors (validation PF 1.25, 0.72, 0.77, 0.88). The one that came closest (G1, PF 1.25 on 45 trades) has z +0.60, nowhere near the deflation bar of about 5.19. Prediction held: Bitcoin about one discovery pass (predicted zero), gold 3 (predicted a handful), validation zero. The discovery maxima (1.60 gold, 1.55 Bitcoin) are what 5,000 draws give on noise; median discovery PF 0.63 to 0.65 says the average outside-state rule loses about a third of its stake to spread and fees, as in GEN1 (0.62). Outside reference states (volatility regime, 1 to 15 minute trend, distance from open in sigma, normal fair-value edge, dollar and yield moves) do not give Kalshi's gold or Bitcoin 15 minute quotes a lag or mispricing that survives one spread and two fees at minute resolution, consistent with GOLDFV1 and XMAC1.

**Forward candidates:** none (nothing cleared validation), so no file in `workers/candidates/`. The forward evaluator `scalper.gen5:evaluate` exists (`python -m scalper.gen5 forward <candidate.json>`) if a later run admits one.

**Files.** `src/scalper/gen5.py`, `src/scalper/gen5_fetch.py`, `workers/GEN5_REGISTRATION.md`, `workers/GEN5_FROZEN.md`, `workers/GEN5_frozen_gold.json`, `workers/GEN5_frozen_btc.json`, this file. Outside bars in `data/gen5/` (not committed).
