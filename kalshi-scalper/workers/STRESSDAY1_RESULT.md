# STRESSDAY1 result (census only): NOT_ENOUGH_DATA

Run once on 2026-11-03/04. Outcomes were never read (the code drops won and net on load).

| | |
|---|---|
| Development days with an entry | 22 (2026-09-08 to 2026-10-02) |
| Entries (Financials 377, Commodities 405, Crypto 0) | 782 |
| VIX cut (67th pct of first 14 days, prior-session change) | +2.97% |
| Stress days (VIX cut or FOMC/CPI/JOBS) | 10 (needs 25) |
| Stress / calm entries | 399 / 383 |
| Stress events (independent ladders) | 80 |

Verdict: **NOT_ENOUGH_DATA.** Entries pass 150 but stress days are 10 against the 25 required, and the days are the unit of independence for a regime claim. With Economics added the days are still only 24. No win-versus-price, net or PF was computed.

## Forward plan
The rule and cut (+2.97%, FOMC/CPI/JOBS dates) are fixed here. Score once, on cheap-side Financials/Commodities/Crypto ladder entries from 2026-10-03T16:00Z (the frozen third) plus later days, when at least 25 stress days (about 55 trading days at a one-third rate) and 150 stress entries exist, with kill rules as registered and a fresh N charge. Needs the USWEEP daily-ladder recorder or fetch to continue past 2026-10-02; also needs entry timestamps stored for A-looks.
