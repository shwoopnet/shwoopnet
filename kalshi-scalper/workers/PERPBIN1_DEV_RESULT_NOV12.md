# PERPBIN1 development result (Idea Desk A, Nov 12, 2026, run once as registered; scorer `desk_a_verify/perpbin1.py` committed and self-tested before the candles landed)

Same inputs as CFRTI-K (LISTS 43262026759, PERPBTC1M 43252136600, CANDLES 43279857619); development = closes 2026-09-12 to 2026-11-04; the top-tercile cut (open interest change of 7,147 contracts or more over the previous quarter hour) was computed from the perp candles alone.

```
PERPBIN1 DEVELOPMENT | markets 5127 | OIchg top-tercile cut 7147.0 over 5113 windows | {'not rising': 3408, 'not mid-band': 709, 'entered': 996, 'no OI': 14}
try A (buy YES when OI rising): n 963 | cash PF 0.91 | mean -2.41c | win 49.8% | thirds n 327 PF 0.93 / n 344 PF 1.00 / n 292 PF 0.79 | z -1.65 (bar 5.46) | FALSIFIED on development (cash PF under 1.0)
try B (buy NO when OI rising): n 971 | cash PF 0.93 | mean -1.84c | win 49.7% | thirds n 324 PF 0.91 / n 346 PF 0.86 / n 301 PF 1.04 | z -1.25 (bar 5.46) | FALSIFIED on development (cash PF under 1.0)
```

**Plain reading.** Both tries are FALSIFIED on development by the registered label (cash PF under 1.0 with n over 100): **try A (buy YES when OI rising) n 963, cash PF 0.91, mean -2.41c, win 49.8%, thirds 0.93 / 1.00 / 0.79; try B (buy NO) n 971, cash PF 0.93, mean -1.84c, win 49.7%, thirds 0.91 / 0.86 / 1.04.** Both sides win about half the time, so the field carries no direction; the loss is the price and fee at a mid-band ask. The held-out is not read. Limits: the perp candle's freshness is not measured; the premium arm was dropped (no reference price in the candles).

DEVELOPMENT READ ON 2026-11-12 (PERPBIN1, once).

## Dated notes (Nov 12, 2026)
1. **The Verification Analyst MATCHED both tries**; with the cent-inclusive compare (tolerance 1e-9 on the 0.40 to 0.60 band) the figures do not change (A n 963 PF 0.91, B n 971 PF 0.93).
2. **Defect disclosed in the registration and found again by Forensics' audit (4ed0986):** the "rising" cut on development is the top tercile of the WHOLE development sample, so later windows' open interest decides earlier entries. It uses no outcome, so it cannot flatter the result, and both tries lose; **the falsification stands (Head of R&D's ruling).** For any later use the cut must be the frozen constant 7,147 and never recomputed. Limit code cannot settle: the candle's open_interest is the archived value; whether that number was visible at that minute in real time is not known.
