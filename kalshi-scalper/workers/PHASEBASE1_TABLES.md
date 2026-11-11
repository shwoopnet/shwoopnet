# PHASEBASE1: offline FDA base-rate tables (Nov 11, 2026)

Source: Drugs@FDA data files, copied Nov 11, 2026 (files dated Nov 9, 2026; FDA asks that a copied item carry its copy date). No Kalshi call, no price, no PF, nothing registered. Descriptive only. CSVs are in `workers/phasebase1/`.

## What the data are, and the central limit

Drugs@FDA holds only APPROVED (status AP) and tentatively approved (TA) submissions. It has one date per submission, the date of the action (status date). It has NO submission date, NO filing date, NO PDUFA goal date, and NO rejected or withdrawn applications (no complete response letters). Consequences:

1. **An approval RATE cannot be computed.** There is no denominator. The asked-for "original NDA/BLA approval rate by type, class and year" and "first-cycle versus later" cannot be built from this source. Only approval COUNTS can.
2. **Action date relative to the goal date cannot be computed.** No submission date and no goal date are in the files.
3. Advisory committee outcomes, CRLs, and pending applications are not here. The CARDS prior of 70 to 85 percent first-cycle approval is a literature figure and is NOT checked by these tables.

## Table 1: original approvals by type and review class (orig_by_type_review_status.csv, orig_approvals_by_year.csv)

All ORIG (original) submissions, ANDA excluded: NDA approved 5,403, BLA approved 507, NDA tentative 128. In 2018 to 2026 the NDA approvals split roughly 30 to 45 percent PRIORITY, 55 to 70 percent STANDARD (for example 2025: 78 standard, 30 priority, 4 unknown). The BLA split in 2024 and 2025 is about 4 to 1 standard because biosimilar BLAs are counted (they are not novel). The ReviewPriority field is blank on about half of all original rows (older records), so class shares are reliable only from about 2018.

## Table 2: novel approvals (novel_approvals_by_year.csv, novel_approvals_by_month.csv, novel_monthly_count_distribution.csv)

Proxy for CDER's novel approvals: ORIG, approved, NDA or BLA, submission class TYPE 1 or TYPE 1/4. It reproduces CDER's published 2023 count (55) exactly and is within 2 of 2024 (52 here, 50 published); treat it as an approximation of FDA's own list (some Type 1 items are excluded from that list, a few novel items carry other codes).

Yearly: 2015 45, 2016 22, 2017 47, 2018 60, 2019 49, 2020 54, 2021 51, 2022 38, 2023 55, 2024 52, 2025 47, 2026 so far (Jan to Oct) 47.

Monthly count distribution (months in the window, n = months):

| Window | n months | mean | median | sd | min | max |
|---|---|---|---|---|---|---|
| 2015 to 2025 | 132 | 3.94 | 4 | 2.20 | 0 | 10 |
| 2020 to 2025 | 72 | 4.12 | 4 | 1.99 | 0 | 9 |
| 2023 to 2025 | 36 | 4.28 | 4.5 | 1.91 | 1 | 8 |

2020 to 2025 count of months with k approvals: 0:1, 1:5, 2:10, 3:14, 4:13, 5:11, 6:9, 7:4, 8:4, 9:1. Share of approvals by calendar month, 2015 to 2025: December (63) and November (56) highest, January (24) lowest (a year-end rush). Recent months: 2026-05 8, 06 3, 07 6, 08 7, 09 9, 10 2 (October 2026 is complete in the files up to Nov 6). Note counts are dispersed slightly more tightly than Poisson at the mean (variance about 4 against a mean of 4), so a Poisson is a fair first model for a monthly count.

Novel approvals by review class (2015 to 2025): 333 priority, 336 standard.

## Market definitions to compare after 22:15Z (NOT read; no Kalshi data was used)

The CARDS file holds series names only, not rule text. Before any comparison read, from Kalshi's public market objects, the rule text and close time of: KXFDAAPPROVE (approval of a named product by a date: needs a per-drug goal date, not in this data), KXNEWDRUGAPP* (a company's new drug application: same), KXFDANOM (nominee, not a drug question). The monthly count table applies only if a Kalshi series asks how many novel drugs FDA approves in a period; none is known from CARDS, so this table is a base rate for a hypothetical count market, and the named-product markets need a goal date and a sponsor history that this source does not carry.

## What the tables cannot tell

Approval probability for any named product; timing against PDUFA clocks; the effect of advisory committee votes; CRLs and delays; pending applications; anything about price. The one usable output is the monthly novel-approval count distribution and the priority/standard mix of approvals. Even a perfect base rate needs a price comparison (after 22:15Z) before it says anything about edge.
