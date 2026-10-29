# STRUCT1 Part B: gold and Dogecoin time structure (information read, Strategy Research V2, 2026-10-29, research only)

Registration: `workers/STRUCT1_REGISTRATION.md` (pushed before scoring). 14 tries.

## 1. What the ledger already covers (checked in `kalshi-scalper/README.md` before any scoring; not tried again)

| Ledger entry | What it tested | Gold | Dogecoin |
|---|---|---|---|
| GOLD1 Part I (2026-10-21) | descriptive UTC blocks Asia / Europe / US / late, gold vs Bitcoin and Ethereum | yes (read as noise, chi-square 6.14 on 3 df) | no |
| SESS1 (2026-10-22) | L1 when the futures session is closed: Saturday, Friday from 21:00 UTC, Sunday before 22:00 UTC, the daily break 21:00 to 22:00 UTC; pooled 7 commodity series | yes (gold closed +1.01c vs open +1.58c; FALSIFIED pooled) | no (not a commodity) |
| S14 | gold reopen gap fade after the daily break | yes (NOT_ENOUGH_DATA, 11 entries) | no |
| IDEAS20B HOURCLOSE / HALFCLOSE (2026-10-23) | window closes at :00 / at :30 | Bitcoin only | Bitcoin only |
| HOUR3 (2026-10-23) | closes at :00 vs the rest, 7 alt crypto series | no | yes (DOGE +2.79c); forward read HOUR3-F registered for 2026-11-12 |
| IDEAS20C HOURCLOSE (2026-10-23) | closes at :00, against each series' own baseline, XRP, Dogecoin, gold | yes | yes |
| IDEAS20D sessions, US open, 8:30 ET (2026-10-23) | UTC 6 hour blocks, US cash open, data release windows | Bitcoin and Ethereum only | Bitcoin and Ethereum only |
| IDEAS100 (2026-10-23) | 3 hour blocks, weekday, minute of the hour, avoid-lists | Bitcoin and Ethereum only | Bitcoin and Ethereum only |
| HOURS1 / HOURS2 (2026-10-27) | 12 to 18 UTC; four 6 hour UTC blocks, pooled over all series | pooled | pooled |
| CAL1 (2026-10-27) | weekday x 16 series | yes | yes |
| REGIME1 (a), (b) (2026-10-29) | skip 22:00 to 02:00 UTC; skip weekends; pooled L1 | pooled | pooled |
| MKTTIME1 (2026-10-29) and FALS1 | skip one 4 hour US Central block (6), one weekday (7), or Saturday and Sunday, per market | yes (20-24 CT lead, BROKEN by FALS1) | yes |

**So not yet tested for gold and Dogecoin:** the quarter of the hour of the close other than :00 (:15, :30, :45; :30 was tested on Bitcoin only), the one hour either side of the Tokyo, London and New York opens (narrower than and straddling MKTTIME1's 4 hour blocks), gold around COMEX's 13:30 ET settlement, and gold's last hour before the 17:00 ET daily close. Gold weekends are MKTTIME1's (skip Sat and Sun) and SESS1's; only the calendar fact (does gold trade at weekends, which days are missing) is looked up below, not scored.

## 2. Gold's calendar (lookup, not a try)

Gold 15 minute markets in the history files (`hs1.load()` plus `fresh.sqlite`, 5,799 markets, 2026-08-06 to 2026-10-29), counted by New York date and by gaps of more than 15 minutes between closes:

- **Saturday: no trading.** At most one market on a Saturday (the one closing at 00:00 ET); none since 2026-09-19.
- **Sunday: from the 18:00 ET reopen only** (22 to 23 markets each Sunday; 65 on 2026-09-20, which looks like a data artefact).
- **Friday close moved.** Through mid September the last Friday market closed at 24:00 ET (gap 42.25 hours to Sunday); from 2026-09-25 it closes at 17:00 ET (gap about 49.5 hours), so Fridays now have 69 markets.
- **Daily break:** Monday to Thursday a 1.5 hour gap after the 17:00 ET close (next close 18:30 ET) in the later weeks; the 17:00 and 18:00 ET hours have fewer markets in the whole history (176 and 215 against about 248).
- **Thursday 03:00 to 05:15 ET:** a recurring gap of 2 to 2.25 hours (13 Thursdays), consistent with a weekly maintenance window.
- **Holidays:** Labor Day (2026-09-07) traded a full day; 2026-10-12 (Columbus Day) had 78 markets (a few missing); one-off gaps of 27 hours (a Friday 21:15 ET), 7.75 hours (a Sunday 10:30 ET) and 4.75 hours (a Monday 15:15 ET) are in the files and may be recorder gaps rather than closures. No full weekday closure is in the history.

So gold weekends are not a block to skip: gold barely has weekend markets (MKTTIME1 already scored Saturday and Sunday for gold, on the Sunday evening markets).

## 3. Result (run once, 2026-10-29): nothing holds in all three thirds

L1's history entries (`tstop1.load()`), gold 1,726 and Dogecoin 2,531, 1 contract, fee rounded per order. Thirds pooled as `tstop1` cuts them (A / B / C). Lift = kept PF minus baseline PF; z = rest minus block per entry, clustered by New York date (positive means the block is worse). 0 zero-volume signal candles among 2,188 gold and Dogecoin entries with volume data, so dropping them changes nothing. Fees x1.2 change nothing at 1 contract (the fee rounds to 1c throughout).

| # | Market | Skip | Removed n (losses) A / B / C | Lift A / B / C | Removed PF A / B / C | z A / B / C | Holds? |
|---|---|---|---|---|---|---|---|
| 1 | gold | close :15 | 162 (12) / 167 (10) / 147 (5) | +0.463 / -0.046 / -0.135 | 0.81 / 1.13 / 1.88 | +2.02 / -0.43 / -0.99 | no |
| 2 | gold | close :30 | 164 (5) / 130 (9) / 123 (9) | -0.134 / +0.041 / +0.202 | 2.03 / 0.88 / 0.92 | -1.03 / +0.56 / +0.92 | no |
| 3 | gold | close :45 | 149 (8) / 136 (9) / 136 (7) | +0.094 / +0.006 / +0.011 | 1.20 / 0.99 / 1.27 | +0.58 / +0.09 / +0.05 | no |
| 4 | Dogecoin | close :15 | 245 (20) / 240 (11) / 185 (9) | +0.498 / -0.047 / -0.033 | 0.72 / 1.43 / 1.23 | +2.78 / -0.38 / -0.42 | no |
| 5 | Dogecoin | close :30 | 233 (9) / 213 (17) / 187 (13) | -0.082 / +0.369 / +0.091 | 1.61 / 0.76 / 0.89 | -0.64 / +2.00 / +0.81 | no |
| 6 | Dogecoin | close :45 | 213 (6) / 198 (9) / 182 (13) | -0.161 / +0.004 / +0.105 | 2.30 / 1.28 / 0.86 | -1.94 / +0.12 / +1.12 | no |
| 7 | gold | Tokyo open +-60 min | 54 (3) / 46 (3) / 61 (2) | +0.045 / -0.001 / -0.054 | 1.06 / 1.02 / 1.95 | +0.49 / -0.02 / -0.65 | no |
| 8 | gold | London open +-60 min | 36 (1) / 35 (1) / 29 (0) | -0.031 / -0.037 / -0.071 | 2.27 / 2.28 / no loss | -0.54 / -1.24 / n/a | no |
| 9 | gold | New York open +-60 min | 50 (3) / 50 (4) / 44 (0) | +0.037 / +0.036 / -0.124 | 1.12 / 0.72 / no loss | +0.31 / +0.57 / n/a | no |
| 10 | Dogecoin | Tokyo open +-60 min | 52 (2) / 51 (5) / 51 (3) | -0.017 / +0.089 / +0.005 | 1.64 / 0.64 / 1.03 | -0.35 / +1.17 / +0.12 | no |
| 11 | Dogecoin | London open +-60 min | 53 (3) / 42 (2) / 40 (0) | +0.011 / +0.006 / -0.069 | 1.15 / 1.18 / no loss | +0.19 / +0.17 / n/a | no |
| 12 | Dogecoin | New York open +-60 min | 56 (2) / 55 (2) / 45 (4) | -0.026 / -0.018 / +0.052 | 1.84 / 1.67 / 0.60 | -0.58 / -0.27 / +1.08 | no |
| 13 | gold | COMEX settle, entry 13:00 to 14:30 ET | 40 (3) / 31 (2) / 41 (3) | +0.082 / -0.002 / +0.049 | 0.73 / 1.05 / 0.92 | +0.95 / -0.07 / +0.49 | no |
| 14 | gold | last hour before 17:00 ET | 22 (2) / 17 (0) / 22 (2) | +0.049 / -0.030 / +0.046 | 0.77 / no loss / 0.75 | +0.67 / n/a / +0.59 | no |

"n/a": the block has no loss in that third, so its per-entry spread is near zero and the cluster z is not meaningful (the script prints -3.8 to -8.3 there). Baseline PF per third: gold 1.434 / 1.005 / 1.296, Dogecoin 1.298 / 1.296 / 1.105.

**Plainly: nothing holds in all three thirds**, on the pooled thirds or on each market's own thirds (same answer on both), at 1 or 10 contracts. No block even reaches the +0.10 lift in two of the three thirds. The pattern is the familiar one: a block that looks bad in one third (the :15 close in A for both gold and Dogecoin, z +2.0 and +2.8; Dogecoin's :30 close in B, z +2.0) is level or better in the other two. The hand-off, settlement and pre-close blocks are 17 to 61 entries a third with 0 to 5 losses, too few to say anything; the London-open blocks are if anything the better entries. The best pooled z over all days is Dogecoin :15 at +1.25 and :30 at +1.24, against a deflated bar of about 5.17.

Prediction (registered): nothing holds (right); at most one block passes two of three thirds (none did); per-third z mostly within plus or minus 1.5 (right: of the 37 readable cells, 3 are above +1.5 and 1 below -1.5).

Tries: 14 (running count about 438,936). Script and raw output in the session scratchpad only (`struct1.py`, `struct1_B.txt`).
