# PERPDEPTH1 card (draft, Forensics desk, Nov 16, 2026; research only, nothing run)

**Question.** On the liquid perps, does the resting book at the top 5 levels predict the next 3 to 60 minutes of price better than the last price already does?

**Mechanism.** Resting size on one side is a short lived claim on the next trade. If it is real, price moves toward the thin side (follow). If it is stale, spoofed or an inventory artefact, the quote reverts (fade). Both directions are in the grid, so the family does not choose.

**Data.** Only the live perps recorder (book.csv, markets.csv, static.csv, funding), forward from `start_utc` 1794873600 (2026-11-17T00:00Z). No earlier book exists, so the family cannot be back-tested and cannot be peeked at: first read not before 1796688000 (2026-12-08T00:00Z), one read, 10 trade days, 100 decisions a cell.

**Markets.** Gold, US Tech 100, US Large Cap, Bitcoin, Ethereum, NVDA, MU, tickers copied from static.csv. NVDA decisions stop before the H16 hold (1797897600). Auditor B to confirm MU.

**Features and cells.** Two features (book imbalance; depth weighted mid against last price in spreads), three constant thresholds each, follow or fade, five holds: 7 x 2 x 3 x 2 x 5 = 420 rules. Thresholds are written before data exists.

**Look-ahead.** Decision uses rows received by the decision minute; entry is the next quote after it; exit is the first quote at or after the hold; gaps over 2 minutes void and are counted.

**Costs.** Price terms first (basis points after the spread paid both ways, two haircuts, fee ASSUMED). Margin terms (times the recorder's leverage estimate) shown beside, never instead. Income = decisions a day x edge x contract value x leverage.

**Gates.** n 100, PF 1.3 primary and 1.0 secondary, 10 trade days, 3 decisions a day, BH 5% over every cell ever tried. Kill fast as in the spec.

**Honest prior.** Low. Single minute snapshots of a top-5 book are coarse and the recorder cannot see the order flow between them. This is a cheap, bounded test of a field no earlier test had.
