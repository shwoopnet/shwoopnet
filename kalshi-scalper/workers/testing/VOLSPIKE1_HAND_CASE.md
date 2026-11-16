# VOLSPIKE1 hand case, written BEFORE any code (Testing Desk, Nov 16, 2026)
Invented markets V1 to V11, close C = 10000 x k. E = candle ending C - 600, P = candle ending C - 660; prior volumes = candles ending C - 1260, -1200, ..., -660 (P included), only volumes > 0 count. mid = (bid + ask) / 2 rounded to 6 places. b/a = YES bid / YES ask.
| V | prior volumes (oldest to P) | vol(E) | b/a at P | b/a at E | result | outcome |
|---|---|---|---|---|---|---|
| V1 | 10, 20, 10, 30, 10, 20 (median 15) | 45 (= 3 x 15, inclusive) | .60/.62 | .60/.62 | yes | YES, ask .62, win |
| V2 | same as V1 | 44 | .60/.62 | .60/.62 | yes | skip no_spike (baseline: YES .62 win) |
| V3 | same as V1 | 100 | .60/.62 | .62/.64 (mid moved .02) | yes | skip moved (baseline: YES .64 win) |
| V4 | same as V1 | 60 | .60/.62 | .61/.63 (mid .62 vs .61, moved exactly .01, allowed) | no | YES, ask .63, loss |
| V5 | same as V1 | 60 | .30/.32 | .30/.32 (mid .31) | no | NO, ask 1 - .30 = .70, win |
| V6 | same as V1 | 60 | .49/.51 | .49/.51 (mid .50 exactly, YES) | yes | YES, ask .51, win |
| V7 | same as V1 | 60 | .84/.86 | .84/.86 | yes | skip band (ask .86 over .80) |
| V8 | same as V1 | 60 | .78/.80 | .78/.80 | yes | YES, ask .80 (inclusive), win |
| V9 | 10, 0, 20, 10, 30 (4 positive) | 60 | .60/.62 | .60/.62 | yes | skip no_prior (baseline: YES .62 win) |
| V10 | as V1, but no candle ending C - 660 | 60 | none | .60/.62 | no | skip no_candle (baseline: YES .62 loss) |
| V11 | as V1 | 60 | .60/.62 | .00/.62 (bid 0) | yes | skip no_candle (baseline: not two-sided, out) |
Check order: E and P two-sided, else no_candle; at least 5 positive prior volumes, else no_prior; spike, else no_spike; mid moved over 0.01, else moved; ask band, else band. Skips: no_candle 2, no_prior 1, no_spike 1, moved 1, band 1.
Trades (by close): V1, V4, V5, V6, V8: n 5, wins 4.
Fee ceil(round(70 p (1-p), 9)) / 100: p .62, .63, .64, .70, .71, .72 fee .17 (.62 to .64), .15 (.70 to .72); p .65 fee .16; p .51, .52, .53 fee .18; p .80 fee .12; p .81, .82 fee .11.
Cash h0 / +1c / +2c: V1 win +3.63 / +3.53 / +3.43; V4 loss -6.47 / -6.57 / -6.66; V5 win +2.85 / +2.75 / +2.65; V6 win +4.72 / +4.62 / +4.52; V8 win +1.88 / +1.79 / +1.69.
Net +6.61 / +6.12 / +5.63. PF 13.08/6.47 = 2.0216; 12.69/6.57 = 1.9315; 12.29/6.66 = 1.8453.
Halves floor(5/2) = 2: half 1 = V1, V4: PF 3.63/6.47 = 0.5611; 3.53/6.57 = 0.5373; 3.43/6.66 = 0.5150; half 2 = V5, V6, V8: infinite.
Day z at +2c with V1, V4 on day 1 and V5, V6, V8 on day 2: sums -3.23 and +8.86; mean 2.815; se 12.09 / 2 = 6.045; z = 0.4657.
Baseline (two-sided E, side rule, ask 0.50 to 0.80, no spike or still-price or prior condition): V1, V2, V3, V4, V5, V6, V8, V9, V10: n 9, wins 7 (losses V4 and V10); V7 (band) and V11 (not two-sided) are out.

Addendum 1 (Auditor B, before any run): the extract's candle volume is PER CANDLE, not cumulative (checked on the gold series by schema only: within a market it falls from one candle to the next about as often as it rises, e.g. 17829, 15463, 20779, 6859, 4649, 17050). A zero or missing volume(E) is never a spike (volumes at or below 0 are not >= 3 x a positive median); zero prior volumes are ignored (V9). The baseline is printed at 1c and 2c with n and the spike-minus-baseline PF difference, and the spike result passes only if the baseline itself does not clear PF 1.5 at 1c or 2c (otherwise it is not a spike finding). The rule is in the favourite-late family (a closed family); only the spike condition is new. Hand figures above unchanged.
