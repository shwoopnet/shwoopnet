# Queue item 1: US releases at 10:00 ET or later against the recorded 15 minute windows, and wheel spec lines. Desk B, Nov 13, 2026, written 21:06Z by this desk's clock. No Kalshi price, outcome or candle read; no Kalshi request.

Times are Eastern (EST, UTC-5 after Nov 1: 10:00 ET = 15:00Z, 10:30 ET = 15:30Z, 12:00 ET = 17:00Z, 2:00 PM ET = 19:00Z). EVENT830 covers the 8:30 ET releases (SLOT_CALENDARS.EVENT830: claims, jobs, CPI, PPI, retail, GDP and PCE, 15 windows Nov 5 to Dec 23). A release lands "in" a recorded 15 minute market when the window CLOSING at (or containing) the release time exists in R6 or NC15, which every 15 minute series has around the clock or its own trading hours.

## The official calendars (each page read once by a fetch agent; quotes are the agent's verbatim rows)
| Release | Source | Date and time quoted |
|---|---|---|
| BLS JOLTS (October) | bls.gov/schedule/news_release/jolts.htm | "October 2026 | Dec. 01, 2026 | 10:00 AM" |
| Census, 10:00 AM rows (the page states no time zone; Eastern is an assumption) | census.gov/economic-indicators/calendar-listview-2026.html | Nov 17 Manufacturing and Trade: Inventories and Sales; Nov 19 Advance Services Report; **Nov 25 New Residential Sales** (and steel imports); **Dec 1 Construction Spending**; **Dec 3 Full Report - Manufacturers' Shipments, Inventories and Orders**; Dec 7 two Quarterly Financial Reports; Dec 9 Monthly Wholesale Trade; Dec 10 Quarterly Services Survey; Dec 11 Business Formation Statistics; Dec 16 Manufacturing and Trade: Inventories and Sales; Dec 22 steel imports; **Dec 23 New Residential Sales**; no row in the window is at a time other than 8:30 AM or 10:00 AM |
| EIA Weekly Petroleum Status Report | eia.gov/petroleum/supply/weekly/schedule.php | "The standard release time and day of the week will be at 10:30 a.m. eastern time on Wednesday with the following exceptions"; the exception table lists nothing between Nov 13 and Dec 31, so Wednesdays Nov 18, 25, Dec 2, 9, 16, 23, 30 (derived from the standard rule) |
| EIA Weekly Natural Gas Storage | ir.eia.gov/ngs/schedule.html | "The standard release time and day of the week will be at 10:30 a.m. eastern time on Thursdays with the following exceptions"; exceptions "November 13, 2026 | Friday | 10:30 a.m. | Veterans Day" and "November 25, 2026 | Wednesday | 12:00 p.m. | Thanksgiving Day"; so Nov 13, Nov 19, Nov 25 (12:00), Dec 3, 10, 17, 24, 31 (derived from the standard rule) |
| FOMC | federalreserve.gov/monetarypolicy/fomccalendars.htm (updated Nov 12) | meeting "December" "8-9*"; the page states NO time of day for the statement (2:00 PM ET is the practice, not stated there); minutes "released three weeks after the date of the policy decision" (so about Nov 18 for the Oct 27-28 meeting and about Dec 30 for Dec 8-9, estimates, no date printed) |
Not covered: private releases at 10:00 ET (ISM, University of Michigan, Conference Board, NAR existing home sales) have no government calendar and their terms are not read, so they are left out.

## Which of these are plausible, and the honest counts
EVENT830's mechanism, as the Head states it, is the cheap side (5c to 50c, YES spread 10c or less) bought 3 to 2 minutes before the close of the window that closes AT the release, 1 contract, held. Each line below is a 7g version of it (same rule on a release it does not list); there is no evidence for any of them. Events to Dec 31 (the NC15 and R6 recording stop dates):
| Place | Release windows (close, ET) | Market | Events by Dec 31 | Paper list or shadow |
|---|---|---|---|---|
| EIAPET | Wednesdays 10:30 | WTI oil 15 minute | 7 | paper list (under 30; weekly, about 30 events by mid 2027) |
| EIAGAS | Thursdays 10:30 (and Nov 25 at 12:00) | natural gas 15 minute | 8 | paper list (same reason; the series is on the paused list in the bot but recorded in NC15) |
| FOMC | Dec 9 at 2:00 PM, the statement time not stated on the Fed page; minutes about Nov 18 and Dec 30 | EUR/USD, USD/JPY, GBP/USD, silver | 1 (plus 2 estimated minutes) | paper list, 1 to 3 events |
| JOLTS | Dec 1 at 10:00 | EUR/USD, USD/JPY | 1 | paper list |
| HOUSING and ORDERS | Nov 25 and Dec 23 (new home sales), Dec 1 (construction), Dec 3 (factory orders) at 10:00 | EUR/USD, USD/JPY | 4 | paper list; Census low-impact releases, plausibility low |
The other Census rows (inventories, services, wholesale, steel imports, quarterly reports, business formation) are low-impact; I do not write places for them.

## Wheel spec lines (one rule, one market, shared parameters; EVENT830's own parameters unchanged, the entry minute set by the window that closes at the release)
- **W-EIAPET-WTI:** the EVENT830 cheap-side rule on KXWTI15M in the window closing at 10:30 ET on every Wednesday EIA petroleum release in the quoted schedule. 1 contract, hold. State: Idea, no evidence, paper list only.
- **W-EIAGAS-NATGAS:** the same rule on KXNATGAS15M in the window closing at 10:30 ET on the Thursday storage release (12:00 ET on Nov 25). Idea, paper list only.
- **W-FOMC-FX:** the same rule on KXEURUSD15M, KXUSDJPY15M, KXGBPUSD15M in the window closing at 2:00 PM ET on Dec 9 (confirm the statement time from the Fed's own statement page first). Idea, paper list only; one event is not a test.
- **W-JOLTS-FX:** the same rule on EUR/USD and USD/JPY in the window closing at 10:00 ET on Dec 1. Idea, paper list only.
None can reach 30 events inside the recording period, so none can be a forward test before the recorders stop; a card with 150 entries would need all of them pooled and a longer recording.
