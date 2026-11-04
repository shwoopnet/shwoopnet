# TENNIS1 registration: the CHEAP side of Kalshi ATP and WTA tour-level match-winner markets against a walk-forward Elo built from ESPN results (written 2026-11-04, before any candle was fetched or any match result joined; 2 tries, running count about 730,327 before, +2 after, z bar about 5.27)

Research only. Nothing places an order. No live code, no functions/, no L1, no OICORE, no promote verb. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, DUPLICATE. **Owner rule (strict): cheap side only (ask 3c to 30c). No favourite-side result is computed or printed anywhere in this test, no 15 minute crypto or gold candle is used.**

## 1. Duplicate check (grep of README.md and workers/ for tennis, golf, MMA, UFC, boxing, table tennis, esports, underdog, Elo, Sackmann; SP1, SPORTCONS1, FAMSPORTS, BOOKS1, BOOKS2, INPLAY1, CALIB1, USWEEP*, NEWLIST1, OICORE_SHAPE_INVENTORY)
| Earlier test | Input | Verdict | Why this is not it |
|---|---|---|---|
| F6 (2026-10-27) | Kalshi tennis quote only: favourites 0.75 to 0.95; information line "underdogs under 0.35 -1.93c (z -3.53)" | FALSIFIED / information | a price bucket, no outside probability; the underdog line was not conditioned on anything |
| SC1, FP1, FP3, MAKER1 | tennis in play: jumps, tape, maker fills | FALSIFIED | in play, price paths only |
| SP1, ESPN1, SPORTSPRE, SPORTCONS1, FAMSPORTS | team sports, ESPN win probability, box scores | FALSIFIED / forward | team sports, not individual-sport underdogs |
| ESPORT1 (2026-11-02) | Elo from Kalshi's own esports maps, both sides, 8c gap | FALSIFIED | esports; Elo from Kalshi's own results; a gap rule, not a cheap-side ratio |
| CALIB1 Sports row | cheap side 5c to 10c, all sports pooled: +1.81c [-2.14, +6.24] on 186 events | information | no reference model |
| BOOKS1, BOOKS2, INPLAY1, USWEEP*, NEWLIST1 | sportsbook lines for team totals/spreads; in-play; sweep listings | various | not tennis, no Elo |
`grep -i sackmann README.md` finds nothing; `grep -n -i "\bElo\b"` finds only ESPORT1. **Individual-sport underdog against an outside Elo has not been tested: not a duplicate.**

## 2. Reachability (checked 2026-11-04)
Jeff Sackmann's tennis_atp and tennis_wta on GitHub raw: **blocked in this sandbox** (HTTP 404 for files that exist; add_repo refused; jsDelivr and tennis-data.co.uk 403/404). So the specified Sackmann Elo is NOT obtainable and its surface column is lost. Reachable and used: ESPN `site.api.espn.com/apis/site/v2/sports/tennis/{atp,wta}/scoreboard?dates=YYYYMMDD` (one request returns the whole tournament that is on that date; sampled every 4 days from 2024-01-01 to 2026-10-03, 1 thread, 0.3 s pause, cache outside the repo): 40,000 completed singles rows. **Disclosed deviations from the brief: (a) no surface adjustment (ESPN has no surface field), one overall Elo per gender; (b) ESPN covers tour level only (ATP and WTA tours, slams, Masters, 250/500, some 125s). Challenger and ITF have no free results source here, so they are NOT_RUNNABLE.**

## 3. Census (listings, names and close times only; no candle, no price, no result was read)
Settled markets closing before the frozen cut 2026-10-03T16:00Z (live `/markets` plus `/historical/markets`, series list scanned for the sports below):
| Series | Settled events before the cut | Reference obtainable? |
|---|---|---|
| KXATPMATCH | 4,778 events from 2025-06-18 | **yes, ESPN: 4,082 matched by both names within 2 days of the ticker date; 3,489 with both players at least 10 earlier ESPN matches** |
| KXWTAMATCH | 4,760 events from 2025-06-18 | **yes, ESPN: 3,925 matched; 3,591 with both players ready** |
| KXATPCHALLENGERMATCH / KXWTACHALLENGERMATCH | 8,234 / 1,534 events (from 2026-01) | no results source (Sackmann blocked, ESPN is tour level): NOT_RUNNABLE |
| KXITFMATCH / KXITFWMATCH | 16,641 / 14,863 events (from 2026-04) | same: NOT_RUNNABLE |
| KXUFCFIGHT | 643 events | ESPN has records not a rating history; with about 5% treated that is about 30 trades: NOT_ENOUGH_DATA |
| KXPGAH2H, KXPGA3BALL | 1,340 / 158 events | no free round-level scoring history joined here; about 50 treated: NOT_ENOUGH_DATA |
| KXDARTSMATCH | 435 events | no results source: NOT_RUNNABLE |
| Table tennis KXTTMATCH | 233 events | NOT_ENOUGH_DATA |
| KXMMAFIGHT 16, KXBOXINGFIGHT 1, KXATPGAME/KXWTAGAME/KXTABLETENNIS/KXGOLFH2H/KXTTELITEGAME 0 | | NOT_ENOUGH_DATA |
Name matching: Kalshi `yes_sub_title` ("Jakub Mensik") and ESPN `athlete.displayName` are both lower-cased, accent-stripped, punctuation-stripped, suffix-dropped (`norm`); an event matches when both names equal an ESPN singles match's two names and the ESPN start date is within 2 days of the date in the Kalshi event ticker. Unmatched events are counted and dropped, not tried another way. The expected treated count (Elo at least 3 times the ask, ask 3c to 30c) cannot be known before prices; the universe is 7,080 ready matches, so 150 treated is a 2.1% hit rate; below 150 the verdict is NOT_ENOUGH_DATA with the forward plan in section 9.
The last third is frozen: no match with close time on or after 2026-10-03T16:00Z is listed, fetched or joined.

## 4. Question, counterparty, prior
Is the underdog of an ATP or WTA match priced below what a rating built only from earlier public results implies? **Counterparty:** retail buyers who anchor on rankings and names and sell the unfancied player, plus favourite-longshot bias (cheap contracts are usually overpriced, the opposite of this trade). **Honest alternative (expected):** quoters follow sportsbook lines, which are better than any results-only Elo; an Elo-over-ask gap of 3 times is then the Elo's error (injury, form, surface, fatigue), and win rate equals price or less. F6 saw underdogs under 0.35 at -1.93c. **Prior of a pass: 2%.**

## 5. Reference (fixed now)
Two ratings, men's and women's singles, from ESPN completed singles competitions (de-duplicated by competition id across both feeds), ordered by start time. Start 1500, scale 400, `K = 250 / (n + 5)^0.4` with n the player's earlier matches. Only matches with ESPN status `STATUS_FINAL` update the ratings (retirements and walkovers do not). **Strictly walk-forward: the rating used for a match contains only ESPN matches that START before that match's ESPN start.** Both players need at least 10 earlier rated matches. Elo probability for a side = `1/(1+10^((R_opp-R_side)/400))`.

## 6. Universe, look, trade (fixed now)
Kalshi events of KXATPMATCH and KXWTAMATCH with close time before the cut, matched to one ESPN match as in section 3 (the earliest ESPN start if two). One request of 1 minute candles for the event's first market by ticker, from ESPN start minus 24 hours to ESPN start (historical or live endpoint by where the market lives). **Look:** the last candle that ends at or before start minus 10 minutes and has a valid two-sided quote (0 < yes bid < yes ask < 1, closing values); both sides are priced from it (YES ask, NO ask = 1 - YES bid). No such candle: no trade, counted. **Cheap side:** the side whose ask is in [0.03, 0.30]; if neither, no row. **Treated trade:** Elo probability of that side >= 3 x its ask, hard limit 0.30; buy 10 contracts at the ask, held to settlement, fee 7% x C x p x (1-p) rounded UP to the cent per order (stress line fees x1.2), one trade per match. A quote is not a fill; stated. **Control:** every cheap-side row in the same universe, same fee. Event is the cluster.

## 7. Numeric prediction (written before any result)
Treated win rate about 0.85 of mean ask or lower (Elo overstates underdogs), mean net about -3c per contract, PF about 0.6, treated minus control about 0 to +1c, not significant. If anything beats the bar I suspect the ESPN start time (a match that already began), checked first.

## 8. Kill rules
FALSIFIED if the treated mean net after fees is not above 0 in BOTH halves (split at the median ESPN start of the treated trades) or PF is under 1.5. NOT_ENOUGH_DATA if fewer than 150 treated trades (with months-to-go from the forward plan). NOT_YET_FALSIFIED only if mean > 0 in both halves, PF >= 1.5, mean >= 2c, event-cluster z >= 5.27 and the treated mean beats the control mean. A pass would only mean a forward test on the post-cut third, never a trade.

## 9. Forward plan
The frozen third (matches from 2026-10-03T16:00Z, now about a month, growing about 400 tour-level events a week) is untouched. If NOT_ENOUGH_DATA, the same `tennis1.py run` is read once on the post-cut matches when treated n there is projected at 150. Challenger and ITF would need a results source (Sackmann files if the sandbox is ever opened, or tennis-data.co.uk).

## 10. Count
Two tries (one rule, ATP and WTA ratings; the combined read is the verdict, the split by tour is information). Registered N +2.

Code `src/scalper/tennis1.py`, tests `tests/test_tennis1.py` (synthetic, passing before this commit).
