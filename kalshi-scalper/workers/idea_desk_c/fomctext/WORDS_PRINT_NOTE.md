# FOMCTEXT `words` print (Nov 14, 2026, run once on the Head of R&D's go)

- Reader: History Miner `fomctext.py` at 3ff49369, sha256 3b7fb809b0015fca8e62c8f46b249368b6b4bac0c48b50ed371397b7bb35f917 (Auditor B CLEAN).
- Command: `words <FOMCTEXT_HIST_A job> <run folder>`, run once, from a separate working folder with `python3 -I`.
- Job file: main `kalshi_pull_jobs/FOMCTEXT_HIST_A.json`, sha256 6b79651769c6e115c64585f74f1b6e752e180b5d3fff6f8df42c2d55a41df7e4.
- Run folder: `pull/FOMCTEXT_HIST_A/2026-11-14T0022Z_43533675204` on `kalshi-pull-data`. Auditor B checked its structure as CLEAN.
- Output: `WORDS_PRINT.json`, 407 development strikes on 11 KXFEDMENTION events, 2025-01-29 to 2026-04-29.
  - Per meeting: 15 / 30 / 30 / 33 / 31 / 41 / 40 / 41 / 44 / 54 / 48.
  - Fields: market and event ticker, decision date, and the text known in advance (title, subtitle, yes and no sub-title, custom strike, rules).
  - No price, volume or result field was printed or read. This desk never opened the run itself.
- Next: two blind matching passes against the eleven Board statements under Clarification 4's rule. Then the settled table, committed before any candle job.

## Stage 0: the `events` print (Nov 14, 2026)

- **Source:** the History Miner ran `events` once with `fomctext.py` aff0320a (Auditor B CLEAN) on FOMCTEXT_EVENTS `2026-11-14T0027Z_43534267368`.
- **The print:** `claude/history-miner` 4b053d6a, `real/FOMCTEXT_EVENTS_PRINT_2026-11-14.json`, sha256 984b7e47f095655b46433855b8eb2c3d5bfeaca433935a6bb8433308a9185194.
- **What was read:** this desk read only that print (event ticker, series, title, date). It holds 22 events dated 2025-01-29 to 2026-05-31; 9 were dropped unread as held out or undated.
- **Finding:**
  - All 11 development FOMC press conferences are in KXFEDMENTION, one per decision date, and FOMCTEXT_HIST_A already pulled those.
  - The other three series hold only speeches, a board meeting and a confirmation hearing on non-FOMC days: KXPOWELLMENTION 7, KXJPOWMENTION 3, KXWARSHMENTION 1. None falls on a development decision date.
  - So the card's universe is KXFEDMENTION only, and no per-event job is needed for the other three series.
