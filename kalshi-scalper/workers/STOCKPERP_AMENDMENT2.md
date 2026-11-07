# STOCKPERP_AMENDMENT2: development cut moved one trading day later, a common cut with PERPEQ (Strategy Research V2 worker; written 2026-11-07, owner decision relayed by main; before any held-out read, nothing scored)

## What changes (only these)
- **Development:** trading dates 2026-11-06 to **2026-12-21** inclusive = **31 trading dates** (16 in Nov 6 to 30, 15 in Dec 1 to 21; Thanksgiving 11-26 closed, 11-27 half day counted). The 30 cluster bar now has one date of slack. **First development read: 2026-12-22, after the close.** The scorer refuses `dev` before that date.
- **Halves:** D1 = 2026-11-06 to 11-30 (16 dates), D2 = 2026-12-01 to 12-21 (15 dates).
- **Held out (never loaded by the scorer):** from **2026-12-22**, for the same number of trading dates as Amendment 1's window (2026-12-21 to 2027-01-29 holds **27** trading dates, excluding 12-25, 01-01 and 01-18; 12-24 is an early close day and counts): 2026-12-22 to **2027-02-01** (27 dates: 7 in Dec 22 to 31, 19 in Jan 4 to 29 excluding 01-18, plus 02-01). Read ONCE on or after **2027-02-02**, only for a LEAD. (Amendment 1 said 'about 27 after counting the closures', now stated exactly.)
- **Scorer edit, the only code change:** `workers/stockperp/score.py` `dev` mode: refuse before 2026-12-22, load 2026-11-06 to 2026-12-21 inclusive (was 12-19 and 12-18). sha256 of the scorer: Amendment 1 version 9a3503e095eb06643818a4b60f062671fcae5e9d3af82c50439a2bbea47cef3d, new 796f78a5750f8b2e13a0bfe11efd5bc308f55225f1781273dc32952af31a60cf (original at cc46567: 57fddb44e4662e76281d8dcce5bdcb3bd4c0a559a002300973d57b6f7a8b2219).

## What does NOT change (explicitly)
Every bar and verdict rule, the cost assumption (close ask and bid plus 12 bp a side, also 14.4 and 24), the universe (19 names, 3 times median spread screen), every trigger, trade and control of SPLAG1, SPAUCT1, SPLIQ1, SPFUND1, SPW1 and SPHALT1, and the N accounting (N +14, running about 1,230,521 to about 1,230,535, bar about 5.3; no try added). The 2026-11-05 pilot and the 2026-11-06 descriptive counts stay as disclosed. sha256 of the original registration (unchanged on disk): cedd078e4cd7f7c9440280dddf45d10923d34ee14cc2fc454ef7db7cc91fec2e. sha256 of Amendment 1 (unchanged on disk, superseded where it conflicts): 57abd1bc587ffca5e43088278fbed58042c6c54d7b747f22df238a4a114ea22f. The hash of THIS file is in the README ledger entry.

## Read dates (all on the single read, 2026-12-22; a later read inside development does not exist)
- **SPLAG1:** pilot rate about 6 trades a day (one trend morning); the 100 trade bar around 2026-11-26 if it holds; 30 clusters possible on 2026-12-18, so a verdict on 2026-12-22 needs trades on 30 of the 31 dates. Else NOT_ENOUGH_DATA.
- **SPAUCT1:** 0 triggers in 16 close reads; expect NOT_ENOUGH_DATA on trades (about 85%).
- **SPLIQ1:** 0 triggers; expect NOT_ENOUGH_DATA (about 90%).
- **SPFUND1:** about 31 trades by 12-21, 100 trades about 2027-03-30; NOT_ENOUGH_DATA.
- **SPW1:** 7 weekends in development (Mondays 11-09, 11-16, 11-23, 11-30, 12-07, 12-14, 12-21); the 30 weekend bar stays 2027-06-06.
- **SPHALT1:** expect 0 to 3 halts; NOT_ENOUGH_DATA.
