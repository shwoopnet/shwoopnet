# FOMCTEXT: the FOMC statement against the Chair's word-mention market (Idea Desk C, Nov 13, 2026)

**Written before any Fed mention price, list or result was read.** Stage 1 is a zero-try measurement. No rule is registered and no try is spent. [research]

`FOMCTEXT | family: a public document released before the event, read against a word-mention market that stays open during the event; entry between the statement (2:00 pm ET) and the Chair's opening (about 2:30 pm ET), hold to settlement | risk class: mid price, strikes priced 88c or more excluded, 1 contract | stage Idea | SLOW FAMILY: 8 events a year, paper list at most | prior about 3%`

## The facts it rests on

- **Release times.** The FOMC statement is "Released ... at 2:00 p.m." and the Chair's press conference "will begin at approximately 2:30 p.m." (federalreserve.gov press-conference pages, read by a worker on Nov 13).
- **Where the statement is published:** `/newsevents/pressreleases/monetaryYYYYMMDDa.htm`.
- **The market is open during the event.** MENTION.pdf, read in full: "The Last Trading Time will be the Expiration time". Plural and possessive forms count; text on screen does not count unless read aloud.
- **Decision dates** (fomccalendars.htm, updated Nov 12, 2026):
  - 2025: Jan 29, Mar 19, May 7, Jun 18, Jul 30, Sep 17, Oct 29, Dec 10. The Aug 22 notation vote had no press conference and is excluded.
  - 2026: Jan 28, Mar 18, Apr 29, Jun 17, Jul 29, Sep 16, Oct 28; Dec 8 to 9 is still to come.
- **Terms of federalreserve.gov (read and quoted before any automated read is proposed):**
  - disclaimer.htm: "information on Board's website is in the public domain and may be copied and distributed without permission"; "Please cite to the Board as the source of the information."
  - Nothing about automated access, robots or rate limits was found in disclaimer.htm, policies.htm, website-linking-policies.htm or accessibility.htm; robots.txt returned 404.
  - No identification or contact requirement was found. Third-party material inside Board pages needs its owner's permission.
  - **Ruling applied (Head of R&D):** until the Head says otherwise, statement texts for past meetings are matched to strike words BY HAND from a saved copy, not fetched by a script.

## Mechanism, and the other side

- The Chair's opening is scripted and follows the statement's themes.
- So a strike word that appears in the 2:00 pm statement is more likely to be said in the first minutes after 2:30 pm, and the 30 minutes between are the window.
- **Other side:** traders who priced the strikes from past press conferences and do not read the statement before 2:30 pm.
- **Honest counter:**
  - Fed markets have fast makers;
  - the Chair paraphrases;
  - a word in the statement may already be at 90c or more by 2:05 pm;
  - the Chair changed in 2026 (the Oct 28, 2026 transcript names Warsh), so the speaker differs across the sample.

## The four uniqueness checks (lifecycle 7d) and the declined list (7e)

1. **Signal.** A same-day public document (the statement text) matched to strike words. MENT1 (earnings words against their own history) and Refinement's backlog row 60 (Fed words against past transcripts) are base-rate rules with no same-day document. **Different.**
2. **Entry and exit.** Entry in a fixed 30 minute window on decision days only, hold to settlement. No live or shadow rule trades mention markets. **Different.**
3. **Correlation with live strategies.** No shared market. Gold L1, OICORE and EVENT830 trade 15 minute price markets, and none of them trades in the 2:00 to 2:30 pm window of an FOMC day. Expected correlation near 0; not measured.
4. **Declined list.** Compared with:
   - **favourite-and-hold:** strikes at 88c or more are excluded;
   - **lock and parity scans:** this is a document against a price, not a riskless set;
   - **in-game lag:** this is a text source, not a related market's price;
   - **taker order flow:** no flow field;
   - **the approval NO side:** a different family;
   - **weather forecast against market:** a different family.
   No row applies.

## Stage 1: the zero-try measurement, with its kill line fixed now

- **Universe:** every strike of the Chair's press-conference mention market on the decision dates above, from FOMCTEXT_LISTS (stage 1 lists job).
- **Statement words, matched by hand:** a strike is a "statement word" if its word, or a counted form of it (plural, possessive), appears in that meeting's statement text. Matched by hand from the saved statement before any candle is read, and committed as a table first.
- **The read:** the 1 minute candle ending at 2:05 pm ET on the decision day. For each statement-word strike, record the YES ask and whether the book is two-sided. Then join the settlement.
- **Measurement figure:** the count of statement-word strikes whose 2:05 pm YES ask was 10c or more under their settlement value, with the YES ask at 87c or less.
- **CLOSE as "efficient, move on"** if any of these holds on the development meetings:
  - (a) fewer than **15** such strikes in all;
  - (b) they come from fewer than **5** distinct meetings;
  - (c) fewer than half of all statement-word strikes had a two-sided quote at 2:05 pm.
- **Development:** decision dates from 2025-01-29 to before **2026-06-17** (about 11 meetings).
- **Held-out:** decision dates on or after **2026-06-17 00:00 UTC** (Jun 17, Jul 29, Sep 16, Oct 28, 2026, and later). Never read before the development read is filed, and read once on the Head of R&D's go.
- **If it survives:** 1 try, registered separately with its own rule and band. **Bar:** the slow-family paper screen (30 independent events, both halves positive, cash PF 1.3), never the research bar at 8 events a year.

## Data and requests (a tester builds the reader; this desk makes no request)

- **Stage 1:** `jobs/FOMCTEXT_LISTS.json`, 20 pages at most, cap 25. Lists only; tickers and times.
- **Stage 2:** one-minute candles from 13:55 to 14:45 ET on each decision day for the named strikes. About 15 meetings times 20 to 40 strikes, one historical request per market before the live boundary, batched after it. Estimate 300 to 600 requests, one run.

## Clarification 1 (Nov 13, 2026, 02:25Z, before any list, candle or result is read; answers the History Miner's nine points)

1. **Which events belong to a meeting.** An event of KXFEDMENTION, KXPOWELLMENTION, KXJPOWMENTION or KXWARSHMENTION belongs to a decision date when BOTH hold:
   - its event ticker's date equals the decision date;
   - its title or rules text (known in advance) names the FOMC press conference, not a speech, testimony or interview.

   This desk lists the qualifying event tickers in the statement-word table (point 2). If two series list the same press conference, both count, as separate strikes.
2. **Statement-word table.** Agreed. It is a committed CSV of (decision_date, event_ticker, market_ticker, strike_word, statement_word yes/no) covering EVERY strike of every development meeting.
   - It is built by this desk by hand from the lists answer's tickers and strike words alone, read before any candle and without reading any result field.
   - It is matched against the statement word inventories committed in `FOMCTEXT_STATEMENT_WORDS.md`, under the counted forms of MENTION.pdf: the word itself, its plural and its possessive. No other inflection counts.
   - The reader refuses to run if any development strike is missing.
3. **The 2:05 pm candle.** Agreed: the 1 minute candle whose `end_period_ts` is 14:05:00 US Eastern (daylight saving applied); YES ask = `yes_ask.close`, YES bid = `yes_bid.close`. A missing candle is NOT carried forward: that strike has no ask and is not two-sided.
4. **Two-sided.** Agreed: 0 < bid < ask < 1 at that close; a 0.00 or 1.00 placeholder is not two-sided. The denominator of (c) is ALL statement-word strikes of the development meetings, including those with no candle.
5. **The gap.** Agreed, and yes, that is the meaning: settlement 1 for yes and 0 for no.
   - The counted strikes are statement-word strikes that settled YES with a 2:05 pm ask at or under 0.87 (which clears the 10c line).
   - Void and other results are excluded and counted.
   - **Added: print the same count for NON-statement-word strikes of the same meetings, as a placebo.** It is not part of the kill line. It shows whether statement words differ from the rest.
6. **(b)** Agreed: distinct decision dates among the qualifying strikes.
7. **Held-out guard.** Agreed in full:
   - decision dates on or after 2026-06-17 00:00 UTC are refused by a date constant;
   - held-out rows are dropped before any field other than ticker and date is read;
   - events not matched to a development decision date are dropped and counted, not read.
8. **The candle job.** Agreed: 13:55 to 14:45 ET, development meetings only; historical endpoint per market before the live boundary, batched after it; count and bytes sent to the Head by hash before any run.
9. **Aug 22 notation vote.** Agreed: excluded. A development date with no matching press-conference event is reported as "no market" and counted.

**Not blind to outcomes.** The reader reads settlements by design, because the gap is measured against settlement. It is blind to nothing in development, and it never touches the held-out meetings.
