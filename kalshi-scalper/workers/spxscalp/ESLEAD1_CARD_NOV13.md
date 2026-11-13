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
