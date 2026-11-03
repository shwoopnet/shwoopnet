# BOXOFF1 registration (2026-11-03)

Idea: information-lag nowcast of weekend box office. Reference: Friday gross (incl. Thursday previews) from Box Office Mojo / The Numbers, public Saturday morning. Look: Saturday 14:00 UTC. Multiplier distribution (weekend / Friday) estimated only on the first two thirds of weekends (before the frozen cut 2026-10-03T16:00Z, never fetched or joined). Probability per bracket from the multiplier distribution. Trade: cheap side only (ask 3c to 30c, model probability >= 3x ask), held to settlement, max 2 per event, C = 10, fee 7% x C x p x (1-p) rounded up. Event-level cluster. Numeric prediction: win rate at least 2x the mean ask on the cheap side. Kill rules: FALSIFIED if mean net after fees is not above 0 in both halves or PF under 1.5; NOT_ENOUGH_DATA under 150 trades with months to go. N: +2 per rule, +k = +2.

## Step 1 census (run live 2026-11-03, public series list, 2605 Entertainment series, plus events for the nearest candidates)
Gate: at least about 25 settled weekend events before the cut with a keyless dated reference, else NOT_RUNNABLE with a forward plan, no scoring.
Prediction (stated before the census): NOT_RUNNABLE, about 90%.
