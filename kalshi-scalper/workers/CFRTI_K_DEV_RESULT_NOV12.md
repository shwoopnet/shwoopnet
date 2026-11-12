# CFRTI-K development result (Idea Desk A, Nov 12, 2026, run once as frozen; scorer `desk_a_verify/cfrti_k.py` committed and self-tested before the candles landed)

Inputs: LISTS run 43262026759, PERPBTC1M run 43252136600, CANDLES run 43279857619 (215 of 215 answers, 5,127 tickers, 81,822 candles) on `kalshi-pull-data`. Development = closes 2026-09-12 to 2026-11-04.

```
CFRTI-K DEVELOPMENT | markets 5127 | decisions: {'not cheap': 3686, 'no edge': 839, 'trade': 601, 'spread over 3c or crossed': 1}
rules text of the first market (the strike is taken to be the index at the window's open; if this says otherwise, STOP and tell the Head of R&D): If the simple average of the sixty seconds of CF Benchmarks' BRTI before 6:45 PM EST on Nov 4, 2026 is at least the simple average of the sixty seconds of CF Benchmarks' BRTI before 6:30 PM EST on November 4, 2026, then the market resolves to Yes.
registered line: n 601 | cash PF 1.07 | mean +0.94c | win 17.0% | days 54 | z 0.60 (bar 5.46)
thirds by date: n 175 PF 0.95 / n 210 PF 1.19 / n 216 PF 1.07
haircut (a) random 34% drop, 1,000 draws seed 20261114 (about n and spread, not the expected PF): median PF 1.08 (5th 0.94, 95th 1.21)
line (b) ran rows dropped (next candle ask 1c or more above the ask seen): n 435 of 601 known, ran share 27.6%, 0 rows without a next candle excluded | cash PF 0.16 | mean -12.53c
LABEL: carried: not falsified, research bar not cleared | note: the research bar is unlikely to be reachable at this size
BLOCK P condition (cash PF 1.3 or better in EACH third on the registered line AND line (b) above 1.0 on all development rows): NOT MET
lead/lag, 1 minute log-change correlation perp vs Kraken at lags -2..+2: -2: -0.008, -1: 0.072, +0: 0.938, +1: -0.028, +2: -0.018
peak at lag +0
```

**Plain reading.** n 601 trades on 54 days; registered line cash PF 1.07, mean +0.94c, win rate 17.0%, day-clustered z 0.60 against the bar 5.46; thirds by date PF 0.95 / 1.19 / 1.07. By the registered labels it is NOT FALSIFIED (PF at or above 1.0 with n over 100) and nowhere near the research bar, which is also unreachable at this size. **Line (b) is the live-use judge and it fails: with the 27.6% of rows whose next-minute ask ran 1c or more above the ask seen dropped, the same rule reads cash PF 0.16, mean -12.5c on 435 rows.** The whole registered edge (+0.94c) is in the rows where the price moved away before a fill could be had; the rows that did not run lose. Block P condition: NOT MET (first third PF 0.95; line (b) PF 0.16), so Block P is never pulled. The perpetual does not lag Kraken (lead/lag peak at lag 0, correlation 0.938). **Verdict for the record: no tradable edge; no live use; the held-out read on Nov 20 keeps its date.** Limits: the perp candle's freshness is not measured; the candle is one instant a minute.

DEVELOPMENT READ ON 2026-11-12 (CFRTI-K, once).

## Dated notes (Nov 12, 2026, after the Verification Analyst's re-derivation and Forensics' audit; no held-out was touched)
1. **Two sets stated; the cent-inclusive set is the one quoted from now.** The Verification Analyst matched every figure above, but found that a NO-side ask of exactly 0.30 computes as 1 - 0.70 = 0.30000000000000004 and failed the inclusive 5c to 30c band, dropping 9 trades. With a cent-inclusive compare (tolerance 1e-9 on the band and the edge) the scorer gives: **n 610, cash PF 1.09, mean +1.12c, win 17.4%, z 0.71; thirds 0.95 / 1.20 / 1.10; line (b) n 441 of 610, ran share 27.7%, cash PF 0.19, mean -12.11c; Block P NOT MET.** (First run: n 601, PF 1.07, mean +0.94c, z 0.60; line (b) n 435, PF 0.16.) The fix is in `cfrti_k.py` (and the same tolerance in `perpbin1.py`, whose figures do not change). Verdict unchanged.
2. **Line (b) is a diagnostic, not a rule.** It uses the price one minute after the decision and is mechanically correlated with the outcome (a market that ran toward the winner is dropped), so PF 0.16 to 0.19 is partly selection. The live-use judge remains the R6 book replay at the Nov 20 sitting.
3. **Forensics' audit (leak tests, 4ed0986): cfrti_k.py CLEAN**, no look-ahead; notes: at 1 contract the real fee rounds up (up to 0.9c above the unrounded fee, about the size of the registered mean); the model uses the perp at the open instant while the strike is a 60 second average (noise, not look-ahead).
