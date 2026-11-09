# S-HOLDVSSELL forward (registered 2026-11-07 before the forward script is run). Read only.
Question: on NEW live early sells, does holding to settlement beat the 25c exit?
Sample: gold (KXGOLD) and Dogecoin (KXDOGE) L1 orders with result "exit", count > 0, order ts AFTER 2026-11-07T20:24:00Z. None of the 30 already read (hvs.py, REGISTRATION.md) are included.
Statistic: per sell D = hold minus actual, both fill-booked, same definitions as hvs.py. Sum in dollars, per contract (sum D / sum contracts), paired bootstrap 90% interval (10,000 resamples, seed 1), hold-better count, would-have-won count (public market result by ticker, no key).
Read point: 30 new early sells (about 2 weeks at the recent pace). Before that the script prints "NOT AT READ POINT n/30" and nothing is decided.
History prior (not evidence for the forward read): the 30 sells hold minus actual +21.85 (90% CI -22.0 to +69.5); whole record hold PF 1.32 vs actual 1.20; EXIT1 history PF 0.96 hold vs 0.92 live line. The early window (13 sells before Oct 29) had the opposite sign (-5.24).
Rule at 30 new sells:
 1. Per contract hold minus actual above 0 AND the 90% interval entirely above 0: bring a promotion packet idea to main (hold-to-settle for gold and Dogecoin instead of the 25c exit). The packet must note that the exit watch protects the tail: worst day -36.32 with the exit vs -27.46 held on history. The owner decides; nothing here changes the exit.
 2. Interval includes 0: extend by 30 more new sells and read again.
 3. Point estimate negative: close it (keep the 25c exit).
 Rule 3 is checked first if the point estimate is negative, whatever the interval.
Multiplicity: exit-shape tests tried so far = EXIT1's shapes (hold vs every exit shape; exact count is in the research README, not in this checkout) + S-HOLDVSSELL (hold on live gold/Dogecoin) + W-GOLDEXIT180 (shadow of a 180s mid-drop exit). So at least 3 families; a single interval above 0 is not at the research bar and goes to the owner as an idea only.
Descriptive and read only. No rule change, no deploy.
