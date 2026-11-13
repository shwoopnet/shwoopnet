# Lane (a), mention markets: one candidate, one "what it would need" (Idea Desk C, Nov 13, 2026)

For the Head of R&D. No Kalshi request; contract terms read in full from Kalshi's public terms PDFs; nothing stored. [research]

**Counts:** sources read 14. Candidates 1 (FOMCTEXT, a slow family, so paper list at most). "What it would need" 1 (earnings releases). Dropped 1 (State of the Union excerpts: one or two events a year).

## The contract facts that matter (MENTION.pdf and EARNINGSMENTION.pdf, read in full)

- **Trading is open DURING the event.** "The Last Trading Time will be the Expiration time." The latest expiration is 14 days after the scheduled date, moved earlier under Rule 7.2 once the event occurs.
- **What counts:**
  - plural and possessive forms count; other grammatical changes do not;
  - text shown on screen does NOT count unless read aloud;
  - who counts is set per market.
- **How a mention is judged:** video first, then transcripts (per-market text as quoted by mirrors, unverified).
- **Cancelled or postponed events:** a cancelled event goes to the "does not occur" strike if one is listed, else to the last fair price. A postponement past 14 days is "does not occur", and so is an event with no live broadcast.
- **Shortened events:** words said in the part that happened count.

## Candidate: FOMCTEXT

**Mechanism.** The FOMC statement is published at 2:00 pm ET (federalreserve.gov). The Chair's press conference starts about 2:30 pm with a SCRIPTED opening statement that follows the statement's themes. So for the Chair's mention market, the statement text is a public fact, available 30 minutes before the speaking starts and while the market is open, about which words the opening will contain.

- **Who is on the other side, and why they lose:** traders who price the strikes from past press conferences or general expectations, and who do not read the 2:00 pm text before 2:30 pm. This is the "public fact not yet priced" kind of edge, the one kind Desk B's arithmetic says can reach 9 to 12 points.
- **Honest counter:**
  - makers in Fed markets are fast and read the statement within seconds;
  - the opening statement is not the statement (the Chair paraphrases);
  - only spoken words count;
  - the Chair changed in 2026 (the October 2026 transcript names Warsh), so earlier press conferences are a different speaker.
- **Exact data:**
  - **History:** Kalshi's own 1 minute candles of the Fed mention series between 2:00 and 2:30 pm ET on meeting days. The series are KXFEDMENTION and the Chair-named mention series; Refinement's census counted about 15 Fed mention events.
  - **The statement text:** federalreserve.gov (a US government work; its terms page is still to be read).
  - **Forward:** not on any recorder today. The politics recorder's 30 minute quotes are too coarse for a 30 minute window.
- **Closest closed or registered work, and why it differs:**
  - MENT1 (earnings words against the word's history, PF 0.92, not enough data) and Refinement's backlog row 60 (Fed speech words against past transcripts) are BASE-RATE rules. This uses a document released the same afternoon.
  - In-game lag (closed) is about related markets repricing within a minute. This is a text source, not a price.
  - It is not favourite-and-hold, provided the band excludes strikes already at 88c or more. A word in the statement may already be priced high, which is exactly what the measurement must show.
  - Rule-edge-case flag (POLITICS_RULES): not applicable, since nothing turns on a settlement clause.
- **Signals:** 8 meetings a year, each with roughly 20 to 40 word strikes (unverified count), clustered by meeting. That is a SLOW family (8 independent events a year), so the most it can reach is the slow-family paper list (30 events), and even that is about 4 years of meetings.
- **Cheapest honest first step (zero tries), for whichever desk takes it:**
  - For past meetings, list which strike words appear in the 2:00 pm statement.
  - Read the 2:00 to 2:30 pm candles of those strikes.
  - Count how many had an ask more than 10c under their eventual settlement at 2:05 pm.
  - If the asks already sit near 1 within five minutes of 2:00 pm, the card closes as "efficient, move on".
- **Prior:** low, about 3% to reach even the paper list.

## What it would need: earnings press releases before the call

- **Mechanism:** the release (and, for about a quarter of companies, posted prepared remarks) comes out 30 minutes to hours before the call. Words in it that the executives will read aloud are a public fact about the mention strikes.
- **Events:** many large-cap calls a quarter (MENT1 counted 6,346 word markets on 178 company series in a year), so not a slow family.
- **What it would need:**
  1. **A permitted source for the release text.** SEC EDGAR allows automated reads but requires a User-Agent with a contact e-mail. That conflicts with our rule of sending no personal contact details, so it needs the owner's decision (for example a company contact address). Newswire and investor-relations site terms are unread.
  2. **A count of how often the words in a release are read aloud.** River Markets' 856-market study (https://www.rivermarkets.com/research/forecasting-future-language.html) forecast from prior transcripts and news a week ahead and only matched the market (Brier 0.1392 against 0.1402). Nobody has tested the same-day release.
  3. **Regulatory risk:** the CFTC is reviewing mention markets, and Kalshi pulled its sports mention markets (DeFi Rate).
