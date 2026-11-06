# RV1 result (run 2026-11-06, development only): NOT_ENOUGH_DATA

Registration `RV1_REGISTRATION.md`; code `src/scalper/rv_perps.py`; output `workers/RV_output.txt`.
Stock-perp relative value (Tech 100 vs member basket, SPY/QQQ vs index, six sector pairs): the 10 equity-class perps in the development window (2026-10-21 to 10-31) have **0 valid quotes** (status inactive, bid 0); they first quote on 2026-11-05T18:39Z, all inside the holdout (US Central: 2026-11-05 12:39). **0 development trades; nothing scored.** Matches the prediction.
Enough data: the single-stock quotes need about 3 days of warm-up plus about 8 development days at the 4 a day cadence (nine spreads at about 1.4 trades a day each, from RV2's rate), so about **2026-11-20** for a rerun with a new frozen cut (the cut moves, so then these dates become development). Single names are thin, so the quoted spread may disqualify some on cost then. N +2.
