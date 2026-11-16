# NBALADDER: a many-rule search on the NBA player-points ladder (Idea Desk C, Nov 16, 2026; engine family spec; the Head of R&D's order of 16:13Z; written before any price is pulled)

**Question.** Among the player-points rungs (KXNBAPTS) of one game, does any simple rule on timing, rung position, price, recent move, spread, volume or rung age earn more than it costs? The engine searches many rules at once and ranks them; no rule is chosen by hand.

**Why a search and not one idea.** The ladder has about 49 rungs a game and about 7.5 games a day, so the data is large. A hand rule has a weak prior (the late-rung pitch was passed at about 5%). A search is honest only if every cell counts in the deflation, which the engine does.

**Uniqueness and flags.** Closest: SIBHIT (the pace count; its development days are spent for it), PROPS1 (cheap side, closed), PROPUNDER (NO at 50c, closed unread). Not cheap-side (bands 30c to 70c), not favourite-and-hold (the side is a search dimension, not a band rule), not lead-lag (no cross-market price is read), not parity (the sum of rungs is never compared with a total). Family flag: none.

**The clock (a correction to the pitch).** The data has no tip time. `occurrence_datetime` is a schedule-shaped game END estimate (one value per game, on :00 or :30), so the timing feature is **time to scheduled end** = occurrence - D, not time to tip. It uses the same clock check as SIBHIT: one value per game, exactly on :00 or :30, else the game is dropped and counted.

**The grid (computed from the spec; a subset fixed before any price of these markets is read).**
- Decision time D, as time to scheduled end: **120, 60 or 30 minutes**. Rungs closed by D are skipped.
- Price band of the side's ask: **30 to 40, 40 to 50, 50 to 60, 60 to 70 cents**.
- Side: **yes or no** (a search dimension).
- Exit: **H** (hold to settlement) or **M10** (sell at the mark ending 10 minutes before the scheduled end, if the rung is still open; else held).
- Filter (none, or exactly one; additive options as the engine counts them): none (1); recent move over 30 minutes in the rung's YES mid: down 5c or more, flat, up 5c or more (3); rung distance from the player's current line (the same player's rung whose YES mid is closest to 0.50 at D, ties to the higher strike): below it, at it, above it (3); spread at D: 3c or less, 6c or less (2); volume change (last 10 minutes against the 10 before): rising, not rising (2); rung age (D minus the rung's open_time): under 6 hours, 6 hours or more (2). That is 13 options.
- **Rules this spec tries: 3 x 4 x 2 x 2 x 13 = 624.** The spec checker's number and the engine's must match.

**Gates (the Head's, Nov 16).** Each rule must have **3 signals a day or more** (at least 48 trades on the 16 development days), n of 100 or more for a pass, cash PF 1.3 or more at 1c with both halves 1.0 or more, 2c PF 1.0 or more, and Benjamini-Hochberg alpha 0.05 over every cell ever tried (the TALLY). Ranking: dollars a week at 5 contracts, among rules that clear the gates.

**The unit, so n is honest.** A game has about 49 correlated rungs. The engine's `day` is the UTC date (several games share a date). The print adds: the number of games, the number of player-games, and a **z clustered by game**. A pass needs the game-clustered z, and the card states n in games first, rungs second.

**Cost model.** 5 contracts for the dollars-a-week rank, 10 contracts for the engine's PF (fee per order, rounded: the standing form). Haircuts 1c (primary) and 2c. "Candle replay, upper bound, not fill-checked."

**Windows, as epochs (re-derived with timegm).**
- Development: KXNBAPTS closes **1792540800 (2026-10-21) to before 1793923200 (2026-11-06)**.
- **Never pulled:** closes 1793923200 to before 1794528000 (2026-11-13): PROPUNDER's reserve.
- **Validate:** closes **1794528000 (2026-11-13) to before 1796342400 (2026-12-04)**, pulled after Dec 4, read once on the Head's go. This is also SIBHIT-R's fallback window: **one joint read for both, one print, one m.**
- PROPS1's 2025-26 window is not used (no occurrence field).

**Independence.** The development days are the same days SIBHIT and the NBA fade/follow cards read for counts and prices. PROPUNDER (closed unread) is read-exposed. Any pass here still needs the Dec 4 read.

**New code, said plainly (`needs_new_code`).**
1. A ladder-grid plugin (feature builder, the 624 cells, per-cell cash and the print), with a hand case, audited once.
2. A loader extension: candle volume (the generic loader returns bid and ask only).
3. A candle job: live batched candles for the development rungs over [D - 30 min, scheduled end + 30 min], about 210 minutes a rung, 5,851 rungs, about 140 requests at 42 tickers each, **estimated near 185 MB, so two runs** (the 200 MB cap), pacing 5 s.
Nothing is built or pulled until the Head and Auditor B approve this design.

**Prediction (numeric, before any read).** Under no edge the best of 624 cells reaches PF 1.15 to 1.30 by luck on 16 days, so a development winner proves little; P(a rule clears every gate on development and then holds on the joint Dec 4 read) about 4%. Kill fast: no rule with 48 or more trades and PF 1.3 or more at 1c with both halves 1.0 or more, or BH-adjusted nothing survives.
