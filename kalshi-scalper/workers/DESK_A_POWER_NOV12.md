# Idea Desk A: power analysis of the queue, and which cards can reach a verdict (Nov 12, 2026)

Asked for by the Chief of Staff (owner directive): spend scarce Kalshi reads only on tests that can reach a verdict; retire the ones that cannot. No Kalshi read was made for this file. Scripts: `workers/desk_a_held/power.py`, `power2.py`. Desk B's cards are covered in its own file (`IDEA_DESK_B_POWER.md` on `claude/idea-desk-b`); the two tables agree where they overlap (this one uses z 5.34, that one 5.3). **Recommendations only: the queue is Main's and every retire is Main's call.**

## 1. What the bars cost in sample size

A bet bought at price p, held to settlement, fee 0.07 x p x (1 - p). "Needed" = INDEPENDENT bets for a TRUE cash profit factor of 1.5 to reach the z score.

| Price paid | Win rate at a true PF of 1.5 | Needed for deflated z 5.34 (even chance) | Same, 80% chance | Needed for lenient z 4.39 | Plain z 2 (no deflation) | True PF 1.3, z 5.34 |
|---|---|---|---|---|---|---|
| 0.10 | 15.1% | 1,800 | 2,412 | 1,217 | 252 | 4,335 |
| 0.20 | 28.7% | 1,027 | 1,375 | 694 | 144 | 2,472 |
| 0.35 | 46.4% | 737 | 987 | 498 | 103 | 1,775 |
| 0.50 | 61.7% | 685 | 917 | 463 | 96 | 1,649 |
| 0.70 | 79.0% | 839 | 1,123 | 567 | 117 | 2,020 |
| 0.92 | 94.9% | 2,470 | 3,309 | 1,669 | 346 | 5,948 |

How often each screen used in this repo passes, by what is TRUE (simulated, independent bets):

| Screen | Price | Passes when the truth is PF 1.0 (no edge) | PF 0.9 | Passes when the truth is PF 1.5 |
|---|---|---|---|---|
| PF 1.3 or better in both halves, 40 a half | 0.20 / 0.50 / 0.92 | 4% / 3% / 18% | 2% / 1% / 12% | 39% / 43% / 45% |
| PF 1.5 on one sample of 40 | 0.20 / 0.50 / 0.92 | 12% / 11% / 41% | 7% / 6% / 35% | 48% / 53% / 67% |
| PF 1.5 on one sample of 100 | 0.20 / 0.50 / 0.92 | 4% / 3% / 23% | 1% / 1% / 16% | 51% / 52% / 59% |
| PF 1.5 on one sample of 300 | 0.20 / 0.50 / 0.92 | 0.2% / 0% / 6% | 0% / 0% / 2% | 52% / 48% / 53% |
| Proven bar: PF 1.3 over 100 fills, 2 of 3 windows | 0.20 / 0.50 / 0.92 | 11% / 7% / 15% | 5% / 2% / 9% | 67% / 67% / 45% |
| Shadow gate: PF 1.3 over 150, second half 1.2 | 0.20 / 0.50 / 0.92 | 7% / 4% / 16% | 2% / 1% / 9% | 69% / 73% / 54% |

How often a card is wrongly FALSIFIED (development PF under 1.0) when it is in fact good:

| Sample | Price | Truth PF 1.0 | Truth PF 1.2 | Truth PF 1.5 |
|---|---|---|---|---|
| 40 | 0.20 / 0.50 | 53% / 47% | 33% / 26% | 16% / 9% |
| 100 | 0.20 / 0.50 | 56% / 48% | 26% / 17% | 5% / 2% |
| 300 | 0.20 / 0.50 | 51% / 52% | 10% / 6% | 0% / 0% |

Four things follow.

1. **The research bar needs about 700 to 2,500 independent bets even when the edge is real.** Independent means clusters (days, print days, games, election dates), not markets. Only families with roughly 300 or more clusters a year can reach PASS inside a year or two; everything else can only be falsified or carried as a lead.
2. **Favourite-priced screens are close to useless at small n.** At 92c a zero-edge rule shows PF 1.5 on 40 trades 41% of the time and passes the proven bar 15% of the time. Any screen on favourites needs n in the hundreds before it means anything. (This is the arithmetic behind the favourite-late record.)
3. **A FAIL at n 40 is wrong about one time in ten for a truly good rule** (9% to 16%); at n 100 it is 2% to 5%; at n 300 it does not happen. So the floor for calling FALSIFIED should be about 100 trades, and a FAIL under that should be worded "no evidence at n = x", as Refinement's own audit already suggests for two of its six.
4. **The proven bar and the research bar are different instruments.** The proven bar (PF 1.3 over 100 fills, 2 of 3 windows) lets a zero-edge rule through 7% to 15% of the time. That is acceptable for a capped probe that then keeps being measured; it is not evidence of an edge. Reports should say which bar a "pass" cleared.

## 2. The queue, row by row

"Clusters" = independent units. "Can it PASS" is against the research bar at 80% power. Reads are Kalshi requests still owed.

| # | Queue item | Clusters held | Clusters a year forward | Needed | Can it reach PASS? | Can it be FALSIFIED on what is held? | Reads owed | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 1 | Approval and generic ballot calibration | about 130 events with quotes (daily 65, ballot 48, others 19), same-week correlated; no cell has 30 a third | about 365 daily plus 52 weekly, but one story a week | about 920 at mid price (300 if the truth were PF 2) | Not in under 2 to 3 years | Only the cheap-YES cell (already ruled out) | about 1,680 for the unpulled history | **Do not spend the 1,680 reads at today's rate (67 hours of the whole shared budget).** It would add about 400 weekly-correlated events: enough to falsify, not to pass. Forward log from the politics recorder costs nothing |
| 2 | Sports singles calibration | 3,266 games; moneyline and totals have large n and are flat (FAIL stands) | thousands | 2,400 for a 10c cell | **Yes. The only queue item with the clusters to reach either verdict** | Yes | spread markets of the unpulled games (hundreds to low thousands) | **Best use of reads in the queue**, but only for the SPREAD cheap cell, registered as ONE cell with the cut fixed first. The lead itself is weak: a zero-edge 10c cell shows PF 1.45 in both thirds at n 56 only 2% of the time, but it was the best of many cells, so by chance about one such cell is expected per 50 cells looked at |
| 3 | Economics: overshoot fade plus official components | about 70 print days | about 36 | about 920 (340 for a time exit at a true 2c) | No (decades at PF 1.5) | The fade: yes, in one run. Components: no (12 a year) | about 70 for the fade's count step | Fade: ONE falsification run through the pull route when it exists, not from today's budget. **Official components: retire as a PF test** (12 events a year; Desk B retired the same shape three times) |
| 4 | Politics scheduled events and nothing-happens | 58 and 26 events, 7 a third scored | a few a month | about 920; nothing-happens buys NO at 60c to 88c, where 1,100 to 2,500 are needed | No | No (n 7 a third says nothing either way) | 0 | **Forward log only. Spend no reads.** State plainly in the queue that this row cannot produce a verdict before 2028 |
| 5 | Politics-leg combos | n/a | n/a | n/a | No: combos carry no posted asks, so nothing can be priced from public data | No | 0 | Simulation only, as V2 found. Spend no reads |
| 6 | Clinical 90 day | tens of settled events | tens | about 920 | No | No | census done | Forward log only; any further read is description |
| 7 | Weather day-end rounding (WXDAYEND) | 20 of 40 city-days read, 0 qualify; the book sits at 0.99 bid, 1.00 ask | 5,000 city-days | the bar is a count: 3 of 40 | Yes in principle (a count) | Nearly: if the true rate were 5%, seeing 0 of 20 has a 36% chance, and 3 or more in the other 20 has an 8% chance; at 10% it is 12% and 32% | 22 (job file written, section 3 of the jobs note) | Finish it, but **last**: it is cheap, and it is the only way to close the card under its own rule. Not from today's budget |
| 8 | Mentions persistence (card 84) | 65 calls scored | hundreds | about 990 at 35c | The family could (hundreds of calls a year); this rule cannot | **Yes, and it is. Wrong-fail chance under 1 in 10,000** (train PF 0.58 on 36 and validate 0.36 on 44 are both far below what a PF 1.5 rule produces) | 0 | FALSIFIED stands. No more reads on this rule |
| 9 | Attention signals (Wikipedia, POL-n1) | 10 markets; I expect 30 to 80 spikes | about the same again a year | about 920; the card's own screen needs 80 | No | No | about 15, plus Wikipedia | **Retire as a PF test.** If Main wants the count for the record, it needs no price read: market open dates and pageviews only |
| 10 | News fade, three delays | undefined universe; my guess 50 to 150 shocks | similar | about 920, and three tries | No | One delay could be, at n near 100 | unknown | Do not start until the universe file exists and counts at least 100 events; otherwise it is three tries that can only return "not enough data" |

## 3. The two reads that are waiting

**MMSIM1 held-out, about Nov 24.** Development (re-derived, `DESK_A_VERIFY_NOV12.md`): 168 quotable hourly events, mean +5.07c an event, standard deviation 41.6c an event, PF 1.41. That is z 1.58 by event and 2.35 by day (10 days). At the same mean and spread:

- the deflated bar (z 5.34) needs about **1,900 events, about 80 days** of the hourly ladder;
- the held-out block to Nov 24 is about 400 events, where a TRUE edge of this size is expected to show z about 2.4;
- development PF is already under 1.5.

So **the Nov 24 read cannot be a research-bar PASS whatever it shows.** It is a fair falsification test, though: if the development figure is the truth, 400 events show a negative mean only about 1 time in 100. Decide before the read what each outcome will be called. My suggestion: held-out PF 1.3 or better with a positive day-clustered mean = "lead confirmed, keep recording, read again at 1,900 events (about late January; the book recorder has no stop date)"; PF under 1.0 on 400 events = FALSIFIED (that is a fair n); anything between = "not decided, keep recording". And pin the cutoff constant in `mmsim1.py` first (see the audit).

**CFRTI1-BTC held-out, about Nov 22 at 50 rows.** Development n 36, PF 2.54.

| What is true | Chance the 50 row read shows PF 1.5 or better | Same at 130 rows |
|---|---|---|
| PF 0.9 | 5% | under 1% |
| PF 1.0 (no edge) | 10% | 1% |
| PF 1.2 | 25% | |
| PF 1.5 | 54% | 48% |
| PF 2.0 | 86% | 94% |
| PF 2.5 | 97% | 99.6% |

A 50 row read fails a truly good (PF 1.5) rule almost half the time and passes a zero-edge rule one time in ten, and this rule was picked from several. 36 + 50 = 86 rows reach the deflated z only if the true PF is about 3 or more; at a true PF of 2.5 it takes about 170 rows (80% chance), at 2.0 about 300. Suggestion: read at 50 as registered, call it "lead" or "falsified" only (falsified = PF under 1.0), and name about 170 rows in all as the size for a real verdict. The R6 extension to Nov 20 for Bitcoin and Ethereum is what feeds it; after Nov 20 nothing does, so a decision on extending that recorder for Bitcoin is due before Nov 20.

## 4. Yesterday's FAIL calls: could any be a wrong fail?

| Call | n | Chance of this result if the truth were PF 1.5 | Reading |
|---|---|---|---|
| CRONCLUSTER1, RETAILFRAC1 stage A (V2) | 3.8M and 20M+ trades | n/a (measurements) | Re-derived independently, CONFIRMED (`DESK_A_HELD_DATA_NOV12.md`) |
| Card 84 mentions persistence | 36 and 44 | under 0.01% | Safe FAIL |
| W-SWEEP-EXT1 held-out, three cells PF 0.75 to 0.87 | not stated in the audit | 5% to 8% a cell at n 40, 1% to 3% at n 80; all three together far less | Safe FAIL if each cell had 80 or more held-out rows; ask Refinement for the three n |
| W-POL-APPR1 | no cell with 30 a third | cannot be computed: the bar was never testable | Not a FAIL. UNDERPOWERED, as Refinement's audit says |
| W-CAT-SPORTS1, spread cells | 56 and 57 a third | the registered floor was 60, so it was not tested | Not a FAIL for SPREAD (queue row 2). FAIL stands for moneyline and totals |
| Card 74 WXDAYEND | 20 of 40 | a count bar; see queue row 7 | "0 of 20", not FAIL, until the other 20 are read |
| Politics step 2 | 7 a third | a PF 1.5 rule shows a losing 7 trade third about a quarter of the time | DATA_LIMITED, correctly labelled |
| TIECOND1 (V2) | 13 cells of 300 or more windows; best lower bound 1.96% against 6% | a rate bar on large n | Safe closure; not re-derivable here (V2's tables are not on a branch) |

No call flips to a pass. Three are labelled stronger than their n supports (the same three Refinement's audit names), and one (sports SPREAD) is an untested cell with enough clusters in the world to test properly.

## 5. This desk's own open cards

| Card | Clusters | Data | Can it reach a verdict? | Recommendation |
|---|---|---|---|---|
| 4 ORHARVEST1 | daily (365 a year; 14 cities share weather days) | BLOCKED: the weather recorder holds three morning looks only, nothing near the close | Yes in principle, in about 2 years of days, or sooner as a count | Parked behind MMSIM1 as ruled. Needs a recorder change before any test; not worth a recorder until MMSIM1 reads |
| 5 RACEMAKE1 | 96 windows a day | BLOCKED: the Coin Race series is in no recorder | Yes, quickly, if recorded | Parked behind MMSIM1. If MMSIM1 holds, adding `KXCRYPTOLEAD15M` to a recorder is the cheapest next step in the family |
| 6 RESIL1 | thousands of sweeps | held (R6) | Yes | Held by the family rule (a third FALSIFIED closes order flow for good). Unchanged |
| 9 PERPBIN1 | 24 windows a day on the hourly perp file (about 450 held before Nov 9) | held (`perp-data`, `quote-data`), zero reads | Can be falsified on what is held; the 920 for a pass arrives about mid December | The one card of mine that fits today's rule (held data, no reads). Prior 2%. It needs a protocol and counts one try; I will write the protocol only if Main wants the try spent |
| 11 AUCTION1 | about 80 coupon auctions a year | daily recorder | No (over 10 years at PF 1.5) | **Retire as a PF test**; keep the mid-December descriptive line only if it is free |
| Q2 POL-n1, Q3 ECONFADE | see queue rows 9 and 3 | | | as above |
| P8 MMMAP1 | measurement | R6 done; NC15 from about Nov 15 | Yes (a map, not a PF) | Keep: R6 part done today |

After this, the desk's live list is: MMMAP1 on the non-crypto books (Nov 15), the two parked market-making cards, and RESIL1 on hold. PERPBIN1 waits on Main's word. Everything else of mine is closed or retired.
