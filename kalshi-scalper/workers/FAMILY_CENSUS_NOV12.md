# Untouched-family census (Idea Desk B with the Forensics desk; started Nov 12, 2026)

**Status (16:55Z, Nov 12, corrected 17:00Z): FIRST CUT of the family list is below, built from V2's Nov 3 sweep files with no new read.** It covers the 337 series those sweeps counted. The fresh listing (`CENSUS_LISTING`, dispatched first by Main, not landed yet) adds the series the sweeps never reached, the fee class and one day of volume. Full table due 16:00Z on Nov 13. Asked for by the owner through the Head of R&D: "find more", breadth and not depth.

## What the census is

One row per Kalshi FAMILY (a category plus a group of series that work the same way): category, how fast it settles, independent events a year, recent volume and typical spread, fee class, what kind of data it gives (order book, tape, candles, or only a list quote), and TOUCHED or UNTOUCHED. Touched means a registered test exists; it is named with its verdict. Untouched means no registered test of any kind.

**Split with Forensics (agreed Nov 12):** this desk writes the family list, touched or untouched, events a year, fee class and the listing job. Forensics fills volume, settlement speed, spread, depth and data kind for every family we already RECORD, from recorded files only. For a family with no recorder, volume comes from the listing below.

## The fresh listing job

`workers/desk_b_jobs/CENSUS_LISTING.json`, 40 requests, at most 88 pages, about 120 MB (estimated at 1.7 KB a market), one run. It passes the pull script's own check. A listing only: no candle, no test, nothing scored.

| Part | Requests | What it gives |
|---|---|---|
| The whole series list (`/series`, limit 20000) | 1 | every series: ticker, title, category, frequency, fee type and multiplier, settlement source |
| Every non-combo market that settled on Nov 10, 2026 UTC, hour by hour (`/markets`, settled, close-time bounds, combos left out), at most 3 pages of 1,000 an hour | 24 (at most 72 pages) | per family: markets and events settled in a day, final volume, open interest, last price |
| The series list again by single-word category | 15 | a fallback if the whole list is cut at the 5 MB answer cap |

Where the calls come from: the first two are exactly the calls V2's sweep made (`src/scalper/usweep2.py` on `claude/epic-ptolemy-0amjd9`: 330,612 markets crawled in 72 hourly windows, 1,481 series seen). The category parameter on the series list is the one call not seen in that code, so it is placed last, where a refusal cannot stop anything before it.

**Limits, said now.**

1. One day is one day: Nov 10 is a Tuesday. A family that settles weekly or monthly, or only at weekends (NFL Sundays), shows in the series list but not in the settled crawl. Events a year for those come from the series' stated frequency, marked as such.
2. V2 saw about 4,600 settled non-combo markets an hour. At 3 pages an hour, a busy hour is cut at 3,000; the reader flags every cut hour and reports its counts as a lower bound. A full day would not fit under the 200 MB a run cap.
3. Volume in a settled market object is that market's own total; a family's volume is the sum over one day, not a yearly figure.
4. Open markets are not listed by this job (the size cap again). Typical spread therefore comes from Forensics for recorded families and is "not known" for the rest until a second job is asked for.
5. Combos are left out on purpose; the combo recorder covers them.

## What V2's old sweep already says about untouched ground

The universe sweeps (USWEEP1 to 3, Nov 3) stopped at the rate limit: 13,856 in-scope series were never tested by the first, about 14,000 were not reached by the second and about 10,000 custom or one-off series by the third. Their rule was a cheap-tail calibration grid, a crowd-bias rule, and found nothing on what it did read. So a large part of Kalshi has had no registered test of any kind, and the one rule that brushed its edge was of the kind that cannot reach the bar. That is the ground this census maps.

## The reader

`workers/census/read_listing.py` (written and self-tested before the pull lands): per series, the markets and events settled on the day, summed volume and open interest, joined to the series list's category, frequency and fee fields. It prints counts and sums only, and flags every cut hour.

## Where the "13,856 never tested" figure comes from (for the Verification Analyst)

All three lines are in V2's research README, `kalshi-scalper/README.md` on branch `claude/epic-ptolemy-0amjd9` at commit `79724f0`:

| Figure | File and line | Exact words |
|---|---|---|
| 13,856 | README.md line 8363 (result USWEEP1, run 2026-11-03) | "15,663 series listed, 1,753 read, **119 unique series tested** (13,856 in-scope series NOT tested: API rate limit, stopped by count), 281 cells" |
| about 14,000 | README.md line 8537 (result USWEEP2) | "Bulk `/markets` crawl of 3 days (330,612 markets, 1,481 series), 607 exact counts, 174 eligible, **62 tested** (60 Sports), 112 eligible not tested (candle budget), ~14,000 series not reached" |
| about 10,000 | README.md line 8586 (result USWEEP3) | "1,189 non-Sports candidates counted exactly (832 with no settled market in 60 days) ... **49 series, all tested** ... About 10,000 custom or one_off series not reached" |

**How to read it, so it is not over-quoted.** 13,856 is a count of series NAMES that the first sweep did not get to, not of live markets. The same record shows most of them are empty: the second sweep saw only 1,481 series with any settled market in 3 days, and of 1,189 non-sports candidates counted exactly, 832 (70%) had no settled market in 60 days. The honest size of the untested ground is therefore: **174 series met the second sweep's activity rule (300 or more settled markets in 60 days on 20 or more dates, median volume 100 or more) and 112 of those were never read; the rest of the 13,856 are mostly one-off or dormant names.** The Nov 10 listing will replace these Nov 3 figures with a fresh count. Do not quote 13,856 to the owner without that sentence.

## First cut of the family table (Nov 12, from V2's sweep files; no new read)

Built by `workers/census/first_cut.py` from `USWEEP1_SERIES.json`, `USWEEP2_SERIES.json` and `USWEEP3_SERIES.json` (V2's branch, public counts taken 2026-11-03 over 60 days). Per-series rows: `workers/census/first_cut_series.csv` (337 series, each with its family); per-family sums: `workers/census/first_cut_families.csv`.

**Counts (corrected 17:00Z after a second pass over V2's later entries, which moved esports, cricket, rates and Netflix to TOUCHED): 46 families listed (337 series from the sweep files, plus the known families the sweep files do not hold). By state: 30 TOUCHED (a registered test of a mechanism), 9 SWEEP ONLY (only the cheap-tail sweep read it), 7 UNTOUCHED (no series ever read). Untouched or sweep-only with 300 or more independent events a year: 12. Cards written from them: 0 so far.**

Three states, because "touched" hides a real difference:

- **TOUCHED**: a registered test of a named mechanism exists. Tests and verdicts are listed.
- **SWEEP ONLY**: the only thing ever read is V2's universe sweep, one crowd-bias rule (buy the cheap tail, ask 5c to 15c, hold). Verdict for all of them: no lead. No mechanism has been tested.
- **UNTOUCHED**: the series met the sweep's activity rule and was never read at all (the candle budget ran out).

"Events a year" is independent events (games, days, releases), not markets. Where it comes from a league schedule or the stated frequency and not from an observed count, it says "schedule". Volume is the median settled market's contracts in V2's Nov 3 count, the middle series of the family. Fee class, spread and data kind are blank until the listing and Forensics' table arrive.

### Sports

| Family (series) | State | Events a year | Median market volume | Tests and verdicts |
|---|---|---|---|---|
| US game winners: NBA, NHL, NFL, MLB, college football, MLS (5 series in the sweeps) | TOUCHED | about 6,000 games (schedule) | about 300,000 | SP1 FALSIFIED; F6, F7 FALSIFIED; ESPN1 FALSIFIED; SWING1 FALSIFIED; INPLAY1 not enough data; BOOKNCAA1 not enough data; SPORTCONS1 no lock; sports calibration (Refinement) no edge; USWEEP2 no lead |
| US spreads and totals | TOUCHED | same games | not in the sweeps | FAMSPORTS FALSIFIED (totals against a box-score model, both tries); SPORTCONS1; Refinement's spread cell (read Nov 12, failed both lines, reproduction pending) |
| NFL quarters and halves: winner, spread, total (17 series) | SWEEP ONLY, 10 UNTOUCHED | 285 games (schedule) | about 12,000 | USWEEP2 no lead on 7; SPORTCONS1 touched game against first-half total |
| College football quarters, halves, overtime (6 series) | UNTOUCHED | about 900 games (schedule) | 100 or more | none |
| **NHL periods: winner, spread, total, periods 1 to 3 (9 series)** | **UNTOUCHED** | **1,312 games (schedule), 3 periods each** | 100 or more | none |
| NBA and MLS halves (6 series) | SWEEP ONLY, 3 UNTOUCHED | about 1,800 games (schedule) | about 8,900 | USWEEP2 no lead on 3 |
| NFL player and team props (20 series) | TOUCHED | 285 games | about 5,200 | PROPS1 not enough data; NFLANYTD1 FALSIFIED; OUT1 not enough data; USWEEP2 no lead on 4; 16 series never read |
| College football props (2 series) | UNTOUCHED | about 900 games (schedule) | 100 or more | none |
| NHL player props | TOUCHED | 1,312 games | not in the sweeps | NHLG1, NHLALL1, NHLAST1, NHLFG1 all not enough data; saves series never read |
| MLB player props; Japanese and Korean baseball winners | TOUCHED | 2,430 games | 14 (hits allowed) | SCOUT1 not enough data; MLBHR1 FALSIFIED; NPBKBO1 not enough data (4 treated of 150); USWEEP1 no lead |
| Tennis: match winner, games total and spread (8 series) | TOUCHED | over 10,000 matches (schedule) | about 240,000 winner; about 5,000 totals | SC1 FALSIFIED (4 rules, in play); USWEEP2 no lead on 6; games spread and women's games total never read |
| Soccer, big leagues: game, total, spread (12 series) | TOUCHED | about 2,800 games (schedule) | about 22,000 | SOCCER1, SOCCERELO1, XI1 FALSIFIED or not enough data; TIE1 not enough data; USWEEP2 no lead |
| **Soccer, smaller leagues: total, spread, game, first half (52 series, about 30 leagues)** | **SWEEP ONLY on 22, UNTOUCHED on 30** | **about 9,000 games (schedule)** | about 5,900 | USWEEP2 no lead on 22 |
| **Soccer extras: team totals, corners, both teams to score (11 series)** | **UNTOUCHED on 10** | about 2,800 games (schedule) | about 1,600 | USWEEP1 no lead on 1 |
| **Basketball outside the US: Australia, Germany, Turkey, Adriatic, VTB totals and spreads (10 series)** | **UNTOUCHED** | about 1,100 games (schedule) | 100 or more | none |
| **Minor hockey: AHL and KHL game winner (2 series)** | **UNTOUCHED** | about 1,900 games (schedule) | 100 or more | none |
| Esports: Dota 2 and Valorant game, map, total maps (4 series); virtual sports | TOUCHED | thousands of maps (not counted) | about 6,800 | ESPORT1 FALSIFIED (map 1 winner against a rating built from Kalshi's own results, both tries); ESPORTM1 not enough data; VIRT1 not enough data, every sign negative; USWEEP2 no lead |
| Cricket, T20 match | TOUCHED | about 1,500 matches (V2's census) | about 48,000 | CRICT20 not enough data (10 treated of 150); USWEEP2 no lead |
| College women's volleyball match | UNTOUCHED | seasonal, thousands (schedule) | 100 or more | none |
| NASCAR: race, top 3, top 10 | SWEEP ONLY, 2 UNTOUCHED | 38 races. SLOW | about 10,000 | USWEEP2 no lead |
| Golf, season win totals (not in the sweep files) | TOUCHED | slow | not in the sweeps | GOLF1, SEASON1 not enough data |

### Everything that is not sports

| Family (series) | State | Events a year | Median market volume | Tests and verdicts |
|---|---|---|---|---|
| Daily city high and low temperature (48 series) | TOUCHED, CLOSED | 365 days, 24 cities | about 1,100 | WX1 twice, WX3, WXDEAD1 FALSIFIED; WXNEW1; family closed under the three-falsified rule; WXDAYEND remainder with the Testing Desk |
| Daily and weekend rain (2 series) | TOUCHED | 365 days | about 14,000 | RAINFACT1 FALSIFIED; RAINCAL retired unread |
| Hazards: biggest earthquake, tornado and hurricane counts | TOUCHED | 365 days (quake); monthly for the rest | about 850 | EQUAKE1 (base rate against the market); COUNT2 not enough data and source mismatch; WXOTHER1 not runnable; USWEEP1 no lead |
| Gas and diesel prices, daily by state and weekly (55 series) | TOUCHED | 365 days, one underlying | about 460 | GAS1 nothing; GAS2 FALSIFIED (control PF 0.15); ECONNEW2; USWEEP1 and 3 no lead |
| Commodity daily and weekly ladders: gold, silver, copper, gas, WTI, Brent (11 series) | TOUCHED | about 250 days | about 200 | CMD1 nothing; COMDAY1 not enough data; E5 and E5B; USWEEP no lead |
| Currency daily and weekly ladders (13 series) | TOUCHED | about 250 days | about 25. THIN | FXUSD; USWEEP no lead; six series have a median volume of zero |
| Index ladders: S&P 500, Nasdaq 100, Dow hourly (3 series) | TOUCHED | about 250 days | zero at the median strike | IDX1, IDXFUT1, XLADDER1, calendar slices (Refinement); USWEEP no lead |
| Rates: Treasury yields daily (2, 5, 7, 10, 30 year), SOFR daily, mortgage weekly (7 series) | TOUCHED | about 250 days, one underlying | about 460 | SOFR1 not enough data and closed (1 trade in 44 days: the ladder has only about 2 strikes a day near the last rate); TNOTE1 FALSIFIED (no bracket ever quoted cheap enough); MORTGAGE1; USWEEP3 no lead |
| Macro releases: CPI, payrolls, unemployment, PCE, Fed | TOUCHED | about 44. SLOW | about 200 | CPI1, NOWCAST1, FEDIMPL1 not enough data; ECONLAG registered (this desk), ECONFADE (Desk A) |
| **Texas power grid daily peak demand (1 series)** | **SWEEP ONLY** | **365 days** | about 560 | USWEEP3 no lead |
| **Truflation daily index (1 series)** | **SWEEP ONLY** | **about 250 to 365 days** | about 340 | USWEEP3 no lead |
| Approval and generic ballot, daily (2 series) | TOUCHED | 365 days | about 29,000 | APPROVAL1 not enough data; ROLLOFF proxy killed (this desk); Refinement's calibration and NO-side tests |
| Truth Social post counts, daily and weekly (2 series) | TOUCHED | 365 days | about 22,700 weekly; 440 daily | COUNT1 not enough data; COUNT1B no definition matches; COUNT1D forward; its outside source is now barred |
| Mentions: what will a speaker say (3 series) | TOUCHED | about 150 events (observed 26 dates in 60 days) | about 17,000 | MENT1 not enough data (71 events, negative); USWEEP no lead |
| Daily top music video, weekly song and album charts (6 series) | TOUCHED for songs; SWEEP ONLY for the daily video | 365 days (video); 52 weeks (charts) | about 1,000 | SPOTD1 FALSIFIED (daily top song, model worse than the market); DIGMET1 not runnable; USWEEP3 no lead; chart sources are barred or unread |
| Netflix weekly rankings (7 series) | TOUCHED | 52 weeks. SLOW | about 800 | CHART1 not runnable (no history of the daily list); USWEEP3 no lead |
| Open-weights AI share (1 series) | SWEEP ONLY | one-off | about 3,100 | USWEEP3 no lead |
| Shiba daily ladders (2 series) | SWEEP ONLY | 365 days | zero | dead: nobody trades it |
| Crypto 15 minute, hourly and daily ladders (not in the sweep files) | TOUCHED, heavily | about 35,000 windows a series | recorded | several hundred registered tests; the live strategies are here |
| Altcoin ladders | TOUCHED | daily | not in the sweeps | ALTLAD1 not enough data |
| Kalshi perpetuals | TOUCHED | continuous | recorded | 52 named tests, no lead (see `REOPEN_RANKING_NOV12.md`) |
| Combos | TOUCHED | thousands of combos | recorded | MVE1 not enough data; COMBO1; S3 paper registration (this desk); COMBOPRICE1 designed, not run |
| Long-dated politics and elections | TOUCHED | under 52. SLOW | not in the sweeps | FLB1; XV2 not enough data; BALLOTNO parked (this desk); politics recorder running |
| Company earnings and earnings mentions | TOUCHED | about 2,000 reports a year, 4 seasons | not in the sweeps | EARNPR1 not enough data, both arms negative |
| Monthly one-touch markets | TOUCHED | 12 a series. SLOW | not in the sweeps | BARRIER1 not enough data |

### What the first cut says

1. **The untouched ground that is active is nearly all sports sub-markets.** Of the 112 active series the second sweep left unread, 107 are sports and are still unread: periods, props, small-league soccer, foreign basketball, minor hockey, esports maps. The other 5 were read by the third sweep. Outside sports, every series that met the activity rule has been read by a sweep; what is left there is "sweep only", meaning no mechanism was ever tested.
2. **The one number for "efficient, move on" on the cheap side, everywhere:** V2's pooled calibration (CALIB1, 16,041 cheap-side entries, 3,535 events, run once Nov 3) loses in every price bucket, from -2.4c a contract at 3c to 5c to -10.4c at 20c to 30c, every upper bound below zero. So no card in any of these families will be a cheap-side or crowd-bias rule. The nearest to break-even was sports at 5c to 10c (+1.8c, interval -2.1c to +6.2c, 186 events).
3. **Families with 300 or more independent events a year that have had no mechanism test (the card pool, 12):** NHL periods; college football periods; college football props; small-league soccer totals and spreads; soccer extras; foreign basketball; minor hockey; college volleyball; NBA and MLS halves; Texas power demand; Truflation; the daily top music video. (Esports, cricket and daily rates were in the first version of this list by mistake: each has a registered test, named in the table.) Volume on the never-read ones is only known to be "100 or more at the median"; the listing gives the real figure.
4. **What the first cut cannot say yet:** fee class, spread, depth, and everything about series the sweeps never counted (new series since Nov 3, and whole categories such as companies, health, transport, world events and science that the sweeps reached only through one-off series). Those wait for the listing.

### How the touched column was checked, and what is still open

The first version of this table was built from the level-two "Result:" headings of V2's README only and missed tests filed under other heading styles (ESPORT1, ESPORTM1, VIRT1, CRICT20, SOFR1, TNOTE1, MORTGAGE1, SPOTD1, CHART1, EQUAKE1, FAMSPORTS, NPBKBO1). A second pass searched the whole file by family keyword. For the seven UNTOUCHED families the search found no test of any kind: no entry names an NHL period, a college football quarter, a foreign basketball league, the AHL or KHL, volleyball, corners or both-teams-to-score, and the only soccer totals entry is about US leagues. Desk A's and Refinement's records are still to be searched the same way before the full table.

### Rows added after the first cut (Nov 12, 17:05Z)

Families that are not in the sweep files and were missing from the table above; they go into the full table.

| Family | State | Events a year | Tests and verdicts |
|---|---|---|---|
| Non-crypto 15 minute series (oil, silver, copper, gas, forex pairs, HYPE, BNB) | TOUCHED | about 35,000 windows a series | EVENT1, TODSEAS1, VOLSLOT1 FALSIFIED, FXUSD, the 15 minute grammar sweeps (closed, declined list); one live probe |
| College basketball game winner | TOUCHED | 5,283 events last season (V2's census) | BOOKNCAA1 not enough data (0 treated of 1,081); its sportsbook source is now barred. Spreads, totals and halves: not known until the listing |
| NBA and WNBA player props | TOUCHED | 1,230 NBA games | PROPS1 not enough data (9 treated; control cheap side PF 0.68, n 397) |
| Weekly official counts: shipping transits, executive orders | TOUCHED | 52 weeks a series. SLOW | GOVCOUNT1 duplicate, not runnable; PHYSCOUNT1 not enough data; TSA1 FALSIFIED (weekly passenger counts) |

### Cost, settlement speed and data kind (Forensics desk)

Forensics measured these from recorded public data and wrote them under this desk's family names: `kalshi-scalper/workers/forensics/FAMILY_COSTS_NOV12.md` on branch `claude/forensics-desk`, section "The same figures under Desk B's family names". The full table will carry the columns; until then that section is the source. Its "too costly, move on" flags, each closing a family or part of one before any card:

| Family (or part) | Spread | Round trip | Note |
|---|---|---|---|
| Daily city LOW temperature | 10c | 11.5c | the HIGH side is 1c and 3.3c |
| Currency daily and weekly ladders | 8c to 16c | 10.6c to 17.2c | volume 0 to 32 a strike |
| Index ladders, S&P 500 and Nasdaq 100 | 9c and 15c | 10.5c and 16.4c | zero volume at the median strike |
| Daily Treasury yields | 8c to 18c | 9.7c to 20c | SOFR is cheap (2.1c) but two-sided on 31% of quotes |
| NHL spread and total | 3c to 4c | 6.4c to 6.9c | NBA and NFL are 4.5c |
| Monthly one-touch, smaller coins | 4c to 10c | 5c to 13c | 12 events a year |
| Combos as a two-way trade | 3.4c on the 4.5% that are two-sided | not measurable | buy and hold or nothing |

Data kind, in Forensics' words: candles are current (measured on the Bitcoin 15 minute series only); order book reads are current; market-list quotes are a copy up to about 11 seconds old and not simultaneous across markets. No recorder, so no cost row at all: the 107 unread sports sub-market series, tennis, soccer, esports, cricket, gas prices, hazards, power demand, Truflation, charts, earnings, mentions, long-dated politics.

## The Nov 10 listing, scored (pull landed 17:04Z on Nov 12, scored 17:10Z)

Run `pull/CENSUS_LISTING/2026-11-12T1703Z_43265329747` on `kalshi-pull-data`: 87 requests, all answered, complete. Read with the committed `census/read_listing.py`, then grouped with `census/family_day.py`. Count tables: `census/listing_nov10/family_day.csv` (by family), `series_day_active.csv` (the 562 series that settled a market that day), `series_list_counts.csv`. Counts and sums only; no price and no result was read.

**Counts: series in the lists read 11,070; series that settled at least one market on Nov 10 (UTC, a Tuesday) 562; markets read 70,906; families seen that day 57 (46 mapped, the rest one-off groups by category); series seen that V2's sweep files do not hold 254; of those with 3 or more events and some volume 175.**

**Three limits, each a lower bound or a gap:**

1. **23 of the 24 hours hit the 3,000-market page cap.** Every day figure below is a LOWER BOUND, most of all for the ladder families with hundreds of strikes an event. The 15 minute series read 71 to 92 of their 96 windows, which gives a feel for the size of the cut where it is smallest.
2. **The whole-series list and the Sports list were cut at the 5 MB answer cap.** So the category, frequency and fee fields are known for 11,070 series in the other categories and for NO sports series (and for only 2 weather series: a category name with a space cannot be sent). 308 active series are therefore "not in the list read": nearly all sports.
3. **One Tuesday.** Weekly, monthly and weekend families are "count from stated frequency, not observed". US evening games of Nov 10 close after midnight UTC, so the NBA, NHL and college games here are mostly Monday's.

### Fee class (from the series lists read)

| Fee class | Series | Which |
|---|---|---|
| Standard taker fee, multiplier 1 | 11,024 of 11,070 | every non-sports family in the table |
| Standard fee plus maker fees | 32 | CPI, inflation, payrolls, unemployment, GDP, Fed funds and Fed meeting, rate-cut count, eggs, monthly gas, S&P and Nasdaq yearly, the Emmys, IPOs, two "when will Bitcoin hit" series, and ten GPU price series. On Nov 10 only CPI and eggs settled |
| Zero fee (multiplier 0) | 14 | all slow one-offs or annual: Bitcoin and Ethereum end of year, annual GDP, tech layoffs, and ten politics and Iran one-offs. None is a fast family and none settled on Nov 10 |
| Sports and weather | not known | the lists were cut; a follow-up of one small read a series would fill it (see the end) |

So the fee-class column is "standard" for every non-sports row, with the maker-fee exception on the macro release row. There is no fast zero-fee family.

### The day by family (lower bounds; the 25 largest by events)

| Family | Series settling | Events | Markets | Contracts traded | Contracts a market | State |
|---|---|---|---|---|---|---|
| 15 minute series (28 of them, not 16: also Solana, Zcash, NEAR, Brent, platinum, palladium, the S&P 500 and four Treasury rates) | 28 | 2,119 | 2,439 | 410.9 million | 168,000 | TOUCHED, grammar closed |
| Virtual sports: e-soccer, e-basketball, Liga Pro | 3 | 681 | 1,812 | 3.3 million | 1,800 | TOUCHED (VIRT1, not enough data, negative) |
| **ITF tennis, singles and doubles** | 4 | 408 | 816 | 61.9 million | 75,900 | **series never read**; tennis mechanisms tested on tour level only |
| Esports: CS2, Dota 2, Valorant, League of Legends, Rainbow Six | 15 | 267 | 480 | 4.4 million | 9,300 | TOUCHED (ESPORT1, ESPORTM1) |
| Crypto hourly and daily ladders | 19 | 194 | 35,631 | 12.1 million | 340 | TOUCHED, heavily |
| **College basketball, men and women: game, spread, total, first half, overtime** | 10 | 168 | 1,520 | 36.4 million | 23,900 | game winner TOUCHED (BOOKNCAA1); **spread, total and first half never read** |
| NBA player props | 18 | 134 | 3,688 | 10.9 million | 2,900 | TOUCHED (PROPS1, not enough data) |
| Tennis, tour and challenger | 11 | 132 | 296 | 140.8 million | 475,700 | TOUCHED |
| **NBA quarters and halves: winner, spread, total, team total** | 19 | 124 | 1,432 | 8.2 million | 5,800 | **never read** (one series by the sweep) |
| Hourly commodity ladders | 5 | 92 | 6,705 | 0.4 million | 59 | thin; HRLYFX1 not runnable |
| **Hourly city temperature (4 cities)** | 4 | 87 | 900 | 0.7 million | 800 | **never run**; V2 called it a duplicate of the daily weather tests |
| Hourly Treasury rate ladders and rate events | 10 | 83 | 2,768 | 21,000 | 8 | DEAD: nobody trades it |
| Soccer, smaller leagues and cups | 30 | 81 | 399 | 23.9 million | 59,900 | sweep only or never read |
| Basketball outside the US (EuroCup, FIBA, Japan, Korea, Brazil, Argentina, VTB) | 20 | 62 | 246 | 1.6 million | 6,300 | never read |
| Gas prices by state | 52 | 52 | 928 | 1.1 million | 1,200 | TOUCHED |
| NFL props and weekly markets | 36 | 47 | 2,423 | 13.3 million | 5,500 | TOUCHED in part |
| Elections one-offs | 26 | 45 | 303 | 7.8 million | 25,600 | SLOW |
| Daily city temperature | 45 | 45 | 270 | 1.0 million | 3,800 | TOUCHED, closed |
| NBA race, winning margin, team total | 3 | 37 | 390 | 1.0 million | 2,400 | never read |
| Tennis set winner and exact score | 3 | 28 | 72 | 4.7 million | 65,300 | never read |
| US spreads and totals | 8 | 26 | 694 | 21.0 million | 30,300 | TOUCHED |
| Soccer both-teams-to-score (8 leagues and cups) | 8 | 25 | 25 | 0.75 million | 30,100 | never read |
| Currency ladders | 24 | 25 | 410 | 0.4 million | 890 | TOUCHED, too costly |
| NHL periods | 9 | 25 | 92 | 0.4 million | 4,500 | never read |
| Index intraday up or down (S&P 500, Nasdaq 100) | 6 | 24 | 3,439 | 2.4 million | 700 | not in V2's files; a price ladder, grammar closed without a new source |

Smaller but relevant: overtime markets (NBA, NHL, college basketball: "will the game go to overtime", 12 events, 5,500 contracts a market, never read); Texas power peak 39 contracts a market and Truflation 84 (both too thin to matter, whatever the mechanism); NFL periods 54,000 contracts a market on the one game that day.

### What the listing changes

1. **The shape of period markets is confirmed.** NHL periods, NFL quarters, NBA quarters and halves, college basketball first halves and soccer first halves each list three markets an event, one of them a Tie (ticker ending in TIE). That was an inference in card 18; it is now seen.
2. **Volume on the never-read sports sub-markets is real:** about 3,000 to 6,000 contracts a market on NHL periods, 2,500 to 27,000 on NBA quarters and halves, 4,000 to 24,000 on college basketball, 30,000 on soccer both-teams-to-score. One contract fills. Spread is still unknown for all of them.
3. **New never-read families the sweeps did not hold** (they started or grew after the sweeps' 60 day window): NBA quarters and halves, college basketball spreads, totals and first halves, ITF tennis, tennis set winner and exact score, overtime markets, NBA race and margin markets, hourly city temperature, index intraday.
4. **Two pool families drop out on volume alone:** Texas power (39 contracts a market) and Truflation (84).
5. **Outside sports there is no large fast family left unread.** Every non-sports family with more than a handful of events that day is a price ladder (15 minute, hourly, daily), daily weather or gas, or a slow one-off. The 2,515 election, 2,460 politics, 2,606 entertainment, 193 company, 137 world and 94 health series are almost all one-off or annual: together they settled 45, 16, 23, 0, 0 and 0 events that day.

### Follow-up reads, named and not asked for yet (the Head ruled: first cut first)

- **Fee and frequency fields for sports and weather series:** one small read a series (`/series/{ticker}`), about 60 for the pool series. Changes the fee-class column only.
- **A spread read on open markets, at most 10 families** (the Head's limit). The ones where a spread would change a ranking: NHL periods, NFL quarters, NBA quarters and halves, college basketball first half and totals, soccer first halves, soccer both-teams-to-score and team totals, overtime markets, ITF tennis, tennis set winner, hourly city temperature. Both cards' first stage measures spread from candles for their own families, so this job is only needed for families with no card.
