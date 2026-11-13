# Unique-card hunt on the non-order-book recorders (Idea Desk C, Nov 13, 2026, about 18:55Z)

For the Head of R&D's 18:49Z request. No recorder field, Kalshi price, list or result was read (Forensics' ranking is still to come). Only this desk's earlier notes, the registry and the declined list were used. [research]

**Counts:** 6 recorders checked; 0 cards; 6 lines saying why, and what each would need.

| Recorder | Candidate mechanisms considered | Why no unique card |
|---|---|---|
| Politics (quotes every 30 min, results) | Time decay of "by date" markets; approval and generic ballot against polls; mention markets | Decay is the "nothing happens" rule (POLITICS_RULES) or the favourite side above about 70c; approval is POLAPPR1; ballot is BALLOTNO; mentions are MENT1, MENTPERSIST1 and FOMCTEXT. The outside record (`POLITICS_NEAR_RESOLUTION_EVIDENCE_NOV12.md`) supports only the favourite side, which is banned |
| Combos | Combos with a leg already settled (COMBODONE); combo price against the product of leg prices | COMBODONE is this desk's card, waiting for a week of recording; combo against legs is the lock and parity row, and COMBOPRICE1 |
| In-game sports (Kalshi's relayed scores) | Halftime overreaction; score-state win probability against price; break-in-play repricing | Halftime: practitioner-only, about 54% (PF about 1.15), not replicated. A score-state model is the in-game lag family (closed) and a sports pace or count model (excluded). The break flag adds no field the lag tests lacked |
| NWS weather | Forecast against market; reading-driven near-certain brackets | Forecast is the closed weather family; reading-driven is WXDAYEND's mechanism and mostly buys the near-certain bracket |
| Kalshi temperature index | Blend against one station (TEMPBLEND); a station dropping out of the blend near the hour | TEMPBLEND is this desk's card. A dropout shifts the blend by the same composition mechanism, so it is a version of TEMPBLEND, not a new card |
| Perps (minute candles, funding, the 30 second list) | Weekend gap, funding drift, overnight reference | Lane (c) was empty on Nov 13 (`LANES_B_C_NOV13.md`): stock perps do not trade at weekends and the overnight reference is frozen; funding is FUND1 |

## What a card would need

1. **In-game:** a published, replicated in-play effect of 11 points or more at mid prices on a sport Kalshi relays. None was found in two reads (Nov 12 and Nov 13).
2. **Politics:** a non-favourite direction with outside support. None was found (Le 2026, Burgi et al., Page and Clemen).
3. **Index dropout:** if Forensics' ranking shows the station status field changes often near the hour, a TEMPBLEND amendment (not a new card) after TEMPBLEND's held-out read.
