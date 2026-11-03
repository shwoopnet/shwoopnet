# Result: SWING1 (run once on 2026-11-03; W1 and W2 only, frozen W3 unread): FALSIFIED

Registration `workers/SWING1_REGISTRATION.md` (sha256 prefix 3092cee9eabff7e9). Code `src/scalper/swing1.py`, tests `tests/test_swing1.py` (5 pass, synthetic), raw output `data/swing1_result.txt`. Data `data/espn1.sqlite`, college football and MLB game winners, 1,389 games, no new API calls.

| | n | win vs mean ask | mean net | PF | excess vs matched control |
|---|---|---|---|---|---|
| W1 | 150 | 20.0% vs 19.1% | -0.20c | 0.99 | +4.52c (z +1.84) |
| W2 | 152 | 21.7% vs 19.7% | +0.92c | 1.06 | +5.96c (z +2.23) |
| W1+W2 | 302 | 20.9% vs 19.4% | +0.36c | 1.02 | +5.25c (z +2.98) |
| W1+W2 fees x1.2 | 302 | | +0.14c | 1.01 | +5.03c (z +2.86) |
| half 1 / half 2 | 151 / 151 | | -0.31c / +1.03c | 0.98 / 1.07 | +4.42c / +6.07c |
| college football | 94 | 18.1% vs 19.9% | -2.99c | 0.83 | +2.06c (z 0.51) |
| MLB | 208 | 22.1% vs 19.1% | +1.87c | 1.13 | +6.69c (z 3.08) |

Fee cost on these prices: 0.4c (at 5c) to 1.5c (at 30c) a contract, 5% to 8% of the price; the cheap side must win 0.4 to 1.5 points more often than its ask just to break even.

**Verdict by the registered rules: FALSIFIED.** Profit factor 0.99 in W1 and 1.06 in W2, far under the 1.5 bar (and 1.02 pooled). The excess is positive in both halves, but it is not the swing doing anything: the cheap side after a swing wins about as often as its price (20.9% vs 19.4%, +1.5 points, z about 0.7, before a 1c fee), i.e. FAIRLY priced, so there is no overreaction to harvest. The matched control (the cheap side in non-swing in-play minutes, 4,115 game-cell means) loses -4.51c a contract, the ordinary longshot bias, so "swing minus control" looks good only because the control is bad. The market does not systematically over- or under-react to a 25c in-play swing in these two leagues; the price after the swing is about right, and the fee takes what is left. MLB alone is +1.87c (z of the net not significant, 208 trades, one of seven cuts looked at, not a finding); college football is -2.99c.

Frozen W3 (start from 2026-10-03T16:00Z) was not opened (the rule opens it only if W1 and W2 both pass). **No capped-probe spec is written** (nothing to probe). N: +2.
