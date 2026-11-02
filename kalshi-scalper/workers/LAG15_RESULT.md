# LAG15 result (2026-11-02; registered in 0aea1f9 before any candle; `src/scalper/lag15.py`, `tests/test_lag15.py`, run once)

**crypto-new (HYPE, BNB, Zcash, NEAR): FALSIFIED.** **metals and FX: NOT_RUNNABLE** (not scored; no keyless minute history beyond 7 days reachable: Pyth Benchmarks and Hermes 401, Yahoo and Dukascopy 429, Stooq reset).

Data: 25,668 settled markets (6,417 per asset, 2026-08-27 to 2026-11-02, 68 UTC dates), 25,660 with candles; OKX 1 minute klines (97,500 per pair). Look s = 60 s, C = 10 contracts, taker at the ask, fee 7% x C x p x (1-p) rounded up (x1.2 stress), N = 728,714, z bar 5.27.

Printed result (verbatim from the one run):
```
KXHYPE15M: eligible 6380, qualifying 742, banned under 0.2 870, share priced 0.88 to 0.97 36% -> scored
KXBNB15M: eligible 6350, qualifying 930, banned under 0.2 1084, share priced 0.88 to 0.97 33% -> scored
KXZEC15M: eligible 6326, qualifying 785, banned under 0.2 704, share priced 0.88 to 0.97 32% -> scored
KXNEAR15M: eligible 6269, qualifying 792, banned under 0.2 458, share priced 0.88 to 0.97 40% -> scored
Try A edge 0.03 (verdict): eligible markets 25325 on 68 dates; Brier model 0.0764 market mid 0.0287
W1: n 982 days 22 PF 0.87 mean -2.27c z -1.39 | fees x1.2 mean -2.48c
W2: n 968 days 23 PF 0.98 mean -0.27c z -0.21 | fees x1.2 mean -0.49c
W3 holdout: not read
pooled (windows read): n 1950 days 45 PF 0.92 mean -1.28c z -1.22
Try A: FALSIFIED | Brier model no better than the market mid; W1 PF 0.87 and W2 PF 0.98 under 1.5; not positive at fees x1.2; pooled mean -1.28c under 2.0; pooled z -1.22 under 5.27
Try B edge 0.06: Brier same; W1 n 724 PF 0.91 mean -1.75c; W2 n 726 PF 1.01 mean +0.23c (x1.2 -0.02c); pooled n 1450 PF 0.96 mean -0.76c z -0.61 -> FALSIFIED
```
Reading: the OVERLAPS_L1 test did not fire for any asset (32% to 40% of qualifying entries priced 0.88 to 0.97, bar 50%), so the rule is not just the favourite band here, and all four assets were scored. The spot model is far WORSE than the quote mid in Brier (0.0764 against 0.0287): the quote already tracks spot, and the model with a 5 return sigma and one venue is noisy. The numeric prediction (Brier worse, PF 0.4 to 1.2, pooled mean -6c to +1c) held. Nothing in the quote lags the spot enough to pay a taker at the ask after the fee on these assets, on 1 minute data.

Limits and disclosures (none changes the verdict):
- 1 minute candles allow only the s = 60 look (RECORD1 also uses 45, 30 and 15 s); a lag shorter than a minute is invisible here and RECORD1's per second read stays the real test. One venue (OKX USDT) is not the CF Benchmarks index; the basis is not measured.
- Fetch code changed during the fetch, before the scored run and without reading any outcome: candle requests batched four windows at a time (rate limit), and OKX requests carry a plain `User-Agent: lag15-research/1.0` (the default Python agent is blocked). One Yahoo retry with a changed User-Agent was refused by the sandbox and not repeated.
- A format check of the batch candle endpoint printed the results of the three most recent HYPE markets (data format only; they were not used to choose anything).
- The pooled "windows read" line excludes W3 (holdout unread because W1 and W2 failed).
- 3,116 qualifying cheap-side entries under 0.20 were skipped by the ban, so the rule is stricter than RECORD1's.

Forward read: crypto-new does not need a recorder (Kalshi candles and OKX klines are retrievable later) but, being FALSIFIED, none is planned; if the owner wants one anyway, 30 fresh days after 2026-11-02 gives 2026-12-02. Metals and FX would need a recorder of a keyless spot feed (none reachable). RECORD1's own per second read on the five original assets is expected about 2026-11-05 to 2026-11-08.
