# OPENGAP1 hand case, written BEFORE any code (Testing Desk, Nov 16, 2026)
Invented events. Times are seconds relative to the cash open O (09:30 ET): the 09:25 candle ends at O - 300, the entry candle E at O + 60, the 09:45 candle at O + 900; the previous-day 16:00 ET candle ends at its own timestamp (any earlier time). b/a = bid_close / ask_close of the perp candle; mid = (bid + ask) / 2. g = (U_open / U_prev - 1) - (P_0925 / P_prev16 - 1). Trigger: round(|g|, 9) > round(2 x ((ask - bid) / 2) / mid of E, 9), strict. Closure at candle t: sign(g) x (g - (mid_t - P_0925) / P_prev16) <= 0.5 x |g|. Fee 0.0012 a side (0.0024 round trip) primary; also printed at fee 0. h in perp price units.
| Event | U_prev, U_open | prev16 b/a | 09:25 b/a | candles after O | outcome |
|---|---|---|---|---|---|
| E1 | 100, 101 | 9.99/10.01 | 10.04/10.06 | O+0: 10.20/10.22 (before E, ignored); O+60 (E): 10.06/10.08; O+120: 10.07/10.09; O+180: 10.30/10.32 (after exit, unused) | g = 0.01 - (10.05/10.00 - 1) = 0.005; E half spread fraction 0.01/10.07 = 0.000993, 2x = 0.001986 < 0.005: trigger, long at ask 10.08; O+120 mid 10.08: gap_t = 0.005 - (10.08 - 10.05)/10.00 = 0.002 <= 0.0025: exit at its bid 10.07 |
| E2 | 50, 49.5 | 4.995/5.005 | 4.995/5.005 | O+60 (E): 4.99/5.01; O+120: 4.99/5.00; O+300: 4.98/4.99; O+900: 4.98/4.99; O+960: 4.00/4.01 (after 09:45, unused) | g = -0.01 - 0 = -0.01; E: 0.01/5.00 = 0.002, 2x = 0.004 < 0.01: trigger, short at bid 4.99; closure needs gap_t >= -0.005: O+120 mid 4.995 gives -0.009, O+300 mid 4.985 gives -0.007, O+900 mid 4.985: not closed; exit at the 09:45 candle's ask 4.99 |
| E3 | 200, 202 | 19.99/20.01 | 19.99/20.01 | O+60 (E): 20.01/20.03; O+120: 20.05/20.07; O+360: 20.14/20.16 | g = 0.01; E: 0.01/20.02 = 0.0005: trigger, long at ask 20.03; O+120 mid 20.06: gap_t = 0.007 > 0.005 no; O+360 mid 20.15: gap_t = 0.0025 <= 0.005: exit at bid 20.14 |
| E4 | 100, 100.15 | 99.99/100.01 | 99.99/100.01 | O+60 (E): 99.90/100.20 | g = 0.0015; E: 0.15/100.05 = 0.0014993, 2x = 0.0029985 > g: skip no_trigger |
| E9 | 100, 100.2 | 99.99/100.01 | 99.99/100.01 | O+60 (E): 99.90/100.10 | g = 0.002 (float 0.00199999...), E: 0.1/100 = 0.001, 2x = 0.002: equal at 9 places, strict: skip no_trigger |
| E5 | no Databento open | 9.99/10.01 | 10.04/10.06 | O+60: 10.06/10.08 | skip no_underlying |
| E6 | 100, 101 | 9.99/10.01 | no candle at O-300 | O+60: 10.06/10.08 | skip no_perp |
| E7 | 100, 101 | no candle at the previous 16:00 | 10.04/10.06 | O+60: 10.06/10.08 | skip no_perp |
| E8 | 200, 202 | 19.99/20.01 | 19.99/20.01 | O+60 (E): 20.01/20.03 and nothing after | trigger, but skip no_exit |
Skips: no_underlying 1, no_perp 2, no_trigger 2, no_exit 1. Trades by entry time: E1, E2, E3 (days d1, d2, d3), n 3, wins at net: 1.
Returns sign x (exit - entry) / entry with the haircut on both fills (entry at ask + h or bid - h, exit at bid - h or ask + h):
| | h 0 | h 0.01 | h 0.02 |
|---|---|---|---|
| E1 long 10.08 to 10.07 | (10.07 - 10.08)/10.08 = -0.00099206 | (10.06 - 10.09)/10.09 = -0.00297324 | (10.05 - 10.10)/10.10 = -0.00495050 |
| E2 short 4.99 to 4.99 | 0 | (4.98 - 5.00)/4.98 = -0.00401606 | (4.97 - 5.01)/4.97 = -0.00804829 |
| E3 long 20.03 to 20.14 | 0.11/20.03 = 0.00549176 | (20.13 - 20.04)/20.04 = 0.00449102 | (20.12 - 20.05)/20.05 = 0.00349127 |
Net at fee 0.0012 a side (return - 0.0024): E1 -0.00339206 / -0.00537324 / -0.00735050; E2 -0.0024 / -0.00641606 / -0.01044829; E3 +0.00309176 / +0.00209102 / +0.00109127.
PF at fee 0.0012: h 0: 0.00309176 / 0.00579206 = 0.5338; 1c: 0.00209102 / 0.0117893 = 0.1774; 2c: 0.00109127 / 0.01779879 = 0.0613. Halves floor(3/2) = 1 by entry time: half 1 = E1 (PF 0); half 2 = E2, E3: 0.00309176 / 0.0024 = 1.2882 (h 0), 0.00209102 / 0.00641606 = 0.3259 (1c), 0.00109127 / 0.01044829 = 0.1044 (2c).
Day z at 2c (net, fee 0.0012; days d1, d2, d3): values -0.0073505, -0.01044829, +0.00109127, mean -0.00556917, sample sd 0.00597246, z = -0.00556917 / (0.00597246 / sqrt 3) = -1.6151.
At fee 0 (return only): h 0 returns -0.00099206, 0, +0.00549176: PF 0.00549176 / 0.00099206 = 5.5355. Break-even fee per side (mean return / 2): h 0: (0.00449970 / 3) / 2 = 0.00074995.
