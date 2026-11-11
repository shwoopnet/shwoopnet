# GEN13 result (2026-11-11): FALSIFIED on development, 0 survivors of 300,000, held-out never read

Registration `workers/GEN13_REGISTRATION.md` (commit 60699e98, before any score), code `src/scalper/gen13.py`, output `workers/GEN13_search_output.txt`, frozen list `workers/GEN13_frozen.json` (empty). Basis: CASH, 1 contract, unrounded fee 0.07 p (1-p) on entry and every sale, mid-price band (ask 0.30 to 0.88, spread <= 0.03, both sides), 17 series (15 GEN12 series + XRP + SOL), development 608,007 rows, 54,336 windows, 77 days.

- Drawn and scored: 300,000 (276,051 with a trade; 249,246 with n >= 150). N 1,100,000, z bar 5.34 (4.36 at N 7,731; the 8,795 bar is about 4.4).
- Cash PF >= 1.0: 2,939. PF >= 1.3 with n >= 150: 8. Stage 1 (PF >= 1.5, n >= 150, 25 days): 1 (PF 1.51, n 157, 41 days, day-clustered z 2.62, below the 3.0 freeze screen and far below 5.34).
- Frozen list: empty. Held-out (370,197 rows, 37 days) NOT read. Survivors: 0. No overlap read, no IMPLEMENT, KILL or RETURN rules.
- Next best development PF (n >= 150): 1.44 (n 151, 11 days), 1.39 (n 255, 27 days), 1.37 (n 157, 55 days).
Verdict: FALSIFIED for this grammar. Matches the prediction (mid-price round trip costs up to 3.5c of fee plus spread).
