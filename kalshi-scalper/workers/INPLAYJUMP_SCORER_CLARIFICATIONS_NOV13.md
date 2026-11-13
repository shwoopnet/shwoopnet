# INPLAYJUMP: clarifications settled between the two scorers (Idea Desk A with the Testing Desk, Nov 13, 2026, before any candle has landed; copy the Head of R&D and Auditor B)
These settle choices the registration text (Amendments 1 to 6) leaves open, so that the two independent scorers (Desk A's `inplayjump.py`, hash c889c333..., and the Testing Desk's `inplayjump_second.py`) print the same figures. No registered number changes. Where the two builds had differed, the choice below is the one the Desk A engine already implements, so that the audited engine does not change; the Testing Desk adjusts its scorer.

| # | Item | Settled reading |
|---|---|---|
| 1 | In play | clock families: a minute is in play from S + 60 s (candle end at or after S + 60 s); tennis: a minute is in play only if the alive rule holds AT that minute for that contract (3 of the 20 one-minute steps ending at t-1 moved the two-sided mid by 2c or more, both minutes two-sided); the match's first in-play minute (for elapsed minutes) = the first minute at which the alive rule holds for EITHER contract |
| 2 | Elapsed minute | clock: (t - S) / 60 for the jump minute's end ts t; tennis: (t - first in-play minute) / 60 |
| 3 | Placebo search | the NEXT matches after X in (start or open, ticker) order, no wrap-around, up to 20; a failed condition at the placebo match's elapsed minute, INCLUDING the e + 1 ask band or spread, sends the search on; "used" only when a placebo bet is made |
| 4 | Two contracts qualifying in one minute | no bet, counted |
| 5 | Mid and entry | the pre-jump mid is minute t-1's two-sided mid; the entry reads minute t+1's close |
| 6 | Candle time | the END of the minute (`end_period_ts`) |
| 7 | Volume | tested on the jump minute t only (above zero) |
| 8 | Void and no-result | price refunded, fee kept, counted in n, PF, z; a non-void no result is the same |
| 9 | COST KILL (settled) | the kill reads the median one-way cost over EVERY qualifying decision that has a two-sided entry minute (before the ask band and spread filters), as the text says "at qualifying decision minutes" and the Head\'s ruling; a kill that read only entries passing the 4c spread filter could never fire. Print also, as information, the median over the entries that pass the band and spread |
| 10 | Halves (settled) | the bets sorted by (market close time, event ticker); first half = the first n // 2 bets, second half = the rest (a count split in date order, not a calendar midpoint); the same split for the rule and its printed halves |
| 11 | z clusters (settled) | the UTC date of the market\'s CLOSE time for the rule\'s day-clustered z and its largest-day share (a cluster label, not a decision input); the match (one bet each) as the second; the smaller z is used |
| 12 | Placebo buckets and re-weighting | buckets min((round(p x 100) - 20) // 10, 6); a rule bucket with no placebo bet is dropped and the weights renormalised (printing the dropped count is welcome); difference SE = sqrt(sum of weighted bucket variances of the placebo / their sizes + the rule\'s per-bet variance / n) |
| 13 | Hourly screen | "last present close before H" skips hours with no candle; a contract with no candle in an hour adds nothing to that hour\'s test; an hour with no candle for any contract is dead and skipped |
