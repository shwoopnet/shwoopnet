# ELECT1 result (2026-11-04): NOT_YET_FALSIFIED, one election night, no probe (scored once at 12:10 UTC on the registered snapshot)

Registered before the polls closed (workers/ELECT1_REGISTRATION.md; snapshot workers/ELECT1_SNAPSHOT_2026-11-03.csv, reference ratings workers/ELECT1_REFERENCE_2026-11-03.csv). Scored once with `python3 -I src/scalper/elect1.py score workers/ELECT1_SNAPSHOT_2026-11-03.csv`; raw settled rows in workers/ELECT1_RESULTS_RAW.csv, scorer output in workers/ELECT1_SCORE_LOG.json.

| arm | settled n | wins | mean ask | net after fee | net per trade | PF |
|---|---|---|---|---|---|---|
| CONTROL (all cheap-side races, ask 3c-30c) | 65 | 0 | 9.5c | -66.10 | -1.02 per trade (state-clustered bootstrap [-1.21, -0.82] over 33 states) | 0.00 |
| REF (rating says the cheap side has a real chance) | 5 | 0 | 4.5c | -2.41 | -0.48 per trade (bootstrap [-0.61, -0.36], 5 states) | 0.00 |

- By party (REF): R n 4 net -1.99, D n 1 net -0.42. By race type (REF): SENATE n 4 net -1.73, GOV n 1 net -0.68.
- 52 markets were still UNSETTLED at scoring (2028 Senate/governor/chamber control, 2027 governors, House and Senate races not yet called): they are NOT in the table above and carry no verdict. The scorer must be rerun on them as they settle (a continuation of the same registered rule, no new N); until then the result is partial.
- Read: every cheap-side race that settled lost (0 of 70), the same sign as the rest of the cheap-side record (CALIB1: cheap side wins 0.4 to 0.65 of its price). Cap = NOT_YET_FALSIFIED: one election, 33 states, and 52 markets unsettled; no probe spec, no lead. N unchanged.
