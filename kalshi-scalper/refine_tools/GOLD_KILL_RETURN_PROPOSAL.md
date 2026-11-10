# Gold L1: kill and return conditions (PROPOSAL, owner approves the numbers before anything is built)
Date 2026-11-10. Registered first: scratch `w_goldkill/REGISTRATION.md` (grid fixed before scoring); results `w_goldkill/out.txt`, script `w_goldkill/run.py`. Read only, descriptive, no pass bar.

## Basis
Gold L1 live, cash basis (scorer.py): 325 settled, **PF 1.30 in dollars (1.46 per contract), net +$53.77**, 18 early sells, sizes 1 to 28 (median 11). Before Oct 20: PF 4.74 (94 trades, +$31.85). Last 3 weeks: **PF 1.13 (231, +$21.92)**. Largest own-peak drawdown ever: $41.31. Now: $24.46 under the $78.22 peak, rolling-60 PF 0.73, rolling-100 0.85. Today gold has no strategy-level kill, only the shared 12 percent stop ($117.51), the window cap and the 25c exit.

## Kill rules replayed on the whole record (fires / first fire / FALSE = next 100 trades net > 0 or PF >= 1 / dollars saved by being flat for the next 60)
| rule | fires | first (trade) | false | saved first fire | last 3 wks |
|---|---|---|---|---|---|
| K1 own-peak drawdown $40 (4% of $979.25 is $39) | 1 | Nov 6 (285), 30 days | 1 of 1 | -$16.85 | 1 |
| K1 drawdown $60 (6%) and $80 (8%) | 0 | never | n/a | n/a | 0 |
| K2 net below -$10, -$20, -$40 after 40 trades | 0 | never | n/a | n/a | 0 |
| K3 rolling-100 PF < 1.0 | 1 | Nov 9 (296), 33 days | 1 of 1 | -$2.60 | 1 |
| K3 rolling-100 PF < 0.8 | 0 | never | n/a | n/a | 0 |
| K4 rolling-60 PF < 0.7 (the tripwire) | 1 | Nov 6 (285) | 1 of 1 | -$16.85 | 1 |
| K5a 2 losses in a row (early sells count) | 3 | Oct 13 (52), 6 days | 2 of 3 | -$20.33 | 2 |
| K5a 3 or 4 in a row | 0 | never | n/a | n/a | 0 |
| K5b 3 early sells in 40 trades | 4 | Oct 27 (172) | 2 of 4 | -$40.36 | 4 |
Negative "saved" means being flat cost money (the next 60 trades were profitable). Every rule that fired on gold fired mostly on a gold that then kept earning; no rule fired and then saved dollars. The rules that never fired are the ones that cannot false-kill and also never had a chance to catch anything: gold has not had a real failure yet, so detection power cannot be measured on gold alone. Power context (W-TRIPSIM): with a true PF of 1.55 the K4 and 100-trade rules false-trip 28 percent by 100 trades and 40 percent by 200; if the true PF is 1.0 they miss by 100 trades 32 percent of the time. An alert is a coin flip.

## Return rules replayed after each simulated kill (chained: skipped trades, half size 30 trades, then full)
- Shadow series is the candle model (GOLDALL rows are in Firestore, not in the report; PF 1.26 over 1,298 windows). Bar B (PF 1.3) is ABOVE the series' own whole-history PF, so a normal gold would stay out under B. Bar A (PF >= 1.0, n >= 60, 7 days, second half >= 1.0) and B differed only for 2 in a row (179 versus 188 dark trades).
- Cool-off 3 versus 7 days: identical results, because the 7 day span in the bar binds first. Cool-off adds nothing.
- K1 $40, K4, K3: the one fire (Nov 6 and Nov 9) is still dark at the end of the data (40 and 29 trades skipped, +$16.85 and +$2.60 of net given up). Not decidable yet: the bar cannot pass before Nov 13.
- K5a 2 in a row: 3 kills, returned Oct 20 and Oct 29, 179 to 188 dark trades, **-$49 to -$54 versus never killing**. K5b: 2 kills, returned once (Nov 4), -$32.
- Half size for 30 trades gave up $3 to $9 after a return (2 in a row), and gained $5.61 after the early sell return (those trades lost).
- Lesson versus OICORE (W-DOLLARKILL, W-KILLCAL2): the same holds. A fixed dollar or short-streak rule false-kills a strategy whose wins are small and losses large (gold wins about 6c, loses about 90c, so 2 losses in a row and 3 early sells in 40 are ordinary). Differences: gold pays about 90c so dollars follow contract count, which grows; a dollar number must scale with the sizing base (percent), not be fixed; and it has 325 trades of history, so a wide drawdown line sits clear of normal ($41 max).

## Proposed numbers (nothing built)
- **Kill (hard, latch, owner approves return):** K1 own-peak drawdown of 6 percent of the sizing base ($58.75 at $979.25; scales with the base), measured on cash dollars with early sells counted as losses, from the later of the last re-arm and the reviewedAt date. Plus K2: net below -$20 after 40 trades since re-arm. Neither fired on the record; the first sits 1.4 times above the worst drawdown seen and half of the shared 12 percent stop.
- **Alert only, no latch:** K4 rolling-60 PF under 0.7 and K3 rolling-100 under 1.0 (both would fire today or within days; both false in the replay), and 3 early sells in 40.
- **Return:** no cool-off beyond the 7 day shadow window; shadow bar A (cash PF per contract >= 1.0 over n >= 60 and >= 7 days, second half >= 1.0, from the kill time); owner approves; re-entry at half size for 30 trades, then full; rules re-armed fresh.
- Read at 100 trades after any change and whenever a rule fires. Expected frequency: about 0 fires per 300 trades at these lines on this record; they are a backstop, not a detector of a slow decay (that stays the weekly review).

## How it would be coded (draft)
- Option 1, slot-style latch: reuse the `killCheck` pattern in `functions/kalshiSlotLib.js` (sticky over every prefix, `reviewedAt` re-arms, latch only switches OFF) as a new `goldKillCheck(orders, latch, base)`, with the latch document map in the existing `kalshiSlotControl/killed` (key `L1GOLD`) written where the settle is recorded (`functions/kalshiSlotStoreLib.js`). `runL1Tick` (`functions/kalshiLiveLib.js` line 842) skips only KXGOLD15M candidates when it reads killed. The exit watch still sells open gold.
- Option 2, check in `runL1Tick` only: compute the drawdown from `recentList` after `botRisk` (line 885); but the tick reads 24 hours of orders, so a 40 trade net or a peak since re-arm needs a stored running peak, a new write on every settle. More code in the hot path.
- Tests to add: `test/kalshiGoldKillGates.test.js` (drawdown, net, early sells as losses, sticky, reviewedAt re-arm, base scaling, exit watch unaffected, fail closed on an unreadable latch); update `test/kalshiL1Gates.test.js` (gold candidate removed when killed) and `test/siteFreshnessGates.test.js` plus the Bot page rules text (SF). Must not change: `test/fixtures/offEquivalence.json` (SW0) and `offEquivalenceIndex.json` (SI0): with the rule never tripping and no latch document, gold must make the same reads, writes and orders (a new read of `kalshiSlotControl` in `runL1Tick` WOULD change the fixture, so Option 1 must reuse a read already made or the latch read must be added in a way that is proven byte-identical; this is the main cost of Option 1).
- Needs `bash functions/deploy-sizing.sh`. Nothing is built until the owner approves the numbers.

## The owner chooses
A. (Recommended) Hard kill K1 6 percent of base plus K2 -$20 after 40, alerts only for the rest, return by shadow bar A plus owner approval plus half size for 30 trades. Backstop that has never false-killed gold; honest that it is not an early detector.
B. Alert only, no new hard kill (the 12 percent stop stays the only one). No false kills, no new code risk, and a real failure costs up to $117.51 before it stops.
C. Tighter hard kill (K1 $40 or 2 in a row). Would have fired on gold's normal variance (false in 1 of 1, and 2 of 3), and cost $17 to $54 of profit in the replay.
