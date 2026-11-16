# MENTTWIN: the same Trump word in two events of the same day (Idea Desk C, Nov 16, 2026; engine family spec; written before any price for it is pulled)

**Question.** When Kalshi lists the same word in two Trump mention events with the same ticker date (for example a rally and a press conference on one day), do the two prices disagree by more than they should? If they do, is the cheaper one underpriced?

**Mechanism (a guess, said plainly).** Traders watch one event more than the other, so a word's price in the quieter event lags its twin. It is a guess with a weak prior: the two events can differ honestly, because a speaker can say a word at one event and not the other.

**Uniqueness.**
- The signal is the price gap between twins of the same word on the same day. No card has used it.
- Nearest: MENT1 and MENTPERSIST1 (a word's own history), TRUMPTOPIC1 (post counts), LATEWORD (listing time).
- Flag: parity, which it borders. It is not a lock: the twins are different events with different outcomes.
- Declined-list rows checked: lock and parity scans (not a lock), favourite-and-hold and cheap-side-late (band 0.30 to 0.70, YES only).

**Rule (constants in `engine/menttwin.py`).**
- **Universe:** KXTRUMPMENTION and KXTRUMPMENTIONB, development (own occurrence 2026-04-17 to before 2026-08-06), from the landed MENTDRIFT_LISTS_A.
- **A twin:**
  - The same word title (lowercased) and the same ticker date code, in two different events.
  - A word in three or more events uses the two whose markets opened first.
  - "Event does not qualify" is skipped.
- **Decision:** D = the later twin's open_time + 30 min. Both twins must still be open at D.
- **Quote:** the latest two-sided candle in [D - 180 s, D] for each twin.
- **Trade:** if the mids differ by 0.15 or more, buy YES on the cheaper twin when its ask is 0.30 to 0.70. One trade per pair.
- **Size and exit:** 10 contracts, held to settlement (exit H).
- **Tries:** 1.

**Costs and the bar.**
- **Engine:** `engine1_core.py` (Desk A's, copied byte for byte, sha256 53317e4b...).
- **Fee:** per order, rounded, at 10 contracts.
- **Haircuts:** 1c (primary) and 2c.
- **Bar:** n 100+, PF 1.3+ at 1c with both halves 1.0+, PF 1.0+ at 2c.
- **Kill fast:** PF under 1.0 at 1c on the first read.
- **Label:** "candle replay, upper bound, not fill-checked".

**Prediction.** 255 twin pairs on about 19 dates. After the gap and the band, expect 20 to 60 trades: "no evidence" is the likely outcome. If n reaches 100, PF at 1c is 0.8 to 1.2.

**Windows.**
- Development as above.
- Held-out: own occurrence 2026-10-03 to before 2026-11-05, read once on the Head's go.
- TRUMPTOPIC1's spent Aug 6 to Oct 3 and its forward window from Nov 5 are never pulled.

**Data.**
- `MENTTWIN_CANDLES_P1` and `_P2`: 510 historical single-market reads, windows ending at D.
- Disclosure: to size this I read time fields and word titles of the landed list only.

**Joint held-out (the Head of R&D, Nov 16, 15:46Z).** The window of own occurrence 2026-10-03 to before 2026-11-05 is read ONCE for every Trump-word family that passes development (LATEWORD, MENTTWIN, MENTBREADTH and any later one), in one print, with m counting every family. No family reads it alone.

## Closed Nov 16, 2026 (the Head of R&D's rate rule, not a failed bar)
Closed unread by the rate rule: about 200 to 500 days to 100 trades, over the 30 day limit. No result was read; any MENTTWIN_CANDLES_P1 data that lands stays unread. Its spec stays signed for the record, and the held-out joint read no longer counts it.
