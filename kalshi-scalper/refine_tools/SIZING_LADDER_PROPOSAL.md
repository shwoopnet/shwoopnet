# Sizing ladder proposal (2026-11-10, a proposal only: no rule, cap or Charter text changed by this file)
Owner: "a little more than 1 contract per trade ... we'll never make significant profits at 1". Registration and script: scratchpad w_ladderprop (REGISTRATION.md, an.py).

## What sizing can and cannot do
Sizing changes the dollars at risk and the dollars won or lost. It does not change the edge (cash PF). Gold is PF 1.46 whole record (1.31 last 28 days); OICORE PF 1.16 on 92 fills (the dash quotes 1.11 to 1.32 by window). At PF 1.2 to 1.5 even 5 to 15 contracts is small money, and the dollar expectation can be negative inside the interval: every "expected $/week" below has a 90 percent range that includes losses for the 28 day gold read and for OICORE at every size.
Size did not hurt fills (W-SIZESLIP: slip, fill rate and partials flat across sizes; gold 3 way permutation p 0.64). A bigger size does hurt one way: the loss is bigger. Gold's only evidence that bigger orders do worse (add-on orders 1.64c vs 2.75c) is p 0.67, noise.

## Evidence basis (cash recompute, scorer.py rows(): avgFill, avgFee, realised exit limit)
Gold since Oct 7: 325 fills, 67 a week, +2.13c per contract (mean of orders), 90 percent CI [+0.26, +3.92]; last 28 days +1.60c [-0.67, +3.64]. Contract weighted +1.55c; realised +$53.77 in 34 days = $11 a week at an average 10.7 contracts. Losses: early sell 0.73 to 0.75 per contract (18), full settled loss 0.91 (2). Worst rolling 24h observed: 2.68 per contract summed.
OICORE: 92 fills, 58 a week, +1.62c (mean of orders) CI [-4.05, +7.77]; contract weighted +2.86c (about the +3.1c quoted); realised +$24.47 in 11 days at 9.3 contracts. Median price paid 0.074, losing orders average 0.115, worst 0.48 plus fee (-$5.49 at 12). Worst rolling 24h observed: 2.27 per contract summed.

## Ladder (expected $ a week = mean c per contract x contracts x fills a week; CI is the 5000 resample bootstrap on per-order results)
| Strategy / stage | Contracts | $ per order cap | Worst loss per order | Worst day (observed 24h x size) | Expected $/week (90% CI) whole record | same, gold last 28d |
|---|---|---|---|---|---|---|
| Gold incubator (a new gold variant, slot) | 3 | 2.9 | 2.8 settled, 2.2 early sell | 8.0 | +4.3 [+0.5, +7.9] | +3.2 [-1.3, +7.3] |
| Gold early live | 8 | 7.5 | 7.4 / 6.0 | 21.4 | +11.5 [+1.4, +21.1] | +8.6 [-3.6, +19.6] |
| Gold proven live (today: balance sized, 15 to 18) | 16 | 14.9 | 14.9 / 12.0 | 42.9 | +22.9 [+2.8, +42.1] | +17.2 [-7.2, +39.1] |
| OICORE incubator (after a re-arm) | 3 | 1.5 (worst 0.48 each) | 1.4 | 6.8 | +2.8 [-7.1, +13.6] | n/a |
| OICORE early live | 5 | 2.4 | 2.4 | 11.4 | +4.7 [-11.8, +22.7] | n/a |
| OICORE proven (live now, steps 10, 12) | 10 | 4.8 | 4.8 (observed -5.00) | 22.7 | +9.5 [-23.7, +45.4] | n/a |
| OICORE next steps 15 / 20 / 30 | 15 / 20 / 30 | 7.2 / 9.6 / cut to about 20 by the $9.79 cap at a 0.48 price | 7.2 / 9.6 / 14.4 | 34 / 45 / 68 | +14 / +19 / +28 (CIs [-35, +68], [-47, +91], [-71, +136]) | n/a |
Worst day is the worst 24h seen so far scaled by size, an observation and not a bound; the hard bounds are below.

## Caps (base $979.25) and which steps need a Charter change
Charter slot caps: $9.79 per order, $19.59 per window and per day, $58.76 lifetime; shared 12 percent stop $117.51 and window cap 5.5 percent $53.86 (gold alone could place 57 contracts, the ceiling is 50).
- Inside the Charter, no change: gold slot incubator 3 and early 8 (8 x 0.93 = $7.9 under $9.79; two full losses $15 under the $19.59 day cap), OICORE 3, 5, 10, 12, 15 (price 0.48 x 15 = $7.2 + fee). The OICORE ladder daily cap (max of $19.59 and 2.5c per contract size, at most 6 percent of base) is already coded and already above the Charter 2 percent day cap: 25 at 10, 30 at 12.
- Owner only, Charter change: any slot strategy above 10 contracts of a 0.93 gold-priced contract (per order $9.79); OICORE 20 or 30 at high prices (per order cap binds, cuts size); a slot day cap above $19.59 for gold sizes (16 contracts, two full losses is $30); OICORE 20 and 30 need minBase 1030 and 1350, so they wait for the balance to grow anyway, not a rule edit.
- Gold L1 itself is not under the slot Charter: today's 15 to 18 comes from balance / $43 plus an add-on capped at 25 percent of base, ceiling 50.

## Step up evidence (reference: the coded OICORE ladder 20 fills and 7 days at the step, win rate 0.20 or more, net 1c a contract or more, PF 1.3 or more, drawdown under 3c a contract)
- Incubator to early live (any strategy): 40 cash fills and 14 days, cash PF 1.3 or more, net of at least +1c a contract, no kill rule hit, owner approves. Honest limit: at 58 fills a week, 40 fills cannot separate +2c from 0 (the OICORE interval at 92 fills is [-4, +8]); this step is cheap because the dollars are small, not because it is proven.
- Early live to proven: 100 cash fills in 3 windows, PF 1.3 or more in at least 2 of 3, lower bound of the c per contract above -1c; the 5 to 8 contract step is where losses start to be noticed, so the owner signs.
- Gold has no ladder today. It uses the balance (one contract per $43 of base, 2 percent), a review that steps the cap up at most every 3 days and down at once, an add-on of at most 25 percent of the base count, the 12 percent stop and the 5.5 percent window cap. Proposal: no new gold ladder for the proven market; use stage sizes only for a new gold variant.
## Step down (automatic, coded)
OICORE (existing): back one step (two with a win-rate hit) if drawdown from the step peak reaches 3c a contract x size, or the last 40 have win rate under 0.15 or net under -2c x size; stop at the lesser of 5c x size, 12 percent of base, $150 from its own peak; daily loss cap above. Proposed for the incubator and early stages: one step down on the first kill rule, latch at -$10 demote, -$20 stop (W-DOLLARKILL sensitivity). Gold: W-SUPPLY2 tested half size after an early sell and half size while rolling PF under 1; neither improved net over drawdown in both halves (1.37 and 1.49 vs 1.47 live), so no new gold step-down is proposed beyond the existing down-at-once review and the 12 percent stop.

## Bottom line
At 5 to 8 contracts gold earns about $9 to $11 a week with a range that can reach about -$4 (last 28 days); OICORE at 10 earns about $10 to $16 a week against a possible -$24. Neither is significant money. The ladder is a risk dial, not a profit source: raising size 3x raises both the expected dollars and the worst day 3x. A real raise in profit needs a higher PF, not a bigger step.
