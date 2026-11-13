# Re-read check: NOT_ENOUGH_DATA cards and Desk B's re-open ranking (Idea Desk C, Nov 13, 2026, about 20:00Z)

For the Head of R&D's 19:29Z request. Two workers read the repository and its data branches only: counts and dates, no Kalshi request. **Disclosure:** to get trade rates, the perps worker opened V2's result files, which contain development outcomes. Only counts, rates and dates were taken from them; no outcome is reported here. sha256 values are of the registration file at the branch tip (first 16 characters). [research]

**Counts:** 27 items checked.
- **Readable now: 1** (WXDAYEND's final count).
- **Readable on a date: 9** (CXS1, CLEAD1, RV1, RO1, XS1, OVN3, EARNPERP1, EARNPERP3, ESPORTM1).
- **Cannot accrue: 8.**
- **Closed or retired: 8.**
- **Readable only once a pull is sent: 1** (ECONFADE).

**No registration explicitly allows a re-read after NOT_ENOUGH_DATA without a new try,** except:
- NHLROUND1, which allows one forward application, but its source is now banned;
- COUNT2, which allows a forward read at 40 trades, but at about 0.6 a year;
- ESPORTM1, which allows one read once 150 treated post-cut trades exist.
The crypto three and RV1 say "rerun with a new (frozen) cut". A new cut turns their held-out dates (Nov 1 to 6) into development, so that is a new try in substance; the Head rules.

## Readable now, or on a date

| Item | Verdict | Re-read clause | Registration (sha256, first 16) | Held-out line (HELDOUT_REGISTRY) |
|---|---|---|---|---|
| WXDAYEND final count | **READABLE NOW.** All 40 city-days are on kalshi-pull-data (TESTING_LISTS_BUNDLE Nov 12 18:48Z; WXDAYEND_B's four in TIE3_CANDLES Nov 13 00:07Z); no final count line yet | Not needed: one registered count | testing-desk: WXDAYEND_REGISTRATION.md b70d7abcc935b785 | Row 199: no held-out |
| CXS1 (perps, crypto) | About 2026-11-28 by the worker's arithmetic (the result file says about 2027-01) | "with a new cut" | epic-ptolemy: CXS1_REGISTRATION.md 01278431d885031d | Dev 2026-10-21 to 10-31; held out 11-01 to 11-06; READ (spent) |
| CLEAD1 (perps, crypto) | About 2026-12-03 | "about 2026-11-20 with a new cut" | b211ca7e567ef627 | Same as CXS1 |
| RV1 (stock-perp spreads) | About 2026-12-20 (about 2027-01-15 with a third held out) | "rerun then with a new frozen cut" | b9bd3276ad6d327d | Cut from 2026-11-01; OPEN |
| RO1 (gold and Tech 100 perps) | About 2027-01-20 for development | Not stated; cut fixed at Nov 1 | f448bd6d8768faca | LEAD_COMMON rules; UNKNOWN |
| XS1 (perps cross-section) | About 2027-01-28 for development | Not stated | 6a9b699e90926f32 | LEAD_COMMON rules; UNKNOWN |
| OVN3 (perps weekends) | About 2027-05 (30 weekends) | Not stated | 48be30bae8627443 | Last third held out; READ (spent) |
| EARNPERP1 | Scheduled development read 2027-03-01, likely still short of n (bar about 2027-05-15) | One read, no re-read | 39e26637f214022b | Cutoff constant 2027-03-01 |
| EARNPERP3 | Same date; arm (b) likely cannot reach 30 | Same | df6c7fba111aa927 | Same |
| ESPORTM1 remainder | About 2027-01-13 (the worker's projection from the treated share); only FALSIFIED is reachable; the Head ruled it not re-opened | Yes: one read at 150 post-cut treated trades | epic-ptolemy: ESPORTM1_REGISTRATION.md fdaf79a9c2a0ba1b | Cut 2026-10-03T16:00Z; READ (spent) |
| ECONFADE count | Readable once ECONLAG_CALENDAR's pull lands (it is on main, not yet run); it can only close | Loosening is a new registration | idea-desk-a: IDEA_DESK_A_PROTOCOLS2.md 9bf0e2171d679280 | No row |

## Cannot accrue

| Item | Reason |
|---|---|
| CASHGAP1, CASHOPEN1 | They need Yahoo cash bars (stopped Nov 11); the 30 second recorder still has no open-window files |
| CMD2 | Retired "DO NOT RERUN"; Yahoo source |
| CPREM1 | About 0.2 trades a date; n is not reachable |
| NHLROUND1 | Look time and E come from ESPN, banned since Nov 11 |
| COUNT2 | About 0.6 trades a year |
| XETH1 | No forward reader; about 746 more days at its rate |
| POL-i1 | Never registered; well under 100 jumps a year (Desk B's count) |

## Closed or retired (no read)

GF1 and GF2 (CLOSED UNREAD), FEDIMPL1 (RETIRED UNREAD), POL-i2 (closed on cost), UNRATEROUND (RETIRED UNREAD), W-POL-APPR1 (already run, no survivor), W-CAT-CAL1 finance and indices (CLOSED UNREAD), SPREAD historical block (closed after the cell FAILED).

## Notes for the Head

1. **Sources.** The crypto scorer for CLEAD1, CPREM1 and CXS1 fetches Coinbase and Hyperliquid candles when it runs. Hyperliquid's terms are not recorded, and the owner's Coinbase risk acceptance covers only `record_quotes.py`, so those reads need a terms ruling first.
2. **A recorder that is not producing.** The 30 second perps recorder (`perps30/`) has only one file (Nov 6 close) and no open files, even after the Nov 12 schedule fix. The hourly recorder still shows about 3 to 4 samples a day, not 24.
