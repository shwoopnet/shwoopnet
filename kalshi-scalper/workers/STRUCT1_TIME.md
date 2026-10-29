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

(Results follow below once scored.)
