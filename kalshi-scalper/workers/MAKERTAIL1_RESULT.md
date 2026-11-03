# MAKERTAIL1 result (run once on 2026-11-03, DEV only; registration `workers/MAKERTAIL1_REGISTRATION.md`, commit 49a0fce, pushed before any book row was opened)

Code `src/scalper/makertail1.py`, tests `tests/test_makertail1.py` (synthetic book and tape, pass), raw scorer output `data/makertail1_result.txt` (not committed). Maker fee 0 (KXBTCD `fee_type: quadratic`). The recorder's book files are read from the history of `origin/quote-data` (the branch tip carries only the newest runs); 28 runs, 2026-10-29 to 2026-11-03.

**Verdict by the registered code: NOT_ENOUGH_DATA (143 pessimistic fills in DEV, bar 150).** The sign is already against it: pessimistic net per resting order is negative in DEV and in both halves, so no pass is possible without a reversal; I do not call it FALSIFIED only because the registered order of words puts the 150 fill floor first.

DEV = closes 2026-10-29 to 2026-11-01 (175 orders, 52 hourly closes with an order, 0 without a result):

| bound | fill rate | win rate | mean price | net per resting order | net per fill | PF | day z |
|---|---|---|---|---|---|---|---|
| PESSIMISTIC (queue never cancels; verdict) | 81.7% (143) | 4.2% | 5.8% | -1.28c | -1.57c | 0.71 | -1.01 |
| OPTIMISTIC (queue ahead all cancels; info) | 99.4% (168) | 5.4% | 5.2% | +0.12c | +0.12c | 1.03 | +0.13 |
| middle (half the queue cancels; info) | 90.3% | 3.8% | 5.3% | -1.37c | -1.51c | 0.70 | -1.07 |

Pessimistic halves: H1 -1.56c per order (PF 0.65), H2 -0.96c (PF 0.78). Tape-gap orders: 6 of 175 (not filled under pessimistic, excluded from optimistic).

Win rate against the price paid (pessimistic fills): bid 1c to 4c 1.4% vs 2.4% (PF 0.57); 5c to 9c 4.4% vs 6.9% (PF 0.63); 10c to 15c 10.7% vs 12.2% (PF 0.86). Every bucket wins less often than the price, the adverse-selection shape of MAKER1 to 3. Under the optimistic bound the 10c to 15c bucket is +4.43c per order (PF 1.44, 30 orders), which is one cell of three, 30 orders, and not a result.

Side split (information, not a try): YES-side tails (strike above spot) win 1.4% at 5.8% (PF 0.23, -3.88c per order, z -2.88); NO-side tails win 6.9% at 5.7% (PF 1.25, +0.96c, z +0.63). Not registered as a rule; seeing it after the fact makes it a hypothesis for a new registration, not a finding (one 3.5 day sample, 81 and 94 orders, strikes in one close are one correlated BTC move).

**Taker comparison** (same orders at the ask at look + 1 s, displayed size at least 10, fee 7% x 10 x p x (1-p) rounded up): 172 orders, win 5.8% at mean ask 6.2%, -0.87c per order, PF 0.86 (x1.2 fee: -0.96c, PF 0.84). The taker is less bad than the pessimistic resting order: a resting buy is filled when the price is falling (82% filled), so resting gives away more than the saved spread and fee.

**Fill rate vs prediction.** I predicted 10% to 25% pessimistic and got 82%. The tail strikes print heavily over the 34 minute life (look at T-25 min to T-1 min), so the queue ahead (median small) is cleared almost always; the lever is not queue position but WHICH fills come: they come as spot moves through the strike. Orders per close was 3.4 (predicted 1 to 3) because both sides of the 7 strikes give tail bids.

**Forward plan.** Rule unchanged on closes from 2026-11-03 16:00Z, read once on 2026-11-12 (or when 150 forward pessimistic fills exist; at about 36 fills a day, about 4 days). The recorder was still committing at 2026-11-03 20:03Z, so it is running. The HOLDOUT (2026-11-02 00:00Z to 2026-11-03 15:00Z, 134 orders) was not opened because DEV did not pass; it is the first confirmation set if a later registration changes the rule.

**Capped probe spec (not recommended; only on a pass, owner decides):** 1 contract, resting buy at the best bid at 25 minutes before the hourly close, bid at most 15c, KXBTCD only, cancel at T-60 s; kill after 40 fills if net is negative; about 36 fills a day at about 3.4 orders a close; worst day 24 closes x 4 orders x 15c = $14.40 (realistic worst about $3 to $5); not a 15 minute series (no L1 overlap). Not warranted by the DEV result (PF 0.71).

Tries: 2 (pessimistic, optimistic). N +4.
