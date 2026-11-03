# PUB20 result (run once 2026-11-03; registered in 1879dab, code and Amendment 1 in 5739adf, both pushed before the run)

Code `src/scalper/pub20.py`, tests `tests/test_pub20.py`, raw `data/pub20_score.json`. Universe A = EURUSD, GBPUSD, USDJPY, silver, copper, WTI,
natural gas, platinum, palladium 15 minute; B = KXINXU and KXNASDAQ100U 4 pm ladders (47 closes). No crypto, no gold. Look 180 s, fill 120 s
ask, held, C = 10, fee 7% x C x p x (1-p) rounded up. W1 08-06 to 09-04, W2 09-05 to 10-04, **W3 (10-05 on) was NOT read for any rule**
(none passed W1 and W2, or none had 150 trades). N +20, about 728,755, z bar about 5.27. PF is net of fee; x1.2 fee shown in the JSON.
Excess for calendar rules = event trade net minus the control mean (control as amended); for the others it is the mean net per contract.

## One line per rule (verdict | n W1+W2 | window | win rate vs price paid | PF | excess)
- **P01 NR7 compression breakout (Crabel 1990): FALSIFIED.** n 1,431 (W1 474, W2 957), win 13.7% vs 15.8% paid, PF 0.77 / 0.77, mean -2.94c, z -3.76.
- **P02 VOLEXP volatility clustering (Engle 1982): FALSIFIED.** n 2,855 (893, 1,962), win 15.4% vs 15.8%, PF 0.90 / 0.90, mean -1.25c, z -2.23.
- **P03 DOWFRI Friday afternoon: FALSIFIED.** n 538 (186, 352), win 16.2% vs 16.6%, PF 0.90 / 0.90, mean -1.33c; excess vs Tue to Thu +2.8c (z 1.9) and +0.5c, but PF under 1.5.
- **P04 XSREV cross-sectional reversal (Jegadeesh 1990): NOT_ENOUGH_DATA.** n 106 (W1 0, W2 106; only 2 series had history in W1), win 54.7% vs 52.9% paid, PF 1.02, mean +0.31c, z 0.07.
- **P05 NDXLEAD S&P/Nasdaq ladder lead-lag: NOT_ENOUGH_DATA.** n 0 in W1 and W2 (1 trade in W3, unread), 47 closes cannot carry it.
- **P06 FIXES benchmark fix windows (Evans 2018): NOT_ENOUGH_DATA, flagged positive in both halves.** n 41 (16, 25), win 19.5% vs 13.2% paid, PF 1.18 / 1.81 (pooled 1.50), mean +2.4c / +7.5c, excess vs +-2h control +6.1c / +17.1c (z 0.6, 1.1), 29 trade days. z 0.68: no claim.
- **P07 MONTHEND month-end flows (Melvin and Prins 2015): FALSIFIED.** n 1,428 (450, 978; 4 independent month-end days in W1+W2 plus 3), win 15.2% vs 15.3%, PF 0.80 / 0.97, mean -0.97c; excess vs other weekdays +1.4c (z 2.2) / +4.7c (z 4.5) but net still negative, PF under 1.5.
- **P08 SMILE strike-ladder interpolation residual (Breeden and Litzenberger 1978): NOT_ENOUGH_DATA.** 0 trades (largest quote-to-fit gap in 850 strike quotes was 3.07c, trigger 4c; the ladder is smooth to within the spread).
- **P09 SETTLE futures settlement windows: NOT_ENOUGH_DATA.** n 82 (38, 44), win 17.1% vs 15.2%, PF 1.30 / 0.97, mean +2.7c / -0.4c, excess +6.6c / -6.5c; not positive in both halves.
- **P10 REOPEN first hour after a halt: FALSIFIED.** n 158 (47, 111), win 17.7% vs 16.2%, PF 1.64 (z 2.1) / 0.84, mean +6.8c / -2.0c, excess +8.7c / +2.9c; failed W2 PF, 18 trade days. Note W1 alone looked like a hit and W2 reversed it.

## Tally
0 of 10 clear the bar. 5 FALSIFIED (P01, P02, P03, P07, P10), 5 NOT_ENOUGH_DATA (P04, P05, P06, P08, P09). Both big cheap-side rules lose about the
fee and more (NR7 -2.9c, volatility expansion -1.3c); the three calendar rules that had enough trades (P03, P07, P10) beat their controls
but not the price: the controls were even worse than the rule. The pass bar was not close for any rule with n above 150.

## Flag: P06 FIXES (positive net in W1 and W2, stated mechanism). Capped-probe spec, for the owner; NOT a recommendation and nothing here trades
- **Why it is only a flag:** 41 trades on 29 days, z 0.68, W1 n 16; the verdict is NOT_ENOUGH_DATA, W3 (56 trades) is unread; fix windows are
  4 pm London and 10 am New York for EUR/GBP/JPY, 12:00 London for silver. Mechanism: benchmark order flow is price insensitive and reverses
  (Evans 2018, Melvin and Prins 2015); counterparty: dealers filling fix orders. Prior of a real, net-positive edge after the fee: about 3%.
- **Probe:** 1 contract per window, cheap side as registered (ask 0.05 to 0.50, HARD LIMIT 0.50, the highest fill in the data was 0.46), held
  to settlement, weekdays only, those windows only, no size change ever. Fee on 1 contract about 1c to 2c.
- **Worst-day loss, named:** all 7 fix windows (3 pairs x 2 fixes + silver) fill at 0.50 and lose: 7 x about $0.52 = **$3.64**. Typical day: 1.4 trades.
- **Kill rule (decided now):** stop at the first of (a) cumulative net after fees below -$3.00 at any point, (b) 40 fills with PF under 1.5,
  (c) 40 fills with a mean net below 0. A pass at 40 fills is NOT a promotion: it permits a registered 150-fill read.
- **When 40 fills would exist:** at 1.41 trades per trade-day, 29 trade days, about 6 weeks of weekdays from the first order. It also needs
  the same 2 hour offset controls recorded live. Reading W3 now (56 more historic trades) would reach 97 and is a cheaper first step; that read needs
  the owner's go because it spends the frozen holdout.
- No other rule is flagged (P09 and P10 are not positive in both halves; P07 has positive excess but negative net).

## Disclosures
- Amendment 1 (before any result): coarser control keys (P03, P07, P10), sparse ladder candles read as last-5-minutes and first-5-minutes, and the
  P08/P05/P04 power problems stated from quotes only.
- SETTLE times (silver 13:30, copper 13:00, WTI and gas 14:30 Eastern) were from memory and not checked against CME; a wrong time makes P09 a test
  of another window. Trades inside one close are not independent across the 9 series; the z uses day clusters.
- P01/P02 use strikes as the spot at the open (floating strikes); a rounded strike can make a zero move.

## Addendum: P06 W3 read authorised by owner 2026-11-03 (written and pushed BEFORE the read; no W3 outcome seen)
Owner said yes via main: read W3 for P06 ONCE, no re-definition, no re-run. Exact windows (unchanged from the registration): weekdays, windows closing at
16:00 London (UTC 15:00 in BST, 16:00 in GMT after 2026-10-25) and 10:00 US Eastern (UTC 14:00 in EDT, 15:00 in EST after 2026-11-01) for EURUSD,
GBPUSD, USDJPY, and 12:00 London for silver; Central time = Eastern minus 1 hour. W3 = closes 2026-10-05 to the end of the data (56 trades counted
from quotes in `counts`, no result read). Cheap side, ask 0.05 to 0.50, HARD fill limit 0.50, fill at close-120 ask, held, C = 10, fee 7% x C x p x (1-p)
rounded up; control = same series 2 hours before and after (at least 10 control trades) as registered.
**Decision rule (fixed now):** holds up only if W3 mean net after fees is positive AND W3 PF is at least 1.5 AND pooled W1+W2+W3 PF is at least 1.5.
Disclosed in advance: W1 PF was 1.18, below the registered per-window 1.5 bar, so under the strict registered kill rule P06 is already
not a pass; this read decides only whether the owner-authorised probe spec is written. Else FALSIFIED and stop.

### P06 W3 read (run once, 2026-11-03): FALSIFIED
W3 alone: n 56 on 19 days, win 10.7% vs 12.5% paid, PF 0.78 (x1.2 0.77), mean net -2.43c, z -0.62; excess vs +-2h control +1.8c (z 0.45, 56 diffs).
Pooled W1+W2+W3: n 97 on 48 days, win 14.4% vs 12.8% paid, PF 1.09, mean +0.93c, z 0.22, excess +4.2c (z 1.08), highest fill 0.48.
Decision rule: W3 net negative and W3 PF under 1.5, pooled PF under 1.5: **FALSIFIED**. The W2 result (PF 1.81 on 25 trades) was noise. The capped-probe spec above is WITHDRAWN. Stopped; no re-run.
