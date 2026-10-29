# ESPN1 check: is this a reword of a tested sports idea? (2026-10-29)

No. Every sports test in the ledger uses Kalshi's own prices only; none brings in an outside forecast of the game.

| Test | What it asked | Information used | Why ESPN1 differs |
|---|---|---|---|
| SP1 (2026-10-13) | Buy 88c to 97c favourites 12 hours before the expected end, 12 series | Kalshi hourly ask only, pre-game | Pre-game price bias; ESPN1 is in-play and uses an outside model |
| F6 (2026-10-26) | Tennis pre-match favourites 0.75 to 0.95 | Kalshi quote 5 to 6 hours before close | Favourite-longshot bias; no outside source |
| F7 (2026-10-26) | Buy the under at mid 0.40 to 0.60 on game totals | Kalshi pre-game quote | Public "over" bias on totals; no outside source |
| SC1 (2026-10-27) | Follow or fade a 5c in-play jump in tennis | Kalshi's own 1 minute mids | In-play, but the trigger is Kalshi's own price move |
| FP1 / FP3 | Footprint (trade tape) behind tennis jumps | Kalshi's own trade tape | Order flow on Kalshi, not a game-state model |
| MAKER1 (2026-10-27) | Resting orders on deep tennis markets | Kalshi tape | Execution (earning the spread), not a forecast |
| ARB5 (2026-10-29) | Crossed totals ladders | Kalshi quotes of two strikes | Internal no-arbitrage relation |
| F6/F7 in the 2026-10-08 section | L1 on gold / Bitcoin only (same letters, different tests) | not sports | not related |

ESPN1 is the first test where the signal is an outside, public, timestamped forecast of a game (ESPN's per-play win probability) compared with Kalshi's in-play ask. The nearest earlier idea is GOLDFV1 (an outside price, COMEX gold, against a Kalshi market), which is a different family (commodity, not sports) and was FALSIFIED because Kalshi already priced the outside source. ESPN1 asks the same question of sports: is Kalshi's in-play quote slower than ESPN's model. The research director listed it as never run (`DIRECTOR_2026-10-29.md`).

What the data turned out to carry (checked 2026-10-29 before any Kalshi price was read):
- ESPN's `summary` endpoint has `winprobability` rows (home win %, tie %, playId) for NFL, college football, NBA and MLB. NHL has none, so NHL is out of the universe for that reason only.
- The probability rows carry NO publication time. The core API's `lastModified` on them is a post-game batch rewrite (03:20Z to 06:18Z on a game that ended 03:18Z). The only clock is the linked play's `wallclock` (when the play happened, to the second; present on every play checked in all four leagues). So t = the play's wallclock, and the lag from the play to the moment ESPN shows the number has to be measured live (see the registration).
