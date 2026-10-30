# EXITOI-G result (V2 worker EXITOI-G, 2026-10-30, research only)

Registration `workers/EXITOI_G_REGISTRATION.md` (commit c5c2ab3, pushed before any scoring). Code `src/scalper/exitoig.py`
(NEWH3's `h3` unchanged, with a loader that takes the series; `PYTHONPATH=src python -m scalper.exitoig run`, run once). Printout
`studies/exitoig_result_2026-10-30.txt` (aggregates only). Nothing closing on or after 2026-10-28 was loaded; nothing was changed
after the score and nothing was re-run. **Parity:** the Bitcoin line reproduces NEWH3's H3 exactly (1,331 / 1,028 entries, 26 / 29
triggers, PF10 0.988 / 1.001 and 0.955 / 1.006, +$9.47 / +$30.07, day z +1.51), so the code path is the same.

Rule (unchanged): L1 entry at the 360 s look, side in 88c to 97c, filled at the 300 s candle's ask; if open interest at 180 s is at
most 0.95 x that at 360 s, sell at the 120 s side bid, else hold. C = 10, fee rounded up per order on the buy and the sale.

## Verdicts (N = 4)

| Line | Disc entries / trig / hold PF10 / rule PF10 / rule-hold $ | Val entries / trig / hold / rule / rule-hold $ | Day z | Verdict |
|---|---|---|---|---|
| Gold KXGOLD15M | 976 / 21 / 1.237 / 1.123 / -$48.50 | 697 / 30 / 1.197 / 1.236 / +$7.76 | -1.66 | NOT_ENOUGH_DATA |
| Dogecoin KXDOGE15M | 1,449 / 20 / 1.390 / 1.301 / -$43.79 | 1,011 / 9 / 1.287 / 1.240 / -$20.02 | -2.89 | NOT_ENOUGH_DATA |
| Ethereum KXETH15M | 1,427 / 13 / 1.096 / 1.086 / -$7.34 | 960 / 17 / 0.856 / 0.877 / +$16.68 | +0.47 | NOT_ENOUGH_DATA |
| Pooled (gold, Doge, ETH, BTC) | 5,183 / 80 / 1.158 / 1.120 / -$90.16 | 3,696 / 85 / 1.040 / 1.059 / +$34.49 | -1.24 | **FALSIFIED** |
| Bitcoin (NEWH3, reference, not counted) | 1,331 / 26 / 0.988 / 1.001 / +$9.47 | 1,028 / 29 / 0.955 / 1.006 / +$30.07 | +1.51 | (NOT_ENOUGH_DATA in NEWH3) |

The pooled line has the triggers (80 and 85, over the 50 bar) and fails on every other condition: rule PF is 0.038 BELOW hold in
discovery, only +0.019 above in validation (bar +0.03), and the day z is -1.24 (bar +2.0). The three single markets lack the 50
triggers per window, but none is close to the bar either: gold and Dogecoin lose to holding in discovery by 0.115 and 0.089 PF, and
Dogecoin loses in both windows (z -2.89).

## The other lines asked for

- **Fees x1.2 (rule minus hold, C = 10):** gold -$48.93 / +$7.31, Dogecoin -$44.10 / -$20.19, Ethereum -$7.57 / +$16.41, pooled
  -$91.56 / +$33.15. Same sign as at x1.0 everywhere.
- **C = 1 PF, hold / rule:** gold 1.114 / 1.006 and 1.081 / 1.106; Dogecoin 1.243 / 1.159 and 1.156 / 1.109; Ethereum 0.977 / 0.966 and
  0.767 / 0.784; pooled 1.038 / 1.000 and 0.934 / 0.946.
- **Gold's ladder size:** neither NEWH3 nor TIMEX1 registered one, so no ladder-size line was computed. At 10 contracts the gold
  difference is -$48.50 then +$7.76 (-$40.74 over both windows); it scales linearly with size apart from fee rounding.
- **Trigger loss rate vs the rest:** gold 9.5% vs 5.1% (disc), 36.7% vs 4.2% (val); Dogecoin 25.0% vs 4.5%, 11.1% vs 5.3%;
  Ethereum 38.5% vs 5.4%, 52.9% vs 6.9%; pooled 35.0% vs 5.1%, 45.9% vs 5.5%. Triggered entries do lose more often, but on gold and
  Dogecoin not often enough: selling them at the 120 s bid costs more on the ones that recover than it saves on the losers
  (gold discovery: triggered entries held made +$4.37, sold -$44.13).
- **Zero bid at 120 s:** 0 of 80 and 0 of 85 triggered entries (0% on every market); every trigger had a sellable bid, so the "hold
  on zero bid" clause never applied.
- **Zero volume both ways:** no entry's fill candle had volume 0 on any market; both lines are identical.
- **Gaps:** no fill at 300 s: gold 9, Dogecoin 21, Ethereum 43, Bitcoin 14; open interest missing: Dogecoin 1.
- **Trigger rate:** 0.9% to 4.3% of entries per market and window (prediction 1% to 3%; gold validation 4.3% was above it).

## Reading

The prediction held on the verdicts (three NOT_ENOUGH_DATA, pooled FALSIFIED) and on the loss-rate gap. What Bitcoin showed (selling
after a 5% open interest fall beats holding) does not carry to the other live markets: on gold, L1's ladder market, the exit was
worse than holding in discovery and slightly better in validation, net -$40.74 at 10 contracts over both, and on Dogecoin it was
worse in both windows. Bitcoin's result reads as Bitcoin-specific or noise, consistent with TIMEX1: on L1's favourites, selling in the
last minutes mostly sells positions that recover, and open interest flow does not change that. No forward check is proposed (the bar
was not met). Nothing touches the live bot.

## Count

**N added: 4** (gold, Dogecoin, Ethereum, pooled; the Bitcoin reference line is not counted). Running count about 592,061 before,
about **592,065** after (plus other workers' additions).
