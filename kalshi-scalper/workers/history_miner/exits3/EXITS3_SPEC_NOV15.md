# EXITS3: three fixed scalp exits beside hold (History Miner, 2026-11-15 ~14:50Z; the Head's order of 14:40Z, owner direction item 2; written before any read)

**Scope.** For every card on the recompute list (OIREL, FLIPS0-X, XRPFAV6, XRPFAV10, SEARCH1, HRSEAS1 night lull, BAND2) and every scoring shadow (the WH-NC15 places, the CFRTI-K places, OICORE's own record):
- The card's own entries are taken exactly as its scorer or extract gives them: same rule, same data, same windows, development only, no held-out window opened.
- Each entry is replayed under hold (the card's baseline) and three exits. **Each exit is one try per card** (3 tries a card, added to the deflation count). Nothing else is varied; there are no grids.

**The three exits, fixed now.** Let e be the RAW entry price of the side bought: its ask at the decision, before the haircut. Triggers use raw quotes, so every haircut line takes the same exit minute; the haircut changes only the prices.
- **T, take profit:** the first mark after entry where the side's bid is at least min(2 x e, 0.90). The position is sold at that mark.
- **S, stop:** the first mark after entry where the side's bid is at most e / 2. The position is sold at that mark.
- **M, time exit:** the position is sold at the mark ending 180 s before the close. An entry made at or after that mark has no M exit and is held (counted and printed).
- **If T or S never triggers** before the last mark (the candle ending 60 s before the close), the position is held to settlement. Hold pays 1 or 0.

**Marks and quotes.**
- Candle cards: a mark is a 1 minute candle close after the entry candle (end_period_ts later than the entry candle's). A missing candle is skipped, never carried forward.
- Book shadows (WH-NC15 on nc-data, CFRTI-K on its own source, OICORE's record): a mark is each recorded poll after the decision poll, with the card's own clock and offset rules. The side's bid is the best bid of that side (YES: yes_bid; NO: 1 - yes ask).
- **Sellable mark:** the side's bid is above 0 and below 1 (a NO sell needs yes_ask < 1). A trigger on a mark that is not sellable waits for the next sellable mark.

**Haircut (RND_QUEUE C1 to C11; exit at bid - h):**
- Entry = raw ask + h. A sale = that mark's side bid - h, never below 0.01. h = 0, 1c, 2c are all printed.
- Primary h:
  - 1c, except 2c when the entry or the exit mark is in the last 2 minutes (C8);
  - 2c at every mark on NC15 series (C11);
  - book shadows still use h on the best bid (a size walk is a separate fill check, not here).
- Fees: taker fee on every leg at the haircut price, rounded up to the cent per order at the card's own contract count, divided back per contract (C4).
- Fill assumed: "upper bound, not fill-checked" (C5, C9).
- A void refunds the price and keeps the fees, counted (C10). On an exited trade, a void after the exit changes nothing.

**Per card and variant, printed:**
- n, cash PF, halves by count floor(n/2) in entry order, mean cents a trade, day-clustered z;
- exits by reason (T, S, M, held), and the never-sellable waits;
- at h = 0, 1c and 2c, with the primary marked.
- Bar (paper, as ruled): PF 1.3+ at 1c with both halves 1.0+, AND PF 1.0+ at 2c. On NC15 series the primary is 2c (C11), so 1.3 and both halves are read at 2c there.

**Gate (the Head's, lighter for paper):** one build (this one) plus Auditor B's quick sanity check before the read. Results go by message only, no live figure in any file.

**Data needed, not yet located (I will not open anything held-out):**
- (1) per-card entry extracts from Forensics (rule, side, entry minute, raw ask, ticker, close), plus the candle or book path after each entry to the close;
- (2) the shadow files for WH-NC15 and CFRTI-K, and their decision polls;
- (3) OICORE's own record: whether this is the live order record (live figures by message only) or the candle history of its rule.
- For each I need the source and the held-out cut.
