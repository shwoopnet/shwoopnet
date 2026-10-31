# ECONNEW2 result (Strategy Research V2, 2026-10-31, research only)

Registered first: `workers/ECONNEW2_REGISTRATION.md` (commit 715ec87, with `src/scalper/econnew2.py`, before the discovery fit, any candle download or any score). Run once; raw output `data/econnew2_result.txt` (local, data/ is not committed). Candle parser: both field names (`pick`), so the ECONNEW1 parser bug does not apply.
Deviations to disclose: (1) the registration says 126 eligible AAA events and a 76 / 25 / 25 split; after requiring every settled value and RBOB bar to parse the run had 123 eligible events, 76 / 22 / 25 (the date cuts are as registered, three validation events dropped). (2) The registration mentioned a 72-hour look as information only; it was not run. (3) The holdout was not read (the rule: only if both windows pass).

## Angle A, GAS-RBOB: weekly AAA ladder (KXAAAGASW) against a wholesale pass-through model: NOT_ENOUGH_DATA (the PFs are far under the bar)

Model (form fixed in the registration, fitted on the 76 discovery weeks only, frozen): weekly AAA change = -0.0059 + 0.1552 x (RBOB change over 14 days, $ a gallon) + 0.2645 x (previous week's AAA change); residual sd $0.0278. Universe 280 strikes (fair 0.10 to 0.90) on 123 weekly events; 142 had a two-sided quote at the look 24 hours before settlement; trades need a spread of at most 10c and a 5c edge, 10 contracts, held.

| Window | Trades | Events | PF | Mean per contract | Event-clustered z | Loss rate |
|---|---|---|---|---|---|---|
| Discovery (closes before 2025-11-14) | 30 | 30 | **0.07** | -11.98c | -4.35 | 97% |
| Validation (2025-11-14 to 2026-05-07) | 29 | 14 | **0.27** | -7.98c | -2.28 | 93% |
| Pooled disc + val | 59 | 44 | 0.16 | -10.01c | -4.46 | 95% |
| Pooled, fees x1.2 (disc / val) | 30 / 29 | | 0.07 / 0.27 | -12.09c / -8.11c | | |
| Frozen holdout (2026-05-08 on) | not read | | | | | |

Information only: edge 0.03: 61 trades PF 0.15; edge 0.08: 57 trades PF 0.18; quote candle with volume: 50 trades PF 0.17; quote candle with zero volume: 9 trades PF 0.00. Brier on 75 markets: model 0.2729, market mid 0.0489 (the market is far better).
What is new against GAS1: the RBOB term does carry information about the weekly AAA change. Validation RMSE of the weekly change (22 weeks): full model $0.0946, persistence-only (no RBOB) $0.1349, zero change $0.1418, RBOB coefficient +0.155. So wholesale leads retail, as expected. It does not matter for the ladder: at the look the market already prices the daily AAA print (which the model does not have; only the weekly settlement history is public here), so its Brier is five times better than the model's, and 95% of the entries lose. The disagreement is the model's error, not an edge.
Verdict under the registered rule: `NOT_ENOUGH_DATA` (30 and 29 trades against 100 and 50), because FALSIFIED needs the minimum count. Read plainly: PF 0.07 and 0.27 with z -4.35 and -2.28 are not close to the 1.5 bar, and the mean loss of 10c a contract is about the size of the edge threshold plus the fee. Prediction before the run: 150 to 400 trades, PF 0.5 to 1.1, z -3 to +1; actual trades 59 (fewer, because most strikes have no quote within 10c at the look) and PF worse than predicted. The entries concentrate where the model's centre sits a few cents away from the market, which is exactly where a daily-print-aware market is right.
Forward-only date: the trade rate is about 0.6 a week; 100 discovery-style trades need about 3 years. Not worth a registration unless the daily AAA number is added as an input (it is public only on gasprices.aaa.com's current page; no history without a key or a paid feed), in which case it is a different, closer-to-GAS1 test, the daily ladder already FALSIFIED.

## Angle B, PCE-NOWCAST: core PCE (KXPCECORE) against the Cleveland Fed core PCE nowcast: NOT_ENOUGH_DATA (a reword of CPI1 on a new series, with the owner's go-ahead)

Same structure as the registered CPI1 (vintage dated before the price candle, expanding error distribution of at least 36 earlier months, edge 5c, 24 hours before, held), 25 events (15 / 5 / 5 by release date), 137 strikes, 49 with a quote at the look within 6 hours and a spread of at most 10c available; nowcast file sha256 64e8254608c4fb8d.

| Window | Trades | Events | PF | Mean per contract | z | Loss rate |
|---|---|---|---|---|---|---|
| Discovery (releases to 2025-12-19) | 13 | 9 | 0.37 | -12.28c | -1.52 | 77% |
| Validation (2026-01-29 to 2026-05-28) | 8 | 5 | 0.84 | -2.60c | -0.21 | 75% |
| Pooled | 21 | 14 | 0.53 | -8.60c | -1.20 | 76% |
| Holdout (2026-06-25 on) | not read | | | | | |

Information only: edge 0.03: 25 trades PF 0.49; edge 0.08: 19 trades PF 0.54; Brier on 37 markets: model 0.2457, market 0.1020. Look-ahead check (nowcast RMSE by vintage age): 0.079 at 1 and 5 labels before the end, 0.084 at 10, 0.120 at 20 (n 158 to 159): the error grows with age, so the file is not obviously back-filled.
Verdict `NOT_ENOUGH_DATA` (13 and 8 trades against 100 and 50); the 21 trades have PF 0.53 and are not a claim in either direction. Prediction before the run (10 to 40 trades, NOT_ENOUGH_DATA): met.
Date the bar could be met: the series has 5 to 8 strikes per release and one release a month; this rule trades about 1.5 strikes per release, so 100 trades needs about 65 more releases, roughly 2032. Not worth waiting for. Forward-only registration is therefore not recommended. The next release is core PCE October on Nov 25; it would add at most 2 trades.

## Tries and ledger

Two angles, one rule each, N +2: running count about 728,690 (z bar about 5.27). Nothing else scored; the holdouts of both angles stay unread. Nothing here is a promote verb or an input to trading code.
Files: `src/scalper/econnew2.py`, `workers/ECONNEW2_REGISTRATION.md`, this file.

## Proposed README section (for the lead to paste; README.md not edited)

### ECONNEW2, weekly AAA gas ladder against RBOB futures, and core PCE against the Cleveland Fed nowcast (worker, 2026-10-31; `workers/ECONNEW2_REGISTRATION.md`, `ECONNEW2_RESULT.md`, `src/scalper/econnew2.py`)

Owner opened economic releases; two angles registered before any score (GAS1 had no futures input and tested the daily ladder; the PCE angle is a reword of CPI1 on KXPCECORE). **A, KXAAAGASW** (123 eligible weekly events 2023-10 to 2026-10): weekly AAA change = a + b1 x RBOB change over 14 days + b2 x last week's AAA change, fitted on the first 76 weeks only (b1 +0.155, residual sd $0.028), 5c edge at 24 hours before settlement, spread at most 10c, 10 contracts, held. Discovery 30 trades PF 0.07 (z -4.35), validation 29 trades PF 0.27 (z -2.28), pooled mean -10.0c, model Brier 0.273 against the market's 0.049; holdout not read. `NOT_ENOUGH_DATA` by the count rule (30 and 29 against 100 and 50), with PFs nowhere near 1.5. The RBOB term does predict the weekly AAA change out of sample (validation RMSE $0.095 against $0.135 without it), but the market at the look already sees the daily AAA print, which no public history gives this model. **B, KXPCECORE against the Cleveland core PCE nowcast** (25 releases): discovery 13 trades PF 0.37, validation 8 trades PF 0.84, pooled 21 trades PF 0.53; `NOT_ENOUGH_DATA`; about 1.5 trades a release, so 100 trades is about 2032: no forward registration recommended. Deviations disclosed: 123 not 126 eligible events (76 / 22 / 25), the 72 hour information look was not run. N +2, running count about 728,690 (z bar 5.27).
