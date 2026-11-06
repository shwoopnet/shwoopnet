# CASHSPREAD1 result (2026-11-06): NOT_ENOUGH_DATA (Part A run once on 2026-11-06; Part B has no data)

Registration: `workers/CASHSPREAD1_REGISTRATION.md` (commit 7240d44). Hourly development dates 2026-10-21 to 2026-10-31 (53 snapshots); dates on or after 2026-11-01 were never read. Times New York (US Central is one hour earlier).

**Verdict: NOT_ENOUGH_DATA.** The rule needs at least 15 MID snapshots in each half; the Indices class has 15 in D1 (2026-10-21 to 10-26) and only 6 in D2 (10-27 to 10-31), because the hourly recorder samples about 4 times a day at irregular times and only 21 of the 53 development snapshots fall in a weekday 10:30 to 15:30 New York. Universe: 9 of 10 non-equity perps passed the 90 percent active rule; US 2000 (`KXUS2000PERP`) was inactive in every dev sample and is out. Equities have no dev book at all (inactive until 2026-11-03).

**Information only (not a verdict).** Median spread in basis points of mid, MID against OFF (nights and weekends):

| perp | MID | OFF |
|---|---|---|
| US 500 | 0.82 | 1.03 |
| US Tech 100 | 0.83 | 1.38 |
| gold | 0.25 | 0.26 |
| silver | 1.48 | 2.15 |
| copper | 4.62 | 5.15 |
| platinum | 5.13 | 8.88 |
| palladium | 6.62 | 8.23 |
| aluminum | 6.91 | 8.63 |
| WTI | 2.94 | 3.97 |

Median ratio R = MID/OFF across the 9 perps 0.79 (D1 0.06, D2 1.01); Indices only 0.69 (D1 0.08, D2 0.86), bootstrap by date of the pooled Indices ratio 0.10 to 0.98 (median 0.60). The D1 figure is dominated by a wide overnight or weekend book in D1 (US 500's off-hours median 68.5 bps in D1 against 0.95 in D2); in D2, with 6 MID snapshots, the ratios are 0.86 and 1.01. Direction: every metal and index except gold had a lower MID spread, by 10 to 40 percent. Registered LEAD needed R at most 0.75 in both halves and 15 snapshots per half, so none is claimed. Spreads are already 1 to 7 bps while the assumed fee is 12 bps a side, so the cycle in the spread is small next to the fee.

**Part B (open or close hour against settled, 30 second files): NOT_ENOUGH_DATA.** No `perps30/` file exists on origin/perp-data as of 2026-11-06 16:00 UTC (the 09:10 to 10:30 window had already ended). Read date 2026-12-01 (dev files 2026-11-06 to 2026-11-30, bar 12 days); files from 2026-12-01 stay held out.

N +1 as registered. Research only.
