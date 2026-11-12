# Stale-quote audit: every result that used a market-list quote as "the price at that second" (2026-11-12)

Asked by the Head of R&D on the owner's instruction. Read-only: no test was re-run for this file, no settlement result was opened, zero Kalshi requests, nothing about the live account. Sources swept: the research README (9,229 lines), `workers/` and `src/scalper/` (501 modules, 15 worker scripts) on `claude/epic-ptolemy-0amjd9`; `claude/refine-live`; `claude/idea-desk-a`; `claude/idea-desk-b`. Three sweeps were run by helpers (code, write-ups, the other three branches); this desk spot-checked the rows that carry a positive figure or a flag against the source lines before writing them here.

**Background.** `QUOTEVSBOOK1` and `TAPECLOCK1` (this folder) showed that Kalshi's market LIST endpoint returns a copy refreshed about every 11 seconds, so a quote read from it is 0 to 11 seconds old (about 5.5 on average) and about 7 seconds behind the trade tape. The order book endpoint is current. `LADDERSTATE1` (this folder, new today) shows the hourly ladder file has the same staircase: `ladder.csv` strikes change every 10.2 to 10.3 seconds at the median (middle half 9.6 to 12.8 s) although they are polled every 3.2 s, and strikes inside ONE poll cycle refresh at different times (in 70% of cycles some strikes changed and some did not, in 0% all changed). So two list quotes read in the same second are not simultaneous either.

## Counts

| | Rows |
|---|---|
| **Examined** | **31 rows, covering about 75 named tests** |
| Flattered by the old quote (a lag, underpricing or lock rule at seconds scale) | 18, plus 4 mildly or in part |
| Re-scorable from data already held (R6 books, the hourly book recorder, tapes), in full or in part | 11 (rows 1, 3, 5, 10 to 16, 22) |
| Call: **RE-SCORE** | 5 (2 already done today, 3 to do) |
| Call: **VOID** (cannot be re-scored for its dates, or superseded; figure withdrawn) | 10 |
| Call: **STANDS** (staleness cannot change the verdict) | 11 |
| Pending reads that must be changed BEFORE they are read | 4 |
| Cannot be classified by this desk (the bot's own "seen" quote) | 1 |

**What rests on the stale file.** Four positive figures: the GEN4 generator's passes (rows 4 and 5), the CFRTI1 Bitcoin lead (rows 15 and 16), LATECAL's "61 of 61" lead (row 7) and RECORD1's positive mean (row 1). **Nothing live and nothing promoted rests on any of them**: the three live strategies come from candle research, and none of these four reached a pass. Every falsified result in the list was falsified in spite of a quote that flattered it, so those verdicts are safe.

Columns: **Priced** = what the list quote supplied (S signal, F fill, both). **Effect** = FLATTERS (the rule gains from a quote that has not caught up), NOISE, or NONE.

## A. Seconds-level tests on the quote recorder (`quotes.csv`, `ladder.csv`)

| # | Test (owner, date) | Priced | Verdict then | Effect | Re-scorable from held data | Call |
|---|---|---|---|---|---|---|
| 1 | **RECORD1** (V2; registered Oct 22, read once Nov 3). Model chance from per-second spot against the same poll's ask, last 60 s, five crypto series | S and F | NOT_ENOUGH_DATA; mean +3.81c, z 1.60, n 300 | FLATTERS: the rule is literally "spot beats the quote" | Partly: closes Oct 29 22:15Z to Nov 3, Bitcoin, Ethereum, XRP, Dogecoin (R6 book plus the recorder's own spot file). Not Solana, not Oct 22 to 29 | **RE-SCORE** the covered part; the rest VOID |
| 2 | **RECORD1B** (V2; registered Nov 4, unread). Same rule on clock-fixed runs | S and F | Pending | FLATTERS. It polices milliseconds on a quote that is seconds old | Forward on R6 (Bitcoin to Dec 15) | **VOID as registered.** Do not read it on `quotes.csv`; register a book version if the question is still wanted |
| 3 | **record_info "quote follows a spot jump"** (V2; Oct 22 to 23): followed in 10 of 22 jumps, median 4.6 s, 90th percentile 8.7 s | Descriptive | Information | The delay measured IS the copy's age (mean 5.5 s, maximum about 11 s) | Yes, on R6, no outcome needed | **VOID.** The live question ("does the book lag spot") is Refinement's W-SPOTLEAD1, which is on R6 books |
| 4 | **GEN4 discovery and validation** (V2; Oct 29): 51 of 113 generated rules passed its screens; favourite core PF 1.61 (n 50) and 1.57 (n 35); ten spot-momentum rules | S, F and exit | NOT_YET_FALSIFIED at its screens, sent to forward | FLATTERS, most on the spot rules (`sp*`, `zd`, `edge`); the quote-change features (`dm5/15/30`) are garbled by an 11 s staircase. Its latency check (next poll 0.6 s later) is usually the same copy and proves nothing | No: windows Oct 22 to 29 predate R6 | **VOID** |
| 5 | **GEN4 forward ledger rows** (V2; 52 rows frozen Oct 30, last scored Nov 4). Favourite core below 1 (PF 0.81, n 113); spot-momentum rows above 1 (PF 1.31 to 1.73, n 92 to 122) | S, F and exit | Accruing, none READY | FLATTERS. "Favourite core dead, spot rows alive" is the pattern a stale ask produces | **Yes, in full**: closes Oct 30 to Nov 4 are inside R6 and before the CFRTI held-out block | **RE-SCORE (first)** |
| 6 | **FALS3** (V2; Oct 29). Recorder reproduction PF 1.61 / 1.57; falsified on 8,041 candle windows (PF 0.77) | Reproduction only | BROKEN | The verdict is on candles. Its explanation ("the recorder's windows were a lucky subset") never considered staleness; part of the gap from candles to recorder on the same windows may be the old ask | n/a | **STANDS** (subject to CANDLEVSBOOK1 for candle freshness) |
| 7 | **LATECAL** (V2; Oct 29). Bitcoin 90 to 60 s left, ask 0.95 to 0.98, "won 61 of 61" | S and F | NOT_ENOUGH_DATA, a lead | FLATTERS mildly: a late favourite drifts toward 1, so an old ask is on average below the real one | No: Oct 22 to 29 | **VOID.** Its candle follow-up already read PF 0.73 / 0.96 (n 31); it is also favourite-and-hold, which is on the declined list |
| 8 | **BTCAVG** (V2; Oct 29). Averaging-window model against the ask at 45, 30, 15 s | S and F | NOT_ENOUGH_DATA; 7 to 16 trades, net negative | FLATTERS, and still negative | No: Oct 22 to 29 | **VOID** (figures); nothing rested on it |
| 9 | **QUOTE1** (V2; Oct 28). Resting quotes both sides, last 150 s, Bitcoin and Ethereum | Posting price, queue, flatten price | PF 0.00 at the taker fee, 0.09 at zero maker fee | NOISE on posting and queue; the flatten leg is priced up to 11 s old | No for its dates; the same question on books is MAKER5 (R6) | **VOID, superseded by MAKER5** |
| 10 | **MM1 / MM1S** (V2; registered Oct 29, gold). Scorer runs itself at 300 gold windows; no result found | Posting price, queue, cross fills, flatten | Pending | Same as QUOTE1; cross fills arrive late | Yes: R6 gold books and tape from Oct 29 | **RE-SCORE**: point the scorer at R6 before it reads |
| 11 | **GOLDFILL, recorder side table** (V2; Oct 30; 13 signals) | Fill model, no outcome | Information | The immediate fill rate is overstated (the "live" poll 1 s later is usually the same copy) | Yes | **VOID** (side table only). Superseded by GF1, GF2 and GOLDHAIRCUT1, all on R6. The headline (candles plus tape) stands |
| 12 | **LOCK2** (V2; read Oct 30). 15 minute quote against ladder quote within 1 s | Both legs | FALSIFIED: 1 lock in 25 Bitcoin closes (lasting 0.0 s), 0 in Ethereum | FLATTERS: two copies out of phase can only add false locks | Bitcoin, from R6 plus the hourly book | **STANDS** a fortiori. The one lock is probably the artefact |
| 13 | **XSER1** (V2; Nov 11). 15 minute quote against the hourly ladder BOOK | 15 minute leg | "A lead at best, below any cost"; 556 violations in 33,090 pairs, "clustered in a few windows" | FLATTERS: an old leg against a live leg makes violations whenever the price moves | Yes, in full (R6 plus hourly book) | **STANDS** as "not a strategy". The violation counts are overstated and should not be quoted |
| 14 | **AVG1** (V2; Nov 11, retired Nov 12). Hourly ladder quote against an averaged spot model | S and F (`ladder.csv`) | NOT_ENOUGH_DATA; largest cell PF 7.2, n 28, called "not a finding" | FLATTERS, on top of an outcome proxy built from the same spot series | Bitcoin only | **VOID** (already retired) |
| 15 | **CFRTI1** (V2; Nov 11). Model chance minus ask at least 5c at close minus 120 s | S and F | Pooled FALSIFIED (PF 1.14, n 211); Bitcoin PF 2.54, n 36, "a lead to watch", shortlisted | FLATTERS: QUOTEVSBOOK1 Part 2 found the quote 2c or more below the book on about a third of the picked rows against 6% of the others | Partly: 28 of 68 development rows have an R6 book | **RE-SCORE, done today**: `CFRTI_DEV_REPLAY_NOTE.md` (fills 9 to 10 of 16 at the ask seen) and Desk A's CFRTI-B on books ("no evidence at n = 16") |
| 16 | **CFRTI1-BTC verification, three-venue and Kraken-only** (Desk A; Nov 12). PF 2.54 (n 36) and 1.33 (n 32), plus single-venue side looks | S and F | "CONFIRMED" as a re-derivation; carried to held-out | FLATTERS, same mechanism | As row 15 | **RE-SCORE, done.** Already relabelled by Desk A: "priced at a stale copy, not tradable" |
| 17 | **CFRTI development replay join, quote-recorder columns** (Desk A; Nov 12): fills "2 s / 6 s later" taken from later `quotes.csv` rows | F | "No evidence at n = 16 and n = 12" | Invalid: a quote 2 s later is often the same copy | The R6 columns of the same table | **VOID** (Desk A's own correction already says so) |

## B. Pending reads on the quote recorder: change before reading

| # | Test | What is wrong | What to do |
|---|---|---|---|
| 18 | **CFRTI1-BTC held-out read** (first allowed Nov 20). Script `desk_a_verify/cfrti_heldout.py` on `claude/idea-desk-a` | The registered lines are already labelled "not tradable". **But the lines the amendment says "are the only lines that can support anything", printed as "BOOK-REPLAY +2 s / +6 s", are not a book replay**: the `replay()` function (lines 72 to 82) walks later rows of the same `quotes.csv`. Only the `--r6` stale-ask count reads the real book. Checked against the source by this desk | Replace `replay()` with a replay on the R6 book (this desk's `cfrti_dev_replay_grid.py` does exactly that) and re-commit BEFORE Nov 20. Otherwise the sitting prints a stale-copy replay under a "book" label |
| 19 | **CFRTI1-BTC forward shadow** (V2 `SHADOW_RULES_NOV12.md` section 2; Desk A hand-off task 5; from Nov 23) | Reads `quotes/`, timed by send time, quote "within 3 s" | Rebuild on R6 books (Bitcoin is recorded to Dec 15), or it measures the copy's age |
| 20 | **GEN4 gold run** (registered on the quote recorder "after Nov 6"; no result found; a status note speaks of R6 instead) | Ambiguous which data it would use | On R6 or not at all |
| 21 | **INGAMELAG1** (V2; registered Nov 8, unread; in-game recorder, 20 s polls of the market list) | Its deliverable is "the measured catch-up time" of a side market after a moneyline jump. An 11 s copy on a 20 s poll, with markets of one event refreshing at different times, can make or hide that lag | **VOID as designed.** No sports book is recorded, so it cannot be re-scored. Desk B's candle version (INGAMELAG1-M) is the live form and waits on CANDLEVSBOOK1 |

(Row 21 is counted under VOID above; rows 18 to 20 and row 23 are the four "pending, change first".)

## C. Other market-list quotes

| # | Test (owner) | Priced | Verdict then | Effect | Call |
|---|---|---|---|---|---|
| 22 | **W-DERIBIT1** (Refinement; Nov 11). Deribit-implied chance against the Kalshi list ask, 60 to 30 minutes before the hourly Bitcoin close | S and F | DATA_LIMITED, leaning FAIL | Mild FLATTER (the Kalshi quote is up to 11 s older than the Deribit read; my estimate 1c to 2c near the money against a 6c edge) plus noise | **STANDS** (leaning fail in spite of the flatter). Its Dec 1 re-score should price from the hourly book where the strike is covered (7 strikes nearest the money) |
| 23 | **DERIBIT-IMPLIED** (V2; read refused before 2027-01-01). Same recorder, 5c edge rule | S and F | Pending | Same | **Pending, change first**: price from the hourly book, or widen the edge by the measured staleness |
| 24 | **LADCOH1 daily mode** (V2; 7 half-hourly snapshots, zero locks; re-read Dec 5) | Both legs, one list response | NOT_ENOUGH_DATA | Legs in one response are not simultaneous (LADDERSTATE1), which can only add false locks | **STANDS.** A lock found at the Dec 5 read must be confirmed on a book before it is believed |
| 25 | **Lock scans on list snapshots**: ARB1 to ARB4, the Oct 23 and Oct 26 structure scans, PARLAY1, ELECT1 (V2), IMPLY1 (Desk B). Nine tests | Both legs | All negative (zero or sub-cost locks) | False locks only | **STANDS** a fortiori. Lock and parity scans are on the declined list |
| 26 | **Slow looks, V2**: RAINCAL, SPORTS-PRE, WXENS1, WXLOW1, BARRIER1 forward, NOWCAST1 forward, USWEEP1 forward, FEDIMPL1, EVM4, SOFR1, ORHARVEST1 stage 1. Eleven tests | S and F | NOT_ENOUGH_DATA or pending | NONE: the look is hours or a day before the close | **STANDS** |
| 27 | **Slow looks, Refinement**: W-WXPRIOR1 (FAIL), ROW75 WXREVISE (DROP) | S and F | Negative | NONE | **STANDS** |
| 28 | **Shadow-rule reads** (GOLDALL, XRPYES10, XRPFAV6, LANTERN; Refinement's tools) | S (band) and paper F | "Candidates, never passes"; the registry is now empty | NOISE. On `origin/main` the shadow rows are built from the minute function's list read (`/markets?series_ticker=`), not the single-market read the live order uses, so a shadow price can be several seconds older than the price a live order would have seen. At a 6 to 10 minute look that blurs band membership by a cent or so; it does not reward lag | **STANDS** (no verdict was drawn). Any future shadow rule should say its price is a list quote, or read the market itself |
| 29 | **S3 combo house side** (Desk B; registered Nov 12, unscored; 30 minute snapshots) | S and F | Pending | NONE on the price level; the fill count is slightly flattered (a posted ask up to 11 s old is not a fill) | **STANDS** as designed, with that sentence added to its limits |
| 30 | **Perps tests on the perps list recorder** (V2; PBOOK1 to 3, CPREM1, CLEAD1, CXS1, CSPR1, LL1, XS1, RO1, the CASH family, OVN, PERPEQ, STOCKPERP; about 17 tests) | S and F | All NOT_ENOUGH_DATA or FALSIFIED | Not known: a different list endpoint, freshness never measured. CLEAD1's own note already called its gap "a staleness artefact" | **STANDS** (no positive to protect). Measure that endpoint before any perps test is priced to seconds |
| 31 | **Tests on the bot's own "seen" quote in live exports**: FILLIMP1, FLIP1 (read due Nov 14), FLOOR1, THIN1 (V2); W-GLIMIT1, S-LIM1-LIVE and the slip scorers (Refinement) | "Improvement" or "slip" = fill against the quote seen | Various | **Not known.** Both live engines price an order from the single-market read (`/markets/{ticker}`; checked on `origin/main`), whose freshness is unmeasured. If that read is also a copy, "fills cheaper than the seen book" and "limit missed by a cent" are partly the copy's age | **Cannot classify.** It waits on Main's log-only book read beside the send. FLIP1's Nov 14 read should carry that caveat. This desk has no live rows and makes no claim about the bot |

## Checked and not affected (no list quote used as a price)

- On R6 or NC15 books and tapes: MAKER5, L1Q1, GF1, GF2, DEPTH1, BOOKCH1, TAPEFLOW1, RETAILFRAC1, CRONCLUSTER1, NC15DEPTH1, W-SPOTLEAD1, W17 / S-FLOW1, S-LIM1, MAKERREPLAY1, CFRTI-B, and everything in this folder.
- On the hourly book recorder: QUOTE2B, MAKERTAIL1, MAKERMID1, BOOKIMB1, FLOWHR1, LADCOH1 book mode, LADBFLY1 (a) and (b), BFLY2, MMSIM1, MMSIM2, MMHOUR1, MMMAP1.
- On 1 minute candles: LAG15, SETTLE1, HOURLY1, VOLGAP1, LADFADE, LADL1, GEN3, G3H1, CORR1, GEN6 to GEN8, EVENT830, OICORE's research, W-SPOT1, W-SPOTGOLD1 and 2, the calibration families, NEWS_FADE, CFRTI-K as re-specified. **Candle freshness is its own open question**: CANDLEVSBOOK1 measures it as soon as the candle slice lands.
- Read once, no price: SETTLELAG1 (results poll times), W-HUNT2 (a data check), the combo and in-game inventories of Desk B (counts only).
- Not stated in the files (four one-line Refinement dispositions: W-GOLDLADDER, W-ROW40, W-ROW6, W-ROW59): all FAIL, so nothing positive rests on them.

## Things the old write-ups assumed

- "The book does not move in 0.6 s, so latency is not what limits these" (GEN4's result) and LATECAL's matching "next poll" column: consecutive polls are usually the same copy, so both latency checks are void.
- "Simultaneous quotes with sizes" (the recorder as described in V2's status file and NEWH13): not simultaneous, per market.
- RECORD1's clock gate (100 ms) and the whole RECORD1B clock fix: the clocks were fine; the data was old.
- The Oct 7 idea ledger row L5 already said "list price lags the single-market read by about 2c" and was never run. That is the one early sign that the single-market read is fresher than the list; it is a note, not a measurement.

## Re-score order (task 3; each is the same test with its registered rule and bar unchanged, book price beside the old figure, no new try)

1. **GEN4 forward rows** (row 5): V2's own evaluator fed R6 book rows in place of `quotes.csv` rows, closes Oct 30 to Nov 4, the spot-momentum rows and the two favourite references side by side with the ledger's figures. Held data only.
2. **RECORD1** (row 1): the registered rule on R6 books for closes Oct 29 22:15Z to Nov 3, four series. Held data only.
3. **MM1 gold** (row 10): if time allows; otherwise it goes back to V2 with the instruction "R6, not `quotes.csv`".

No outcome is joined for any Bitcoin 15 minute close on or after 2026-11-05.

## Limits of this audit

The V2 write-ups sweep read the files that matched a search for the recorder's names, not all 648 worker files; about 40 code modules that mention a bid or ask field were classified from their loader line only. The Refinement status file is heavily redacted and ends Nov 10. A test that read a list quote under a name none of the searches used would have been missed. Not checked by the Verification Analyst.
