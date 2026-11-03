# AUDIT1 report: was the search real, and does any family beat chance? (2026-11-03, research only, N +0)

Read-only audit. It reads `README.md` and `workers/*_RESULT.md`, writes `workers/AUDIT1_TABLE.csv`, and computes everything below
with `cd src && python -B -m scalper.audit1 table` then `... report` (tests: `python3 tests/test_audit1.py`). It changes no result,
runs no strategy, adds no try. The deflated bar the owner set is z about 5.27 at N about 730,000 (the ledger's own running count).

## Short answer

1. The search was real in effort: 379 registered families and 659 table cells were located, kill criteria
   written first, and most results were registered before they were read. It was also narrow: 47% of the families are
   15-minute Bitcoin, Ethereum or gold, and the shapes are mostly "favourite held" and "round trip".
2. The z values are **not consistent with N(0,1) noise** (far too many above 2 and 3), **but they are even less consistent with
   an edge**: for every threshold the left tail (significantly losing) is 1.6 to 2.9 times the right tail (significantly winning).
   The excess over N(0,1) is overdispersion from correlated re-scores and a fee drag, not a bulk of positive results.
3. **No family clears the owner's bar.** The only z above 5.27 that is a registered test are GEN3 (5.66, **void**: universe
   look-ahead, FALSIFIED on a clean file by CORR1), USWEEP1's zero-variance cells (the ledger calls them a statistic artefact) and
   IV1's comparator (its first read was discarded for a look-ahead). The best live candidate, OICORE, is at 4.53 (FALS4 4.42).
4. The one pre-registered holdout that a development pass survived and kept (E3B, XRP and Dogecoin, z +3.97) was followed by a
   live miss (XRP paused 2026-10-28, PF 0.49 over 65 fills). The other holdout "survivor" (GEN3-H1) was a data bug.

## Coverage (what was parsed, honestly)

| | count |
|---|---|
| Family rows (one per registered ID with a result or a registration) | 379 |
| ... high confidence (a "Result" heading in README or a `workers/*_RESULT.md`) | 283 |
| ... hand-read from README prose (SEARCH1, OVERNIGHT, STRATSEARCH42, OICORE, L1, L1-GOLD-FIRST) | 6 |
| ... low confidence (id found only in a paragraph that mentions a verdict word; verdict left `unknown`, the word kept in `verdict_mention`) | 69 |
| ... registered, no result located (mostly forward reads still waiting: FWD1, REV1, R6T, COUNT1, ELECT1, FEDIMPL1, USWEEP2, ...) | 21 |
| Table-cell rows (level `try`: one per row of a results table with a z column) | 659 |
| Families with a parsed z | 238 (63%) |
| Families with a parsed PF pair (discovery, validation) | 144 (38%) |
| Families with a parsed N charged | 127 (34%); they sum to 280,416 of the ledger's roughly 730,000 |
| Verdict words: FALSIFIED 209, NOT_ENOUGH_DATA 36, NOT_YET_FALSIFIED 13, NOT_RUNNABLE 7, NO_WINNER 5, PASSED/SURVIVES/MIXED/DUPLICATE 6, unknown or none 103 | |

Not covered: the 42 S-strategies one by one (one hand row, STRATSEARCH42), the forward ledger and its REF_ rows, the generators'
per-strategy lists (GEN1 to GEN11 are one row each plus the cells their tables print), and any number that appears only in
`data/*.txt` or `studies/`. The dates run from the first README verdict (2026-10-05) to 2026-11-03; a date is the first date in
the text, so a few (FALS3 shows 2026-08-06) are a data date, not a run date. The holdout flag is noisy (24 yes, 239 no, 116
unknown) and is **not used for the survival numbers**; those are hand-read (section 3). Lane and shape were assigned by keywords,
then by a hand list for 230-plus IDs; shape is the least reliable column (`other/unclear` is 17 families).
A z in a note that is arithmetic on a derived quantity (|z| of 15 or more, for example HOUSE3's "z +34", PPW1's "z +32") is dropped
and counted in `n_z_dropped`. A z derived from "mean ... 95% CI" is implemented but rarely appears.

## 1. The z distribution against the null

Unit of analysis: the first reported z of each table cell, and of each family that has prose z values but no table. The first
mention is used, not the largest, so the choice does not select on size. Clean = without USWEEP1 cells with z 5 or more (the
ledger's own "degenerate z" artefact) and without rows labelled pooled or information. Expected counts are for N(0,1):
P(z>2) = 0.0228, P(z>3) = 0.00135.

| Sample | n | z>2 (expected) | z>3 (expected) | z<-2 | z<-3 | mean z | sd | share z>0 |
|---|---|---|---|---|---|---|---|---|
| All cells | 750 | 74 (17.1) | 37 (1.01) | 165 | 89 | -0.67 | 2.92 | 0.38 |
| Clean cells | 711 | 67 (16.2) | 30 (0.96) | 160 | 86 | -0.79 | 2.77 | 0.37 |
| One per family, clean | 211 | 28 (4.8) | 14 (0.28) | 45 | 29 | -0.56 | 3.02 | 0.47 |

Read: against N(0,1) the right tail is enormously enriched (exact binomial p below 1e-20 in the first two rows). That is not
evidence of edges, for three reasons. (a) The sd is about 3, not 1: cells of one family re-score the same trades (discovery,
validation, slices, GEN6's thirteen survivors are one bet), so they are not independent draws. (b) The left tail is larger than
the right at every threshold (sign test on the two tails, right tail at least as large as left: p 0.98 to 1.00 in every sample).
A net-of-fee z drifts negative by construction (the ledger's own finding: "cost is the binding constraint"), so this test is
conservative against the owner's hope, but it is also the honest direction: the search found many significantly losing
cells and fewer significantly winning ones. (c) A mirror test has no power against one or two real edges; it says the
search as a whole did not produce a bulk of winners, not that none exists.

Best-of-k per family (best reported z, k = number of z values the family reported, p = chance of a best that large among k
standard normals): 202 families, 50 with p below 0.05 against 10.1 expected; p-curve among those 50: 44 below 0.025 (binomial p 1.6e-8).
The p-curve assumes independent tests with uniform null p-values; the same dependence breaks it, and the largest z are the
re-scores named above. Treat this as "the right tail is heavier than a naive null", nothing more.

**By lane** (clean cells; right = significantly winning, left = significantly losing; z>2 / z>3 against expected, tail sign test p):

| Lane | families | cells | z>2 (exp) | z>3 (exp) | z<-2 | z<-3 | best z | sign p |
|---|---|---|---|---|---|---|---|---|
| 15-minute crypto+gold (both) | 103 | 228 | 26 (5.2) | 12 (0.31) | 61 | 47 | 5.40 | 1.00 |
| 15-minute crypto | 61 | 127 | 14 (2.9) | 7 (0.17) | 26 | 8 | 4.75 | 0.98 |
| 15-minute gold | 15 | 29 | 2 (0.7) | 0 | 1 | 0 | 2.94 | 0.50 |
| other 15-minute series | 41 | 87 | 4 (2.0) | 2 (0.12) | 15 | 5 | 4.41 | 1.00 |
| hourly ladders | 30 | 58 | 1 (1.3) | 1 (0.08) | 12 | 7 | 5.66 (void) | 1.00 |
| daily/weekly ladders | 14 | 39 | 4 (0.9) | 1 (0.05) | 6 | 4 | 3.71 | 0.83 |
| perps/venues | 21 | 17 | 3 (0.4) | 2 (0.02) | 7 | 3 | 3.83 | 0.95 |
| cost/execution (size, fee, fill comparisons) | 23 | 27 | 10 (0.6) | 4 (0.04) | 8 | 7 | 5.25 | 0.41 |
| economics/macro | 12 | 16 | 1 (0.4) | 0 | 5 | 1 | 2.76 | 0.98 |
| sports | 13 | 20 | 0 (0.5) | 0 | 4 | 1 | 1.84 | 1.00 |
| politics | 3 | 42 | 0 (1.0) | 0 | 14 | 3 | 1.46 | 1.00 |
| weather | 6 | 2 | 0 | 0 | 0 | 0 | -1.55 | 1.00 |
| entertainment | 4 | 2 | 0 | 0 | 0 | 0 | -0.39 | 1.00 |
| other / options | 33 | 17 | 2 (0.4) | 1 | 1 | 0 | 3.05 | 0.50 |

Enrichment, such as it is, sits in the lanes with the most re-scoring: the 15-minute crypto and gold lanes (the generators and
the L1 variants), plus cost/execution, where a z is a comparison (maker beats taker on fills it gets) and not an edge.
Hourly ladders, other 15-minute series, sports, economics, politics, weather and entertainment show no right-tail enrichment
at all. Smallest-cell lanes (weather, entertainment) have too few parsed z to say anything.

**By rule shape** (clean cells): the enriched shapes are favourite held (16 above 2 against 2.7 expected, but 23 below -2),
generator/search (29 against 5.1; 50 below -2), exit/risk rules (4 against 1.1; these are L1-upkeep questions) and filters on
L1 (4 against 0.4; the only shape whose tails lean right, p 0.19 for the tail sign test, 18 cells, all on one set of entries).
Round-trip scalps (5 above 2, 41 below -2), cheap side (2 against 20 below -2), model-vs-price (2 against 11) and structural
locks (0 against 2) have no enrichment; makers have 2 against 4 with a mean z of -2.3.

## 2. Positive in both development halves, and what survives the holdout

Automated flag (first PF pair above 1.0 in both): 18 of 379 families (4.7%; 12.5% of the 144 with a parsed pair). The holdout
flag is too noisy to count survivors automatically, so survival is hand-read from README (every line has its source in
`audit1.DEV_PASSES`):

| Candidate | Development result | Next out-of-sample read | Outcome |
|---|---|---|---|
| L1 | z 1.45 on 30 days (halves +0.71c, +1.22c), below its bar | no frozen holdout; backward windows: z 2.68, 3.20, 68 days 2.52 | persisting, thin, live |
| OVERNIGHT 4 survivors | pooled z 3.46 over 311 rules | forward check 2026-10-08 | NOT_ENOUGH_DATA, later outcome not located |
| E3 XRP, Dogecoin | z 2.37, 2.97 | **E3B holdout z +3.97 (kept)** | survived; live XRP then PF 0.49 over 65 fills, paused |
| L1B Ethereum, gold | z 2.24, 2.73 on older days | none frozen | live; gold kept, Ethereum capped |
| PERP1 | z 2.76 over 17 years | none | decayed: 2022 on is 0.00% |
| FEAT2 | kept set z 3.85 | FEAT2-F, dated | unresolved; monthly gain shrinking |
| GEN3-H1 (hourly ladder) | validation z 5.66 vs bar 5.17 | frozen holdout passed 1 of 2 | **void**: universe look-ahead |
| OICORE | PF 2.28 / 1.85, z 4.53 | no frozen holdout; forward running | unresolved, below the bar |
| GEN7 B01, B02 | PF 3.28 / 1.80, 1.75 / 1.71 | forward ledger | not independent of OICORE |

Survival: of 9 development passes, 2 faced a frozen out-of-sample window and kept their pass (E3B, GEN3-H1); one of those two was a bug and
the other has since missed live. None is a confirmed edge on this evidence. The base rate of the pass itself is also modest: GEN6 on Bitcoin
had 128 of 5,000 pass discovery, 13 pass validation against a family control of 2.7%, and the ledger says they are mostly one bet.
Out-of-sample reads that were pre-registered and failed include SEARCH1 (437 rules, best design z 2.99, holdout best z 1.62 and -0.90c),
E5B, GEN3-H2 and HRSEAS1's frozen slot. STRATSEARCH42 (0 of 42 survive, best z 1.17) was no better than its null's best of 42 (P 0.596),
while OVERNIGHT's best (3.46) did beat its null (P 0.008) and then had no readable forward result.

## 3. Where the live strategies sit

| | L1 (gold first) | OICORE (second slot) |
|---|---|---|
| Sibling tries charged before it was chosen | 8 hypotheses (60 second scalp, H1 to H5, H7) plus a 437-rule search = 445 before its first run, 448 with L2 and L3 registered with it; N about 4,598 by E3 on 2026-10-13 | about 501,174 before GEN6; GEN6 charged 62,163 (Bitcoin: 128 of 5,000 passed discovery, 13 validation); running count 563,337 after it |
| Its own first read | z +1.45, FALSIFIED against 2.1 (positive in both halves) | validation z 4.53; FALS4's re-implementation 4.42 |
| Bar that applied then | 2.1 (undeflated); deflated bar for ~450 tries about 3.7 | about 5.2 |
| Later evidence | backward windows z 2.68, 3.20; 68 days z 2.52; per series Bitcoin 0.81, Ethereum 1.26, gold 2.94 (gold chosen after this split, 3 looks, charged 0) | no frozen holdout; forward rows running, 0 settled at last count |
| Honest status on this table | a thin positive that never met its own bar, kept on later windows and the live record; selection of gold is post hoc | below the owner's bar, best live lead, forward unread |

The table has 14 families dated on or before L1's registration (2026-10-07) because most early results were bold verdict lines
rather than Result sections; the README's own sentence is the source for the 445 to 448 figure, not the CSV. L1's family row and
the L1-GOLD-FIRST row are hand-read and flagged `confidence=manual`.

## 4. Per lane: tries, positives, best z, holdout survivors

(families | clean cells | cells above 2 | best clean z | NOT_YET_FALSIFIED families | frozen-holdout survivors, hand-read)

15-minute crypto+gold 103 | 228 | 26 | 5.40 | 1 | 0 (SS1, SS2, SEARCH1 failed). 15-minute crypto 61 | 127 | 14 | 4.75 | 5 | 1 (E3B, then live miss).
15-minute gold 15 | 29 | 2 | 2.94 | 1 | 0. Other 15-minute series 41 | 87 | 4 | 4.41 | 1 | 0. Hourly ladders 30 | 58 | 1 | 5.66 void | 1 | 1 (GEN3-H1, void).
Daily/weekly ladders 14 | 39 | 4 | 3.71 | 1 | 0. Perps/venues 21 | 17 | 3 | 3.83 | 2 | 0. Economics/macro 12 | 16 | 1 | 2.76 | 0 | 0.
Sports 13 | 20 | 0 | 1.84 | 0 | 0. Politics 3 | 42 | 0 | 1.46 | 0 | 0. Weather 6 | 2 | 0 | none | 0 | 0. Entertainment 4 | 2 | 0 | none | 0 | 0.
Options 2 | 0 | 0 | none | 0 | 0. Cost/execution 23 | 27 | 10 | 5.25 | 1 | 0.

No lane other than 15-minute crypto has ever produced a holdout survivor that was not a bug, and that one went on to miss live.

## 5. The five lanes with the most untested territory by this table

Ranked by Kalshi daily-series contracts traded (the 2026-10-20 census in README: contracts over 69 days) per family in this
table, then checked against the lane's cells. Higher means more market per attempt.

| Rank | Lane | Census volume | Families here | Contracts per family | Why it counts as thin |
|---|---|---|---|---|---|
| 1 | Weather | 165 million (51 series) | 6 | 27.5 million | WX1 (-3.3c), WX3, WXNEW1, FAMWX (duplicate), RAINCAL and USWEEP1's two rule shapes only; the model-vs-forecast angle has one live recorder and no read until 2027-01 |
| 2 | Economics/macro | 61 million (56 series) | 12 | 5.1 million | CPI1, MENT1, ECONNEW1/2, MORTGAGE1, TSA1, NOWCAST1 mostly NOT_ENOUGH_DATA by count (releases are monthly or weekly) |
| 3 | Politics | 15 million (5 series) | 3 | 5.0 million | ELECT1 is a one-night pre-registration with no result yet; no approval or poll-average market has been tested |
| 4 | Daily/weekly ladders | 27 million (commodities 22M + financials 5M) | 14 | 1.9 million | USWEEP1 read 119 of about 13,975 in-scope series with two rule shapes; five daily favourites registered forward |
| 5 | Sports | 9 million (1 series daily; game markets are not in the census) | 13 | 0.7 million | tested mainly through in-play and ESPN models; NOT_RUNNABLE or FALSIFIED on counts, 0 cells above 2 |

Also thin but not rankable by this census (no volume figure): entertainment (4 families, most NOT_RUNNABLE), options (2 families,
STRADDLE1 and BUYDIP1) and the 16 never-tested 15-minute series (7 not trading at all). At the other extreme, 15-minute
crypto and gold absorb 179 of 379 families and most of the N charged (GEN9 51,067, GEN6 62,163, ...).

## What this says about whether the search was real

Real: it is an unusually well-documented search. Rules, bars and kill criteria were written before results, falsifiers were
built (FALS1 to FALS5, CORR1), a look-ahead that produced a "pass" was caught and the pass was voided, placebos and null
best-of-N simulations were run for the first searches, and the ledger kept a running N and a bar. The 209 FALSIFIED verdicts out
of 289 high-confidence or hand-read rows are the search doing its job.

What the numbers say: the z distribution is not a draw from N(0,1); it is overdispersed (sd about 3) from correlated re-scores and
has a heavier left tail than right in every lane and shape except filters on L1 (18 cells on one set of entries). There is **no
lane in which the right tail beats the left**, and no lane where a registered test clears the owner's deflated bar of 5.27 and then
kept it through a clean holdout. The nearest are OICORE (4.53), E3B (3.97, followed by a live miss) and FEAT2 (3.85, shrinking).
The enrichment in the 15-minute crypto and gold lanes is where most of the effort and the most overlapping re-scores are, so it is
what an in-sample search of one narrow area looks like as much as what a weak edge looks like. The data cannot separate those; only
forward reads can, and the table's honest finding is that the forward reads on OICORE, FEAT2, E3F and the five USWEEP1 favourites
are the only things that could change the answer.

Limits of this audit: parse coverage is 63% for z and 34% for N charged; shape and lane are partly keyword based; first-z-per-unit
treats a family's first number as its headline; the mirror test cannot detect one real edge among hundreds of losers; and the
fee-drag null (z centred below zero) is stated, not estimated. Nothing here is a trading result or changes any verdict.

## Correction (2026-11-03, added by the coordinator after APPROVAL1)
AUDIT1 stated that no approval-rating market had been tested. README APP1 (2026-10-21) already ran the Trump-approval ladder on all sides (97 entries, NOT_ENOUGH_DATA), and APPROVAL1 (2026-11-03) added the cheap-side ratio rule (NOT_ENOUGH_DATA, control PF 0.59). Lane coverage in the politics row is therefore wider than the table shows; the table's keyword assignment missed APP1.
