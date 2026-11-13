# Unclaimed-category census, Desk B, Nov 13, 2026, written 21:31Z by this desk's clock. From the Nov 12 census listing I hold (`census/listing_nov10/series_day_active.csv`, 562 series with category, frequency, fee type and the Nov 10 settled counts) and `FAMILY_TABLE.md` (63 families; 18 NEVER READ). No price or outcome read; no Kalshi request.

## What "unclaimed" means here and what the listing cannot say
A family is claimed if a registered card, a declined row or a retired test touches it. FAMILY_TABLE was built Nov 12; I cross-checked it against what the desks registered since (named below) and removed those. **The census listing carries no settlement source** (the series list has category, frequency and fee type only; the rule text and source are not in it, "list cut"), so for every family below the settlement source is the sport's official result and **its terms are UNREAD**; the leagues' own sites ESPN, NHL, MLB and NBA.com are barred by a repo gate, and for the rest I have not read any terms page. Recorded now: R6 (BTC, ETH, gold, XRP, DOGE 15 minute), NC15 (11 non-crypto 15 minute series), the in-game recorder (NBA, NHL, NFL moneyline and one pair of spread and total markets per game, Kalshi data only), the wheel book recorder (esports, e-soccer, table tennis, tennis; first files Nov 12), the politics, daily, REF and perps recorders. None records the families below.

## Removed because a card now touches them
NHL periods and overtime (TIE3, ENDNET, NHLOT); NFL quarters (TIE3); soccer first halves and ties (TIE3, SOCDERIV, SOCCER1); ITF, challenger and tennis sets (INPLAYJUMP, DBLTB, SC1); esports, e-soccer, table tennis, e-basketball (MAPBREAK, INPLAYJUMP, REMATCH, ESOCTIE, PREMOVE); hourly city temperature (HOURLYTEMP, the weather family); index intraday up or down (SPXOI1, OPENGAP1); hourly commodity ladders (HRLYFX1 census, not runnable); US game winners, spreads and totals (SP1, FAMSPORTS, SPORTCONS1, USWEEP2). Politics, elections, mentions and economics series are claimed by the politics lane, ELECT1, MENT1 and the macro cards. Hourly Treasury rate ladders are DEAD (8 contracts a market).

## What is left: nine families, all sports, ranked by events a year and then by contracts a market (the liquidity)
| Rank | Family | Events a year | Nov 10 events (contracts a market, spread) | Settlement source and terms | Recorded? |
|---|---|---|---|---|---|
| 1 | College basketball spread, total, first half, men and women (8 series) | over 5,000 games | 168 (23,933, 2.5c) | official game result; terms unread | no |
| 2 | Soccer, smaller leagues: total, spread, game, first half (30 of 52 series never read, about 30 leagues) | about 9,000 games | 81 (59,919, 4c) | official match result; terms unread | no |
| 3 | NBA quarters and halves: winner, spread, total, team total (18 series) | 1,230 games, 4 quarters and 2 halves each | 124 (5,756, 2.5c) | official game result; terms unread; the NBA's own site is barred | no |
| 4 | Basketball outside the US: EuroCup, FIBA cups, Japan, Korea, Brazil, Argentina, Australia, Germany, Turkey, Adriatic, VTB | about 1,100 games | 62 (6,307, 4c) | official result; terms unread | no |
| 5 | Minor and European hockey: AHL, KHL, Champions Hockey League | about 1,900 games | 9 (4,963, settles 31 minutes after the close) | official result; terms unread | no |
| 6 | NBA race to a score, winning margin, team total (3 series) | 1,230 games | 37 (2,445, 2.5c) | official game result; terms unread | no |
| 7 | College football quarters, halves, overtime and props (8 series) | about 900 games, Sept to Jan | not on the Nov 10 page | official result; terms unread | no |
| 8 | NASCAR race, top 3, top 10 (2 series never read) | 38 races, slow | none | official result; terms unread | no |
| 9 | Darts, chess, bowling; college women's volleyball | 18 events on Nov 10 (360 contracts a market); volleyball seasonal | tiny | unread | no |
Ranking by source access: **none of the nine has a source whose terms are known and allow automated reads**; the only access that needs no outside source is Kalshi's own prices, books and listings (a Kalshi-native mechanism), plus Kalshi's live-data endpoints if the owner's accepted terms risk (Nov 13) is applied after the exception is on main. Every family above would need a Kalshi-native mechanism, and the ones I can state are inside closed families (cross-market consistency: SPORTCONS1, ARB2 to ARB5; favourite-late; in-play jump follow or fade: INPLAYJUMP on other sports; period ties: TIE3).
## Top 5 for VA notes, and the honest state of each
| Item | Candidate mechanism I can state | Closest existing | Status |
|---|---|---|---|
| 1. College basketball spread, total, first half | none yet that is outside a closed family | SPORTCONS1 (game against first-half total), USWEEP2 | needs a mechanism before a note |
| 2. Soccer smaller leagues | the same rules as the big leagues (a version of SOCCER1, SOCDERIV, TIE3) | SOCCER1, SOCCERELO1, SOCDERIV | version risk: not new |
| 3. NBA quarters and halves | a period-tie measurement like TIE3 (the Head's own TIE3 covers NHL, NFL, soccer), on NBA | TIE3 | version of TIE3 on a new sport (7g) |
| 4. Basketball outside the US | in-play follow or fade like INPLAYJUMP | INPLAYJUMP | version, and no in-play recorder for these series |
| 5. Minor and European hockey | goalie pull at the end like ENDNET | ENDNET | version on new leagues, no state source |
I can send the VA a note for any of these the Head wants, but none has a mechanism that is not a version, so by the owner's standing order (work only if NEW) I would expect NOT NEW; I am not sending five notes to hear that.
