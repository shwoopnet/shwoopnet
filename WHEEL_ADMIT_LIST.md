# The wheel: shadow admit list (kept by the Head of R&D)

Rules: `ROTATION_LANE.md` on this branch (v1.0, approved by the owner Nov 12, 2026; `docs/ROTATION_LANE.md` on main). No live account figure is in this file. [design]

**What a line here means.** A place on the shadow list: one rule on one market, with one set of parameters shared by every market of that rule. Only signals logged AFTER the batch date count toward its entry block. A place cannot take a live seat until (a) the premise test WHEEL0 has been read, (b) the controller and logging have passed the Chief of Staff's security review, (c) its exact spec has been put to the owner in a popup (batched popups are fine) and merged by the Chief of Staff, and (d) its own forward record clears the entry bar. A rule whose registered research read is falsified loses all its places at once.

**Not on this list and not admissible without the owner's word:** anything on the declined list, including the favourite-late copies retired by name on Nov 11; gold L1 (its own latch and return rule); OICORE and EVENT830 (live under their own rules).

## Batch 1, dated 2026-11-12 (written 19:57Z, on the owner's instruction through the EA to "register the per-market shadows to fill toward 20 to 30")

| # | Rule (registration) | Market | How its forward record can be logged today | State |
|---|---|---|---|---|
| 1 | DEPTH1, a book-state rule (V2's registration; Desk A's frozen wrapper, sha256 starting 75844354) | Bitcoin 15 minute | replay of the R6 book recorder, which runs to Nov 20; after that an extension of that recorder or depth fields in the bot's logger | waits for a log source after Nov 20 |
| 2 | DEPTH1 | Ethereum 15 minute | as above | as above |
| 3 | CFRTI-K, the Kalshi-only Bitcoin cheap side with a model edge (Desk A's registration) | Bitcoin 15 minute | replay of the R6 books plus the public candles of the Bitcoin perpetual; same limit after Nov 20. It buys the same market, side and minute as OICORE, so rule 4.7 may keep it off a seat | waits for a log source after Nov 20 |
| 4 | MAPBREAK, the esports break rule (Desk B, with Amendments to 6) | CS2 matches | no recorder follows this series; needs a book or quote recorder with polls 4 seconds apart or closer around the looks | no log source yet |
| 5 | MAPBREAK | Dota 2 matches | as above | no log source yet |
| 6 | INPLAYJUMP, follow an in-play price jump (Desk B, Amendments to 6; engine by Desk A) | e-soccer | needs in-play quotes of every open match each minute plus a second look; no recorder follows it | no log source yet |
| 7 | INPLAYJUMP | table tennis | as above | no log source yet |
| 8 | INPLAYJUMP | e-basketball | as above | no log source yet |
| 9 | INPLAYJUMP | ITF tennis | as above; markets are open about 18 hours, so the read cost needs sizing first | no log source yet |
| 10 | INPLAYJUMP | challenger tennis | as above | no log source yet |
| 11 | REMATCH, fade the previous loser's fall when the same two players meet again (Desk B, Amendments to 4) | e-soccer | as rows 6 to 8 | no log source yet |
| 12 | ESOCTIE, the e-soccer tie against its walk-forward base rate (History Miner, NOTES to 8; scorers frozen) | e-soccer | as rows 6 to 8 | no log source yet |

Valorant and League of Legends are not admitted for MAPBREAK: they sit under its registered 150 match minimum.

**12 places on 6 mechanisms. Only the three Bitcoin and Ethereum places have a log source today, and only to Nov 20.**

## Next, as their rules are written or their owners confirm (not admitted yet)

- NC15DEPTH1, the registered depth cell on the 11 non-crypto 15 minute series (silver, copper, oil, three currency pairs, HYPE, BNB, AUD/USD, USD/CAD, natural gas): 11 places if Desk A confirms the registered rule can be read one series at a time with unchanged parameters. Its books are already recorded (NC15, to Dec 31), so these would have a log source at once.
- A period-tie rule on NHL periods, NFL quarters and soccer first halves: after the TIE3 measurement, if a cell survives and a rule is written.
- The hourly temperature nowcast (four cities): after its settlement-source and cost measurement.

## What this list needs that research cannot supply

1. **A log source for the nine sports and esports places.** The bot's shadow logger takes price, spread and open interest rules on a series; these rules need state from sibling markets, in-play minute paths or pair histories. The cheaper route is a public book recorder on those series (as R6 and NC15 do for the 15 minute markets) and a replay by the research engines that already exist and are audited. A new continuous recorder is over the charter's runner-minute guideline, so it needs the owner's popup; the Chief of Staff sizes it.
2. **R6 past Nov 20** for the Bitcoin and Ethereum places, or depth fields in the bot's logger.
3. The owner's batched popup with the exact specs before any of these can take a seat.
