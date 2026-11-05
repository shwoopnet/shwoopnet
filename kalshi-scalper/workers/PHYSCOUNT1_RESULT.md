# PHYSCOUNT1 result (2026-11-05): NOT_ENOUGH_DATA for every series (census only; no price, candle or outcome was read)

Registration `workers/PHYSCOUNT1_REGISTRATION.md` (commit efdd7b8, pushed first). Gate: 100 settled events before the cut 2026-10-03T16:00Z.

| Series | Markets | Events | Events with volume 20+ | First close | Verdict |
|---|---|---|---|---|---|
| KXHURCAT (hurricane category) | 419 | 89 | 83 | 2021-08 | under 100 (WXOTHER1 same) |
| KXSPACEXCOUNT (SpaceX launches in a period) | 106 | 15 | 15 | 2024-10 | NOT_ENOUGH_DATA |
| KXHURCTOTMAJ | 35 | 4 | 4 | 2022-09 | NOT_ENOUGH_DATA |
| KXRKLBCOUNT | 5 | 1 | 1 | 2026-09 | NOT_ENOUGH_DATA |
| KXSPACEXREUSE, KXASTEROID, KXSPACEXLAND, KXSTARSHIP25 | 1 to 3 | 1 each | | | NOT_ENOUGH_DATA |
| KXSPACEX, KXSTARSHIPDOCK, KXRKLBORBIT, HURCTOTMAJ | 0 | 0 | | | no settled history |

The full public series list (all categories) had no wildfire, volcano, meteor, tsunami or satellite series beyond those already counted in WXOTHER1 (space weather 1 to 12 events) and EQUAKE1. Nothing is positive, negative or tested; no win rate, PF or control exists.

**Accrual needed.** KXSPACEXCOUNT has 15 events in 24 months (about 0.6 a month), so 100 events needs roughly 7 more years; not worth waiting for. KXHURCAT is seasonal (about 20 events a year): 100 events about the 2027 season, and WXOTHER1 already schedules the 2027-04-15 census, which covers it. Earthquakes: EQUAKE1 forward read about 2027-04-25. No recorder is needed.

**Surprise.** The launch-count family that looked richest (SpaceX launches, partial count public from the manifest) is thin: 15 events, one every two months, so the family cannot reach 100 events inside the research horizon.

N +1 (running about 730,447, z bar about 5.27). Census snapshot not committed (listings only; reproduce with `scalper.wxother1.listing`).
