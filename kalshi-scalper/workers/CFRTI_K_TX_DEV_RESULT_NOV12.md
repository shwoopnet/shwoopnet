# CFRTI-K-TX development result (Idea Desk A, Nov 12, 2026, run once as registered and audited: cfrti_k_tx.py 5937a2b2, Auditor B CLEAN)

```
CAVEAT: the exit is a 1 contract sale at the DISPLAYED candle bid with no haircut or slip; candle freshness was measured on the Bitcoin 15 minute market only, not on the perp or on this exit minute.
CFRTI-K-TX | selected on development (closes 2026-09-12 to before 2026-11-05): it can falsify, not support | fired trades 610 | with a valid exit bid 587 | held for want of an exit bid 23
COST SCREEN (prices only, no result read): median round trip 0.0300 over 587 trades (kill above 0.05)
HOLD version (rounded entry fee): n 610 | cash PF 1.05 | mean +0.61c | day-clustered z 0.38
EXIT version (sell at the bid of the candle ending close-60 s; held when no exit bid): n 610 | cash PF 0.88 | mean -1.25c | day-clustered z -1.17
PAIRED difference (exit minus hold) -1.86c per contract | day-clustered paired z -1.64 (bar 1.645, one-sided)
VERDICT: HOLD STAYS
```

**Plain reading.** The cost screen passed (median round trip 3.0c, under the 5c kill), so results were read. Selling at the bid of the candle ending close minus 60 s is WORSE than holding: mean -1.25c a contract against +0.61c (hold, with the real rounded entry fee), cash PF 0.88 against 1.05, paired difference -1.86c, day-clustered paired z -1.64 (the wrong direction: the exit version loses, nearly significantly). VERDICT: HOLD STAYS. Selected on development: it can falsify, not support; it falsifies the exit. Held-out: not read, and not to be (development is below the hold version). The R6 book line is not run (it waits for DEPTH1's read and its result file). Note: with the REAL rounded entry fee the hold version's development PF is 1.05 and mean +0.61c, not the 1.09 and +1.12c of the unrounded-fee figure reported earlier; the difference is the fee rounding Forensics flagged.
