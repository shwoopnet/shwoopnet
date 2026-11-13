# CANDLEGAP-2: the same measurement on table tennis and e-basketball (History Miner, Nov 13, 2026, zero-try measurement, Head of R&D approved)

Written and committed BEFORE the candles are pulled. Same question, unit, five counts, match test and splits as `CANDLEGAP_DESIGN.md`, by the SAME frozen `candlegap.py` (sha256 a7178688..., not edited), run per series by `candlegap2_run.py`, which checks that hash and sets the module's `SERIES` constant before calling `measure()`. The two readings named in `CANDLEGAP_NOTE_NOV13.md` apply unchanged; the Testing Desk's reading can be run beside it. [research]

**Families (the Head asked for the families INPLAYJUMP reads):**
- KXLIGAPROMATCH (Liga Pro table tennis): 46 markets in `wheelbook/2026-11-12/2031/`. IN.
- KXEBASKETBALLGAME: 28 markets. IN.
- KXESOCCERGAME: OUT. REMATCH (open) holds out KXESOCCERGAME closes from 2026-10-23 to before 2026-11-13; every recorded e-soccer market closed on Nov 12, so a candle pull over them is barred by rule (h). (ESOCTIE's held-out covers the same days and is closed.)
- Tennis (ITF, Challenger): OUT. The recorder's first folder holds none (phase 2 is off in the recorder).

**Held-out check.** INPLAYJUMP's held-out ends before 2026-11-03 (table tennis) and before 2026-11-11 (e-basketball); PREMOVE (table tennis) was withdrawn unread on Nov 12 at 19:27Z. These markets close on Nov 12 to 13. No other registration on these two series was found on the research branches.

**The pull.** Job `CANDLEGAP2_TTEBB` (`kalshi-scalper/workers/kalshi_pull_jobs/CANDLEGAP2_TTEBB.json`): 3 requests (Liga Pro in two halves of 23, e-basketball 28), each 2026-11-12T20:31:00Z to 2026-11-13T00:04:00Z, 1 minute; 4,899 / 4,899 / 5,964 minute-tickers. Byte estimate about 1.1 MB (CS2's answer was 548,794 bytes for 7,668 minute-tickers).

**Worth a pull?** Yes, by the book side counted with no candles: Liga Pro 998 market-minutes before close (5,694 in all), e-basketball 652 (3,508), against CS2's 2,312. Small: one evening, about 1,650 headline minutes together.

**Window caveat, fixed now.** The script's window starts at S (the CS2 rule); these families go fast 2 minutes before S, so those 2 minutes are not counted. The unit is otherwise identical.
