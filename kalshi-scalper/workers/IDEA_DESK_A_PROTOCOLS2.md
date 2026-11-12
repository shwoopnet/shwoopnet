# Idea Desk A: protocols for queued cards, batch 2 (Nov 12, 2026)

Asked by Main: ready-to-run protocols for WXDAYEND (card 74), the economics release fade (card 87, counted with the official-components idea) and the Wikipedia attention test (POL-n1). Written before any outcome of these tests was read by this desk. The desk writes protocols; V2 or Refinement runs them. Zero Kalshi calls were made to write this. Conventions as in `IDEA_DESK_A_PROTOCOLS.md` (cash basis, 1 contract, taker fee 0.07 x p x (1-p) unrounded unless stated, development then a held-out part read once, shared deflation count).

Status of the three:
- **Q1 WXDAYEND: do not write a second test. It already has a registration and a FAIL on the Refinement branch.** What is below is only a zero-call way to finish the half of the sample that was never pulled.
- **Q2 POL-n1 Wikipedia attention: full protocol below.**
- **Q3 Economics release fade: waiting on Refinement** for card 87's rule text (the row is redacted on the branch tip) and for what its economics worker has already pulled. I will not guess a rule for someone else's card. A short frame of the points the protocol must fix is at the end.

---

## Q1. WXDAYEND (card 74): finish the existence check on recorder data, no new test

**What already exists.** `refine_tools/CARDS_74_84_REGISTRATION_AND_RESULT.md` on `claude/refine-live` registered card 74 on Nov 11 and ran its first step. Facts it established: the daily high markets close one hour after the standard-time climate day ends only for events dated 2026-11-01 onward (before that there was no after-the-day window at all), and on 20 of the 40 city-days it pulled, the winning bracket's YES ask was 1.00 on every one minute candle of the last two hours. Verdict recorded there: FAIL, no priced window.

**The one loose end.** The registered rule was "FAIL if fewer than 3 of 40 city-days show an ask at or under 0.96 after the day ends". The pull stopped at 20 of 40 (New York 9, Los Angeles 9, Denver 2, Dallas 0). By the letter, the 20 unpulled city-days could still hold 3. I do not expect them to, but the verdict as written rests on half the registered sample.

**How to close it with zero Kalshi calls.** The weather recorder (`quote-data:wxens/quotes/` and `quotes_low/`, columns `slot_ts, city, target_date, ticker, event_ticker, close_time, strike_type, floor_strike, cap_strike, yes_bid, yes_ask, last, volume, status`; `results/` with `result` and `expiration_value`) has every bracket of 14 cities twice an hour up to the close since Nov 4.
1. Universe, fixed here: every city-day (highs and lows apart) with `target_date` from 2026-11-04 on whose event has a result on the branch. About 14 cities x 2 x the days recorded.
2. For each, the day-end instant is 00:00 local STANDARD time after `target_date` (the watchlist's `std_offset_h`); the close is one hour later. Take the snapshots of the bracket whose `result` is yes with `slot_ts` in [day end, close).
3. Count city-days with at least one such snapshot where `yes_ask <= 0.96` and `yes_ask > yes_bid` (a real two-sided quote, not an empty book shown as 1.00). Also report how many city-days have no snapshot at all in that hour (two snapshots an hour should give one or two).
4. Rule, scaled from the registered one (3 of 40 is 7.5%): **FAIL if fewer than 7.5% of city-days with a snapshot show it.** A FAIL closes card 74 for good, on about five times the sample. If it does not fail, nothing is traded: the edge-bracket test that card 74 describes still needs station readings in tenths and a held-out design, and it goes back to Refinement, whose card it is.
5. This is the registered existence step finished on other data, not a new try. It reads the settled result only to know which bracket to look at, as the registered step did.

**Flag for whoever reads card 74 later.** Buying a bracket that is already decided at a price under 97c is a favourite-shaped buy. Refinement's registration says card 74 is "edge-bracket only" and has no cell at 88c or above within 6 hours of the close. Any variant that buys the decided bracket in the 88c to 97c band needs the owner's own ruling under lifecycle 7e before it is even measured.

---

## Q2. POL-n1: Wikipedia pageview attention spikes on "out as / leaves / fired / charged" markets

Source card: `refine_tools/POLITICS_CARDS_NOV11.md`, row POL-n1 (Refinement). Owner rule (politics rulebook, popups 17 to 28): attention signals are tested in BOTH directions, pre-registered. Terms as recorded on that card's terms table: the Wikimedia pageviews REST API is PERMITTED (public CC0 data; Wikimedia's User-Agent policy asks for a descriptive agent with a contact; rate limits apply).

**Claim to falsify, two arms, 2 tries counted:**
- **FOLLOW:** after a pageview spike on a named person's article, the YES side of that person's "leaves office" market, bought cheap, gains over the next 7 days.
- **FADE:** after a spike on a day when YES jumped, the NO side, bought at 60c to 88c, gains over the next 7 days. (The card scored this arm as a control only; the owner's both-directions rule and the "nothing happens" rule, NO at 60c to 88c, make it a registered arm here. It is a NO-at-a-high-price position, so it stays inside that rule's limits and is flagged as such.)

**Universe, frozen before any pageview or price is read.** The ten series named on the card: KXLEAVEWALZ, KXWALZOUT, KXPOLISOUT, KXMODIOUT, KXLEAVEMERZ, KXBURNHAMOUT, KXCARNEYOUT, KXLEAVETULSIGABBARD, KXTRUMPFIRECOOK, KXSCHIFFCHARGE. One file `poln1_universe.csv` committed first: `series, market ticker(s), person, exact English Wikipedia article title, market open date, market close date`. The article title is the person's main biography page; no disambiguation or topic pages. Open and close dates come from Kalshi's market list (a count-only read, about 10 to 20 requests from the tester's budget or one `kalshi-pull` job). Adding a market after this file is committed is a new registration.

**Signal (no look-ahead).**
- Daily views `v(D)`: the pageviews API, project `en.wikipedia`, access `all-access`, agent `user`, daily, one request per article for the whole range (about 10 requests in all, at most 1 a second).
- `mu(D)` and `sd(D)`: mean and sample standard deviation of `v` over days D-60 to D-1 (never D itself). A SPIKE is a day with `v(D) >= mu(D) + 4 x sd(D)` and `v(D) >= 2000`.
- A day's count is published the following day. **Decision time = 15:00 UTC on D+1**, fixed here, which is after publication with margin. Nothing dated after D is used.
- One entry per market per 14 days: a second spike inside 14 days of an entry is ignored and counted.

**Prices.** Kalshi hourly candles of each market over its life (`/series/{s}/markets/{t}/candlesticks` or the historical path; about 2 to 6 requests a market, 30 to 60 in all). Entry price = the ask of the side bought at the close of the hourly candle ending 15:00 UTC on D+1; YES ask as given, NO ask = 1 minus YES bid. Skip (and count) if that candle has no two-sided quote or the YES spread is over 5c.

**Rules.**
- FOLLOW: if YES ask is 0.05 to 0.40, buy 1 YES.
- FADE: only if the YES mid at the close of day D is at least 10c above the YES mid at the close of day D-1; then if NO ask is 0.60 to 0.88, buy 1 NO.
- Exit, both arms: at the close of the hourly candle 7 days (168 hours) after entry, sell at that side's bid; if the market settles first, take the settlement. Fees: the taker fee on entry and again on the sale; none on a settlement.
- A spike can enter at most one arm (FADE needs the jump, FOLLOW needs the cheap ask; if both hold, both entries are recorded, each in its own arm).

**Step 1, counts only (the likely end of the card).** After the universe file and the pageviews are in: the number of spikes that fall on days when the market existed, per person and in total. **NOT_ENOUGH_DATA and stop, before any price is read, if there are fewer than 80 such spikes** (the card's floor is 40 per half). State the count either way. With ten markets and a four-sigma trigger I expect this to be where it ends; that is an honest outcome, and it costs about 10 pageview requests and 15 Kalshi list requests.

**Step 2, scored once, only if step 1 clears.**
- Cuts: entries sorted by decision time, first two thirds development, last third held out and read once for a survivor. Cluster = person (one person's spikes are one story).
- Bars: development n at least 40 entries in an arm from at least 5 people, cash PF 1.5 or better, mean net above +2c, person-clustered z reported against the shared deflation bar (about 5.3) and the lenient one; held-out PF 1.5 or better. FALSIFIED if development PF is under 1.0 at n 40 or more. The card's own kill also applies: a median entry spread over 3c closes it.
- Report beside each arm: the same rule on non-spike days chosen by a fixed seed (same person, same price band), as the baseline; and the result with entry one day later (D+2), which should be weaker if attention leads.

**Limits a live version would hit (said now).**
- The politics rulebook's live limits are "hold to settlement" and a 30 day maximum to settlement. These markets are mostly long-dated and this rule exits after 7 days. So even a pass here could not go live as written: it would need the owner's exception for a time exit, or a version restricted to markets that settle within 30 days of the entry, which is a far smaller sample. The protocol is still worth running as research because step 1 is nearly free.
- The User-Agent: Wikimedia asks for a descriptive agent with a way to contact the operator. What goes in it is the owner's choice (the project rule is no personal details in requests to outside services). The pull must not run with a default library agent.
- The host: `wikimedia.org`, one path prefix (`/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/`), GET only, no key. A one-off pull inside a tester's session is what the queue allows; adding the host to the signal logger is a separate reviewed change with its own gate and is not needed for the backfill.
- Ten people is ten clusters. A person-clustered statistic on ten clusters cannot reach the deflation bar; the best honest outcome is a lead.

**What would make the result a lie.** (1) Using `v(D)` in its own mean or deviation. (2) Entering on day D. (3) Picking the article after looking at its view history (the universe file is committed first). (4) Dropping markets that were delisted or settled early: every market that existed on the spike day is in. (5) Counting the two arms as one try.

---

## Q3. Economics release fade (card 87, with the official-components idea): frame only, pending Refinement

I asked Refinement (Nov 12) for card 87's rule text and for what its economics worker has pulled. Until that arrives I will not write a rule for it. The points the protocol has to fix, so the reply can be turned into one quickly:

1. **Event list, frozen first:** the release days and times, from the official schedules (BLS for CPI and payrolls; the Fed for decisions), keyed by hand like EVENT830's calendar. No date found after the fact.
2. **Markets:** which series the fade trades (the card's ranking line says the Fed meeting series) and which strike of it (the one nearest 50c at the last candle before the release, fixed before the print).
3. **Shock definition without look-ahead:** the move from the last candle that closed BEFORE the release second to the candle closing 10 minutes after; a shock is 15c or more. The reference candle must end before the release, not at it.
4. **Entry and exit:** the side against the move, at the ask of the candle closing at minute 10; a TIME exit at the bid of the candle closing at minute 20 (this is the first card in the queue with a real time exit, which the lifecycle notes as a gap). Entry and exit fees both count.
5. **Counted together:** the fade and the official-components idea share one deflation count (owner, popups 29 to 40). The official-components rule has to be stated by its own card before either is scored.
6. **Sample honesty:** about 12 CPI and 12 payroll prints a year and 8 Fed decisions; three years is under 100 events before the shock filter, so NOT_ENOUGH_DATA is the expected first verdict and the protocol must say when n 40 per half could exist.
7. **No duplicate pulls:** use whatever candles Refinement's economics worker already holds; list the gaps as a `kalshi-pull` job, not a second crawl.
