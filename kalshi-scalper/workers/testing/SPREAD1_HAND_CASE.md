# SPREAD1 hand case, written BEFORE any code (Testing Desk, Nov 16, 2026)
Definitions (Auditor B's conditions b, a, d). Spread = YES ask - YES bid of a candle, in dollars, rounded to 6 places. mid = (bid + ask) / 2 rounded to 6 places. Median: odd count = the middle value; even count = the mean of the middle two (so 4 values 0.02, 0.02, 0.06, 0.06 give 0.04). The widening floor is 0.03 in dollars, threshold = max(0.03, 2 x median), compared as spread(E) >= threshold on 6 decimals (inclusive). Two-sided = 0 < bid < ask < 1. The prior set = two-sided candles ending at or before C - 660 (P included), at least 3, at most 4 exist. Check order: E and P two-sided (else no_candle); at least 3 prior two-sided candles (else no_prior); widening (else no_widen); move |d| >= 0.01 with d = mid(E) - mid(P) at 6 places (else no_move); side by the sign of d; ask band 0.35 to 0.80 inclusive (else band).
Relation to QR1 JUMPFADE600 (Nov 15, a registered and failed read, no pass; its figures went to the Head by message): QR1 faded a jump at the same E and P geometry; SPREAD1's baseline (the same side, same band and the same move rule, with no widening condition) is the plain follow-the-move rule, so widening is the only new input. The baseline is printed against the SPREAD1 result at 1c and 2c, and SPREAD1 does not pass if the baseline itself reaches PF 1.5 at 1c or 2c.
Invented markets, close C = 10000 x k; prior b/a oldest to P (candles ending C-840, C-780, C-720, C-660); E = candle ending C-600.
| S | prior b/a (spreads), P last | E b/a (spread, mid) | d | result | outcome |
|---|---|---|---|---|---|
| S1 | .50/.52 x4 (.02 x4, median .02, threshold .04) | .54/.58 (.04, .56); P mid .51 | +.05 | yes | widening at exactly threshold; YES ask .58 in band; win |
| S2 | as S1 | .54/.57 (.03 < .04) | +.045 | yes | skip no_widen (baseline: YES .57 win) |
| S3 | .50/.51 x4 (.01 x4, median .01, threshold max(.03, .02) = .03) | .48/.51 (.03, .495); P mid .505 | -.01 exactly | no | widening on the floor, d exactly -.01 allowed; NO ask 1 - .48 = .52; win |
| S4 | as S1 | .49/.53 (.04, .51) | 0 | yes | skip no_move |
| S5 | .30/.32 x4 (threshold .04) | .20/.24 (.04, .22); P mid .31 | -.09 | yes | NO ask 1 - .20 = .80 (edge, inclusive); loss |
| S6 | .85/.87 x4 (threshold .04) | .88/.92 (.04, .90); P mid .86 | +.04 | yes | YES ask .92, skip band |
| S7 | .30/.32 x4 (threshold .04) | .31/.35 (.04, .33); P mid .31 | +.02 | no | YES ask .35 (edge, inclusive); loss |
| S8 | candle ending C-840 missing; three candles .50/.52 (.02 x3, threshold .04) | .54/.58 (.04) | +.05 | no | three prior candles are enough; YES ask .58; loss |
| S9 | C-840 missing, C-780 .00/.52 (bid 0, not two-sided), C-720 .50/.52, C-660 .50/.52 | .54/.58 (.04) | +.05 | yes | two two-sided priors: skip no_prior (baseline: YES .58 win) |
| S10 | .50/.52, .50/.52, .50/.56, .50/.56 (spreads .02, .02, .06, .06, median .04, threshold .08) | .55/.61 (.06, .58); P mid .53 | +.05 | yes | skip no_widen (a lower-middle median .02 would give threshold .04 and trade it); baseline: YES .61 win |
| S11 | as S1 | no candle ending C-600 | | yes | skip no_candle |
| S12 | as S1 but no candle ending C-660 (three priors only) | .54/.58 | | yes | skip no_candle |
Skips: no_candle 2, no_prior 1, no_widen 2, no_move 1, band 1.
Trades by close: S1, S3, S5, S7, S8 (n 5, wins 2).
Fee ceil(round(70 p (1-p), 9)) / 100: .58 fee .18; .59, .60 fee .17; .52, .53, .54 fee .18; .80 fee .12; .81, .82 fee .11; .35 fee .16; .36, .37 fee .17.
Cash h0 / +1c / +2c: S1 win +4.02 / +3.93 / +3.83; S3 win +4.62 / +4.52 / +4.42; S5 loss -8.12 / -8.21 / -8.31; S7 loss -3.66 / -3.77 / -3.87; S8 loss -5.98 / -6.07 / -6.17.
Net -9.12 / -9.60 / -10.10. PF 8.64/17.76 = 0.4865; 8.45/18.05 = 0.4681; 8.25/18.35 = 0.4496.
Halves floor(5/2) = 2: half 1 = S1, S3 (infinite); half 2 = S5, S7, S8 (PF 0).
Day z at +2c with S1, S3 on day 1 and S5, S7, S8 on day 2: sums +8.25 and -18.35; mean -5.05; se 26.6 / 2 = 13.3; z = -0.3797.
Baseline (E and P two-sided, the move rule, the band, no widening or prior condition): S1, S2, S3, S5, S7, S8, S9, S10: n 8, wins 5 (S1, S2, S3, S9, S10); S4 (no move), S6 (band), S11 and S12 (no E or P) are out.
Refusal: a selected market at close_ts 1791043200 stops the run; 1791043199 loads.
