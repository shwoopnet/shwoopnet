# EVM3 registration (2026-11-06): cheap ladder side after the perp has already moved through the strike (Bitcoin, stale-quote test, N +1)

Written before any trade was built or scored. Discovery only. Data, split, definitions, scale check as `EVM1_REGISTRATION.md` (dev = closing dates to **cut 2026-09-20**, 28 dates, D1 / D2 halves; closes from 2026-09-21 never read).

**Prior, stated first.** The ledger already has RAINFACT1 and WXDEAD1: for weather, quotes follow public facts (214 of 221 books were already 0.99/1.00 when the fact was public) and PERPOI1 (surge in perp open interest) lost 7.9c a contract against a lost -4.6c control on this same ladder. The expected result is the same: quoters read the perp. Probability FALSIFIED or NOT_ENOUGH_DATA: 90 percent.

**Counterparty.** Hourly ladder quoters who leave a standing offer on a strike the perp price has already passed.

**Rule (one definition).** At t = C - 25 min, p = 10000 x perp mid(t) (EVM1 definitions). For each strike K of the event with both YES bid and ask in the ladder candle ending at t: YES leg qualifies if p >= K x 1.003 (the perp is at least 0.3 percent through the strike, above) and YES ask in [0.03, 0.30]; NO leg qualifies if p <= K x 0.997 and NO ask = 1 - YES bid in [0.03, 0.30]. At most one trade per close: the qualifying leg with the highest price. Held to settlement (result). Costs: price paid is the recorded ask, Kalshi taker fee 0.07 x P x (1-P) rounded up to the next cent per contract, variant x1.2 on the fee plus 1c slippage. Net per contract in cents.
**Control:** the same price band and one-per-close rule with the perp on the OTHER side by at least 0.3 percent (YES with p <= K x 0.997, NO with p >= K x 1.003): the ordinary cheap tail. Trigger minus control with a bootstrap by date.

**Numeric prediction.** Qualifying trades are rare: a strike priced at most 30c while the perp is 0.3 percent through it is a very large mispricing (25 minute standard deviation about 0.35 percent). Expected development trades 0 to 15, control 200 to 450. If any occur they win about 70 to 90 percent against a mean price near 0.25, i.e. a positive point estimate on a handful of trades that is NOT_ENOUGH_DATA.

**Kill criteria.**
- NOT_ENOUGH_DATA: fewer than 100 development trades (expected; the date at which 100 would exist at the observed rate is stated in the result).
- FALSIFIED: with at least 100 trades, PF below 1.5 in either half or at x1.2, or trigger minus control not positive in both halves.
- LEAD: at least 100 trades, PF at least 1.5 in both halves and at x1.2, trigger minus control positive in both halves, date-cluster z at least 5.27 (running N about 730,458). Held out third then read once.
N +1 (running about 730,458).
