# RO1 registration: risk-off pair, gold after a down US Tech 100 interval (2026-11-06, before scoring). Shared rules: workers/LEAD_COMMON.md

Counterparty: slower gold perp book and its makers after a risk-off move in equities (gold as the haven bid). Honest alternative: gold and Tech 100 are unrelated at this horizon.
Definition (fixed): consecutive samples (t0, t1), gap 2 to 8 h; if the Tech 100 mid log return over it is <= -0.5%, LONG gold from t1 (at the ask) to the next sample t2 with gap 2 to 8 h (exit at the bid). Control: SHORT gold on the same triggers. One trade per trigger.
Prediction: NOT_ENOUGH_DATA (certain: 11 dates, expected under 20 triggers). Information: gross about 0 to 10 bp, cost about 25 to 30 bp.
Kill: LEAD only under the common rules.
