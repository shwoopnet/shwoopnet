# ALL-KALSHI census, first pass (Idea Desk C, Nov 15, 2026; the owner's item 3 via the Head of R&D) [research]

**Scope.** Desk C's families: sports (Kalshi's own game and prop markets; no banned score host), politics, entertainment and mentions. The three effects to look for:
- **underdog bias:** cheap sides (5c to 30c) mispriced by settlement;
- **overreaction:** big moves that revert;
- **late drift:** prices moving toward the outcome in the last hour or day.

This pass made no request and read no price, volume or result.

## Sources, already landed (no new pull)

- **CENSUS_LISTING** (Desk B's job; kalshi-pull-data `pull/CENSUS_LISTING/2026-11-12T1703Z_43265329747`): Kalshi's series list, plus every non-combo market that settled on 2026-11-10 UTC (a Monday).
  - Read with `census_count.py` (in this folder): series ticker, category, frequency and title; market event_ticker and ticker only.
  - Output: `CENSUS_NOV10_COUNTS.json`.
- **Desk B's census tables** (`claude/idea-desk-b`, `kalshi-scalper/workers/census/families.csv` and `first_cut_series.csv`): 60 day settled counts per series from V2's sweep caches, and the tests already run per family.

## What the count says

**Two limits on the counts.**
- **Undercounted day.** 23 of the 24 hourly settled lists hit the job's 3-page cap (3,000 markets an hour), so the Nov 10 market counts are lower bounds.
- **Missing sports series.** The whole series list and the Sports category list were both cut at the 5 MB answer cap, so sports series are mostly missing from the category map. In the count they appear as 308 "series not in list" (16,937 Nov 10 markets). By ticker these are almost all sports: KXESOCCERGAME, NFL, NBA and NCAA props, totals and spreads, ITF, ATP Challenger and Liga Pro tennis, NHL goals.

Of 11,070 series in the list, these settled on Nov 10:

| Category | Series listed | Series settled | Markets settled (lower bound) |
|---|---|---|---|
| Sports | (list cut; about 300 by ticker) | about 300 | about 16,900 |
| Politics | 2,460 | 16 | 75 |
| Elections | 2,515 | 27 | 313 |
| Entertainment | 2,606 | 20 | 278 |
| Mentions | 465 | 9 | 107 |

For comparison, Crypto had 29 series and 36,784 markets that day.

**Biggest settling series on Nov 10 in the four families:**
- **Sports:**
  - KXESOCCERGAME: 1,350 markets, 450 events.
  - KXNFLPASSYDSPRECISE: 1,203.
  - KXNCAAMBTOTAL: 413.
  - NBA player props (KXNBAPTS, REB, 3PT, AST, PRA and their PROT twins): 250 to 390 each, on 8 games.
  - Tennis: KXITFMATCH 322, KXITFWMATCH 282, KXLIGAPROMATCH 294, KXATPCHALLENGERMATCH 168.
  - KXNHLGOAL: 188.
  - KXEBASKETBALLGAME: 168.
- **Politics:**
  - weekly canal and strait traffic (KXPANAMAWEEKLY, KXHORMUZWEEKLY, KXSUEZWEEKLY, KXHORMUZPEAK and MAX);
  - KXTRUMPAPPROVE and KXTRUTHSOCIALD daily;
  - a few one-offs.
- **Entertainment:**
  - YouTube daily top video (several series);
  - Netflix weekly ranks (six series);
  - KXVOICELIMINATION;
  - KXSTEAMTOPSELLER.
- **Mentions:** KXHEGSETHMENTION, KXWORLDNEWSMENTION, earnings-call mentions (ETOR, ZETA, ASTS, TTWO), KXTHEWEEKNIGHTMENTION, KXTRUMPSAY, KXLASTWORDMENTION.

## Price paths that exist

- **Kalshi candles:** 1 minute and hourly for any settled market, by kalshi-pull.
  - Settled before 2026-09-13: `/historical/markets/{ticker}/candlesticks`, one market per request.
  - After that: batched `/markets/candlesticks`, at most 10,000 window-minutes times tickers per request.
- **Recorded:**
  - in-game NBA, NHL and NFL quotes about every 20 s (`sports-data`, from Nov 8);
  - politics quotes every 30 min (`pol-data`, from Nov 11, 45 series);
  - the daily recorder (`quote-data/daily/`, from Nov 4).

## What was already tested, by effect

Taken from the cards' own files; they are not re-read here.
- **Underdog bias:**
  - USWEEP1, 2 and 3's tail rule ran across the non-15-minute series, including sports, entertainment and mentions.
  - CALIB1, LIQ1 and MECH2S used cheap entries across categories.
  - Sports calibration (Refinement) found no edge.
  - So this effect is the most touched. A new card here needs a different field or market type than a plain cheap-side price.
- **Overreaction:**
  - SNAPBACK1 and SPIKE1 (15 minute series) FALSIFIED.
  - NEWS FADE.
  - INPLAYJUMP pulls (esoccer, table tennis, ITF) exist on kalshi-pull-data, owner Desk A or B.
  - Untouched as far as I know: politics and mentions.
- **Late drift:**
  - THETA1 (favourite drift, long-dated) FALSIFIED.
  - INGAMELAG1 (lag at 1 minute) closed.
  - Untouched as far as I know: entertainment ranks and mentions in the last day.

## Next

1. Ask the VA which of the three effects on which of these families are not yet covered.
2. Then write paper cards with a fixed held-out date (the owner's lighter gate: one build plus Auditor B's quick check).
3. Size the first candle pull at 12 a minute, with files under 470 requests, for Main to dispatch.
