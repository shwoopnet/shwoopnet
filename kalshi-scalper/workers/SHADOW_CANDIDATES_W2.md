# SHADOW_CANDIDATES_W2 (Nov 9, 2026, evening). All PF are cash basis (cost = price paid, fee ceil(0.07*C*p*(1-p)*100), C=10).

Honest count: ONE new candidate. The rest of what I scored today failed and is logged as negative.

## 1. GOLD-MOM1 (a filter on gold L1, NOT a new market: same market, side and time, so a variant of what is on deck)
validateShadowRule: {id:"GOLD-MOM1", series:"KXGOLD15M", entry:{sideRule:"favourite", priceMin:0.88, priceMax:0.97, leftMaxSec:390, leftMinSec:330, maxSpread:0.03, extra:"rise3>=0.05"}, contracts:1, registeredAt:"2026-11-09", forwardReadDate:"after 150 shadow signals"}
- History (live gold fills, rows 101 to 307, from REGIME1): dev PF 4.36 n 67; held-out PF 1.61 n 64 (+$24.74). Unfiltered gold in the same rows is PF 0.57 n 64 on the still group.
- Signals per week: about 40. 150 signals in about 4 weeks.
- Needs: the bot logs rise3 already; the shadow logger must record rise3 on every gold signal (main's logger PR).
- Prior: 25% to hold PF 1.3+. Counterparty: none named, a momentum conditioner only.
- Ledger: REGIME1 already counted it (one lead).

## Scored today and FAILED (cheap or mid side on Bitcoin and Ethereum, hist15, 66 to 67 days, cash PF, thirds)
| rule | BTC PF n | ETH PF n |
|---|---|---|
| fav 88-97c at 6 min (this is live L1) | 1.13 n 2,117 (1.18/0.90/1.43) | 1.19 n 1,901 (1.23/1.24/1.10) |
| fav 93-99c at 2 min | 0.99 n 1,784 | 0.96 n 1,728 |
| cheap 4-12c at 10 min | 0.79 n 980 | 0.59 n 999 |
| cheap 30-45c at 6 min | 0.85 n 1,295 | 0.89 n 1,170 |
Not candidates. 8 tries added to the Kalshi ledger (N about 1,500,513).

## What I cannot supply yet
Anything outside gold, Bitcoin, Ethereum, XRP needs a quote read. NEWSER1 (macro series, hourly lead) is still fetching; its cells score after it finishes, and those would need a new quote read (not 15 minute, hourly or slower).
