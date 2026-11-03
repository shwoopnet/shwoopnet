# RULES1 registration (called RULES1B in prose): does fine print in a market's own rules text predict cheap-side mispricing? (Strategy Research V2, 2026-11-03; written and pushed BEFORE any outcome was joined to any entry)

Worker RULES1. Discovery only. No live code, no `functions/`, no L1, no OICORE, no promote verb. **Owner rule (strict): cheap side only, ask 3c to 30c.** No entry above 0.30 is built, counted, scored or printed (the code asserts it); no favourite-side result exists anywhere in this study; no 15 minute crypto or gold candle trigger.

Name note: the id RULES1 was used on 2026-10-29 for the lock rules review (README, "RULES1, closed"). This study is a different test and is stored under the id the coordinator gave (`RULES1_*` files, `src/scalper/rules1.py`); in prose it is RULES1B.

## Duplicate check (done first)
README, workers and code searched for rules-text features. RULES1 (10-29) read `rules_primary` of the two legs of flagged locks (classification of arbitrage traps, no win-vs-price test); SETTLE1 (11-03) tabulated the settlement source of the forex/commodity families as facts and tested an outside reference, not a text feature; ARB3, COUNT1/2, DAILY2, ESPORT1 use `rules_primary` only to parse a strike, a date or a contract month. CALIB1 pooled the same cheap-side entries by category and price bucket, never by rules text. **No rules-text feature test exists. Not a duplicate.**

## Disclosure (what was looked at before this file)
1. `workers/CALIB1`'s entry table (16,041 cheap-side entries from the USWEEP1/2/3 and NEWLIST1 development caches; the caches themselves carry NO rules text) was used only for ticker, series, event, close time, ask and look; the `won` and `net` columns were not read by any census code.
2. Metadata only: for each of the 221 series in that table, TWO markets (the two md5-smallest tickers of different events) were fetched from the public API (`/markets/{ticker}`, fallback `/historical/markets/{ticker}`): 438 markets in all, under the 600 cap. Only whitelisted fields were stored (`rules_primary`, `rules_secondary`, `strike_type`, strikes, `can_close_early`, titles); `result`, `expiration_value` and every price were dropped by the fetch code. The file is `workers/RULES1_META.jsonl.gz`.
3. I READ the rules text of the representatives (templates, no outcome) before writing the keyword list below, and I printed census COUNTS per feature (treated entries, events, series, halves) after writing the code. The regexes were not changed after seeing those counts. No win rate, price-vs-win, net or PF has been computed for any group.
4. Rules text is a series template (all strikes of a series, e.g. the 53 AAA gas series, carry the same wording), so a feature is assigned to a SERIES from its two fetched markets; where the two disagree on a feature the series is UNSTABLE for it (excluded from that feature and from the control). Observed: 0 unstable series, 0 entries without metadata.
5. Frozen thirds: the entry table contains development markets only (CALIB1 verified 0 cached markets on a frozen date); the 15 minute crypto and gold families and the 2026-10-03T16:00Z cut are not in it. Nothing frozen is fetched or joined.

## Mechanism and counterparty
The quote reflects the headline question ("will X be above K"); the contract pays on the fine print: a strict vs inclusive inequality (a tie settles NO or YES), a rounded reference, one specific print instead of a day's move, the first release instead of the final number, an equality bracket, a void or fair-price clause, a named third-party source that differs from the public number retail checks. The counterparty is the cheap-side buyer who prices the headline and not the fine print, so the market maker who reads the clause is paid. If a feature really mattered, cheap-side entries in markets that carry it would win MORE than their price (ties and clauses that quietly pay YES), or the controls without it would win less. Prior that any feature is a bar-clearing lead: about 3%. The cheap side is already mispriced AGAINST the buyer in every CALIB1 bucket (win rate about 0.4 to 0.65 of price), so the expected shape is negative everywhere and the information is the ranking.

## Features (fixed, 8 = N +16)
Regexes run on lower-cased `rules_primary + " " + rules_secondary`. A market is treated for a feature when its SERIES flag is true. Features overlap on purpose (a market can carry several); each is scored alone against the same control.

| id | regex (Python `re`) | reading |
|---|---|---|
| STRICT | `strictly (?:greater\|more\|less\|above\|below)` | a tie settles NO |
| INCLUSIVE | `at least\|or higher\|or more\|or above\|greater than or equal\|\d\+ ` OR `strike_type == greater_or_equal` | a tie settles YES |
| ROUNDED | `rounded to` | settlement value rounded before the comparison |
| PRINT | `candlestick\|at the exact time\|exact time\|at exactly\|opening candlestick` | one specific print, not the day's range |
| FIRSTFINAL | `first release\|sooner of the first\|first reported\|preliminary\|revis\|official and final\|final race results\|provisional\|most recently available` | first release vs final value, fallback to the last published |
| EXACT | `is exactly\|exactly \d` | equality bracket |
| VOID | `fair market price\|does not occur\|postponed\|abandon\|ends in a tie\|no result\|is cancel\|cancelled\|resolve to (?:the )?fair` | void, tie or fair-price clause |
| SOURCE | `according to\|as published by\|as reported by\|reported by\|based on the value reported` | a named third-party source |

CONTROL = entries whose series has none of the 8 features true and none unstable.

## Look and trade (inherited from the caches, nothing chosen)
Entries are CALIB1's rows: the cheap side (YES if its ask is 3c to 30c, else NO if 1 - bid is), two sided quote required, taken at each cache's own fixed looks (USWEEP minutes before the anchor: H 30/15/5, D 1440/360/60, W 4320/1440/360; NEWLIST1 1h/3h/6h after listing and 3h before close). **One entry per market** (the look with the smallest md5 of `market|look`, outcome blind), **at most 2 entries per event** (the two smallest md5 of the market ticker), held to settlement, price is the ask (fill at the quoted ask, hard limit 0.30), fee `ceil(0.07 * 10 * p * (1 - p) * 100) / 1000` per contract at C = 10. Net per contract = 1{win} - ask - fee. Halves: the table is split at the median close time of all kept entries (1790881200 = 2026-10-01T19:00Z), fixed from the census before any outcome.

## Census (counts only, run before this registration)
5,765 entries, 3,535 events, 221 series after the one-per-market and two-per-event rules. Treated: STRICT 1,516 (874 events, 55 series; halves 300 / 1,216), INCLUSIVE 302 (188; 134 / 168), ROUNDED 193 (111; 81 / 112), PRINT 274 (163; 122 / 152), FIRSTFINAL 3,167 (1,824; 1,907 / 1,260), EXACT 42 (32; 21 / 21), VOID 276 (234; 127 / 149), SOURCE 4,391 (2,534; 2,138 / 2,253), CONTROL 646 (499; 417 / 229). EXACT is under 150 and is registered as NOT_ENOUGH_DATA. Over the 150 treated-trade bar for runnability: 7 of 8 features. Caveat stated now: the treated groups are dominated by a few families (STRICT is AAA gas and rain; FIRSTFINAL is mostly the weather ladders, whose rules say "official and final"; SOURCE is most of the sample), so a feature is partly a family label, and the event cluster does not remove day or regime correlation (CALIB1 caveat 1).

## Test and statistics
For each feature and for CONTROL: n, events, series, win rate vs mean price paid, mean net per contract after fee with an event-cluster bootstrap 95% interval (2,000 draws, seed 20261103), profit factor (sum of positive nets over sum of negative), and the same for each half. ONE run (`python3 -m scalper.rules1 score`, which refuses a second run). No threshold, look or regex search; no feature is added or edited after this file. 8 features = N +16.

## Numeric prediction (stated now)
Every feature's mean net is negative (between -2c and -9c a contract, PF 0.3 to 0.9), as in CALIB1's pooled buckets (-2.4c to -10.4c); the gap between a feature and CONTROL stays inside the cluster interval for at least 7 of 8 features; no feature has a positive mean net in both halves. Smallest differences expected for PRINT and ROUNDED (the commodity candle families).

## Kill rules (decided before any outcome)
- **FALSIFIED** for a feature: mean net after fees is not above 0 in BOTH halves, or the whole-sample profit factor is under 1.5.
- **NOT_ENOUGH_DATA** for a feature: under 150 trades (EXACT, registered).
- **LEAD** (a place to look, not an edge): positive in both halves AND PF at least 1.5 AND at least 150 trades; it would then need its own registered forward test on the frozen third and the deflated bar (profit factor 1.5 or better in each of three windows after fees and after the number tried, with a named counterparty).
Note on the family confound, registered now: a LEAD is reported together with the share of its trades from its largest series, and a LEAD with more than half of its trades in one series family is reported as a family result, not a rules-text result.

## Forward plan
If any LEAD: a keyless recorder of cheap-side quotes for that feature's series from the live market list, one frozen read on at least 150 new treated trades. Otherwise none; a rules-text census of new series every 90 days (metadata only) is the only upkeep.

## N
+16 (8 features x 2).
