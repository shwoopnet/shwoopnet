# ESLEAD1: does the ES future lead the KXINX15M mid? (MEASUREMENT, registered before any data is opened)

Registered Nov 13, 2026. Not a strategy: no entry, exit, price band or cost rule, and it spends NO strategy try. It is the measurement behind the owner's remark "spx future charts are usually a little ahead" and sits beside SPXSCALP.

## Question and measurement (fixed now)
On KXINX15M windows closing 2026-11-05 to 2026-11-12 (the same ES bars and candles as SPXSCALP's development), the cross-correlation between the 1 minute change of ES and the 1 minute change of the KXINX15M candle mid (YES mid, the mean of yes bid close and yes ask close) at lags -3 to +3 minutes inclusive, one row per lag, in CFRTI-K's lead/lag table format (the table's exact columns must be given to this desk by the Head; until then rows are lag, n pairs, correlation).
- Lag k pairs the ES change in minute t with the Kalshi change in minute t+k. A positive peak lag means ES leads.
- ES changes come from 1 minute closes (close(t) - close(t-1)); a minute with a missing ES or Kalshi value, or either side one that crosses a window boundary, is dropped and counted. The Kalshi mid is not carried forward across a missing candle.
- Within a window only; pairs are pooled over windows. Windows after 2026-11-12 are not touched.

## Prediction (written before any read)
The correlation peak is at lag 0, so no lead. The test passes the prediction only if the lag 0 correlation is the largest of the seven, and no lag from +1 to +3 exceeds lag 0.

## Data and handling
KXINX15M candles (landing, SPXOI1_CANDLES) and the ES 1 minute bars for Nov 5 to 12 held in the Testing Desk's scratch. The ES bars are Databento-derived: no ES value, figure or derived row is ever written to this repo or any branch; the card only names the source. The scorer takes the ES path as an argument, writes no ES-derived file, and results go by message only (a correlation table is a derived figure and is sent by message, not committed). The scorer must be frozen (commit and sha256) and audited CLEAN by Auditor B, with hand-computed expected figures on a made-up fixture written first, before any landed file is opened.

## Amendment 1 (Nov 13, 2026, before any data is opened): align with CFRTI-K's table format
Desk A sent the exact format (text only, from `lead_lag` in `desk_a_verify/cfrti_k.py`). ESLEAD1 follows it, with these fixed choices:
- Series A = KXINX15M YES mid (mean of yes bid close and yes ask close), series B = ES 1 minute close. Timestamps are whole minutes; the intersection of timestamps present in both is computed once, per window, not per lag.
- Changes: A's change is the plain difference mid(t) - mid(t-60 s) (a probability, not a price level, so no log); B's is the log change ln(ES(t)/ES(t-60 s)). The 60 s lookback is taken from the whole series, not from the intersection.
- Lag k pairs (dA[t], dB[t - 60k]). Positive lag = A (Kalshi) LAGS ES; negative = Kalshi leads. This is the same sign as the first version of this card (a positive peak lag means ES leads) and is stated beside the figure.
- Lags stay -3 to +3 (as registered; CFRTI-K printed -2 to +2). A lag with fewer than 30 pooled pairs is "n/a", a zero variance is "n/a". The fixture is run with the floor lowered to 3 by an argument, and the real run uses 30.
- Printed: CFRTI-K's one line with %+d lags and %.3f values, then (the card's own addition, since CFRTI-K did not print it) the pair count per lag. Pooled over windows before correlating.
- The prediction (peak at lag 0, no lead) is unchanged. EXPECTED_ESLEAD1_fixture.md is rewritten for log changes in the same commit.


## Amendment 2 (Nov 13, 2026, before any data is opened): licensed-data handling
The ES bars are Databento licensed data. They are never sent to any other session and never land in a public repo. Desk B's build 1 is NOT run on them in Desk B's session. The Testing Desk, which holds the file, runs BOTH builds (Desk B's and its own) on the same file; code goes to it, and only the aggregate figures come back. Auditor B compares the printed figures and the input file's sha256 (named by the Testing Desk), never the bars, and is never sent the ES file. Each scorer prints aggregates only (no bar value, no per-bar line, no per-window line that would reveal a bar) and writes no file derived from the ES bars.

## Amendment 3 (2026-11-13, before any data is opened): the Head's three lines
1. **Rule 18.** A candle's mid exists only when 0 < yes_bid < yes_ask < 1. An empty, locked or crossed candle gives no mid and no pair, and is counted as "not two-sided".
2. **Prediction reading.** The prediction (peak at lag 0, no lead) passes only if lag 0 has at least 30 pairs AND the largest correlation, AND no lag from +1 to +3 exceeds it. If lag 0 is "n/a" the result is "untestable at n = x", not a pass.
3. **ES instrument.** A minute whose instrument_id differs from the file's single instrument is dropped and counted (no roll is expected Nov 5 to 12). No row is dropped silently: every drop has a reason count, printed as aggregates.
