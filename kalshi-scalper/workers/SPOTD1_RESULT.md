# SPOTD1 result (2026-11-02; registered in 14b96f5 before any candle; `src/scalper/spotd1.py`, `tests/test_spotd1.py`)

**Verdict: FALSIFIED (both tries), with NOT_ENOUGH_DATA by count as well.** The persistence model's Brier is much worse than the market mid's, and profit factor is under 1.5 after fees in the read windows. N + 2: running count about 728,702 (z bar 5.27). Cost: 7% x C x p x (1-p) rounded up per order, C = 10, taker at the quoted ask, fees x1.2 shown. Holdout W3 not read (W1 and W2 did not pass).

## Try A, KXSPOTIFYD (520 predicted events, 689 universe strikes, 137 with a valid quote of at most 10c spread at the look)
- Brier: model 0.2037, market mid 0.1482.
- W1 n 29 PF 0.45 mean -6.33c z -1.20; W2 n 15 PF 1.33 mean +5.43c z +0.39 (fees x1.2: 0.45 / 1.32). Pooled read windows n 44 events 40 PF 0.82 mean -2.32c event-clustered z -0.39.
- Information gaps (not tried): at 0.05, W1/W2/W3 n 37/18/40; at 0.12, n 17/11/21 (no PF read for W3).

## Try B, KXSPOTIFYGLOBALD + KXSPOTIFYARTISTD pooled (876 predicted events, 933 universe strikes, 146 quoted)
- Brier: model 0.4171, market mid 0.0892.
- W1 n 4 PF 0.00; W2 n 35 PF 0.82 mean -2.36c z -0.41 (fees x1.2: 0.00 / 0.80). Pooled n 39 PF 0.77 mean -2.86c z -0.55.

## Disclosures
- The brief's rank-threshold model was not possible: the series are winner markets (one YES among about 15 titles), so the model is persistence of the number one title from Kalshi's own settled results, with the settlement lag (D+1 about 20:00 UTC) respected, so chart dates up to D-2 feed the look at 00:00 UTC of D.
- Only about 20% of universe strikes carry a valid two-sided hourly quote at the look (hourly historical candles are sparse for thin titles): quoted strikes, not model coverage, limit n. No trade-price fallback was allowed.
- W3 holdout (last third) was never scored. The info-gap lines print n only.
- Fair for non-top titles is not modelled (universe is the three most recent distinct number ones), which is why the model Brier is high on a winner market where the favourite is often not in the last three days.

## Forward read
About 44 trades in the read windows (two thirds of the events) on try A over about 14 months, so roughly 0.13 qualifying trades a day (about 0.2 a day including W3). 150 trades would take about two more years; A and B together about 0.35 a day, so about 14 months. The series settles and candles stay retrievable, so no recorder is needed; but with Brier 0.20 against 0.15 (A) and 0.42 against 0.09 (B) no forward registration is recommended.
