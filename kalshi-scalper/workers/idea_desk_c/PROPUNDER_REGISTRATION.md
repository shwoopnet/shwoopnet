# PROPUNDER registration (Idea Desk C, Nov 12, 2026)

**Registered before any PROPUNDER price, list or result was read.** No Kalshi request has been made by this desk. Rulings applied: the Head of R&D's message of Nov 12, 19:14Z (points 1a to 1g). Card text: `IDEA_DESK_C_CARDS.md`, card C1. [research]

**Tries: 1.** The price-minus-settle gap at the chosen strike is the rule's edge in other units, so reading it against outcomes is the one try (Head of R&D ruling 1a). It is entered in the Head's ledger at this commit.

## 1. The rule (fixed)

| Item | Fixed value |
|---|---|
| Series | `KXNBAPTS` (NBA player points) ONLY. Rebounds, assists and every other prop series are out. Regular season and NBA Cup games; preseason out |
| Decision minute | The 1 minute candle ending exactly 60 minutes before the game's SCHEDULED start. NBA tickers carry the date and teams but not the time, so the start comes from a field of the lists answer that is fixed before the game. The Testing Desk names that field from the first lists answer, before any candle or result is read, and commits the name. If no such field exists, the card closes as not buildable, with no try spent |
| Strike | For each player-game, the one strike whose YES mid ((YES bid + YES ask) / 2 on that candle) is nearest 0.50. A tie goes to the higher strike. Player-games with no two-sided quote at the decision minute are skipped and counted |
| Band and spread | Bet only if the NO ask (1 - YES bid) is 0.40 to 0.60 and the YES spread is 3c or less |
| Entry | Buy NO at the NO ask plus 1c, 1 contract. The fill is assumed (a taker order a few seconds later fills 60% to 73% of the time at the price seen; the +1c is the convention for that) |
| Fee | 0.07 x p x (1 - p) at the entry price p, rounded UP to the cent on 1 contract |
| Exit | Hold to settlement |
| Count | At most one bet per player-game |

## 2. Cost kill (one way, checked BEFORE any result is read)

Over all qualifying player-games in development: median of (NO ask - NO mid) + the fee as charged. **If it is above 4c, the card is CLOSED** with "efficient, move on" and that number. No outcome is joined until this passes.

## 3. Voids

A market that settles with the price refunded is a void: the fee is kept, so it counts as a fee-only loss of 1 or 2 cents. Voids are counted and the count is printed. **The usual void here is a player who does not play.** What Kalshi's rules do with that case is taken from the market's own rules text in the lists answer (`rules_primary` and `rules_secondary`), quoted into the reader's output before any result is read. It is NOT assumed from memory. If the rules settle a non-playing player's market as NO instead of void, that is a real NO win, and the reader prints how many wins came that way, separately. A rules-text search on the public web is running; any clause found is added here by amendment before data lands.

## 4. Windows and the held-out block

- **Data:** this season's games in the cheap window only (closes from 2026-10-15 00:00 UTC). The last-season pull is NOT planned (ruling 1g).
- **Development:** markets closing from 2026-10-15 00:00 UTC to before **2026-11-06 00:00 UTC**. Read in two halves, split at **2026-10-27 00:00 UTC**.
- **Held-out:** markets closing from **2026-11-06 00:00 UTC** to before **2026-11-13 00:00 UTC**. Pulled, but read once and only on the Head of R&D's go. It is never read before the development read is filed.
- These three blocks are the three windows of the bar.

## 5. Pass and fail

- **Pass:** cash PF 1.5 or better in each of the three windows after the fee, voids counted, and a one-sided z of 5.46 or more, clustered by game day.
- **FALSIFIED:** PF under 1.0 in development with at least 100 bets.
- **No evidence:** fewer than 100 bets in development.
- **Honest size:** about 700 bets in all is the desk's estimate (about 170 games so far, several players a game). At that count the z bar needs a win rate near 62% to 63% at 50c, before clustering by game day, which lowers z further. So this card passes only if the effect is as large as the best practitioner figure, and probably not even then.

## 6. Who is on the other side, and the closest work

- **Other side:** fans who buy a named player to reach a round points number (the "over"), and any maker who quotes the ladder symmetrically around the median.
- **Closest work, and why this differs:**
  - The NHL goals and assists ladder reads (NHLG1, NHLAST1 and the others) failed after the fee. They bought ladder rungs on a different sport and did not take one NO at the mid strike.
  - The sports spread cell failed on both lines. It was a team spread, not a player prop.
  - PROPS1 read the CHEAP side of NBA props.
  - FAMSPORTS was a totals model.
  - None of these was a mid-strike NO on player props.
- **Declined list (7e):** checked row by row by this desk. It is not favourite-and-hold (40c to 60c), not cheap-side, not a lock or parity scan, not taker flow, not market making, not in-game. Desk B re-checks it.

## 7. Requests (for the Testing Desk's lists job; this desk makes none)

- Settled lists of `KXNBAPTS` closing in the cheap window: an estimate of 20 to 40 pages.
- Batched 1 minute candles for the chosen tickers around each decision minute: an estimate of 40 to 80 requests.
- In all, 60 to 120 requests, one run.

## 8. Evidence and odds

- **Evidence:** a practitioner figure for NFL season-long props (60% to 63%). A check of whether any data file backs it is running and is added here by amendment.
- **Odds:** 2% to pass; about 85% that it closes at the cost kill or in development.

## Amendment 1 (Nov 12, 2026, before any PROPUNDER price, list or result was read)

**Rules text (replaces the void assumption in section 3).** Kalshi's public contract terms for NBA player stats (https://kalshi-public-docs.s3.amazonaws.com/contract_terms/NBAPTS.pdf, the generic BASKETBALLENTITYSTAT terms, PDF dated 2026-10-05) say:
- "If a given <entity> or <player> withdraws prior to the commencement of <basketball game>, the markets ... will resolve to the last fair price as determined by the Exchange in its sole discretion." So a player who does not play is NOT refunded at cost. The market settles at a price the exchange chooses.
- "If a given <entity> or <player> retires or is injured during <basketball game>, the markets ... will settle based on the end-of-game statistics if <entity> or <player> have played for at least one (1) second."
- Corrections made after the game do not count.

**What the reader does.**
- A market settled at a "last fair price" (anything other than 0 or 1) is booked at that settlement value, minus the fee. It is printed as its own count with its own sum, beside the rest, and PF is shown with and without those rows.
- The reader also prints how many NO wins came from a player who left the game early. This cannot be told from Kalshi data alone, so it reports the count of NO wins at a settled points total far below the strike (under half of it) as a proxy, labelled as a proxy.
- Before any result is read, the reader quotes the `rules_primary` and `rules_secondary` text of the first market in the lists answer, and states whether it matches the clauses above. A CFTC redline for a different contract (who-leads-a-stat) changes "at least one second" to "entered" the game, so the live wording may differ.

**One mechanical reason for the under, now written down.** An injury exit settles on the stats at that moment, which only ever helps NO. This is a small, real, one-directional effect. It is NOT evidence of a crowd bias.

**Evidence check (replaces section 8's first line).**
- The 60% to 63% figure is 4for4's: NFL SEASON-LONG player props at the closing line, 604 props over 2021 and 2022 (unders 61%). The article has tables but no data file, and one line of its text ("60% in 2020") contradicts its own tables.
- PFF states no sample and no win rate (units only).
- No counted sample exists for single-game NBA prop unders. The nearest counted figure is NBA week 1 GAME totals going under 58.2% (Girdner and co-authors, Journal of Prediction Markets, 2013), a game-total figure, not props, and the authors found the market otherwise efficient.

**Odds cut from 2% to 1% to pass.** The card stands on one practitioner table for a different product and season length.

## Amendment 2 (Nov 12, 2026, Head of R&D note 1, before any data)

The reader prints the verdict line (PF in each window, z) twice. The first line includes every settled row, including did-not-play rows and last-fair-price rows, and **is the registered verdict**. The second line excludes those rows, so that nobody mistakes an injury-report effect for a pricing effect. The early-exit NO wins are printed separately, as Amendment 1 says. If Desk B rules this card a DUPLICATE of PROPS1 or a CLOSED ROW, the card closes unread and the try is removed.

## Amendment 3 (Nov 12, 2026, Desk B's check, before any data)

**Closest work, added to section 6: F7 (Oct 26, V2 README).**
- F7's rule: every game-total ladder market (NBA, NFL, NHL, first-half totals) with a YES mid of 0.40 to 0.60 and a spread of 3c or less; buy NO at the ask and hold.
- F7's result: 1,788 games over 43 days, win 50.8% against a price of 50.7%, net -1.56c. It failed on cost.
- PROPUNDER uses the same band and spread line on a different ladder: one NBA player's points instead of a game total. The named other side is fans who buy a named player to reach a round number, which a game total does not have.
- That makes it F7's rule on a new venue. Whether that counts as a new card or a venue of F7 is the Head of R&D's ruling. F7's failure is the base expectation here.

**Start field (to be confirmed).** All 389 KXNBAPTS markets in the Nov 10 listing carry `occurrence_datetime`. On basketball game markets Desk B found it to be 180 minutes after the listed start, so tip = `occurrence_datetime` minus 180 minutes. The Testing Desk confirms this on the first lists answer, before any candle or result is read, as section 1 requires.

**Counts (Desk B, from the Nov 10 listing, times and tickers only).**
- 108 player-games on 8 games.
- A median of 4 strikes a player, in 5 point steps.
- 373 of 389 markets traded.
- With 5 point steps the nearest strike often falls outside 40c to 60c, so Desk B estimates 4 to 6 bets a game, 700 to 1,000 in all, on about 25 game days.
- The z is clustered by game day, so **5.46 is out of reach this season: this read can FALSIFY, not pass.** Stated plainly, as the Head asked.
