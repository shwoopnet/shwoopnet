# MAKERMID1 registration: a resting buy at the best bid in the MID-BAND (16c to 40c, cheap side only) of the hourly Bitcoin ladder (KXBTCD), held to settlement, with the recorded queue and tape (V2 worker, 2026-11-03, research only)

Written and committed BEFORE any outcome, fill or PnL of this band was computed. What was looked at to write it: `workers/MAKERTAIL1_REGISTRATION.md`, `MAKERTAIL1_RESULT.md`, `src/scalper/makertail1.py` and `makertail1_fwd.py`, and the README lines for QUOTE2B / MM1 / COST1. No bid, trade price or result of a 16c to 40c order was opened. **Disclosure:** the same closes (2026-10-29 to 2026-11-01) were scored by MAKERTAIL1 for the 1c to 15c band, and its DEV outcomes (fill 81.7%, net -1.28c per order pessimistic, PF 0.71, bucket 10c to 15c win 10.7% vs price 12.2%) were SEEN. This band's outcomes were not. A close is therefore not fresh information: spot moves that hurt the tail also affect the mid-band, so the forward set is the only independent evidence.

**OWNER RULE (strict, Nov 3): no buy-the-favourite-and-hold research.** Every resting bid is at or below 40c (cheap side of its strike only). No favourite-side result (bid above 40c) is computed or printed. The taker comparison is restricted to orders whose ask is also at or below 40c, so nothing above 40c is bought in any column.

## Duplicate check

- **MAKERTAIL1:** the same order model on the far tail (1c to 15c): -1.28c per order pessimistic, +0.12c optimistic. This card is the next band up (16c to 40c); the 15c edge belongs to MAKERTAIL1, so there is no overlap.
- **QUOTE2B / MM1** (README): two-sided quotes on this same book recorder, mid band, FLAT at T-10 minutes (sold back by crossing or at the mid), not read before 2026-11-12. Different trade: this holds one side to settlement, joins the back of the queue 25 minutes out and has no sale.
- **MAKER5 / L1Q1:** 15 minute series, flattened by crossing. **MAKER2/3:** favourite band, candle proxy (and a favourite rule, not repeated). **MAKER1:** tennis. **G3H1, BOOKCH1:** taker, 15 minute. **COST1:** maker fee 0 on plain `quadratic` series; KXBTCD `fee_type: quadratic` (checked 2026-11-03), so fee 0 here. Why this band at all: maker fee 0 against a taker fee of about 1.2c to 1.8c at 15c to 40c, more probability mass than the tail, but more informed flow.
- `workers/OICORE_SHAPE_INVENTORY.md` has no resting mid-band bid held to settlement.

**New:** a mid-band cheap-side resting buy held to settlement on the hourly Bitcoin ladder scored with the recorded queue and tape.

## Data and the trade (inherited unchanged from MAKERTAIL1 except the band)

Same loaders and queue model, imported from `scalper.makertail1` (`load`, `Poll`, `Order`, `filled`, `tape_gap`, `summarise`, `verdict`, `taker_*`). Look = the last book poll at or before T-1500 s (not more than 20 s earlier). For each of up to 7 strikes and each side: if the best bid b is in [0.16, 0.40] (with a displayed size) place ONE 1-contract resting buy at b, never re-priced, joined at the back of the queue (Q0 = displayed size at b at the look), live from look + 1.0 s, cancelled at T-60 s (unfilled = 0). Fills from the tape: PESSIMISTIC (verdict bound): nothing ahead ever cancels, filled when prints exactly AT our price exceed Q0 or any print goes THROUGH it. OPTIMISTIC (information, counted as a try): the queue all cancels. Middle bound (half) information only. Tape-gap orders (hole over 90 s): not filled pessimistically, excluded from the optimistic. Fee 0. net = (1 if our side won else 0) - b. Taker comparison: the same side and strike at the ask at look + 1 s, displayed size at least 10 and ask at most 40c, fee 7% x C x p x (1-p) rounded up with C = 10, also x1.2.

## Rules (two registered rules, N +2 each)

- **MR1 (base):** the order above, no cancellation.
- **MR2 (adverse-selection guard):** the same order, but it is CANCELLED the first time, after it is live and before it fills, that a later book poll shows the best bid on our side at or below b - 0.02 (or that side's book empty). A fill needs the fill print to be strictly earlier than that poll's time. The guard reads only polls after the look, never an outcome. Scored under the same two bounds.

## Pre-registered readouts (information, not extra tries)

YES-side and NO-side orders separately under both bounds for each rule; bid buckets 16c to 25c, 26c to 33c, 34c to 40c; win rate of fills against price paid; taker comparison; fills per day.

## Frozen split

DEV = closes 2026-10-29 00:00Z to 2026-11-01 23:00Z (same as MAKERTAIL1), halves split at the median close. HOLDOUT = closes 2026-11-02 00:00Z to 2026-11-03 15:00Z, **not opened unless a rule passes DEV** (neither the MAKERTAIL1 holdout orders nor this band's are read). FORWARD = closes from 2026-11-03 16:00Z, read once on 2026-11-12 (or at 150 pessimistic forward fills, whichever is later) with the `scalper.fwdread` guard (refuses early, refuses a second read), per rule.

## Numeric prediction (before any count)

Orders: 2 to 4 per close, about 100 to 220 in DEV. Fill rate pessimistic 55% to 85% (central 70%), optimistic 90% to 100%. Win rate of fills 0.6 to 0.95 x the price paid. MR1 net per resting order pessimistic about -1.5c (range -4c to +0.5c), PF about 0.8; optimistic about -0.3c. MR2 fills fewer (35% to 65%), its net per resting order better than MR1 by 0 to 1c but still not above 0. Taker comparison about -2c per order (fee 1.2c to 1.8c plus spread). Prior of FALSIFIED 85% for each rule; no rule expected to pass.

## Kill rules and verdicts (each rule, pessimistic bound)

- **FALSIFIED:** mean net per resting order not above 0 in DEV, or PF on pessimistic fills under 1.5, or either DEV half not positive.
- **NOT_ENOUGH_DATA:** under 150 pessimistic fills in DEV (the report then gives fills per day and days to 150).
- **NOT_YET_FALSIFIED** is the best word. A pass also needs day-clustered z above the deflated bar (about 5.27), a named counterparty, holdout and forward positive. Nothing promotes; no promote verb.

## Capped probe spec (only if a rule is positive under the PESSIMISTIC bound in both DEV halves; the owner decides)

1 contract, resting buy at the best bid 25 minutes before the hourly close, bid between 16c and 40c, KXBTCD only (not a 15 minute series), cancel at T-60 s, kill after 40 fills if net is negative; worst day 24 closes x 4 orders x 40c = $38.40, realistic worst under $10.

## Tries and N

Two rules, each scored under two bounds counted once as the rule: N +4 (+2 per rule). Running total on the coordinator's books.

Code `src/scalper/makermid1.py`, `src/scalper/makermid1_fwd.py`, tests `tests/test_makermid1.py`; result `workers/MAKERMID1_RESULT.md`.
