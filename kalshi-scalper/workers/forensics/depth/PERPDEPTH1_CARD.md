# PERPDEPTH1 card v3 (Forensics, Nov 16, 2026; lane 3 of the perps lane; research only, nothing run)

**Question.** In the liquid perps, do the resting book, the quote against the liquidation mark and the book before the daily funding print say anything about the next 5 to 60 minutes that the touch does not?

**Features (4, constants fixed now).** F1 top-5 depth imbalance (follow or fade at 0.3, 0.5, 0.7). F2 spread widening against the name's own 24 h median (1.5x, 2x, 3x; direction from the last 5 minute mid move). F3 distance of the mid from `liquidation_mark_price` (1, 2, 3 bps; fade or follow). F4 book thinning in the hour before the 4 PM ET print (depth at or under 0.5, 0.35, 0.2 of the 24 h median, direction from the imbalance; the five equity and index perps only).

**Markets.** Gold, US Tech 100, US Large Cap, Bitcoin, Ethereum, NVDA, MU, TSLA. 666 rules (192 + 192 + 192 + 90), m_total 6,291,326 on the carried 6,290,660.

**Forward only.** Provisional start_utc 1794960000 (2026-11-18T00:00Z), the first full day after the corrected recorder starts; no entry before it. First read not before 2026-12-08 and only at n >= 100 and 10 trade days; short rules get one more read on 2026-12-21 (the last decision, before H16 from 2026-12-22 for NVDA and the two index names).

**Prerequisite found today.** The recorder's first file kept the far book levels (the API lists the best level last). The fix is on `claude/forensics-perps-live-fix`; F1 and F4 have no usable data until it is merged and a new job runs.

**Costs.** Price terms in bps after crossing the touch both ways and a 5 or 12 bps round-trip fee (the Head's scenarios; Kalshi's real fee to be written in first). Margin terms at 10, 25 and 50 percent of the recorder's size specific maximum leverage (sizes 1,000 and 10,000), with a path-based liquidation test (conservative maintenance assumption, to be checked).

**Gates.** n 100, 10 trade days, 3 entries a day, PF 1.3 at 5 bps and 1.0 at 12 bps, BH 5%, kill fast.

**Honest prior.** Low. A tight, liquid perp pays a few bps of spread each way and 5 to 12 bps of fee; a book snapshot a minute apart is coarse. It is a bounded test of fields no candle carries.
