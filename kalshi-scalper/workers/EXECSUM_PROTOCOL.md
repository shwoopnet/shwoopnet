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

---
# RESULT (Nov 11, 2026), appended after the run

Code: not committed as a module (one-off pull, scratch scripts); every rule above was applied as written. Two parsing fixes made BEFORE any dev or held-out number was read (found because the first pass produced zero entries): candle price keys differ between the live feed (`close_dollars`) and the historical feed (`close`), and rules text capitalises "Executive Orders" in 2 markets (matched case-insensitively). No threshold, k, lag, margin or side rule was changed.

## Settled markets held
| Series | Settled markets | Events | Modelled |
|---|---|---|---|
| KXEOWEEK | 120 | 54 | 96 "above N" markets (Sep 2025 on), 35 weeks; 15 "any", 4 "exactly", 3 "at least", 1 bracket-form and 1 other excluded by the registered rule |
| KXBILLSSIGNED | 11 | 1 | with BILLSCOUNT |
| KXBILLSCOUNT | 95 | 11 | 94 BILLS markets (above or exact, from Jul 2025; bracket "between" markets excluded), 10 months |
| KXMAMDANIEO | 32 | 32 | no (no permitted official source) |
| KXJUDGECOUNT | 54 | 11 | no (no permitted official source) |

## Official count versus the settlement source
Kalshi EO rule: signing date recorded in the Federal Register, numbered Executive Orders incl. revoked ones. GovInfo FR bulk XML (EXECORDR "Executive Order N of <date>", 153 orders, numbers 14286 to 14438 with no gap) reproduces the result of EVERY modelled "above N" EO market: 96 of 96 match. Bills: Kalshi counts bills signed into law incl. joint resolutions; GovInfo public laws (approvedDate, 138 laws in the 119th Congress) reproduce 90 of 94 markets; the 4 misses are KXBILLSCOUNT Mar 2026 (Kalshi says 4 signed, public laws show 2) and Jul 2026 (Kalshi settled 0, public laws show 2). So the bills definition does NOT reconcile exactly (2 of 10 months), the EO definition does.

## Table (cash basis, fee 0.07 p(1-p) unrounded, one contract, daily candle quotes)
| Variant | Settled in universe | Entries | Part | n | cash PF | mean $/contract | z (week cluster) | z (market) | Weeks (clusters) |
|---|---|---|---|---|---|---|---|---|---|
| EOWEEK-D0 | 96 | 53 | dev (earlier 2/3, closes Oct 2025 to Aug 7 2026) | 35 | 2.35 | +0.185 | 1.52 | 2.13 | 16 |
| EOWEEK-D0 | | | held-out (read once, only survivor) | 18 | 0.71 | -0.062 | -0.60 | -0.61 | 9 |
| EOWEEK-D0 | | | pooled | 53 | 1.62 | +0.102 | 1.13 | 1.49 | 25 |
| EOWEEK-D3 | 96 | 47 | dev | 32 | 0.62 | -0.075 | -0.83 | -1.05 | 18 |
| BILLS-D0 | 94 | 26 | dev | 17 | 0.73 | -0.033 | -0.60 | -0.41 | 5 |
| BILLS-D15 | 94 | 28 | dev | 13 | 2.05 | +0.093 | 1.22 | 1.01 | 6 |

Held-out for D3, BILLS-D0 and BILLS-D15 was NOT read: none survived development (D3 PF < 1.5, the BILLS variants under 30 dev entries).

## Verdicts
- EOWEEK-D0: dev survived (PF 2.35, 35 entries), held-out failed (PF 0.71, mean negative), pooled week-cluster z 1.13 against the 5.34 and 4.39 bars: FALSIFIED as a tradeable edge on this sample. (The dev edge was 39 of 53 entries on the NO side of cheap-to-mid priced thresholds; it did not hold forward.)
- EOWEEK-D3: FALSIFIED (dev PF 0.62, n 32).
- BILLS-D0 and BILLS-D15: NOT_ENOUGH_DATA (17 and 13 dev entries, 10 events, 94 settled markets; the bills definition also does not reconcile with the official count).
- Registered rule overall: fewer than 100 settled markets modelled in every variant (96 EO, 94 BILLS), so the series verdict is NOT_ENOUGH_DATA. EOWEEK adds about 3 modelled markets a week, so 100 exist about 2 weeks after Nov 11, 2026; that does not fix the multiplicity bar: z 5.34 needs a much larger sample than 35 weeks can give at these effect sizes (pooled z is 1.13). BILLS adds about 10 markets a month (one event a month): 100 markets in about 1 month, but 10 events means 100 months of clusters for a cluster-level z.

## Note (Nov 12, 2026, from Desk A's re-check c2165e0): GovInfo publication lag
GovInfo publishes the Federal Register 3 to 6 days after signing, so any "count so far this week" derived from GovInfo is blind to the current week (the latest weeks Oct 25 and Nov 1 show zero only because they are unpublished). The EXECSUM development and held-out results used weeks whose counts were complete in GovInfo at the time, but they cannot be applied live without a second count source. See BASERATES1_TABLES.md corrections.
