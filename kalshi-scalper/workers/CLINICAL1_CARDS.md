# CLINICAL1: feasibility and idea cards (Nov 11, 2026). No outcome scored.

## Feasibility (first)

**Verdict: NOT_ENOUGH_DATA, and probably a thin market family regardless.** Held data holds roughly 45 settled FDA, drug or health-event markets across about 12 series. Not one was open to settlement for 14 days or less from its open time; the medians are 99 to 255 days (typically annual or half-year questions). The 14 day cap can only be met by ENTERING in the last 14 days of a long-lived market, which needs candlestick/price history per market (not held for these). The sample is far below the 100 fills proof bar, and any one series produces a handful of settles a year.

Census from held data (data/flb1.sqlite, theta1.sqlite, newlist1.sqlite; category Science and Technology, plus series names matching FDA/drug/health words). No "Health" category appears in any held table. Volume is not held in these tables. "Listed" = markets present in held files (a sample, not the full Kalshi list). Settled within 14 days = open-to-close of 14 days or less.

| Series | Title (from ticker; not read from Kalshi) | Listed | Settled | Median days open to settle | Settled within 14d |
|---|---|---|---|---|---|
| KXFDANOM | FDA nominee/commissioner type | 11 | 11 | 98.8 | 0 |
| KXFDAAPPROVE | FDA approval of a named product | 5 | 5 | 117.7 | 0 |
| KXFDAANNOUNCE | FDA announcement | 1 | 1 | 160.6 | 0 |
| KXNEWDRUGAPPNTLA / CMPS / BEAM | New drug application (per company) | 6 / 2 / 2 | 6 / 2 / 2 | 168 to 176 | 0 |
| KXEBOLACOUNTRY | Ebola by country | 18 | 18 | 91.3 | 0 |
| KXMEASLES | Measles cases | 2 | 2 | 255.2 | 0 |
| KXH5N1COUNT | H5N1 cases | 1 | 1 | 162.1 | 0 |
| KXAIHEALTH | AI in health (tech, not clinical) | 14 | 14 | 23.6 | 7 (not a clinical-data signal) |
| KXNOBELMED | Nobel medicine | 74 | 74 | 10.6 | 74 (annual, one event, not a trial) |
| KXHEALTHCOST, KXHHSYOUTHCARE | health policy | 7 / 1 | 0 / 1 | 26.5 / 40.6 | 0 |

Frequency: all irregular or annual, one-off per drug or event. Series per-drug (NEWDRUGAPP{TICKER}) means a new series per company, so a census must re-list often.

Gap-fill: NOT done. Kalshi reads were not used (0 of 20; the 22:15Z window had not opened). Planned when open: GET /markets?series_ticker=KXFDAAPPROVE, KXNEWDRUGAPP*, KXFDANOM, status=settled and open, 1 per 3 seconds, to get volume, the full listed count, and each open's close date.

What would fix NOT_ENOUGH_DATA: (1) a history fetch of all Kalshi series with FDA/drug/trial/health in the title or Health category plus candlesticks for the last 14 days before each close (about 20 reads); (2) several weeks of recording new listings and prices (a cheap daily recorder, public reads). Even then expect tens of settles, not 100, so the proof bar is likely unreachable on this family: the 100 fills needs more than 100 distinct events (one probe per event).

## Cards (ranked by speed to a verdict)

Declined-list check (origin/main docs/STRATEGY_LIFECYCLE.md 7e, compared with all 11 rows): none of these is a gold, crypto, probe-market or L1 variant. Card 1 and 2 are hold-to-settlement at a mid price (10c to 90c either side), NOT the declined "favourite-and-hold" (band 88c to 97c favourites); the favourite-and-hold ban (Charter checklist item 5) needs a written owner check before any live version. All are signal = official trial/FDA data, a source no live strategy uses.

1. **PDUFAGOAL1 | directional at one entry, hold to settlement | Idea.** Approval on or before the goal date vs price. Data: FDA press releases and company announcements for goal dates (not a clean public feed); approval outcomes from Drugs@FDA / openFDA. Terms: PERMITTED (FDA). Cheapest test: for the 5 to 11 held FDA markets, compare approve rate vs price at 14 days before close. Prior: base rate of first-cycle approval for PDUFA decisions is high (roughly 70 to 85 percent historically), markets may already price it. Speed: fastest (data held, but n tiny). Risk class: single event, binary.
2. **ADCOMM1 | directional, hold to settlement | Idea.** Advisory committee vote vs final decision (FDA follows the vote about 78 percent, a literature figure to verify). Data: FDA calendar and meeting pages (PERMITTED reuse, no API). Cheapest test: list past meetings and outcomes from fda.gov pages; few per year, so n is dozens, slow to prove.
3. **PHASEBASE1 | pricing vs base rate, hold to settlement | Idea.** Approval and trial success rates by phase and application type (oncology NDA vs rare disease, supplement) vs market price. Data: Drugs@FDA files (PERMITTED), ClinicalTrials.gov (AMBIGUOUS until terms read). Cheapest test: build the base-rate table offline (no Kalshi), then compare with prices on the held markets. Prior: calibration edges are small and slow.
4. **CTSTATUS1 | event-driven, hold | Idea.** Trial primary completion date passing, or a status change (Completed, Terminated, Results posted), as a signal for readout and company markets. Data: ClinicalTrials.gov v2 (AMBIGUOUS, must resolve terms first). Cheapest test: track a fixed watch list for 2 to 4 weeks; no Kalshi market maps cleanly to a single trial today, so mapping is the blocker.
5. **HEALTHCOUNT1 | counts vs official data | Idea.** From the census: Ebola, measles, H5N1 case-count markets against CDC/WHO numbers (data source differs from FDA; terms not reviewed here). Long-dated (90 to 250 days), so the 14 day cap fits only late entry. Slow.

Statement: no card should go beyond Idea. The family looks too sparse for the 100 fill, 2 of 3 windows proof bar. Recommended next step is only the cheap history fetch to confirm the count, and the owner reading the ClinicalTrials.gov terms once.
