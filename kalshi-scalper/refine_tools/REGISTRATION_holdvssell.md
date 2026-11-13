# S-HOLDVSSELL forward (registered 2026-11-07 before the forward script is run). Read only.
Question: on NEW live early sells, does holding to settlement beat the 25c exit?
Sample: gold (KXGOLD) and Dogecoin (KXDOGE) L1 orders with result "exit", count > 0, order ts AFTER 2026-11-07T20:24:00Z. Sells already read earlier (hvs.py, REGISTRATION.md) are not included. Statistic: per sell D = hold minus actual, both fill-booked, same definitions as hvs.py. Sum in dollars, per contract (sum D / sum contracts), paired bootstrap 90% interval (10,000 resamples, seed 1), hold-better count, would-have-won count (public market result by ticker, no key).
Read point: 30 new early sells. Before that the script prints "NOT AT READ POINT n/30" and nothing is decided.
Rule at 30 new sells:
 1. Per contract hold minus actual above 0 AND the 90% interval entirely above 0: bring a promotion packet idea to main (hold-to-settle for gold and Dogecoin instead of the 25c exit). The packet must note that the exit watch protects the tail (the worst-day comparison goes in the packet, not here). The owner decides; nothing here changes the exit.
 2. Interval includes 0: extend by 30 more new sells and read again.
 3. Point estimate negative: close it (keep the 25c exit).
 Rule 3 is checked first if the point estimate is negative, whatever the interval. Multiplicity: exit-shape tests tried so far = EXIT1's shapes (hold vs every exit shape; exact count is in the research README, not in this checkout) + S-HOLDVSSELL (hold on live gold/Dogecoin) + W-GOLDEXIT180 (shadow of a 180s mid-drop exit). So at least 3 families; a single interval above 0 is not at the research bar and goes to the owner as an idea only. Descriptive and read only. No rule change, no deploy.


Dated clarification Nov 13, 2026 (Head of R&D ruling): rule words restored from commit 44dda69f^; nothing re-decided. 6 markers: 2 verbatim (rules 2 and 3 text, multiplicity), 4 rewritten, 4 sentences: the question and sample (dropped how many sells were read before), the statistic and read point (dropped the pace and the history prior with its dollar figures), rule 1 (dropped the worst day dollar comparison).

Dated clarification 2 Nov 13, 2026 (Auditor B finding): the history prior was removed as figures; its label is put back as words: the history prior is NOT evidence for the forward read.
