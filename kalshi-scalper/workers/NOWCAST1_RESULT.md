# NOWCAST1 result (Strategy Research V2, 2026-11-03, discovery lane, research only)

Registered first: `workers/NOWCAST1_REGISTRATION.md` (sha256 `001810fc672f95afd566fc8d893a3c8d3fc71dc8ac437309bbda9757a184fd5f` at the first push; Amendment 1 appended before any candle fetch), windows `workers/NOWCAST1_WINDOWS.md`. Code `src/scalper/nowcast1.py`, tests `tests/test_nowcast1.py`, raw output `data/nowcast1_result.txt` (local only). Frozen holdout (44 of 130 release-series, closes from 2025-09-26) never computed.

## Duplicate check
CPI headline and core against the Cleveland nowcast: CPI1 (rerun 2026-10-31, 47 releases, both sides at a 5c edge, PF 1.11, FALSIFIED). Core PCE against Cleveland: ECONNEW2 angle B (NOT_ENOUGH_DATA). Claims vs persistence: ECONNEW1 FALSIFIED. Payrolls and unemployment: NOT_RUNNABLE (no public nowcast). EVENT1/EVT1/EVENT830: the 15 minute series, not these ladders. **New:** GDP (KXGDP) against Atlanta Fed GDPNow, and the cheap-side 3x ratio rule on all four. The CPI/PCE part re-uses cached data under a new rule: a new try on seen data.

## Sources reachable
Cleveland Fed nowcast JSON: yes (cached). Atlanta Fed GDPNow: the Atlanta Fed xlsx URL returns a JavaScript redirect page, but **FRED `GDPNOW` works with `curl --http1.1`** (one value per quarter, the last update before the advance release; no intra-quarter vintages, so GDP has a small lookahead of at most the last update after the 24 hour price look). Kalshi history: KXGDP 13 usable events with "greater" strikes from 2023-04 (one excluded by Amendment 1: Q3 2025 advance settled 25 days after its close); headline CPI 46, core CPI 46, core PCE 25 release-series with at least 36 error months. 130 eligible, 86 development (H1 43, H2 43), 44 holdout.

## Result (development only, one scored read; the rule as registered)
| | Trades | Release dates | Win vs mean price | PF | Mean net (C=10) |
|---|---|---|---|---|---|
| Development pooled | 12 | 10 | 8.3% (1 win) vs 7.8c | 1.00 (fees x1.2: 0.99) | +0.03c |
| H1 (43 release-series) | 1 | 1 | 0% vs 13.0c | 0.00 | -13.8c |
| H2 (43 release-series) | 11 | 9 | 9.1% vs 7.3c | 1.18 | +1.28c |

Information only: headline 4 trades PF 5.05 (one NO trade on the Mar 2025 CPI won +92.5c; the other three lost), core 3 trades 0 wins, core PCE 3 trades 0 wins, GDP 2 trades 0 wins. Ratio 2: 17 trades PF 1.27, ratio 5: 1 trade. No spread cap: same 12 trades.
Every one of the 12 quotes sat at 3c to 14c with the model saying 3 to 14 times that; the one win (1 of 12) carries all of the profit, so PF 1.00 is that single trade offsetting 11 small losses, not an edge. Win rate 8.3% against 7.8c paid is the ordinary longshot calibration.
**Verdict `NOT_ENOUGH_DATA`** (12 development trades against the registered 100; the literal FALSIFIED condition, mean not above 0 in both halves, is met only because H1 holds one trade, which the registration says is NOT_ENOUGH_DATA regardless; the code printed FALSIFIED in run 1 for that reason and was corrected before reporting, same 12 trades in both runs, disclosed). Prediction missed: 20 to 45 trades predicted, 12 found; PF 1.00 sits inside the predicted range 0.4 to 1.4.
Why so few trades: the cheap ratio rule needs a nowcast probability at least 3 times a quote of 3c to 30c, which is rare when the nowcast sd (0.1 for CPI, 1.2 for GDP) is wide relative to the strike spacing; 14% of release-series produced a trade (2025 on: about 26%; before mid 2024 almost none, the historical quote at 24 hours often missing or the spread over 10c).

## Forward plan and months to go
Releases per month for this universe: headline and core CPI plus core PCE = 3 release-series a month, GDP advance 0.33 a month (next KXGDP: Q4 advance, late January 2027). At 14% (all history) to 26% (2025 on) of release-series trading: **0.5 to 0.9 trades a month; 40 forward fills need 47 to 85 months; 150 trades about 14 to 25 years.** A forward candidate is therefore not worth a build; a single dated line is registered (README): forward look 24 hours before CPI Nov 10 (look Nov 9 7:30 CT), core PCE Nov 25 (look Nov 24), CPI Dec 10 (look Dec 9), core PCE Dec 23 (look Dec 22), dates from `studies/EVENT_CALENDAR_2026.csv`; read the first 12 forward release-series on or after 2027-03-01, decides nothing. 

## Probe spec
None. Not positive in both halves with a real sample; the single winning trade is the profit. A capped probe would be 1 contract, hard limit 0.30, but nothing earned it. **Counterparty finding:** none visible; the longshot side of these ladders is priced like every other longshot.

N +2 (running about 730,012).
