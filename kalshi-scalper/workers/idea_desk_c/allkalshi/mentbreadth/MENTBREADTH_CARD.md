# MENTBREADTH: words in wide Trump mention events (Idea Desk C, Nov 16, 2026; engine family spec; written before any price for it is pulled)

**Question.** When a Trump event lists many words, are its words overpriced on YES?

**Mechanism (stated before any read).** A wide listing adds long-shot topics that buyers like to back. The market maker prices each word alone and does not mark the YES side down for how crowded the listing is.

**Uniqueness.**
- The signal is the event's breadth (how many words are listed by the decision time), a field no card has used.
- Nearest: MENT1 (word base rates; the general YES overpricing in mention markets, PF about 1.09 for NO on average, which is the known baseline this must beat), CAL1 and FLB1 (calibration by category and lead). Flag: calibration, which it borders.
- Declined rows checked: favourite-and-hold (band 0.30 to 0.70, NO side), cheap-side-late (not a cheap side), calibration sweeps (this is one conditioned rule, not a sweep).
- Auditor B (Nov 16): no calibration card holds this development block.

**Rule (constants in `engine/mentbreadth.py`).**
- **Universe:** KXTRUMPMENTION and KXTRUMPMENTIONB, development (own occurrence 2026-04-17 to before 2026-08-06), from the landed MENTDRIFT_LISTS_A. This block was SHOWN by TRUMPTOPIC1: it is development only.
- **Decision:** D = each word's own open_time + 30 min. The word must still be open at D.
- **Breadth:** the event's words already open at D.
- **Wide:** breadth of 27 or more. 27 is the median over all 2,768 development words, from open times only.
- **Trade:** buy NO on a wide word when its NO ask (1 - YES bid, from the latest two-sided candle in [D - 180 s, D]) is 0.30 to 0.70.
- **Size and exit:** 10 contracts, held to settlement.
- **Read sample:** the first 460 of the 1,591 wide words by md5("MENTBREADTH-2026-11-16" + ticker), ascending, ticker as the tie break. One file.
- **Tries:** 1.

**Costs and the bar.**
- **Engine:** `engine1_core.py` (Desk A's, byte for byte).
- **Haircuts:** 1c (primary) and 2c.
- **Bar:** n 100+, PF 1.3+ at 1c with both halves 1.0+, PF 1.0+ at 2c.
- **Kill fast:** PF under 1.0 at 1c.
- **z and trade days:** by the UTC date of D (Auditor B, Nov 16: several events share a date and their words are correlated).
- **Control:** the same NO rule on the sample's NON-wide words would need its own candles, which are not pulled. The print says "control not run".

**Prediction.** Of 460 sampled words, perhaps 120 to 200 fall in the band. PF at 1c 0.9 to 1.25. A pass needs breadth to add a lot on top of the general NO tilt (MENT1); P(pass) about 10%.

**Windows.**
- The held-out is the Trump-word families' window, own occurrence 2026-10-03 to before 2026-11-05. Read once on the Head's go: jointly with the other Trump-word families, or by a split written before any read, as the Head decides.
- TRUMPTOPIC1's spent Aug 6 to Oct 3 and its forward window from Nov 5 are never pulled.

**Joint held-out (the Head of R&D, Nov 16, 15:46Z).** The window of own occurrence 2026-10-03 to before 2026-11-05 is read ONCE for every Trump-word family that passes development (LATEWORD, MENTTWIN, MENTBREADTH and any later one), in one print, with m counting every family. No family reads it alone.
