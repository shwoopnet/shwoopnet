# Idea Desk A: protocols for queued cards, batch 2 (Nov 12, 2026)

Asked by Main: ready-to-run protocols for WXDAYEND (card 74), the economics release fade (card 87, counted with the official-components idea) and the Wikipedia attention test (POL-n1). Written before any outcome of these tests was read by this desk. The desk writes protocols; V2 or Refinement runs them. Zero Kalshi calls were made to write this. Conventions as in `IDEA_DESK_A_PROTOCOLS.md` (cash basis, 1 contract, taker fee 0.07 x p x (1-p) unrounded unless stated, development then a held-out part read once, shared deflation count).

Status of the three:
- **Q1 WXDAYEND: do not write a second test. It already has a registration and a FAIL on the Refinement branch.** What is below is what it takes to finish the half of the sample that was never pulled (20 Kalshi requests; my first draft wrongly said zero).
- **Q2 POL-n1 Wikipedia attention: full protocol below.**
- **Q3 Economics release fade (card 87): full protocol below**, written after Refinement sent the card's rule text (Nov 12). Which card is the "official-components idea" is still open; see the note in Q3.

---

## Q1. WXDAYEND (card 74): finish the existence check on recorder data, no new test

**What already exists.** `refine_tools/CARDS_74_84_REGISTRATION_AND_RESULT.md` on `claude/refine-live` registered card 74 on Nov 11 and ran its first step. Facts it established: the daily high markets close one hour after the standard-time climate day ends only for events dated 2026-11-01 onward (before that there was no after-the-day window at all), and on 20 of the 40 city-days it pulled, the winning bracket's YES ask was 1.00 on every one minute candle of the last two hours. Verdict recorded there: FAIL, no priced window.

**The one loose end.** The registered rule was "FAIL if fewer than 3 of 40 city-days show an ask at or under 0.96 after the day ends". The pull stopped at 20 of 40 (New York 9, Los Angeles 9, Denver 2, Dallas 0). By the letter, the 20 unpulled city-days could still hold 3. I do not expect them to, but the verdict as written rests on half the registered sample.

**CORRECTION (Nov 12, same day): it cannot be closed with zero Kalshi calls.** My first draft of this section said the weather recorder holds every bracket "twice an hour up to the close". That was wrong, and I found it when I went to run the check. The recorder starts twice an hour but takes QUOTES only at three fixed morning looks (labels `L0_07`, `L1_07`, `L1_10`). Counted from the files on `quote-data` (36 quote files, 1,248 rows, Nov 4 to Nov 11): the latest quote of any market is 16.5 hours before its close, and no row is within 3 hours of a close. So the recorder has nothing after the day ends and cannot answer the existence question.

**What finishing it takes instead.** The 20 unpulled city-days of Refinement's registered sample (Dallas 10, Denver 8, New York 1, Los Angeles 1), final two hours of 1 minute candles for the winning bracket: 20 Kalshi requests. That is one small `kalshi-pull` job once the workflow exists, or 20 requests from Refinement's share. The rule stays as registered (FAIL if fewer than 3 of the 40 show an ask at or under 0.96 after the day ends). Until then the honest label for card 74 is "FAIL on the half that was pulled, 20 city-days outstanding", not a finished FAIL.

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

## Q3. Economics release fade (card 87, with the official-components idea): frame ## Q3. ECONFADE (card 87): fade a rate-market shock after a CPI or payrolls print

Source card: row 87 of `refine_tools/CARDS_NOV11_ROWS_74_93.md` (Refinement). The row is redacted on the branch tip; Refinement sent me the rule text on Nov 12 and confirmed the card was registered only, never scored, with no 1 minute candles pulled. Refinement's economics worker (W-CAT-ECON1) holds hourly candles on 66 other economics series and nothing on these two, so no pull here duplicates it.

**The card's rule, as sent.** Markets: `KXFEDDECISION` and `KXFED` only (the Fed meeting and rate-level markets). Events: CPI and payrolls prints at 8:30 ET. Shock: a bracket's mid moves at least 15c in the first 10 minutes after the print. Entry: buy the side that the move went AGAINST, only if the move has retraced at least 4c by minute 20; price 10c to 60c; one entry per event. Exit: hold to settlement; a second arm exits after 6 hours. Kill bar on the card: PF 1.3 in both halves, n 40 per half.

**What the card leaves open, fixed here before any candle is read:**
- **Event list.** Every CPI and Employment Situation release with its actual release date and time, keyed by hand from the BLS release archive (not the planned calendar: a release moved by a shutdown or holiday enters at the time it really came out). One CSV committed first: `event_id, kind, release_utc, source line`. Range: as far back as Kalshi serves 1 minute candles for these two series (counted in step 0), at most from 2024-01.
- **Which markets at each event.** Those of the two series whose event is the NEXT scheduled Fed meeting (for `KXFED`, the rate level after that meeting) and whose YES mid at the reference candle is 0.10 to 0.90. Chosen from the reference candle only.
- **Reference.** The last 1 minute candle that ENDS at or before the release second (for 8:30:00 ET, the candle ending 8:30:00, which covers 8:29:00 to 8:29:59). Mid = (YES bid + YES ask) / 2 at its close. A candle that ends after the release is never the reference.
- **Shock.** Among candles ending 1 to 10 minutes after the release, the largest move of the mid from the reference in one direction is at least 0.15. Its extreme mid is `E`, its direction `d` (+1 if YES rose).
- **Retrace.** At the candle ending 20 minutes after the release the mid is at least 0.04 back from `E` toward the reference.
- **One per event.** If several markets qualify, take the one with the largest shock; ties go to the higher volume over the previous day. (The choice uses the shock itself, which is the trigger, and nothing after minute 20.)
- **Entry.** At the close of the minute 20 candle, buy 1 contract of the side the move went against (NO if YES rose) at that side's ask (NO ask = 1 minus YES bid), only if that ask is 0.10 to 0.60. No two-sided quote: skip and count.
- **Arm H:** hold to settlement. **Arm T:** sell at that side's bid at the close of the candle 6 hours after entry. Two tries.
- **Fees.** Taker fee on entry, and on the sale in arm T. Report every figure twice: unrounded, and with the fee rounded up to the cent as a real one-contract order pays (the MMSIM1 check showed the difference can be a tenth of a point of PF).

**Step 0, counts only (one small pull).** For each event, 1 minute candles from 30 minutes before to 25 minutes after the release for the single market of the next meeting nearest 50c at the previous day's close: one request an event, about 70 requests, one `kalshi-pull` job or a tester's budget. Count the events with a shock and with a confirmed retrace. **Stop as NOT_ENOUGH_DATA, before any outcome is read, if fewer than 40 events show a confirmed retrace.** With about 70 prints in three years and a 15c trigger on a rate market, I expect well under 40, so I expect this card to end here and move to a forward log. Say the count.

**Step 2, scored once, only if step 0 clears.** Pull the remaining markets and the 6 hour paths (the gaps only). Cuts: events by release time, first two thirds development, last third held out and read once. Bars: the card's (PF 1.3 in both development halves, n 40 per half) is the screen for a forward shadow; the research bar (PF 1.5 on development and held-out, deflated) applies to anything beyond that. FALSIFIED if development PF is under 1.0 at n 40 or more. Baselines beside each arm: the same entry with no retrace condition, and the follow side (with the move).

**Counted together.** The owner's rule counts this fade and "the official-components idea" in one deflation count. Refinement has no card by that name. The two candidates I can see are Desk B's UNRATEROUND (an official arithmetic prior from an already published number) and Refinement's row 77 (retail gasoline to the CPI gasoline component). Main should say which is meant; whichever it is, its tries are added to this card's two before either is scored.

**Limits a live version would hit (said now).**
- **Hold length.** The rulebook keeps economics positions to 14 days to settlement. A Fed meeting can be six weeks after a print, so arm H is inside the rule only when the meeting is within 14 days of the print. Score all events for research and report the within-14-days subset separately; arm T (6 hours) has no such problem but is a time exit, which the rulebook's "hold to settlement" line does not cover without the owner's say.
- **Overlap with Desk B's ECONLAG** (a 4 hour time exit on the slower macro market after the same prints). Different signal (a lag between markets, not a shock in one), same event days, similar candles. The two should share one candle pull and the Verification Analyst should look at their correlation before both go forward.
- **Sample.** About 24 prints a year. A forward log reaches 40 confirmed retraces in years, not months, unless the trigger is loosened, and loosening it after seeing the count is a new registration.

**What would make the result a lie.** (1) A reference candle that includes the release second. (2) Choosing the market by anything after minute 20. (3) Using the planned release time for a release that was moved. (4) Counting a market's two sides as two events. (5) Reading the held-out third to decide whether to keep the retrace condition.
