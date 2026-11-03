# MAKERMID1 result (run once on 2026-11-03, DEV only; registration `workers/MAKERMID1_REGISTRATION.md`, commit af0ccdd, pushed before any mid-band row was scored)

Code `src/scalper/makermid1.py` (imports makertail1's loaders and queue model; makertail1.py unchanged), `src/scalper/makermid1_fwd.py`, tests `tests/test_makermid1.py`, `tests/test_fwd_makermid1.py` (synthetic, pass). Raw output `data/makermid1_result.txt` (not committed). Maker fee 0. Bids 16c to 40c, cheap side only; no favourite-side result was computed (the taker column is limited to asks at or below 40c).

**Verdict by the registered code: NOT_ENOUGH_DATA for both rules (MR1 84 pessimistic fills, MR2 60; bar 150). The sign is already against both: pessimistic net per resting order is negative in DEV and in both halves, PF under 1, so no pass is possible without a reversal.** Holdout not opened. Only 87 orders on 45 closes (predicted 100 to 220): most strikes in the recorder's nearest 7 are far from 16c to 40c at 25 minutes.

DEV closes 2026-10-29 to 2026-11-01:

| | fill rate | win vs mean price | net per resting order | PF |
|---|---|---|---|---|
| MR1 pessimistic (verdict bound) | 96.6% | 22.6% vs 26.5% | -3.78c | 0.81 |
| MR1 optimistic | 98.9% | 24.4% vs 26.5% | -2.05c | 0.90 |
| MR2 (cancel on a 2c bid drop) pessimistic | 69.0% | 20.0% vs 26.3% | -4.36c | 0.70 |
| MR2 optimistic | 86.2% | 24.0% vs 26.7% | -2.36c | 0.86 |

Halves (pessimistic): MR1 H1 -4.16c (PF 0.79), H2 -3.25c (0.83); MR2 H1 -4.22c (0.68), H2 -4.56c (0.72). The guard did NOT help: it cancels the orders that would have been filled by falling prices, but the survivors still lose, and those that would have recovered are dropped; net per order is worse than MR1 (prediction was 0 to +1c better). Fill rate was far above my prediction (70% central; got 97%): the mid-band queue is cleared almost always, so the queue is not the constraint here either.

Win rate against price paid: every pessimistic cell is at or below the price except where noted: bid 16c to 25c wins 20.5% at 20.0% (+0.51c per order, PF 1.03, 41 orders; optimistic +2.44c, PF 1.17), 26c to 33c wins 25.0% at 29.5% (-4.31c, PF 0.80), 34c to 40c wins 23.5% at 36.8% (-13.24c, PF 0.53, 17 orders). The only non-negative cell is the cheapest third under MR1 (one of three buckets, 41 orders, day z 0.09: noise); it vanishes under MR2 (-2.61c). The loss grows with price: adverse selection scales with the bid.

Side split (pessimistic, readout): YES -2.51c (PF 0.87, 43 orders), NO -5.02c (PF 0.75, 44). The MAKERTAIL1 hint that NO tails beat YES tails does NOT carry to the mid band (NO is worse here). Both sides negative.

Taker comparison (same orders, ask at most 40c, size 10+, fee 7% x 10 x p x (1-p) rounded up): 77 orders, win 24.7% at mean ask 26.3%, -3.01c per order, PF 0.85 (x1.2: -3.28c, PF 0.84). The taker is less bad than the pessimistic resting bid again (-3.78c): resting is filled when the price falls, and that costs more than the spread and fee saved.

Fills per day: MR1 21.0 (7 days to 150), MR2 15.0 (10 days). Day-clustered z is negative (-11.3 and -4.8) on 4 days; with so few days it is not a reliable magnitude, but the sign is unambiguous. Names for the forward set are unchanged: closes from 2026-11-03 16:00Z (12 orders on 5 closes so far), read once on 2026-11-12 or at 150 pessimistic forward fills, whichever is later, via `python -m scalper.makermid1 forward`.

Capped probe spec: not warranted (pessimistic net negative in both halves for both rules).

Tries: 2 rules, N +4.
