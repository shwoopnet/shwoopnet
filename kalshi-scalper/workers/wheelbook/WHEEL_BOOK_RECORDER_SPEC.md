# Spec: a public order book recorder for the sports and esports shadows (Idea Desk B, Nov 12, 2026, 20:05Z)

Asked for by the Head of R&D at 20:02Z; the owner approved the recorder ("Yes, build it"); Main builds it. This desk builds nothing and makes no request. Research only: public Kalshi endpoints, no key, no auth header, no order, nothing under `functions/`, the R6 and NC15 pattern. Counts below are printed by `wheelbook/recorder_load.py` from the Nov 10 census listing (times and tickers only; a lower bound, one Tuesday).

## 1. Series, by exact ticker (phase 1: 9 series; phase 2: 4 tennis series)

| Rule | Series |
|---|---|
| MAPBREAK (CS2, Dota 2) | `KXCS2GAME`, `KXCS2MAP`, `KXCS2TOTALMAPS`, `KXDOTA2GAME`, `KXDOTA2MAP`, `KXDOTA2TOTALMAPS` |
| REMATCH, ESOCTIE, INPLAYJUMP (e-soccer) | `KXESOCCERGAME` (three contracts an event: two players and `-TIE`; all three are recorded) |
| INPLAYJUMP (table tennis, e-basketball) | `KXLIGAPROMATCH`, `KXEBASKETBALLGAME` |
| INPLAYJUMP (tennis), PHASE 2 | `KXITFMATCH`, `KXITFWMATCH`, `KXATPCHALLENGERMATCH`, `KXWTACHALLENGERMATCH` |

The list is fixed in code; adding a series is a reviewed edit.

## 2. What must be recorded for each rule, and how the recorder knows the window from fields known in advance

**The scheduled start S** of an event is the date and four-digit clock at the front of the ticker key (for example `KXESOCCERGAME-26NOV100722GIGIMADD`), read as US Eastern. It is in the ticker from the moment the market is listed. Every window below is set from S, from the market's own `open_time`, or from the market's status turning closed. Nothing is set from a result.

Two tiers. **SLOW:** one read a minute. **FAST:** one read every 3 seconds.

| Series | SLOW tier (60 s) | FAST tier (3 s) | Why |
|---|---|---|---|
| `KXESOCCERGAME` (all three contracts) | from the market's open to S minus 10 minutes | from S minus 10 minutes until the market is no longer open | REMATCH reads the later match's market from before the EARLIER match starts (up to 128 minutes before S: the reference minute and its 5 minute carry), then decides at S minus 6 and enters at S minus 5. ESOCTIE prices the Tie before the start (the History Miner must confirm its look minute is inside one of the two tiers). INPLAYJUMP needs every in-play minute from S to the close. E-soccer markets open about 150 minutes before S, so "from the open" covers REMATCH. |
| `KXLIGAPROMATCH`, `KXEBASKETBALLGAME` | none | from S minus 2 minutes until the market is no longer open | INPLAYJUMP: in play from S plus 60 seconds; the first in-play minute needs the minute before it. |
| `KXCS2GAME`, `KXDOTA2GAME` (the two match contracts) | from S minus 45 minutes to S | from S until the market is no longer open | MAPBREAK: pre-match instant at S minus 10 (stepping back to S minus 40); the two looks fall 2 to 5 minutes after map 1 and map 2 close, at times nobody knows in advance, so the match contracts are recorded fast through the whole match. |
| `KXCS2MAP`, `KXDOTA2MAP` (maps 1 and 2 only) | from S until that map market is no longer open | none | MAPBREAK's state is the map markets' close times and results (section 4); the quotes are only for the count "was the winner's contract at 90c or more in its last quote", for which a minute is enough. |
| `KXCS2TOTALMAPS`, `KXDOTA2TOTALMAPS` | no polling | no polling | Only the listing is needed: a best-of-three is an event with a 2.5 market and none higher. Kept from the list reads. |

Every match of the listed series is recorded, whatever its format; the engines choose best-of-three afterwards from the list. An event whose ticker has no readable clock is recorded SLOW from its open and counted.

**How the recorder finds events:** one list read of open markets per series every 5 minutes (`GET /markets?series_ticker=X&status=open`, cursor followed). On Nov 10 these markets opened a median of about 150 minutes before S (e-soccer, e-basketball) to many hours before it (table tennis, esports), so a 5 minute discovery should lose nothing; the coverage row counts any event first seen after its window began.

## 3. Polling, load and size

- **What a poll keeps:** the best 5 YES bids and best 5 NO bids with sizes, the server's Date header, the send and receive time. One batched read (`/markets/orderbooks`) for as many tickers as the endpoint allows; Main confirms the cap. Fallback to one read a market after 3 failed batches in a row, as R6 does. A 429 waits and doubles, never loops.
- **Tickers at once (Nov 10, 06:00 to 24:00 UTC, lower bound):** FAST mean 53, 95th percentile 76, highest 86 (e-soccer mean 22, table tennis 7, e-basketball 3, CS2 match 11 with a peak of 38, Dota 2 match 10 with a peak of 26). SLOW mean 156, highest 230.
- **Requests a minute:** if one batched read takes 100 tickers: FAST 20, SLOW 2 to 3, discovery about 2, results and candles (section 4) about 2: **about 27 a minute**, a little under R6's 35. If the batch cap is lower than about 90, the FAST tier needs two reads a poll at busy hours (40 a minute); Main then chooses between two request streams and a 4 second poll, and says which in the file.
- **Size, and why "keep every poll" does not fit:** FAST is about 1.5 million ticker-polls a day. R6 stored about 167 bytes gzipped a ticker-poll (36 MB a day for 5 markets at 2 seconds). Storing every poll would be about 250 MB a day, about 20 GB by the stop date. **So: store a book row only when that ticker's top 5 changed since its last stored row, and store one small row for EVERY poll** (poll time, Date header, tickers asked, tickers answered, HTTP status). The book at any poll is then the last stored row at or before it, and the poll log proves the second look happened. My guess, not a measurement: 30 to 60 MB a day, 2.5 to 5 GB by the stop date. That is still too much for one branch that every job fetches whole, so: **one orphan branch a calendar week** (next point). Main measures the first day and reports the real figure; if it is over 80 MB a day the SLOW tier drops to the best level only.

## 4. Results and candles after the close, so the replay needs no other pull

- **Results:** every 10 minutes, per series, one list read of markets that closed in the last 2 hours (`status=settled` and `status=closed`, with a close-time floor). Kept once per ticker, re-read until the result is yes or no or 24 hours have passed: ticker, event ticker, `open_time`, `close_time`, `settlement_ts`, `occurrence_datetime`, `result`, `floor_strike` (total maps), `exchange_index`, the contract titles. In the Nov 10 listing results were posted 2 to 6 minutes after the close in these series.
- **One-minute candles, after the close:** one batched candle read per group of closed markets (up to 100 tickers and 10,000 candles a request) covering each market's recorded window. Reason: the registered rules are DEFINED on minute candles (minute-end bid and ask, and for INPLAYJUMP "volume above zero in the jump minute", which no order book shows). With the candle file the engines read exactly the inputs they were registered on, and the book file is used only for the fill check. About 20 to 40 requests a day.

## 5. Branch, stop date, guards

- **Branch:** its own orphan branches, one a calendar week, named `wheelbook-<ISO year>w<week>` (for example `wheelbook-2026w46`), files under `wheelbook/<date>/<HHMM>/` (`book_fast.csv.gz`, `book_slow.csv.gz`, `polls.csv.gz`, `results.csv.gz`, `candles.csv.gz`, `coverage.csv.gz`). Never main, never `quote-data`, `nc-data`, `sports-data` or `kalshi-pull-data`.
- **Stop date:** 2027-01-31 23:59 UTC, checked in the workflow's first step and in the script. Stop sooner by deleting the workflow.
- **Pattern (R6 and NC15):** public host only, no key, no auth header, redirects refused, a generic User-Agent, triggers every 15 minutes under one concurrency group that never cancels a running job, each job recording to the next 4 hour boundary, the six-try push loop, minimal permissions, a pinned checkout, a coverage row per event (polls, 429s, fallbacks, largest gap, rows stored), an hourly clock check. Gates in `test/` like FB1 to FB12.
- **Runner minutes:** continuous, about 43,000 billed minutes a month like R6 and NC15. Free on a public repo, far over the Charter's 250 minute guideline; the owner's approval and merge accept that figure.

## 6. Standing rule (h): these files carry results by design

Every recorder file holds what happened after the entry: the result field, and prices running to 0 or 1. So:
- Recorder data is a FORWARD record that starts on the day the recorder is merged. It is not any card's development or held-out sample. MAPBREAK, INPLAYJUMP, REMATCH and ESOCTIE keep their registered date constants and their held-out guards; their held-out windows end on or before 2026-11-13 and the recorder holds nothing that early.
- An engine reads recorder files only in a replay mode that is switched on by hand, prints "forward shadow record, not a research read" on its page, and takes the same instants and no later one.
- Nothing is tuned on recorder data. A rule registered after recorder data exists takes later dates as its held-out (rule (h), point 4).
- Nobody browses the files; they are read by the frozen engines only.

## 7. The replay, and what I can and cannot confirm tonight

**The fill check, as the wheel defines it:** the engine decides from the candle file exactly as registered and sets its limit (ask plus 1c). In the book file, take the first poll at or after the decision instant: the YES ask ladder is 1 minus the NO bids. The order is filled only if that poll AND a second poll no more than 4 seconds later (the poll log proves it happened) both offer the order's size at or under the limit; the fill price is the worse of the two. Otherwise it is a miss, counted.

| Engine | Owner | Can it read the recorder's files? |
|---|---|---|
| REMATCH stage 1 reader (`rematch/stage1_measure.py`) | this desk | Yes for the decision inputs: it reads minute candles keyed by the minute's end, which is the shape of `candles.csv.gz` after a small loader. The scorer and the fill check are not built yet; they are built with this file format in mind. |
| MAPBREAK (`breakplay.py`, `scorekit.py`) | Testing Desk | Not confirmed by me. It reads minute candles and lists, so the candle and results files should fit after a loader; the fill check on the book file is new code. The Testing Desk must confirm. |
| INPLAYJUMP (`desk_a_verify/inplayjump.py`) | Desk A | Not confirmed by me. Same position; it also needs the candle volume, which is why section 4 keeps candles. Desk A must confirm. |
| ESOCTIE | History Miner | **Confirmed by the History Miner, 20:06Z:** it decides at S minus 60 seconds on the latest minute where the Tie and both team contracts are two-sided, stepping back no further than S minus 10 minutes, so the FAST tier from S minus 10 minutes covers every look and the fill check. Its engine reads kalshi-pull run folders through the Testing Desk's loaders, so it needs one small loader that yields the same records (markets: ticker, event, open, close, result; candles: time, bid and ask closes); no change to the scorer. |

I am asking the three desks to confirm against this spec and will send Main their answers.

## Phase 2: tennis

ITF and challenger markets are open about 18 hours and carry no start clock, so "from a set time before the start" cannot be written. Two honest options: (a) SLOW from the open for every market (about 600 tickers a minute at once, 6 batched reads a minute) and FAST once the recorder's own slow rows show three 2c moves inside 20 minutes, which is the rule's own in-play test and uses only the past; or (b) leave tennis out until INPLAYJUMP's tennis screen has passed its validation pull. **I recommend (b):** tennis sits on another shard, is the costliest family and may yet be dropped from the card.

## Added 20:06Z (Head of R&D's rulings of 20:06Z; the History Miner's needs)

1. **The per-poll row is what proves the second look,** so it always carries the poll's own send and receive time and the server's Date header (accepted by the Head with change-only book rows).
2. **The candle read after each close is bounded to that market and its recorded window.** It is never a held-out pull: it asks only for tickers the recorder itself has just watched close, on the day they close, and for no earlier date. No recorder request ever covers a card's registered held-out window.
3. **The wheel's record is fill-checked on a real book.** The engines decide from the minute candle exactly as registered; the book file is used for the fill check. A record from candles alone is not a wheel record.
4. **Every event is recorded, not only ones a rule might bet** (ESOCTIE's walk-forward base rate needs each past event's team prices at its own decision minute). The results rows must keep, per market: `open_time` (ESOCTIE's universe guard is "the Tie opened 10 to 240 minutes before S"), `close_time`, `settlement_ts` (its base rate admits a result only 300 seconds after the close), `result` and `exchange_index`. All five are already in section 4's list.
5. Tennis is phase 2 (agreed by the Head).

