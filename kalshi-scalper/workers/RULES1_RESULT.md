# RULES1 (RULES1B) result, run once 2026-11-03: all 7 scoreable features FALSIFIED, EXACT NOT_ENOUGH_DATA; fine print is not where the cheap side is mispriced in our favour

Registration `workers/RULES1_REGISTRATION.md` (sha256 `b8476bc719db3493529628d8cdbec66b027b4864ad8acccc5a137717b124d2b5`, commit 0a37811, pushed before `score`). Data `workers/RULES1_RESULT.json`, code `src/scalper/rules1.py`, tests `tests/test_rules1.py`. Cheap side only (ask 3c to 30c); no favourite-side figure computed. Development markets only, frozen thirds untouched. 5,765 entries (one per market, at most 2 per event), 3,535 events, 221 series.

| feature | n | events | win | price | win - price | net per contract [event-cluster 95%] | PF | H1 / H2 net | verdict |
|---|---|---|---|---|---|---|---|---|---|
| STRICT | 1,516 | 874 | 3.0% | 13.5c | -10.5c | -11.29c [-12.27, -10.26] | 0.18 | -12.01 / -11.11 | FALSIFIED |
| INCLUSIVE | 302 | 188 | 11.6% | 17.8c | -6.2c | -7.23c [-10.90, -2.87] | 0.55 | -5.59 / -8.53 | FALSIFIED |
| ROUNDED | 193 | 111 | 4.7% | 11.1c | -6.4c | -7.13c [-10.28, -3.43] | 0.35 | -6.87 / -7.32 | FALSIFIED |
| PRINT | 274 | 163 | 5.5% | 12.0c | -6.5c | -7.30c [-10.09, -4.00] | 0.37 | -6.27 / -8.12 | FALSIFIED |
| FIRSTFINAL | 3,167 | 1,824 | 8.2% | 11.9c | -3.7c | -4.51c [-5.46, -3.47] | 0.59 | -4.56 / -4.43 | FALSIFIED |
| EXACT | 42 | 32 | 0.0% | 9.8c | -9.8c | -10.42c | 0.00 | -13.64 / -7.19 | NOT_ENOUGH_DATA |
| VOID | 276 | 234 | 15.6% | 21.5c | -5.9c | -7.11c [-11.35, -2.66] | 0.62 | -12.25 / -2.72 | FALSIFIED |
| SOURCE | 4,391 | 2,534 | 6.8% | 12.6c | -5.8c | -6.58c [-7.41, -5.76] | 0.45 | -5.43 / -7.67 | FALSIFIED |
| CONTROL (no feature) | 646 | 499 | 12.1% | 13.8c | -1.7c | -2.62c [-4.92, -0.15] | 0.79 | -3.05 / -1.82 | reference |
| all entries | 5,765 | 3,535 | 7.8% | 13.3c | -5.5c | -6.24c [-6.95, -5.51] | 0.50 | -5.47 / -7.01 | reference |

## Reading
The prediction held: every feature negative with an upper bound below zero, no feature positive in either half (0 of 8), none near PF 1.5 (best 0.62). Features did NOT beat the control; they are worse than it. The control (no fine-print feature) is the least bad group at -2.62c and PF 0.79, and its interval touches zero from below ([-4.92, -0.15]), which is calibration, not an edge. STRICT is the worst (win 3.0% against a 13.5c price) and is almost entirely the AAA gas and rain ladders, so it is a family result (gas moves slowly, cheap strikes far from the average almost never hit, and the tie clause is irrelevant at four decimals), not evidence about the word "strictly". INCLUSIVE and VOID have the highest win rates (11.6%, 15.6%) because they sit at higher prices (17.8c, 21.5c: sports counts and tie clauses), and still lose 6 to 7c. PRINT and ROUNDED (the commodity candle families) match the prediction as the nearest to the group mean, not better. VOID's H2 (-2.72c) is the least bad half anywhere, with an interval that includes zero; it is 149 trades and not a lead (H1 -12.25c).

## Caveats
1. Features are series templates, so each is partly a family label (STRICT = AAA gas and rain, FIRSTFINAL = mostly the weather ladders whose rules say "official and final", SOURCE = most of the sample); the pre-registered family-confound note applies and nothing here is a rules-text effect separable from the family. 2. The control is small (646, 53 series, mostly sports and crypto text without these phrases). 3. The event cluster does not remove day or regime correlation (CALIB1 caveat 1). 4. Entry at the quoted ask at fixed looks, no queue or depth. 5. Cheap side only by the owner's rule. 6. The regexes were fixed after reading templates (no outcome); a different wording list is a new registration. 7. Rules text for a series came from two fetched markets; a clause that appears only on some markets of a series would be missed (0 series were unstable on the 8 features).

## Forward plan
None. No LEAD, so no forward recorder. Not worth re-running with other keywords on this sample: the cheap side already loses -6.24c pooled and the rules-text split only reorders where it loses. New series templates can be re-censused (metadata only) in 90 days.

N +16 (8 features x 2; running count about 730,315 if the coordinator's 730,299 stands).
