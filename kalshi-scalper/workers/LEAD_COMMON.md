# LL1, XS1, RO1 shared rules (cross-asset lead-lag and cross-sectional momentum on Kalshi perps; Strategy Research V2 worker; written 2026-11-06, before any lead-lag, momentum or outcome return was computed)

Discovery only. No live code, no functions/, no index.html, no merge, deploy or promote verb. Three registered tests, one fixed definition each, no lag or threshold scan.

## Data and cut (fixed now)
Source: `origin/perp-data` hourly recorder, read per commit with `git show <commit>:perps/<file>`, de-duplicated on (ts_utc, ticker), loader pattern of `workers/fundcarry/fundcarry.py` (the same loader is imported). 73 snapshots from 2026-10-21 to 2026-11-06, 17 dates, irregular (3 to 7 a day, gaps 0.5 to 12 hours). Only bid, ask, status are used. A quote is missing if status is not active, bid not above 0, ask under bid, or ask over twice the bid (int64 no-ask sentinel).
**CUT: the last third of the recorded dates, 2026-11-01 to 2026-11-06 (6 of 17 dates), is HELD OUT and never read; the code drops those rows on load and no file of a held-out date is opened.** Development = 2026-10-21 to 2026-10-31 (11 dates, 53 snapshots). D1 = 10-21 to 10-26, D2 = 10-27 to 10-31. Day cluster for z = the UTC date of entry. Stock and ETF perps have no development quotes (inactive until 2026-11-05) and are not in any test.

## Universe (cost only, frozen)
A perp qualifies if its median recorded spread (ask minus bid over mid, in bp) over development snapshots is at most 5 bp; no return is used. Expected from siblings: gold, US 500, Tech 100, BTC, ETH, SOL, XRP, silver, copper, WTI. The code prints the list it actually got.

## Cost (stated)
Buy at the recorded ask, sell at the recorded bid (entry and exit rows), plus a fee of 0.12% of notional per side (placeholder, NOT confirmed on Kalshi's fee page), plus funding at the 0.02% of notional per calendar day placeholder, pro rata over the hold. Stress: fee x1.2. The break-even fee per side is reported as information. Control = the same entries with the direction reversed, same cost.

## Verdict rules
Interval returns use mid to mid between CONSECUTIVE recorded samples whose gap is 2 to 8 hours (a pair with another gap is skipped, counted). Overnight and weekend closures of cash-referenced perps are not removed (stated; no return filter).
- **NOT_ENOUGH_DATA:** fewer than 100 development trades or fewer than 30 day clusters. 11 development dates is under 30, so this is certain for all three; the exact date the bar would be met at the recorded rate is reported at the result.
- **FALSIFIED:** at least 100 trades on at least 30 clusters and any of: PF under 1.5 in either half or the whole; mean net not above 0 in whole, D1 or D2; PF under 1.2 at fee x1.2; trigger not better than control; day-clustered z under 5.27.
- **LEAD:** all pass; only then is the held-out part read once, PF under 1.5 there is FALSIFIED.
Below the count bar nothing is declared FALSIFIED: mean, PF, hit rate, gross and the information correlation are reported as information only.

## Duplicate check
Read FUNDP1, RV1 to RV3, CASHSPREAD1, OVN1 to OVN4, PBOOK1 to PBOOK3, PERPEQ1 to PERPEQ4, CPREM1, CLEAD1, CXS1, CSPR1, EVM1 to EVM4. CLEAD1 and CXS1 are crypto perp versus public spot or Hyperliquid, not perp-to-perp across asset classes. RV is index versus members and pairs of stocks. Nobody tested BTC/ETH to index perp lead-lag, cross-sectional momentum across the recorded perps, or gold conditional on Tech 100. Not a duplicate.

## Count
LL1 +1, XS1 +1, RO1 +1: N +3, running about 730,489 (coordinator figure 730,486 plus these), deflated z bar about 5.27.
