# EXECSUM_PROTOCOL (registered Nov 11, 2026, BEFORE any outcome is scored)

Politics sub-family d: executive orders, bills signed, bill counts. Card: workers/POLITICS_CARDS_V2.md section d. Declined list (docs/STRATEGY_LIFECYCLE.md 7e) checked: no row concerns politics, counts or cheap-side count ladders. Not a duplicate of L1, OICORE or EVENT830 (different source: an official count; different mechanism: base-rate model; held to settle, different market family).

What was seen before registering: the market LISTINGS (tickers, strikes parsed from rules text, results present in the listing JSON, rules text) were fetched to learn the shape. No outcome has been compared with any price or model. Candle prices are fetched after this commit.

## Data
- Kalshi public API only, throttled 3 s per call, stop and resume on any 429. Series: KXEOWEEK (primary), KXBILLSSIGNED and KXBILLSCOUNT (secondary group "BILLS"). KXMAMDANIEO (New York City mayor orders) and KXJUDGECOUNT (Senate confirmations) have NO permitted official source here (not the Federal Register, not public laws), so they are listed with counts only and NOT modelled.
- Official counts: GovInfo bulk data only (no key). Executive orders: Federal Register daily XML (govinfo.gov/bulkdata/FR), element EXECORDR "Executive Order N of <signing date>". Bills signed: Public Laws XML (govinfo.gov/bulkdata/PLAW/119/public), signing date from the file. Settlement sources per Kalshi rules text: EO weekly = signing date recorded in the Federal Register, numbered Executive Orders incl. later revoked (matches the FR EXECORDR count). Bills = bills signed into law incl. joint resolutions (check against public laws: a public law count by approved date).
- Weeks are Sunday to Saturday (rules text: "Oct 18, 2026 to Oct 24, 2026").

## Markets and thresholds (fixed now)
- EOWEEK: only markets whose rules_primary parses as "above N executive orders" (yes if count > N). Legacy bracket markets ("between a-b") are excluded and counted.
- BILLS: KXBILLSSIGNED "above N" (yes if count > N); KXBILLSCOUNT "exactly N" (yes if count == N) and "between a-b" (a <= count <= b), monthly calendar month (Jan 2025 started Jan 20 12 PM ET: that first event is excluded as a partial period).
- Only SETTLED markets with result yes or no.

## Model
Negative binomial on the trailing counts. For a period starting at day S: use the k = 8 most recent COMPLETE periods that ended at least 7 days before S (weeks) or the 6 most recent complete months ending before S (bills), mean m and sample variance v of those counts; if v > m use NB with variance v (r = m^2 / (v - m)), else Poisson(m). p_yes = P(count > N) (or exact/between for buckets). k, lag and distribution form are fixed and not tuned.

## Decisions (fixed now)
- Variants: EOWEEK-D0 (decision = end of the first day of the week, daily candle), EOWEEK-D3 (end of the 4th day, Wednesday), BILLS-D0 (end of day 1 of the month), BILLS-D15 (end of day 15). Four variants tested.
- Price: Kalshi daily candle (period 1 day) close of yes_ask for a YES buy, 1 minus yes_bid for a NO buy; a missing quote means no entry. No fill-above-quote; one contract.
- Side: for each market evaluate YES at ask a and NO at price b. Enter a side only if its price is in [0.04, 0.30] (cheap side) or in (0.30, 0.88] and the model favours it (p_side > 0.5), never 0.88 to 0.97, and the edge p_side - price - fee >= 0.05. If both sides qualify take the larger edge. At most one entry per market.
- Fee: 0.07 * p * (1 - p), UNROUNDED, p = the price paid. Cash basis: PnL = (1 or 0) - price - fee, held to settlement. No early exits.

## Split and gates
- Development = the earlier two thirds of settled markets in the variant by CLOSE time (split by event so a week is never cut); held-out = the last third, read ONCE and only if the variant survives development. Survive = on development: cash PF >= 1.5 AND at least 30 entries AND mean > 0.
- A pass additionally requires, on dev plus held-out pooled: cash PF >= 1.5, n >= 100 entered markets (settled markets in the variant universe >= 100), and z above the bar for the shared multiplicity: N about 1,100,000 plus this test's 4 variants gives z 5.34 (also reported against N 8,795: z 4.39). z = mean PnL per week-cluster over its standard error (strikes within a week are one cluster), also reported per market.
- Verdicts: NOT_ENOUGH_DATA if the variant has fewer than 100 settled markets (weeks until 100 exist are stated). FALSIFIED if dev has >= 30 entries and cash PF < 1.5 (or mean <= 0). NOT_YET_FALSIFIED only if dev survives AND held-out holds the same gates; otherwise held-out kills it. A variant with too few entries to compute any of this is NOT_ENOUGH_DATA.
- No tuning after seeing a number. Any further variant is a new registration.
