# ESOCTIE: the listed Tie in e-soccer match markets, against its base rate (registration, Nov 12, 2026)

**Registered before any price or result of these markets was read by this desk.** Written by the R&D History Miner on the Head of R&D's brief of Nov 12 (item 3, "the TIE3 idea on a venue with enough events to read"). Frozen series and constants: `esoctie/ESOCTIE_SERIES.json`. Research on public data only; no live account figure here. [research]

`ESOCTIE | family: a listed third outcome priced under its base rate (TIE3's mechanism, a new venue: a VERSION of TIE3 under lifecycle 7g, ruled by the Head) | entry before the game on the Tie contract, hold to the end of the game (about 10 to 15 minutes) | risk class: mid price (about 15c to 35c), 1 contract, hundreds of events a day, no market or clock shared with any live strategy | stage Idea`

## What has been seen so far

Only shape and times, from the Nov 10 census listing (`CENSUS_LISTING` on `kalshi-pull-data`): tickers, event keys, open, close, occurrence and settlement times of a handful of KXESOCCERGAME events. No price field and no result field was printed or used. Seen: three markets an event (two team markets named by club and gamer tag, and `-TIE`, "Game ends in a tie"); the key reads date and Eastern clock time (26NOV091943 is Nov 9, 19:43 ET); the market closes about 12 minutes after that time and settles about 4 minutes after the close; `occurrence_datetime` is the key time plus 3 hours and is NOT used.

## Rulings and checks it rests on

1. **Mechanism is TIE3's** (Desk B card 18, `tie3/TIE3_REGISTRATION.md` on `claude/idea-desk-b`): team buyers come for a player; the Tie is left to whoever quotes it. The Head's 18:24Z note said "E-soccer does not join TIE3's frozen cells"; this is therefore its own registration, a version on a new venue, counted as its own try. The Head rules whether it counts toward the owner's five as one candidate with TIE3.
2. **Declined list (lifecycle 7e), compared row by row.** TIECOND1 ("tie or frozen-source YES rules"): that row is the 15 minute price markets where an unchanged price settles YES, a rare edge case; this is a listed sports-style Tie that happens perhaps 20% to 30% of the time. Different market, contract and reason; the word "tie" is in that row, so the Head rules, as for TIE3. Favourite-and-hold: not a favourite (the Tie is bought at about 15c to 35c). Cheap-side sweeps: not the 15 minute series and not a sweep; one rule, fixed now. In-game lag: entry is before the game. Lock and parity: not a lock; it can lose.
3. **Closest earlier test:** VIRT1 (V2, Nov 7) read the cheap side of the TEAM contracts of the same series against a player rating: NOT_ENOUGH_DATA at 15 trades, every sign on the falsified side. It never read the Tie contract as a base-rate bet. It is a prior against this venue's makers being careless, not a test of this rule.
4. **Data:** Kalshi's own public markets only, through kalshi-pull. No outside site.

## The instants and prices (pinned)

1. **Scheduled start S:** the key's date and four-digit clock time read as US Eastern time. **Guard:** the event's markets must close between S + 5 and S + 30 minutes; otherwise the event is dropped and counted "start not derivable".
2. **Pre-match instant:** the one-minute candle ending at S minus 1 minute. All three contracts (both teams and the Tie) must be two-sided at that candle's close (0 < bid < ask < 1). If not, step back a minute at a time to S minus 10 minutes; if none, the event is "not filled" and counted. Nothing is filled in from another minute.
3. **Strength f:** the larger of the two team contracts' mids at the pre-match instant. Bucket edges on f: 0, 0.45, 0.55, 0.65, 0.75, 1.0.
4. **Base rate b:** the share of EARLIER development events (market close strictly before this event's S) in the same f bucket that settled Tie. It needs at least 300 such earlier events; until a bucket has 300 the event is "base-building" and no bet is placed. Base-building events are counted and never re-entered.

## The rule (1 try)

At the pre-match instant, **if b minus the Tie's ask is 10c or more and the Tie's spread is 4c or less: buy 1 Tie contract.** One bet an event. Hold to settlement.

- **Price paid:** the Tie's ask plus 1c (a limit one cent through the ask, booked filled there). Fee: 0.07 x price x (1 minus price), rounded UP to the next whole cent. The fill haircut table of `HOW_TO_PRICE_A_PAPER_TRADE.md` (claude/forensics-desk) is shown beside the result: drop 15% (2 s) and 23% (6 s) of bets, worst-case first and at random.
- **Result:** the Tie market's own result, read for every development event in time order (it builds b) and booked for bets.
- **Direction is fixed:** if the Tie turns out OVERPRICED against b, the card closes; it is not turned round.

**Known leans, stated before data.** (a) The base rate pools all player pairs in a bucket; pairs that tie more or less often are priced by makers who know them, so b is cruder than the price and a gap can be b's own error, against us. (b) f is measured from the same quotes the bet uses; a stale Tie quote alongside fresh team quotes would show up as a gap and may be the real thing, or one contract deep. (c) Candle freshness was measured on Bitcoin 15 minute only, not on e-soccer.

## The placebo (what noise alone looks like)

The same statistics for the mirror line: the share of filled events where the Tie's BID is 10c or more ABOVE b (spread 4c or less). With no edge and symmetric noise the two shares should be close. Reported beside the real line.

## Kill rules, read first, before any bet is booked (fixed now)

1. Under 150 filled non-base-building events: "no evidence at n = x".
2. **Closed on cost** if the median round trip on the Tie at the pre-match instant (spread plus two fees at the mid) is above 5c.
3. **Closed, "efficient, move on"** (the 90th percentile of b minus ask as the one number) unless the share of filled events with a gap of 10c or more and a spread of 4c or less is at least 3% AND at least twice the placebo's share.
4. If any of these closes the card, no bet is scored.

## Samples (date constants)

- **Development:** events whose markets closed from 2026-09-12 00:00 UTC to before 2026-10-23 00:00 UTC. Halves split at 2026-10-03 00:00 UTC.
- **Held-out:** closes from 2026-10-23 00:00 UTC to before 2026-11-13 00:00 UTC, about the most recent third of what the live endpoint holds. **Not listed and not pulled** until the Head's go after the development read; read once. Its base rate uses only events closed before each held-out bet's S (development plus earlier held-out events).

## What is reported (counts first)

Events listed; start derivable; filled; base-building; filled and eligible; median spread and round trip; gap median, quartiles and 90th percentile; the 10c and 4c share and the placebo share, each per f bucket. For the rule: bets; wins; mean price paid; cash PF; net cents a contract; each half; each f bucket; the largest share of net from one day; one-sided z with the day as the cluster; the haircut lines.

## Verdicts (fixed now)

- Under 100 bets: "no evidence at n = x".
- 100 or more bets and cash PF under 1.0, overall or in either half: FALSIFIED.
- Cash PF 1.5 or better with both halves above 1.0: "development bar met"; the held-out pull is asked of the Head the same hour.
- Otherwise: "below the bar at n = x, PF y".
- **The research bar:** cash PF 1.5 or better on development AND held-out, one-sided z 5.46 or more on the two together (shared count about 2,113,000 tries). Nothing short of that is called a pass.

## Events and power, said plainly

Nov 10 (a Tuesday, a lower bound): about 450 e-soccer events. Development (41 days) about 18,000 events, held-out about 9,000. If the rule fires on 3% of eligible events that is about 500 development bets; at 5%, about 900. A true PF of 1.5 near 25c needs about 1,000 to 1,200 bets for z 5.46 over both samples, so the read can decide the question only if the rule fires on about 3% or more.

## Prediction (numeric, before data)

Median gap (b minus ask) within plus or minus 3c; the 10c share under 3% (the card closes as "efficient, move on", my probability about 75%); if it does fire, cash PF 0.8 to 1.1. **Probability it reaches the research bar: 1 to 2%.**

## Tries

**1** (one rule, buckets are reported, not separate rules). Added to the deflation ledger through the Head before any bet is scored.

## Requests

- **Lists (`ESOCTIE_LISTS`, written):** 4 requests, at most 81 pages (expected about 55, about 120 MB), development closes only, three date slices, plus the series fee fields.
- **Candles (built from the lists, a reviewed job before it runs):** per event the three contracts from S minus 10 minutes to S, packed by S (window minutes x tickers at most 9,000): estimate 1,000 to 2,000 requests, one or two runs. The exact count comes from the lists.

## NOTE 1, Nov 12, 2026, 19:05Z, before any price or result of these markets is read (Head of R&D's rulings of 18:59Z)

1. **Accepted as registered, 1 try.** For the owner's count it is ONE candidate with TIE3; it sits outside the declined tie row for the same reason TIE3 does.
2. **The Tie's typical price is NOT stated from the listing, on purpose.** The only listing held (Nov 10 census) carries settled markets, whose price fields (last price, bid, ask) are taken after the game ended and so carry the result. They were not printed and will not be read for this. The price is first seen at the measurement.
3. **Cheap-tail close, added as a kill line before scoring:** if the median Tie ask at the pre-match minute, over the filled eligible events, is under 15c, the card is CLOSED there as a cheap-tail contract (pooled calibration loses in every cheap bucket) and no bet is scored.
4. **Constants, not fitted:** the strength bucket edges (0, 0.45, 0.55, 0.65, 0.75, 1.0) and the 300-event minimum are fixed in `ESOCTIE_SERIES.json` and were set before any data. The base rate is walk-forward: only events whose markets closed before the bet's scheduled start count.
5. **Events in the cheap window:** all of them. Development (closes 2026-09-12 to before 2026-10-23) and held-out (to before 2026-11-13) are both after about 2026-09-07, so every candle is on the batched endpoint; no older candle is requested.
6. **Build:** the Testing Desk builds the venue on its `tie3.py`; this desk's `esoctie.py` stays as the reference scorer, and the two must agree on the same input before any read.

## NOTE 2, Nov 12, 2026, 19:10Z, before any price or result is read (Head of R&D's ruling of 19:01Z)

The guard in "The instants and prices" point 1 used the event's own close time, which is known only after the decision. It is REPLACED: an event is kept only if its key's clock reads as a time (S) and the Tie market OPENED between 10 and 240 minutes before S (both known before the decision); otherwise it is dropped and counted "start not derivable". Close time is no longer used to decide whether a bet exists. It is still used, as registered, only to place an event in the development or held-out block by the date constants (a calendar split, the same for every event), and to place earlier events in the walk-forward base rate (an event counts toward b only if it closed before the bet's S, which is known at the decision).

## NOTE 3 (amendment), Nov 12, 2026, 19:20Z, before any price or result is read (Head of R&D's rulings of 19:02Z, from Desk A and Auditor B)

1. **Base rate strictly point-in-time.** A game's Tie result enters b only if that game's close plus 300 seconds is at or before the bet's decision time (the end of the candle used at the pre-match instant). Settlement comes about 4 minutes after the close, so a result inside that gap is not yet known. This replaces "market close strictly before this event's S". Test 6 in `test_esoctie.py` fails if a result inside the 300 second gap can move a decision, and checks that one outside it does.
2. **Cost kill changed from a round trip to the ONE-WAY entry cost.** The rule buys and holds to settlement: there is no second spread and no second fee, and a round-trip line with the 1-contract fee rounded up would close anything with a spread over 1c before one bet is scored. New kill: over the filled eligible events, the median of (Tie ask minus Tie mid) plus the entry fee as charged (0.07 x p x (1 minus p) at the price paid, ask plus 1c, rounded up to the cent); CLOSED on cost if that median is above 4c. It is a request-saving screen, not the bar: the scored profit factor pays the real ask, the 1c slip and the fee. Changed before any price was read, on the Head's ruling for every hold-to-settlement rule registered on Nov 12.
3. **Universe guard** is NOTE 2's (ticker clock and the Tie's open time); NOTE 2 already removed the guard on the close time that Auditor B also flagged.
4. **Reported beside the result:** the count of eligible events whose Tie result is neither yes nor no (void or unsettled); they are not booked.
5. The round-trip line stays in the report as information only.

## NOTE 4, Nov 12, 2026, 19:25Z, before any price or result is read (Forensics' audit notes)

1. **A fired bet whose Tie market has no yes or no result** (void or unsettled) is booked, by a rule fixed now, as a loss of the entry fee only (price refunded, fee kept), and its count is reported. No fired bet is dropped by how its game ended.
2. **Label:** the development figure is reported as "selected on development": it can falsify, it cannot support; only the frozen held-out read can.
3. **Settlement allowance:** the 300 seconds of NOTE 3 is the Head's ruled constant (Forensics suggested 10 minutes as an example; 300 s is above the measured settle delay of about 4 minutes on the e-soccer events seen in the census listing).
4. Haircut: no "ran away" haircut from a later candle is used; the scorer prints the random-drop table of `HOW_TO_PRICE_A_PAPER_TRADE.md` with its caveat that real misses lean toward winners.

## NOTE 5, Nov 12, 2026, 19:30Z, wording only, before any data (Auditor B)

"Price refunded, fee kept" for a void is an ASSUMPTION about how Kalshi settles a voided market, not a measurement; if the fee is also refunded, NOTE 4's booking is slightly conservative. The result page says so beside the void count.

## NOTE 6 (withdrawn, see NOTE 7)

## NOTE 7, Nov 12, 2026, 19:40Z, before any data (Head of R&D)

NOTE 6 is withdrawn (its text and code are removed): the Head made NOTE 4's void booking the standard for every hold-to-settlement card, so no side-by-side booking is printed. NOTE 4 stands unchanged. `esoctie.py` is back to the audited file (sha256 57801716...d833).

## NOTE 8, Nov 12, 2026, 19:45Z, before any data (Head of R&D's standing rule (h), shared held-out windows)

1. The held-out block of KXESOCCERGAME (closes 2026-10-23 to before 2026-11-13) is shared by three cards: ESOCTIE, REMATCH (Desk B) and INPLAYJUMP's e-soccer family. No list or candle request may cover it until every one of them has finished its development read, has its scorer frozen by commit and sha256 recorded on `rnd-queue`, and has a committed read-once marker line (a card that failed development blocks nobody). Then one joint pull, on the Head's go, into a folder whose name starts `HELDOUT_`, read once by each card on its own go.
2. **2026-11-10 is DROPPED from ESOCTIE's held-out block:** its results already sit in a landed file (the Nov 10 census listing). The held-out block is closes 2026-10-23 00:00 UTC to before 2026-11-13 00:00 UTC except those closing on 2026-11-10 (UTC).
3. "The held-out pull is asked of the Head the same hour" now reads: asked the same hour; granted when the other two cards are frozen or out.
4. `esoctie.py` refuses any folder whose name starts `HELDOUT_` by default (test 7). This changed the file's sha256; both auditors are asked to re-run only that check.
