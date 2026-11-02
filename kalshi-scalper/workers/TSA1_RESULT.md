# TSA1 result (2026-11-02; registration `workers/TSA1_REGISTRATION.md`, commit a3bf35e, pushed before any candle was downloaded; code `src/scalper/tsa1.py`, tests `tests/test_tsa1.py`)

One scored read, run once on all settled history (KXTSAW and TSAW weekly ladders, 162 predicted events, 642 strikes with model fair 0.10 to 0.90, all with hourly candles; 297 had a valid quote at the look with spread at most 10c). Cost: fee 7% x C x p x (1-p) rounded up per order, C = 10, taker at the ask; also fees x1.2. N: running count about 728,700 (z bar 5.27).

- Brier on the 297 quoted strikes: **model 0.1813 against the market mid 0.1279.** The model is clearly worse than the market (the registered prediction).
- W1 (earliest third of events): n 41 trades on 28 events, PF 1.12, mean +1.67c, z +0.26, x1.2 PF 1.10.
- W2 (middle third): n 78 on 38 events, PF 1.27, mean +3.24c, z +0.63, x1.2 PF 1.25.
- W3 holdout: NOT read (W1 and W2 both under PF 1.5, and Brier worse than the market).
- Pooled W1+W2: n 119, PF 1.21, mean +2.70c, event-clustered z +0.67 (bar 5.27).
- Information only, gap 0.05: W1 n 47 PF 0.85, W2 n 90 PF 1.29, W3 n 75 PF 0.64. Gap 0.12: W1 n 35 PF 1.01, W2 n 64 PF 1.38, W3 n 49 PF 0.72 (W3 shown as information after the verdict, not part of it).

**Verdict: FALSIFIED** on the registered Brier line (model no better than the market) and on PF under 1.5 in W1 and W2 and z far under 5.27. The script prints NOT_ENOUGH_DATA because it checks the trade count first (119 trades under 150); both facts hold, and the PF and Brier failures do not depend on the count. Prediction (Brier worse, PF 0.4 to 1.1 per window, 150 to 500 trades) was right on Brier and slightly low on PF (1.12 and 1.27, still far from 1.5 and statistically zero), and trades came in under the predicted range.

Deviations: tsa.gov unreachable (HTTP 403), settled values from Kalshi `expiration_value` used; daily KXTSA has no listed market (NOT_RUNNABLE, no try). A quote is not a fill. No variant was run; no promote verb.

## Forward read
Weekly events settle every Monday; the same rule can be re-scored on events after 2026-10-25 from Kalshi candles retrieved after the fact, so no new recorder is needed. At about 16 trades a week (119 trades on 66 events, roughly 1.8 per event), 150 fresh trades would take about 2027-10; a one-sided forward read is not worth scheduling before 2027-06-30. Not recommended given the Brier gap.
