# UNDERDOG2X: hand case (2026-11-15 ~16:10Z, before the code and before any price or result is read)

Rules: UNDERDOG2X_REGISTRATION_NOV15.md with Amendment 1. Fee per order = ceil(round(100 x 0.07 x c x p(1 - p), 9)) / 100 at the order's contract count c.

**Entry:**
- **U1:** candles at 700 s (bid 0.70, ask 0.72, so NO ask 0.30: out), 650 s (bid 0.76, ask 0.78, so NO ask 0.24: in band) and 600 s (NO ask 0.22). The FIRST in band is 650 s: NO, e = 0.24.
- **U2:** a candle at 550 s left with YES ask 0.22 does not qualify (under 600 s left). No entry if nothing earlier qualifies.
- **U3:** a one-sided candle (bid 0.00, ask 0.22) is skipped. The next two-sided in-band candle is taken.
- **U4:** YES ask exactly 0.20, or exactly 0.25, enters (inclusive). 0.26 does not.

**Exits (YES entry at e = 0.22 at 700 s; 1 contract for (a) and (b)):**
- **V1:** marks at 400 s bid 0.30, at 240 s bid 0.45 (>= 0.44), at 180 s bid 0.40, at 60 s bid 0.90; result yes.
  - (a): first bid >= 0.44 at or before close - 180 is at 240 s, so sell 0.45. h 0: fees fee(0.22) = ceil(1.2012) = 2c and fee(0.45) = ceil(1.7325) = 2c, net = 0.45 - 0.22 - 0.04 = 0.190.
  - (b): the same sale at 240 s: 0.190.
  - (c), 2 contracts:
    - buy 2 at 0.22: fee = ceil(100 x 0.07 x 2 x 0.22 x 0.78) = ceil(2.4024) = 3c;
    - sell 1 at 0.45 (fee 2c) at 240 s;
    - the other at the first later bid >= 0.80, which is 60 s at 0.90 (fee ceil(0.63) = 1c);
    - total = (0.45 + 0.90) - 2 x 0.22 - 0.03 - 0.02 - 0.01 = 0.85; per contract 0.425.
- **V2:** marks at 400 s bid 0.30, 180 s bid 0.25, 60 s bid 0.50 (>= 0.44); result no.
  - (a): no bid >= 0.44 at or before 180 s, so sell at 180 s at 0.25. Net = 0.25 - 0.22 - (0.02 + ceil(1.3125) = 0.02) = -0.010.
  - (b): sell at 60 s at 0.50: net = 0.50 - 0.22 - 0.02 - ceil(1.75)/100 = 0.240.
  - (c): sell 1 at 0.50 at 60 s (fee 2c). The other never sees 0.80 later, so it is held; result no, it pays 0. Total = 0.50 - 0.44 - 0.03 - 0.02 = 0.01; per contract 0.005.
- **V3:** no bid ever >= 0.44; result yes.
  - (a): sell at 180 s, at that mark's bid 0.30: net = 0.30 - 0.22 - 0.02 - ceil(1.47)/100 = 0.040.
  - (b): hold: 1 - 0.22 - 0.02 = 0.760.
  - (c): both held: (2 - 0.44 - 0.03) / 2 = 0.765.
- **V4 (haircut h = 1c on V1 (a)):** entry 0.23 (fee ceil(1.2397) = 2c), sale 0.44 (fee ceil(1.7248) = 2c). Net = 0.44 - 0.23 - 0.04 = 0.170. The trigger stays at the raw bid 0.45 >= 2 x 0.22.
- **V5 (void, (b) held):** net = -0.02.

**Summary, per series and pooled:**
- third of a trade = by its market's close against the series' constants;
- PF of thirds 1 and 2 pooled, PF of each third, floor(n/2) halves in close order, mean c, day z;
- third 3 is NOT computed in the development read (the reader drops third 3 markets before reading any candle or result);
- "no evidence at n = x" when a series has under 30 entries in a third.
