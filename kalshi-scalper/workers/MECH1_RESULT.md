# MECH1 result: who is on the other side of the Bitcoin open interest core (research only)

Registration `workers/MECH1_REGISTRATION.md` (commit 839d329, amendment 3ecdcaa) was pushed before any tape was joined to an outcome. Code `src/scalper/mech1.py`: `describe` reads no outcome, and `score` ran once. The data is the public tape for (close - 360, close - 180] of every one of the 555 firing windows (222 discovery, 333 validation): 6.4 million trades and 0 empty tapes. Sources: `/historical/trades` 145 windows, `/markets/trades` 427, the MAKER4 cache 41. Windows run Aug 6 to Oct 27; nothing closing on or after 2026-10-28 was read.

**Deviation from amendment 1:** the run had to end before the 90 minute control wait. The controls used are therefore the seeded random prefix that had downloaded: **58 of 555** (23 discovery, 35 validation), matched on stage and 5c bucket. Comparisons against controls (P1 to P4) are thin. The firing-window figures and the scored look use firing windows only and are complete. `python -m scalper.mech1 fetch K 2` resumes the controls, and `describe` re-prints the tables without reading any outcome.

## Verdict on the hypothesis: NOT HELD

The tape does not show "late favourite buyers OPENING new contracts by taking the favourite ask". Neither P1 nor P5 held.

## The counterparty, as numbers

| measure | FIRE disc | CTRL disc (23) | FIRE val | CTRL val (35) |
|---|---|---|---|---|
| favourite taker share, median | **0.521** | 0.533 | **0.520** | 0.502 |
| volume-weighted favourite taker share | 0.515 | 0.508 | 0.517 | 0.510 |
| volume in the 3 minutes, median | 492,922 | 331,769 | 615,386 | 461,331 |
| trades, median | 6,906 | 5,173 | 9,309 | 7,696 |
| print size, median | 11.8 | 12.2 | 10.0 | 10.0 |
| share of volume in the 10 largest prints | 5.7% | 6.2% | 4.6% | 5.0% |
| share in prints of 1,000+ | 17.9% | 8.2% | 19.8% | 18.0% |
| open ratio doi / volume | **0.240** | 0.080 | **0.204** | 0.081 |
| favourite mid rose (-360 to -180) | 79.7% | 82.6% | 72.4% | 71.4% |
| mean favourite mid rise | +0.116 | +0.171 | +0.090 | +0.138 |
| favourite takers' VWAP minus favourite mid at -180 | -0.037 | -0.075 | -0.016 | -0.053 |

- In firing windows takers split about **52 / 48** between the favourite and the cheap side. That is barely one-sided and no more than the controls (difference -1.2 points in discovery, +1.8 in validation).
- **corr(doi, favourite net taker flow) = -0.27 (disc), -0.23 (val).** The bigger the open interest jump, the more of the taker flow bought the CHEAP side. corr(doi, volume) is 0.51 / 0.52.
- **Descriptive, added after registration, no outcome:**
  - **Favourite share by print size.** Prints of 1,000+ lean to the favourite (favourite share 0.518 / 0.550). Prints under 100 lean to the cheap side (0.474 / 0.462).
  - **By minute.** Favourite share is 0.505 / 0.507 in the first minute and 0.527 / 0.531 in the last minute.
- **Not whales.** No firing window had its 10 largest prints above 50% of volume (0 of 222, 0 of 333).
- **Price.** The favourite rose in most windows, but by LESS in firing windows than in controls, as FALS4 saw. There was no bigger-than-usual push.

**What this means.** The contracts created in the jump come from two flows of about equal size:
- cheap-side takers, mostly small, lifting the cheap ask against resting favourite bids (makers buying the favourite);
- favourite takers, more of them large.

The favourite is the side that loses on average, and it is bought both ways. The tape cannot tell an opening trade from a closing one. The open ratio is the only opening measure, and it is per window only: about one in four or five contracts traded was new, roughly 3 times the controls.

## Predictions

- **P1** (firing share at least 5 points above controls, both stages): **failed** (-1.2 / +1.8, thin controls).
- **P2** (top 10 prints below 30% of volume, print median within 2x of controls): **held** (5.7% / 4.6%; 11.8 vs 12.2, 10.0 vs 10.0).
- **P3** (favourite rose in at least 65% of firing windows, mean rise not larger than controls): **held** (79.7% / 72.4%; +0.116 vs +0.171, +0.090 vs +0.138).
- **P4** (open ratio at least 2x controls): **held** (3.0x / 2.5x; close to mechanical).
- **P5** (the scored look, below): **failed**.

## The one scored look (N +2)

Firing windows split at each stage's median favourite taker share. Core trade: cheap side, -120 ask, C = 10, held to settlement.

| | n | PF | PF fees x1.2 | win | mean fill | net $ | day z |
|---|---|---|---|---|---|---|---|
| disc HIGH (share > 0.521) | 111 | 1.32 | 1.30 | 21.6% | 0.176 | 36.44 | 1.07 |
| disc LOW | 111 | **3.85** | 3.81 | 36.9% | 0.181 | 201.04 | 4.75 |
| val HIGH (share > 0.520) | 166 | 1.87 | 1.84 | 25.3% | 0.172 | 122.11 | 3.03 |
| val LOW | 167 | 1.83 | 1.80 | 29.9% | 0.211 | 132.85 | 3.02 |

HIGH was not above LOW in either stage: discovery went the opposite way and validation was equal. The edge does not concentrate where favourite takers dominate. The discovery LOW half is not a new rule (validation shows no split), and nothing here is promoted.

## For the lead

- The counterparty line for `REF_GEN6_OICORE` should not say "late favourite takers". In jump windows the cheap side is bought by many small takers. The favourite is bought by larger takers and by resting bids, roughly half each. Favourite holders as a group are the losers, and no single taker type carries the edge. In the RULES sense the counterparty is still **unnamed**.
- Finish the controls before quoting P1 (58 of 555 are in).

## Tries

The scored look counts as 2 (HIGH, LOW); descriptive tables count 0. Running count about 592,030 + 2 = **about 592,032**.
