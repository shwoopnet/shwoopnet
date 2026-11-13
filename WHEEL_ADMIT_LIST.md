# The wheel: shadow admit list (kept by the Head of R&D)

Rules: `ROTATION_LANE.md` on this branch (v1.0, approved by the owner Nov 12, 2026; `docs/ROTATION_LANE.md` on main). No live account figure is in this file. [design]

**What a line here means.** A place on the shadow list: one rule on one market, with one set of parameters shared by every market of that rule. Only signals logged AFTER the batch date count toward its entry block. A place cannot take a live seat until (a) the premise test WHEEL0 has been read, (b) the controller and logging have passed the Chief of Staff's security review, (c) its exact spec has been put to the owner in a popup (batched popups are fine) and merged by the Chief of Staff, and (d) its own forward record clears the entry bar. A rule whose registered research read is falsified loses all its places at once.

**Not on this list and not admissible without the owner's word:** anything on the declined list, including the favourite-late copies retired by name on Nov 11; gold L1 (its own latch and return rule); OICORE and EVENT830 (live under their own rules).

## Batch 1, dated 2026-11-12 (written 19:57Z, on the owner's instruction through the EA to "register the per-market shadows to fill toward 20 to 30")

| # | Rule (registration) | Market | How its forward record can be logged today | State |
|---|---|---|---|---|
| 1, 2 | WITHDRAWN at 20:05Z, the Head of R&D's error: DEPTH1 is not one rule. It is 20 registered tries (10 book features on gold and Bitcoin; Ethereum is not in it), and a rule exists only if one try clears its read from Nov 14 00:00Z. No place before that | none | none | withdrawn |
| 3 | CFRTI-K, the Kalshi-only Bitcoin cheap side with a model edge (Desk A's registration) | Bitcoin 15 minute | replay of the R6 books plus the public candles of the Bitcoin perpetual; same limit after Nov 20. It buys the same market, side and minute as OICORE, so rule 4.7 may keep it off a seat | waits for a log source after Nov 20 |
| 4 | MAPBREAK, the esports break rule (Desk B, with Amendments to 6) | CS2 matches | no recorder follows this series; needs a book or quote recorder with polls 4 seconds apart or closer around the looks | WITHDRAWN Nov 13 00:04Z: out on its own registered screen (step 1, counts only: the 10c gap share was 6.8 and 8.3 percent at the two looks against the 10 percent line) |
| 5 | MAPBREAK | Dota 2 matches | as above | no log source yet |
| 6 | INPLAYJUMP, follow an in-play price jump (Desk B, Amendments to 6; engine by Desk A) | e-soccer | needs in-play quotes of every open match each minute plus a second look; no recorder follows it | no log source yet |
| 7 | INPLAYJUMP | table tennis | as above | no log source yet |
| 8 | INPLAYJUMP | e-basketball | as above | no log source yet |
| 9 | INPLAYJUMP | ITF tennis | as above; markets are open about 18 hours, so the read cost needs sizing first | no log source yet |
| 10 | INPLAYJUMP | challenger tennis | as above | no log source yet |
| 11 | REMATCH, fade the previous loser's fall when the same two players meet again (Desk B, Amendments to 4) | e-soccer | as rows 6 to 8 | no log source yet |
| 12 | ESOCTIE, the e-soccer tie against its walk-forward base rate (History Miner, NOTES to 8; scorers frozen) | e-soccer | as rows 6 to 8 | no log source yet |

## Batch 1b, dated 2026-11-12 (written 20:02Z)

| # | Rule | Market | Log source | State |
|---|---|---|---|---|
| 13 to 23 | The NC15 depth cell as a lane shadow: top-5 size imbalance of 0.50 or more at the last poll at or before 600 seconds to the close, buy at the ask between 10c and 90c, hold (Desk A confirms it has no series-specific parameter) | one place each on silver, copper, WTI oil, EUR/USD, GBP/USD, USD/JPY, HYPE, BNB, AUD/USD, USD/CAD and natural gas 15 minute | replay of the NC15 book recorder, running to Dec 31 | logging can start at once; about 9 in-band signals a day a series on average, far fewer on the thin ones (AUD/USD may never fill a block) |

These eleven places are lane shadows only. **They are not reads of the registered NC15DEPTH1 cell**, whose registration says pooled, never split by series; its pooled read (n 3,400, window from Nov 19) is untouched and no try is spent on it here. Eight of the eleven markets are reserved in the bot to EVENT830; a seat there would need the Chief of Staff to resolve that first.

**20 places on 6 mechanisms. 12 have a log source today (1 to Nov 20, 11 to Dec 31).** (Nov 13 00:04Z: MAPBREAK's CS2 place withdrawn on its registered screen, from 21. MAPBREAK's Dota 2 place stays pending the rest of its candles and an amendment that defines the map state from Kalshi's own data at the look.) (Corrected at 20:05Z from 23 and 14: the two DEPTH1 places were withdrawn.) The owner approved a new public book recorder for the nine sports and esports places on Nov 12 ("Yes, build it"); the Chief of Staff builds it from Desk B's spec.

Shards (an order needs money on its own shard; the owner moves money by hand): the e-soccer series reads exchange 0 on every listed market; CS2 and Dota 2 read exchange 0; the crypto 15 minute markets are on the shard the bot trades today.

Valorant and League of Legends are not admitted for MAPBREAK: they sit under its registered 150 match minimum.


## Next, as their rules are written or their owners confirm (not admitted yet)

- NC15DEPTH1, the registered depth cell on the 11 non-crypto 15 minute series (silver, copper, oil, three currency pairs, HYPE, BNB, AUD/USD, USD/CAD, natural gas): 11 places if Desk A confirms the registered rule can be read one series at a time with unchanged parameters. Its books are already recorded (NC15, to Dec 31), so these would have a log source at once.
- A period-tie rule on NHL periods, NFL quarters and soccer first halves: after the TIE3 measurement, if a cell survives and a rule is written.
- The hourly temperature nowcast (four cities): after its settlement-source and cost measurement.

## What this list needs that research cannot supply

1. **A log source for the nine sports and esports places.** The bot's shadow logger takes price, spread and open interest rules on a series; these rules need state from sibling markets, in-play minute paths or pair histories. The cheaper route is a public book recorder on those series (as R6 and NC15 do for the 15 minute markets) and a replay by the research engines that already exist and are audited. A new continuous recorder is over the charter's runner-minute guideline, so it needs the owner's popup; the Chief of Staff sizes it.
2. **R6 past Nov 20** for the Bitcoin and Ethereum places, or depth fields in the bot's logger.
3. The owner's batched popup with the exact specs before any of these can take a seat.
