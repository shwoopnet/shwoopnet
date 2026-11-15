# CALIB3 hand case for the bucket statistics, written BEFORE the code (Idea Desk A, Nov 15, 2026; card CALIB3_CARD_NOV15.md, CLEAN as a registration by Auditor B at d2912033b)
Scope: the pure per-bucket statistics only (the loader waits for Forensics' extract and the Head's go). Invented rows, no data read.
**Definitions pinned (Auditor B's precision):** for one bucket (one look, one side's 5c price range) and one third: rows (event, ask, won). n = rows; wins; w = wins / n; a = the mean ask; gap g = w - a; fee = the mean per-contract fee at the ask, per-order rounded at 1 contract, ceil(100 x 0.07 x ask x (1 - ask)) / 100 (with the CALIB1 rounding of its 9th decimal); E = the number of distinct events; for event e, s_e = sum over the bucket's rows in e of (won - ask); the event-clustered z = mean over events of s_e / (sample sd over events of s_e / sqrt(E)), None under 2 events or sd 0; **a_e = the event's MEAN ask over its rows in the bucket (one term per event)**; the null for the third: sd_t = sqrt(sum over events of a_e (1 - a_e)) / E_t, P(pass third t) = 1 - Phi((fee_t + 0.02) / sd_t); P(both) = the product over the two thirds. The label "understates" stays: rows in an event are correlated and one sd term per event treats them as one draw.
**Thin-third rule:** under 60 events: "no evidence".
## Invented bucket (YES asks in [0.50, 0.55), one look, one third): two events with two strikes each
| event | strike | ask | won |
|---|---|---|---|
| E1 | A | 0.52 | 1 |
| E1 | B | 0.53 | 0 |
| E2 | A | 0.51 | 1 |
| E2 | B | 0.54 | 1 |
Expected, by hand: n 4, wins 3, w 0.75, a = (0.52 + 0.53 + 0.51 + 0.54) / 4 = 0.525, g = +0.225 (22.5 cents). Fees at 1 contract: 0.52 -> ceil(100 x 0.07 x 0.52 x 0.48 = 1.7472) = 2c; 0.53 -> 1.7437 -> 2c; 0.51 -> 1.7493 -> 2c; 0.54 -> 1.7388 -> 2c: mean fee 0.02. E 2. s_E1 = (1 - 0.52) + (0 - 0.53) = -0.05; s_E2 = (1 - 0.51) + (1 - 0.54) = +0.95. Mean 0.45; deviations -0.5 and +0.5; sample variance (0.25 + 0.25) / 1 = 0.5, sd 0.70711, se = 0.70711 / sqrt(2) = 0.5; z = 0.45 / 0.5 = 0.9. Null: a_E1 = (0.52 + 0.53) / 2 = 0.525, a_E2 = (0.51 + 0.54) / 2 = 0.525; sum a_e (1 - a_e) = 2 x 0.525 x 0.475 = 0.49875; sd_t = sqrt(0.49875) / 2 = 0.35311; threshold = fee + 0.02 = 0.04; 0.04 / 0.35311 = 0.11328; P(pass this third) = 1 - Phi(0.11328) = 0.4549. Thin-third: E 2 < 60: "no evidence".
Edge checks: a single-event bucket gives z None; an event whose s_e all equal gives sd 0 and z None; the bucket edge 0.55 belongs to the next bucket ([0.55, 0.60)), 0.50 to this one, with the 1e-9 slack.
