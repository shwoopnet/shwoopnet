# FOMCTEXT statement-word table (Nov 14, 2026)

**Source.** The FOMC statements published by the Board of Governors of the Federal Reserve System (federalreserve.gov, press releases `monetaryYYYYMMDDa.htm`), for the eleven development decision dates only: 2025-01-29, 03-19, 05-07, 06-18, 07-30, 09-17, 10-29, 12-10; 2026-01-28, 03-18, 04-29. No statement dated 2026-06-17 or later was opened. No transcript, minutes, implementation note or market page was read for matching.

**File.** `STATEMENT_WORD_TABLE.csv`, 407 rows, one per development KXFEDMENTION strike from `WORDS_PRINT.json`. Its columns:
- `statement_word`: the feature the reader uses.
- `type`, `word_present`, `count`, `threshold`.
- Both passes: answer, count and type for each.
- `third_reading`, and `context` (at most 125 characters quoted from the statement).

**How it was made (card Clarifications 4 and 6).**
- Two blind passes, A and B. Neither saw the other's answers.
- Matching rule as in Clarification 4.
- Count strikes: the feature is "statement count meets the strike's threshold".
- NOT STATEMENT-TYPE strikes have the feature set to no, and are excluded from the scored set.

**Agreement.**
- 399 of 407 answers, 406 of 407 types, and all 11 counts.
- 9 third readings, by this desk, approved by the Head of R&D on Nov 14:
  - "Balance of Risk" is YES on 8 meetings. Each market's own rules text counts a plural form of the phrase, and the statements say "balance of risks".
  - Judy Shelton is NOT STATEMENT-TYPE.

**Settled.**
- 395 rows statement-type, 12 NOT STATEMENT-TYPE (11 "Good Afternoon", 1 Judy Shelton).
- The word is present in 34 rows.
- The feature is yes on 28 of the 395 statement-type strikes.
- The other 6 present words are count strikes whose statement count is under the threshold, so their feature is no under ruling (a):
  - KXFEDMENTION-25JAN-I40 (Inflation 40+ times, count 6);
  - KXFEDMENTION-25JAN-I50 (Inflation 50+ times, count 6);
  - KXFEDMENTION-25JAN-U8 (Unemployment 8+ times, count 1);
  - KXFEDMENTION-25SEP-UNCE (Uncertainty 5+ times, count 1);
  - KXFEDMENTION-25OCT-UNCE (Uncertainty 5+ times, count 1);
  - KXFEDMENTION-25DEC-UNCE (Uncertainty 3+ times, count 1).

**Process breach, recorded (the Head's ruling, Nov 14):**
- Pass B fetched the 11 allowed statement pages with curl, one GET each, once, and matched them in a local script. Clarification 4 point 3 forbids any script on the Board's site.
- It opened no other page. Its extracted bodies and script stayed in scratch and were never committed.
- The fault was in this desk's instruction, which did not forbid curl. The Head shares it.
- The pass is kept. From now on every worker uses the web reader only on the Board's site: no curl, script or loop.

**Reader note.** The History Miner's reader (`fomctext.py`, sha256 aff0320a) has no `type` column. Its `count` treats `statement_word` = no as the placebo set, so the 12 NOT STATEMENT-TYPE rows fall in the placebo printed beside the kill line, never in the kill line itself. A reader that drops them from the placebo too is an audited amendment, not a table edit.

## The candle job, built and frozen, NOT sent (Nov 14, 2026)

`jobs/FOMCTEXT_CANDLES.json`, sha256 397ee9250b952aab180265ba9f0712713fb8bec5c4a8340c8a3294484b94df98.

- **How it was built.** The History Miner's audited reader (`fomctext.py`, sha256 aff0320a, Auditor B CLEAN) ran `build-candles` on this table and the FOMCTEXT_HIST_A run.
  - The guard list was main's HELDOUT_PULL_RUNS.md, sha256 974f2713.
  - The reader ran the pull runner's own `check_job`.
- **What it asks.**
  - 407 requests (`max_requests` 407), all `/historical/markets/{ticker}/candlesticks`, one per development strike.
  - Window 13:55 to 14:45 ET of its decision date, 1 minute candles, one host, GET only.
  - The latest end is 2026-04-29 18:45 UTC, before the held-out cut.
  - The reader's universe check needs every strike of each event, so the 12 NOT STATEMENT-TYPE strikes are in the request list too.
  - About 7 minutes at 1 request a second, one run.
- **Status.** It is a NEW pull, and the owner's freeze forbids one without the owner's word. So it waits for Auditor B's check and the owner's yes. It is not sent to Main to dispatch.

**Rebuilt at the shared rate (Nov 14, 2026, the Head of R&D).** At `pacing_seconds` 1.0 the job would send 60 requests a minute. The shared R&D Kalshi budget is 12 a minute (`docs/RND_CHARTER.md` section 9, allocated by Main).

The job now has `pacing_seconds` 5.0, so it sends at most 12 a minute and runs about 34 minutes. That is the only change: the 407 requests and every other key are identical to the reader's build, and the pull runner's `check_job` passes.

- New sha256: 636c0b7eb2547c47785d8378c4e34b0cfa7f5e2e070124db1cb3dcb5f5e466aa.
- The 1.0 version, 397ee925 at da62610b, is superseded and never runs.
- Even after the owner's yes, Main dispatches it only in an hour Main has allocated to it.
