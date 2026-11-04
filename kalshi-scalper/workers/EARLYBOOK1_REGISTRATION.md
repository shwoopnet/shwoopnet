# EARLYBOOK1 registration (2026-11-04, written before any outcome was joined)

Idea: BOOKS1, BOOKS2, BOOKNCAA1 and SOCCER1 all looked 2 minutes before the start and found Kalshi's underdog ask equal to the de-vigged DraftKings close within about half a cent. Untested: EARLY looks, hours before the start, against the sportsbook OPEN line.

Duplicate check: grep of README and workers for open line, early look, opening line, convergence found only late-resolution convergence (L1) and unrelated rows. Not a duplicate.

Universe: college basketball (KXNCAAMBGAME), the 2,252 events of the BOOKNCAA1 cache; candle files hold 1 minute bid/ask closes from 4 hours before the start, so the looks are -3h and -1h (-6h is not in the cache and was not refetched). Games from 2026-10-03T16:00Z (frozen third) never joined; all cached games are Nov 2025 to Mar 2026. Soccer and the BOOKS1 cache keep no open line and no early candles, so they are out.
Side: the cached cheap side (the close-line underdog). A row is tradable only if the OPEN line also makes that side the underdog (known at the look). Cluster = game.
De-vig: proportional, two-way moneyline, DraftKings, ESPN odds payload.
Looks: last valid candle (spread <= 10c) ending at or before start minus 3h, and minus 1h.
Reading (a) DIAGNOSTIC only, never a trade: gap = DK CLOSE de-vigged q minus ask (close is not known at the look).
Reading (b) TRADE: cheap side ask 3c to 30c, DK OPEN de-vigged q >= 3 x ask, hard limit 0.30, buy at the ask, hold to settlement, max 1 per game, fee 7% x C x p(1-p) rounded up, C = 10.
Caveat stated up front: the ESPN payload gives open and close lines with NO timestamp, so that the open line existed at the look is an assumption (sportsbooks normally post a day ahead).
Prediction: the gap to the open line is larger early than at -2 minutes (median about +1c), but the ask still sits at or below the open line by a few cents, with a q/ask ratio far under 3.
Kill: FALSIFIED if mean net after fees is not above 0 in both halves, or PF under 1.5; NOT_ENOUGH_DATA under 150 trades. Census gate: under about 150 expected treated, report the gap distributions only (descriptive) and NOT_ENOUGH_DATA, and join no outcome.
N +2 (one rule).
