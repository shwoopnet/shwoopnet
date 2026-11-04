# GOVCOUNT1 result (2026-11-04): DUPLICATE, NOT_RUNNABLE. Nothing fetched, no candle, no price, no outcome read.

Idea: government/official count markets (executive orders, bills signed, Federal Register rules, votes, briefings, FDA, SEC, Truth Social) priced with a count-so-far plus negative binomial pace model, cheap side only (ask 3c to 30c, p >= 3x ask), held to settlement, max 2 per period.

## Duplicate check (README and workers read; grep executive order, Federal Register, count)
- Executive orders (KXEOWEEK, KXEODATE; settle on signing date in the Federal Register): COUNT1 census and COUNT2 table. NOT_RUNNABLE mid-period: publication lags signing by 3 to 7 days (median 5 of 40 recent orders), so the count so far at a mid-week look is not observable; whitehouse.gov/presidential-actions has no dated history. Same pace model and same cheap-bracket rule was the COUNT1 design.
- Bills signed/count (KXBILLSSIGNED, KXBILLSCOUNT, KXBILLSCOUNTWEEKLY, KXHOUSEBILLS, KXSENATEBILLS), press briefings (KXPRESSBRIEFINGCOUNT), nominations (KXTRUMPNOMNUM, 15 events), judges (KXJUDGECOUNT, 11, congress.gov needs a key), pardons (11), deleted posts (7), CBP, BLS, CDC, FRED: COUNT2 table, 1 to 15 settled events or a key or no dated view or a monthly release after the period. All under the 20 event bar.
- SEC, FDA, Steam, GitHub, Wikipedia: COUNT2 found no count or threshold series settling on them.
- Truth Social counts: COUNT1 and COUNT1D (SOURCE_MISMATCH, forward freeze already registered).
- Tornado count (the only government archive family with 20+ events): COUNT2, SOURCE_MISMATCH, 1 trade.
- Senate/House roll call vote counts: no series found in the COUNT2 title/domain search; not re-searched here.

## Census (from those records, no new fetch)
Government count series with a keyless source that returns history AND at least 30 settled periods AND a mid-period observable count: none. Expected treated trades pooled: under 150 (COUNT2 take-up was 0.05 trades per event). Verdict NOT_RUNNABLE / duplicate. No registration hash (nothing to register: no rule was run). Forward plan: none; revisit only if a recorder of whitehouse.gov/presidential-actions post times is built (that would make KXEOWEEK mid-period observable, about 54 events so far, 1 to 5 mixed markets per event), which is infrastructure, not a try. N +0.
