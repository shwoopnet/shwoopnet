# Row 75 WXREVISE: registration and first count (Nov 12 2026)

Written before the count. Shadow only; no trading code touched; no network except a git read of quote-data. NWS-derived look files and Kalshi quotes only (no Open-Meteo-derived data used; the ens files were not opened).

## Definitions (from the card)
- Revision: change in the NWS forecast high for one (city, target_date) between two looks, abs >= 2 F.
- Favoured bracket: the KXHIGH between-bracket containing the new NWS high.
- Lagged: Kalshi mid move of that bracket over the same minutes under 3c. Entry 12c to 70c, one per city-day, hold to settlement (second arm: 90 minute exit, N counted).
- Existence test (card): revisions of 2 F or more per day across cities; under 1 a day means DROP.

## Constants
- DATA_START = 2026-11-04 (wxens/nws/ first file), DATA_END = 2026-11-12 target dates.
- FEE = 0.07*p*(1-p); costs +0c and +1c; N_SHARED = 9465 plus this test's cells (2 arms x 2 slip levels = 4 cells) = 9469.
- THIRDS by target date: T1 = 2026-11-04..2026-11-06, T2 = 2026-11-07..2026-11-09, T3 = 2026-11-10..2026-11-12. Rule: n < 40 per third = DATA_LIMITED, stop, no PF.
- Held layout: wxens/nws/<date>/<hh>.csv.gz, look in {L0_07 same-day 07 local, L1_07 day-ahead target seen at 07, L1_10 day-ahead target seen at 10}. Quotes at the same slot_ts in wxens/quotes. Results in wxens/results.

## Caveat registered up front
The card needs a look right after a 12Z/18Z model cycle and a quote move "over the same minutes". The held files have at most three looks per target day, hours apart (07 and 10 local), and exist only for hours the recorder ran (18 slots in 8 days). So the 10 minute lag test cannot be measured; only hours-apart moves can.

## Result (first count)
- Files: 18 nws slot files, 120 rows, 14 cities, 82 city-days, target dates 2026-11-04..11-12.
- City-days with 2+ looks: 30. Revisions of 2 F or more: 3 (ATL 11-07 65->67, DEN 11-11 63->66, LAX 11-07 81->83). Per day: 3 / 8 days = 0.4 a day, under 1.
- Existence test FAILS (0.4 per day across 14 cities, under the card's 1 a day). Row 75 is DROPPED on the card's own rule.
- Lagged count: 0 of 3 measurable as defined. Favoured-bracket mids moved 21c, 13c and 11c between looks hours apart (ATL 0.595->0.38, DEN 0.565->0.70, LAX 0.465->0.36), none under 3c, and these are hours not 10 minutes, so no lag is shown.
- Favoured and priced 12c to 70c: 3 of 3 by price, but 0 lagged. n per third: T1 0, T2 2 (ATL, LAX), T3 1 (DEN); all far under 40.
- Verdict: DATA_LIMITED and existence-test DROP. No PF computed (no held-out or validate score; n under 40).
- N: 9465 shared + 4 cells registered = 9469; no cell was scored.
