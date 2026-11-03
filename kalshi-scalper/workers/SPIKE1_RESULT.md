# SPIKE1 result (2026-11-03; registered in fc135cc before any outcome; code and tests in 6409fa3 before the run, one run, `data/spike1_score.json`)

**Verdict: FALSIFIED.** W3 (10-05 on) frozen and NOT read (the screen failed). Nine series: EURUSD, GBPUSD, USDJPY, silver, copper, WTI,
natural gas, platinum, palladium (AUD/USD, USD/CAD out: all their history is inside W3). Trigger: Kalshi's own YES mid, 3 sd (trailing 60 minute
RMS of 1 minute mid changes, floor 0.01) and 5c in 2 minutes, nine looks 12 to 4 minutes before the close; no outside spot (Yahoo's keyless
1 minute bars cover only the last 8 days, all inside W3). Fill: next candle's ask, hard limit 0.30 (Try B 0.97), held, C = 10, fee 7% x C x p x (1-p) rounded up.

| | n | win | avg fill | payoff/PF | mean net | z (day-clustered) |
|---|---|---|---|---|---|---|
| **A reversal, W1** (08-06 to 09-04) | 298 | 13.1% | 15.0c | **PF 0.79** (x1.2 0.78, +1c slip 0.73) | -2.84c | -1.31 |
| **A reversal, W2** (09-05 to 10-04) | 559 | 11.8% | 14.6c | **PF 0.72** (x1.2 0.71, +1c slip 0.66) | -3.66c | -3.22 |
| A pooled | 857 | 12.3% | 14.7c | PF 0.74 | -3.38c | -3.19 |
| **B continuation (favourite side), W1 / W2** | 284 / 526 | 86.6% / 87.8% | 86.2c / 86.5c | PF 0.97 / 1.05 | -0.39c / +0.46c | -0.18 / +0.39 |
| B pooled | 810 | 87.4% | 86.4c | PF 1.02 | +0.16c | +0.15 |
| **Control** (cheap side, same series, hour, look, no spike) pooled | 55,339 | 11.7% | 14.1c | PF 0.74 | -3.25c | -9.30 |
| A minus B per window, W1 / W2 / pooled | 284 / 526 / 810 | | | | -2.76c / -4.49c / -3.88c | -0.63 / -1.92 / -1.79 |
| A minus control, W1 / W2 / pooled | 298 / 558 / 856 | | | | -0.03c / -0.68c / -0.45c | -0.01 / -0.56 / -0.41 |

- **Trigger rate:** spike at some look in 5% to 9% of windows with a trailing sd (counts: silver 175/2,089 and 140/1,900 in W1/W2, WTI 163/2,054 and
  175/1,972, FX 24 to 29 of about 440 in W2); eligible Try A trades 857 in W1+W2 (about 15 a day), 40 a day in W3 volume per the counts.
- **Literal cheap-side continuation: n = 0** in every series and third (a spike ends at an extreme, so the cheap side is against the move). Try B is
  the favourite side in the same windows and is the only continuation that can be priced.
- **Which side does the spike favour?** Neither, within error. The reversal side wins 12.3% against 14.7% paid (-2.4 points, the usual longshot
  shortfall; the no-spike control wins 11.7% against 14.1%, the same -2.4 points). The favourite side wins 87.4% against 86.4% paid (+1.0 points,
  +0.16c net after fee, z +0.15). A minus B is -3.9c because the two legs add to about minus the spread plus fees; the spike moves it by under 1c
  (A minus control -0.45c, z -0.41). The cheap side after a spike loses exactly as much as the cheap side without one.
- **Per series (information, not tries), reversal PF W1 / W2 and n:** silver 0.87 (122) / 0.80 (96), copper 1.08 (25) / 0.89 (101), WTI 0.57 (115) /
  0.54 (127), natural gas 1.16 (36) / 0.52 (134), EURUSD W2 0.29 (19), GBPUSD 2.28 (16), USDJPY 0.41 (13), platinum 0.97 (24), palladium 1.16 (29).
  No series is at or above 1.5 with n over 40 in any window; the two above 1.5 are 16 trades. WTI is the worst (PF 0.55 on 242 trades).
- **Prediction check:** PF 0.85 (0.50 to 1.30): observed 0.74, inside the range. Win 16% (14 to 20) and fill 20c (15 to 25): observed 12.3% and 14.7c, both
  missed low (fills were cheaper than guessed, because the next-candle ask on the against-spike side was often already 10c to 15c). Try B PF 0.97: 1.02.
  Control PF 0.85: 0.74. A minus control +1c: -0.45c. All lines of the kill rule failed in both halves except where noted: A PF under 1.5 (both), A minus
  B negative (both), A minus control negative (both), x1.2 PF under 1.0 (both).
- **Killed assumption:** a contract-mid spike on a thin 15 minute market is a liquidity overshoot that reverts. The cheap side after it is priced
  like the cheap side without it; the sweep is mostly information (the underlying moved) or at worst already repriced by the next candle.
- **Caveats:** the mid mixes book moves and underlying moves and SPIKE1 cannot separate them (no outside spot for W1 or W2); fills assume the candle
  ask is hittable (no size), which only worsens A (+1c slip PF 0.66 to 0.73); W1 holds only silver, WTI, copper and gas; one trade per window at
  the first spike, so later spikes in the same window are not seen.
- **Capped-probe spec: none** (no edge; nothing positive in both halves). Smallest live probe: none. N +4 (2 tries x 2). Research only; no promote verb.
