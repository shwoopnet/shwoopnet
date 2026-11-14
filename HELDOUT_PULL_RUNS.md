
## 2026-11-14 00:11Z, one held-out window seen by another card's read (rule (h), standing rule 17)
- Window: KXBTC15M, close 2026-11-14T00:00:00Z.
- Seen by: DEPTH1's registered held-out read (Desk A, frozen wrapper, quote-data pin 2b4ff3957b078def19a6a2bd8d7b83d87f322f7d, run 2026-11-14T00:08:10Z). DEPTH1 cuts by Central close date, so 18:00 CT Nov 13 sits in its block; its guard did not refuse it.
- Card affected: CFRTI-K, whose held-out starts at closes from 2026-11-14T00:00:00Z (inclusive, Auditor B's reading of the registration).
- Consequence: CFRTI-K's read EXCLUDES this one window; its held-out is closes strictly after 2026-11-14T00:00:00Z (first: 00:15Z). Desk A writes the dated card line; both CFRTI-K readers implement it; Auditor B audits it before Nov 20.
- Any other card pooling Bitcoin windows closing at 2026-11-14T00:00:00Z gets the same flag.
