# T2-1 PERPS-ORPHANS: the forward reads V2 left on its perps program (Testing Desk, Nov 12, 2026)

Table only. Nothing was run, scored, pulled or re-registered. Read from `claude/epic-ptolemy-0amjd9` (registrations, results, scorers by file path), `perp-data` (what has actually recorded) and `REOPEN_RANKING_NOV12.md` on `claude/idea-desk-b`. No live account figure.

## Context for the ruling

V2 registered 52 perps tests (110 tries) and a 500,000 rule sweep on Nov 6 and 7, against the 10 to 20 the owner approved. 35 ran, 17 did not; 5 FALSIFIED; every other read NOT_ENOUGH_DATA; no lead. The default is therefore RETIRE unless a row can actually reach a verdict.

## Finding that needs your word first: I count 20 forward reads, not 11

No committed file lists the 11. Desk B's 137-row perps inventory is not on its branch (the ranking file only quotes the summary: "11 have registered forward reads, the first on Dec 1 and Dec 22, the earnings tests on Jun 1, 2027"). Walking the registrations for reads dated Dec 1, Dec 22 or Jun 1, I find 20: 7 dated Dec 1 (CASHCLOSE1, CASHCLOSE2, CASHGAP1, CASHGAP2, CASHOPEN1, CASHOPEN2, CASHSPREAD1 part B), 10 dated Dec 22 after Amendment 2 (PERPEQ1 to 4 and STOCKPERP1 to 6: SPLAG1, SPAUCT1, SPLIQ1, SPFUND1, SPW1, SPHALT1) and 3 dated Jun 1, 2027 (EARNPERP1 to 3). No subset of 11 matches cleanly, so I did not guess which 11 Desk B meant; this table covers all 20 and you can strike rows. Tries in the 20: 44 (CASH 10, PERPEQ 15, STOCKPERP 14, EARNPERP 5).

## What the data actually is today (checked on `perp-data`)

- **perps30 (the 30 second open and close files, needed by every `...1` CASH test and CASHSPREAD1 part B):** 1 file (2026-11-06 close) after a week. The schedule was repacked on Nov 12 (29 starts a day) and runs to 2027-02-26. So 12 dev days by Nov 30 is possible only if every start from Nov 13 lands.
- **Exchange 1 minute perp candles (`kalshi1m/`, PERPEQ and STOCKPERP and the index CASH2 tests):** still recording to 2027-02-26.
- **Cash reference (`cash1m/`, Yahoo bars):** 4 files. Yahoo stopped Nov 11 and is banned, so any test that needs a cash price after Nov 11 is UNREADABLE.
- Reads with a cutoff: the date is written in the registration text for all; a code-enforced constant I could confirm only for `stockperp/score.py` (refuses dev before 2026-12-22) and `cashw` (date cap at load). Others: not verified in code.

## The 20 rows

Columns: registered at | rule | cutoff | scorer on the branch | data and still recording | tries | events expected by the read date vs needed | recommendation.

| id | registered / rule | cutoff | scorer | data, recording? | N | expected vs needed | rec |
|---|---|---|---|---|---|---|---|
| CASHCLOSE1 | `workers/CASHCLOSE1_REGISTRATION.md` (Nov 6). Index and equity perps, sign of the day's move to 15:39 continues into the 16:00 close | date constant in text: dev closes Nov 6 to 30, files from Dec 1 held out; read Dec 1 | none found (result says no data existed) | perps30 close files (1 exists) plus Yahoo 5 min cash bars: UNREADABLE | 1 | needs 150 trades and 12 dev days; has 1 close file | RETIRE UNREADABLE |
| CASHGAP1 | `CASHGAP1_REGISTRATION.md`. Fade overnight gap of 30 bps or more in the first 10 minutes | same style; open files from Dec 1 held out | none | perps30 open files (0 exist) plus Yahoo gap: UNREADABLE | 1 | needs 150 trades; about 50 trading days (its own text: about 2027-01-15 and only with a recorder extension) | RETIRE UNREADABLE |
| CASHOPEN1 | `CASHOPEN1_REGISTRATION.md`. Perp lag behind the cash tape in the first minutes after the open | same | none | perps30 open files (0) plus Yahoo 1 min cache that had to be fetched weekly from Nov 13: UNREADABLE | 1 | needs 150 trades; own text: about 75 days, "NOT_ENOUGH_DATA by construction" | RETIRE UNREADABLE |
| CASHCLOSE2 | `CASHCLOSE2_REGISTRATION.md`. Index perps, 1 minute candles, same close drift | read Dec 1; shared file `CASHW_COMMON.md` | `cashw/score.py` (frozen) | perp candles yes; cash from `cash1m` (4 days, Yahoo): UNREADABLE past Nov 11 | 2 | about 38 trades by Dec 1; 100 about 2027-01-20 | RETIRE UNREADABLE |
| CASHGAP2 | `CASHGAP2_REGISTRATION.md`. Index candle version of the gap fade | read Dec 1 | `cashw/score.py` | as above: UNREADABLE | 2 | its own text: "cannot reach its bar on two index perps in 2026, a descriptive instrument"; 100 trades about mid 2027 | RETIRE UNREADABLE (and UNDERPOWERED) |
| CASHOPEN2 | `CASHOPEN2_REGISTRATION.md`. Index candle version of the open lag | read Dec 1 | `cashw/score.py` | as above: UNREADABLE | 2 | at most about 64 events; 100 trades about 2027-01-15 | RETIRE UNREADABLE |
| CASHSPREAD1 part B | `CASHSPREAD1_REGISTRATION.md` (part A was hourly data, already read). Early-open spread over settled spread, a cost fact, no trade | date constant in text: perps30 files from Dec 1 never read | none found | perps30 only, NO Yahoo, recording (schedule repacked Nov 12, runs to 2027-02-26) | 1 | needs 12 dev trading days by Nov 30 (1 file today; needs nearly every start from Nov 13 to land) | KEEP once on Dec 1, conditional: 12 dev days exist by Nov 30, else RETIRE UNDERPOWERED. Cheapest row here; asks for no pull |
| PERPEQ1 | `PERPEQ1_REGISTRATION.md` + `PERPEQ_AMENDMENT2.md`. Overnight gap fade, perp mid 16:00 to 08:55 ET, 19 names | Amendment 2: dev to 2026-12-21, first read 12-22, held out 12-22 to 2027-02-01 read from 2027-02-02 only after a LEAD. **The registration's own marker line still says 2026-12-30 (stale against the amendment): needs a committed fix before any read** | none (only `perpeq/costmap.py`) | exchange 1 min candles, perp only, no Yahoo, recording | 2 | about 8 trades a date, about 240 over 30 dates vs 100 trades and 30 clusters needed: reachable | KEEP, conditional on a scorer committed before Dec 22 and the marker fix. The one row here that can reach a verdict on enough events |
| PERPEQ2 | `PERPEQ2_REGISTRATION.md`. Five sector pairs, z of the log ratio over 20 hourly points, 18 to 48 hour hold | as PERPEQ1 | none | candles, perp only, recording | 7 | 15 to 25 trades; 100 trades about 2027-05 | RETIRE UNDERPOWERED |
| PERPEQ3 | `PERPEQ3_REGISTRATION.md`. Fade the perp premium to its reference in cash hours | as PERPEQ1 | none | needs `reference_price`, which only the recorder rows carry (4 a day, about 1.5 in cash hours); the 5 minute snapshot request was never granted | 2 | about 12 trades by Dec 1; 100 about 2027-07 | RETIRE UNDERPOWERED |
| PERPEQ4 | `PERPEQ4_REGISTRATION.md`. SPY vs US500 and QQQ vs US Tech 100, ETF-to-index deviation | as PERPEQ1 | none | candles, perp only, recording | 4 | about 6 trades by Dec 1; its useful output is a descriptive deviation size, not a verdict | RETIRE UNDERPOWERED (the descriptive number can be had from the candles without a test) |
| SPLAG1 | `STOCKPERP_REGISTRATION.md` + `STOCKPERP_AMENDMENT2.md`. Stock perp lags a 3 minute cash move | date constant in `stockperp/score.py`: dev read refused before 2026-12-22; held out from 12-22 read from 2027-02-02 | `stockperp/score.py` (frozen; sha256 in Amendment 2) | needs the Yahoo cash tape: UNREADABLE past Nov 11 | 2 | about 20 triggers a day if the cash existed | RETIRE UNREADABLE |
| SPAUCT1 | same. Convergence to the cash auction prints | same | same | needs cash opens and closes (Yahoo): UNREADABLE | 4 | not reachable without cash | RETIRE UNREADABLE |
| SPLIQ1 | same. Perp-only jump with the cash flat, fade it | same | same | needs the cash tape to show "flat": UNREADABLE | 2 | about 2 a day, 100 trades about 2027-01-20 | RETIRE UNREADABLE |
| SPHALT1 | same. Cash halt, resumption gap | same | same | halts detected from missing Yahoo bars: UNREADABLE | 2 | 0 to 3 events a month, "under 5 trades in development" | RETIRE UNREADABLE |
| SPFUND1 | same. Buy after the daily funding stamp when the previous rate was 2 bp or more | same | same | perp candles plus `funding/` (recording), no cash | 2 | about 1.5 trades a day among the 19 names, so about 46 by Dec 21 vs 100 needed; own prediction NOT_ENOUGH_DATA 97% | RETIRE UNDERPOWERED |
| SPW1 | same. Fade the Sunday reopening gap into Monday 09:25 | same | same | perp candles only, no cash | 2 | about 9 trades a weekend, about 6 weekends by Dec 21 vs 30 weekend clusters; the cluster bar is met 2027-06-06 | RETIRE UNDERPOWERED |
| EARNPERP1 | `EARNPERP1_REGISTRATION.md`, `EARNPERP_COMMON.md`. Post-earnings perp drift, events from EDGAR 8-K Item 2.02 | date constant in text: dev events to 2027-03-01, held out 2027-03-01 to 05-31, read once from **2027-06-01** only after a LEAD; marker line committed | none (`earnperp/calendar.py` and `gap_prior.py` only) | EDGAR calendar (public, not Yahoo; Yahoo daily bars used only for information) and perp candles, recording | 2 | 8 single-name events in the next 30 days; about 60 across the season, 30 or more after screens, vs 30 trades and 20 release dates | RETIRE UNDERPOWERED by default; if you keep one earnings row, keep this one (it can reach NOT_ENOUGH_DATA or FALSIFIED on its own bars by 2027-03-01) |
| EARNPERP2 | `EARNPERP2_REGISTRATION.md`. Spread near a release, depth map | same | none | candles carry no sizes (stated in the registration) | 1 | the same events | RETIRE UNDERPOWERED |
| EARNPERP3 | `EARNPERP3_REGISTRATION.md`. Funding crossing sign and carry materiality | same | none | funding stamps are daily at 21:00Z | 2 | the same events | RETIRE UNDERPOWERED |

## Count of recommendations

KEEP 2 (CASHSPREAD1 part B and PERPEQ1, both conditional). RETIRE UNREADABLE 10 (CASHCLOSE1, CASHGAP1, CASHOPEN1, CASHCLOSE2, CASHGAP2, CASHOPEN2, SPLAG1, SPAUCT1, SPLIQ1, SPHALT1). RETIRE UNDERPOWERED 8 (PERPEQ2, PERPEQ3, PERPEQ4, SPFUND1, SPW1, EARNPERP1, EARNPERP2, EARNPERP3; EARNPERP1 is the one to keep if you want a single earnings row). Total 20. All 44 tries stay counted in N whatever is ruled.

## What I need from you

1. Which 11 you meant, or confirm the 20 as the set.
2. Your ruling per row. Nothing is run or re-registered until then.
3. For the KEEPs: a go to commit (before data) a PERPEQ1 scorer and the registration marker fix, or a decision that PERPEQ1 is also retired.
