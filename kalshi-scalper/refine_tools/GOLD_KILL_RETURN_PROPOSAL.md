HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Gold L1: kill and return conditions (PROPOSAL, owner approves the numbers before anything is built)
Date 2026-11-10. Registered first: scratch `w_goldkill/REGISTRATION.md` (grid fixed before scoring); results `w_goldkill/out.txt`, script `w_goldkill/run.py`. Read only, descriptive, no pass bar.

## Basis
[live figure removed, ask Main] [live figure removed, ask Main]

## Kill rules replayed on the whole record (fires / first fire / FALSE = next 100 trades net > 0 or PF >= 1 / dollars saved by being flat for the next 60)
| rule | [live figure removed, ask Main] |
|---|---|---|---|---|---|
| K1 own-peak drawdown $40 (4% of [live figure removed, ask Main] is $39) | [live figure removed, ask Main] |
| K1 drawdown $60 (6%) and $80 (8%) | [live figure removed, ask Main] |
| K2 net below -$10, -$20, -$40 after 40 trades | [live figure removed, ask Main] |
| K3 rolling-100 PF < 1.0 | [live figure removed, ask Main] |
| K3 rolling-100 PF < 0.8 | [live figure removed, ask Main] |
| K4 rolling-60 PF < 0.7 (the tripwire) | [live figure removed, ask Main] |
| K5a 2 losses in a row (early sells count) | [live figure removed, ask Main] |
| K5a 3 or 4 in a row | 0 | never | n/a | n/a | 0 |
| K5b 3 early sells in 40 trades | [live figure removed, ask Main] |
[live figure removed, ask Main] Every rule that fired on gold fired mostly on a gold that then kept earning; no rule fired and then saved dollars. The rules that never fired are the ones that cannot false-kill and also never had a chance to catch anything: gold has not had a real failure yet, so detection power cannot be measured on gold alone. [live figure removed, ask Main] An alert is a coin flip.

## Return rules replayed after each simulated kill (chained: [live figure removed, ask Main]
- Shadow series is the candle model (GOLDALL rows are in Firestore, not in the report; [live figure removed, ask Main]
- Cool-off 3 versus 7 days: identical results, because the 7 day span in the bar binds first. Cool-off adds nothing.
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main] [live figure removed, ask Main]

## Proposed numbers (nothing built)
- [live figure removed, ask Main] [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main] [live figure removed, ask Main]

## How it would be coded (draft)
- [live figure removed, ask Main] `runL1Tick` (`functions/kalshiLiveLib.js` line 842) skips only KXGOLD15M candidates when it reads killed. The exit watch still sells open gold.
- [live figure removed, ask Main] More code in the hot path.
- [live figure removed, ask Main]
- Needs `bash functions/deploy-sizing.sh`. Nothing is built until the owner approves the numbers.

## The owner chooses
A. [live figure removed, ask Main] Backstop that has never false-killed gold; honest that it is not an early detector. B. Alert only, no new hard kill (the 12 percent stop stays the only one). No false kills, no new code risk, and a real failure costs up to $117.51 before it stops. C. Tighter hard kill (K1 $40 or 2 in a row). [live figure removed, ask Main]

Dated line Nov 13, 2026 (Main request, text only): refresh needed against the gold latch trip (rule 2, 2026-11-12T19:09Z, gold off), the GOLDOFF shadow that began 2026-11-12T18:31Z, the rotation lane (docs/ROTATION_LANE.md on main, v1.3 per Main) with its guard of at least 10 losses for an 88c or higher favourite, and the CFRTI-K probation seat. The older text above describes the state before these; the Monday rotation template (MONDAY_ROTATION_TEMPLATE.md, UPDATE Nov 13 block) carries the current structure.
