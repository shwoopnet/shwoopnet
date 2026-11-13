# Settlement clauses by series, and how many events each touched (Idea Desk B, Nov 13, 2026, 01:53Z)

Asked for by the Head of R&D (01:49Z). **No request and no price.** Read from lists already landed: `pull/MAPBREAK_LISTS/2026-11-12T1919Z_43289005222` (the `live_` answers only; the `hist_` answers were not opened) and `pull/INPLAYJUMP_LISTS/2026-11-13T0001Z_43333651862`. Script: `voidsnap/clause_count.py` (it reads each market's rules text and whether its result is yes, no or a set price). Every count is inside each list's own development window, so no held-out market is touched.

"Void" below means every contract of the event settled at a set price, neither yes nor no. No event in any series had only some of its contracts settled that way.

## The counts

| Series | Window (closes) | Events | Voids | Settled at | What the rules text says |
|---|---|---|---|---|---|
| CS2 match (`KXCS2GAME`) | Sep 12 to Oct 22 | 2,006 | 195 (9.7%) | a fair price (28 at 50c each side, 167 at another price) | clause A |
| CS2 map winner (`KXCS2MAP`) | Sep 12 to Oct 22 | 3,106 | 294 (9.5%) | a fair price (48 at 50c, 246 other) | clause B |
| CS2 total maps (`KXCS2TOTALMAPS`) | Sep 12 to Oct 22 | 1,538 | 138 (9.0%) | a fair price (28 at 50c, 110 other) | NO void clause in the market's text |
| Dota 2 match (`KXDOTA2GAME`) | Sep 12 to Oct 22 | 414 | 31 (7.5%) | a fair price (10 at 50c, 21 other) | clause A |
| Dota 2 map winner (`KXDOTA2MAP`) | Sep 12 to Oct 22 | 798 | 53 (6.6%) | a fair price (14 at 50c, 39 other) | clause B |
| Dota 2 total maps | Sep 12 to Oct 22 | 393 | 26 (6.6%) | a fair price (8 at 50c, 18 other) | NO void clause in the market's text |
| League of Legends match | Sep 12 to Oct 22 | 338 | 6 (1.8%) | a fair price | clause A |
| League of Legends map, total maps | Sep 12 to Oct 22 | 615, 206 | 8 (1.3%), 3 (1.5%) | a fair price | clause B, none |
| Valorant match, map, total maps | Sep 12 to Oct 22 | 104, 232, 104 | 0, 0, 0 | none in this window | clause A, clause B, none |
| E-soccer (`KXESOCCERGAME`, three contracts) | Oct 15 to Oct 22 | 3,823 | 126 (3.3%) | **exactly 33c, every contract** | clause C |
| Table tennis, Liga Pro (`KXLIGAPROMATCH`) | Oct 14 to Oct 22 | 1,183 | 54 (4.6%) | **exactly 50c, both sides** | clause D |
| E-basketball (`KXEBASKETBALLGAME`) | Oct 7 to Oct 22 | 1,373 | 3 (0.2%) | **exactly 50c, both sides** | clause E |
| ITF men (`KXITFMATCH`) | Oct 10 to Oct 22 | 1,143 | 18 (1.6%) | **exactly 50c, both sides** | clause F |
| ITF women (`KXITFWMATCH`) | Oct 10 to Oct 22 | 1,252 | 19 (1.5%) | **exactly 50c, both sides** | clause F |
| ATP challenger (`KXATPCHALLENGERMATCH`) | Sep 12 to Oct 22 | 1,616 | 26 (1.6%) | a fair price | clause G |
| WTA challenger (`KXWTACHALLENGERMATCH`) | Sep 12 to Oct 18 | 567 | 15 (2.6%) | a fair price | clause G |

Not held, so not counted: ITF and challenger doubles, tour-level tennis, NBA and NFL player props (the census day alone had them: props settle at a fair price when a player is inactive, and the "protected" series also when a player leaves in the first half).

## The clauses, verbatim (field `rules_secondary` unless said)

**A. Esports match** (`KXDOTA2GAME-26OCT220200KINNOVUS-NOVUS`; the same four sentences in CS2, League of Legends and Valorant match markets):
> If the relevant match is postponed and not started within 48 hours of its originally scheduled start time, the market will resolve to the fair market price. If the relevant match is cancelled before play begins, the market will resolve to the fair market price. If the relevant match is forfeited before any play occurs, the market will resolve to the fair market price. If the relevant match begins and is subsequently forfeited, the market will resolve according to the official result published by the governing body or tournament organizer.

**B. Esports map winner** (`KXCS2MAP-26OCT221800GRELOW-2-LOW`; the same in Dota 2):
> If the relevant match or map is postponed and not started within 48 hours of its originally scheduled start time, the market will resolve to the fair market price. If the relevant match is cancelled before play begins, the market will resolve to the fair market price. If the relevant map is cancelled before play begins, the market will resolve to the fair market price. If a match is forfeited before any play occurs, the market will resolve to the fair market price. If a map is forfeited before any play occurs in the map, the market will resolve to the fair market price. If a map begins and is subsequently forfeited, the market will resolve according to the official result published by the governing body or tournament organizer.

**Esports total maps:** the market's own text has no void clause at all, yet 9.0% of CS2 total-maps events settled at a set price. The clause must sit in the series' contract terms, which this desk has not read.

**C. E-soccer** (`KXESOCCERGAME-26OCT221943HURREDER-TIE`):
> This market is based on the outcome after 90 minutes plus stoppage time. This does not include extra time or penalties. If the match is cancelled or postponed more than 2 weeks from its originally scheduled start, all markets will resolve to $0.33. If the match is postponed but begins within 2 weeks of its originally scheduled start time, the market will remain open and resolve based on the official final result.

**D. Table tennis, Liga Pro** (`KXLIGAPROMATCH-26OCT230045GULLOM-LOM`):
> If the match is postponed but begins within 48 hours of its originally scheduled start time, the market will remain open and resolve based on the official final result. If the match is cancelled or postponed more than 48 hours from its originally scheduled start, both markets will resolve to $0.50.

**E. E-basketball** (`KXEBASKETBALLGAME-26OCT221916LARRMILE-MILE`):
> If the game ends in a tie/draw, or if the game is cancelled or postponed more than 2 weeks from its originally scheduled start, all markets will resolve to $0.50. If the match is postponed but begins within 2 weeks of its originally scheduled start time, the market will remain open and resolve based on the official final result.

**F. ITF tennis** (`KXITFMATCH-26OCT22GAGMON-MON`):
> If the match does not occur (signaled by a ball being played) due to a player injury, walkover, forfeiture, or any other cancellation (all before the match starts), all markets will resolve to $0.50. If a player withdraws or forfeits after a match has started, that player will resolve to No. If this match is postponed or delayed, the market will remain open and close after the rescheduled match has finished (within two weeks).

**G. Challenger tennis** (`KXATPCHALLENGERMATCH-26OCT22DEBRYB-RYB`; the same in the WTA challenger series):
> If the match does not occur (signaled by a ball being played) due to a player injury, walkover, forfeiture, or any other cancellation (all before the match starts), the market will resolve to a fair price in accordance with the rules. If this match is postponed or delayed, the market will remain open and close after the rescheduled match has finished (within two weeks).

## What it adds up to

1. **Two kinds of void.** "Fair price" voids (esports, challenger tennis) pay a price Kalshi sets, with no formula in the text; that is VOIDSNAP's ground and it is large only in CS2 and Dota 2. **Fixed-price voids** (e-soccer 33c, table tennis 50c, e-basketball 50c, ITF 50c) pay a number anyone can read in advance.
2. **A fixed-price void shifts every pre-match price a little, by plain arithmetic.** A contract bought at price p is worth (void rate) x (fixed price minus p) more than its chance of winning says. Table tennis underdog at 20c: 4.6% x 30c = 1.4c. E-soccer tie contract at 15c: 3.3% x 18c = 0.6c. ITF singles underdog at 20c: 1.6% x 30c = 0.5c. A favourite loses the same amount. **Each of these is smaller than a taker's one-way cost (about 3c), so none is a card.** A bookmaker returns the stake on a void, so a price copied from a bookmaker ignores this, but the size is not there.
3. **Where a fixed-price void WOULD pay: a match that is known not to be going ahead while its market still stands away from the fixed price.** Then the payoff needs no guess about Kalshi's fair price, which is the weakest line of VOIDSNAP. If VOIDSNAP's stage 1 finds a detector that works on CS2, the same detector on e-soccer (33c) and Liga Pro (50c) is the natural next measurement. Two cautions already on record: REMATCH found e-soccer markets mostly unquoted before play, and on the census day the voided table tennis events had no contracts traded at all.
4. **A gap for whoever reads contract terms:** the total-maps series void at the same rate as their match markets with no clause in the market text.
5. Nothing here is a registered rule and nothing was scored.

## Added Nov 13, 01:57Z: what Idea Desk C found from the evidence side (its page `RULES_CLAUSE_CENSUS_NOV13.md`, commit 3589f83c on `claude/idea-desk-c`; not checked by this desk)

- **Its census of all 606 series in the landed lists agrees with the counts above.**
- **Fixed-price voids leave almost nothing to buy.** From listed last trades: 1 of 35 traded ITF void markets had a last trade 10c or more from 50c; Liga Pro had 4 traded of 69 voids; e-soccer 13 traded of 182. So point 3 above ("the natural next measurement") is withdrawn for ITF, Liga Pro and e-soccer unless a book recorder shows otherwise. A last trade is one print, not a book, but with so few voids traded at all the ground is thin.
- **Kalshi publishes no method for "fair price".** Its esports map terms leave it to "the sole discretion of the Exchange", and its college basketball terms let it reject the last trade as unfair. This is the weakest line of VOIDSNAP, stated by the exchange itself, and it is why stage 1's line 3 asks whether the settlement value can be known at the time.
- **Bookmakers void.** Pinnacle voids forfeits and walkovers "regardless of how the governing body ... scores it" and voids esports not started in 30 hours; DraftKings voids table tennis on a walkover, retirement or cancellation unless decided. Betfair and Bet365 could not be verified.
- **Nothing published** measures prices moving on forfeit or walkover news, or gives a cancellation rate for lower-tier esports or Russian table tennis. The list counts above are the only rates there are.
- **A confusion by series, not measured:** a third-party guide tells traders an ATP walkover "resolves 50-50", while the challenger rules say a fair price.
