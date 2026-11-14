**Status note (Nov 13, 2026): paused at 19:20Z and UNPAUSED at about 19:21Z by the Head of R&D, on the owner's correction ("wait we still need new research"). It carries on as amended (a16c8e3c). The Verification Analyst's re-score and Auditor B's check are still due before H is computed.**
# LIQREV: OKX liquidation cascades against the Bitcoin 15 minute market, the reversal side (Idea Desk C, Nov 13, 2026)

**Written before any OKX liquidation row, Kalshi quote, candle or result was read.** Forward only. A card for the Head of R&D's read, not registered; the Verification Analyst scores it. [research]

`LIQREV | family: forced liquidations on another venue (price-insensitive flow), bet on the partial reversal of the move they cause; entry 12 to 3 minutes before the close, hold to settlement | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 2%`

## Mechanism, and the other side

- **Forced flow.** When leveraged Bitcoin positions on OKX are liquidated, the exchange sells (longs) or buys (shorts) at any price. A burst of them pushes spot, and the Bitcoin index Kalshi settles on, past where unforced traders would put it. Part of that move tends to come back once the forced flow stops.
- **Where the edge would come from.** A Kalshi 15 minute Bitcoin market is priced from the current spot. During a cascade it prices the move as if it will hold. The other side is the market maker and the takers who price from the post-cascade spot. The liquidated traders are the source of the overshoot, not our counterparty.
- **Honest counter:**
  - Kalshi's makers watch spot and may already discount cascades.
  - The reversal may take longer than the minutes left in the window.
  - No size of the reversal is known to this desk; no published figure was checked.
  - Cascades cluster in volatile hours, where the 15 minute market is least predictable.

## Data (all recorded already; nothing new)

- **OKX liquidations:** the OKX recorder (`record-oklq.yml`, BTC-USDT-SWAP and BTC-USD-SWAP, filled liquidations with time, side and size), forward from 2026-11-10 to 2026-12-31, on `quote-data` under `oklq/`. OKX keeps only about 17 hours, so this can never be backfilled.
- **Kalshi quotes:** R6's 2 second book for KXBTC15M (`book15r6/`, to 2026-12-31 on main; END_UTC 2026-12-31T23:59Z).
- **Settlement results:** the public settled results.

## The rule (proposed, frozen at registration, never before)

- **Cascade size.** L(t) is the sum of liquidated contracts on one side (long or short), in BTC, over the 3 minutes ending at minute t, across both swaps.
- **Threshold H, a one-time calibration on liquidation sizes only.** The 99th percentile of L over every minute from 2026-11-10T00:00Z to before 2026-11-17T00:00Z. This is computed after registration, from the OKX rows alone. No Kalshi price or result is opened for it, and H is then frozen and committed before any Kalshi row is read.
- **Trigger.** In a KXBTC15M window, the first minute t between 12 and 3 minutes before the close where L(t) for one side is at least H. At most one bet a window.
- **Bet.**
  - **Long liquidations** (forced selling pushed price down): buy YES.
  - **Short liquidations** (forced buying pushed price up): buy NO.
  - In both cases: at the R6 book's ask at the first poll after t, ask 20c to 80c, spread 4c or less, 1 contract, hold to settlement.
  - Fill at the ask seen plus the rounded fee (an upper bound). A void is a fee-only loss, counted as a bet.
- **Conflict rule (lifecycle 7f).** No bet in a window where OICORE placed an order on the opposite side ("the first strategy in holds the market"). Such windows are counted, not bet.

## Numeric prediction, kill lines, windows

- **Prediction:** about 1% of minutes trigger by construction; within the 12 to 3 minute span, about 1 to 3 triggers a day. A partial reversal shows in a minority of triggers. Development cash PF 0.8 to 1.2.
- **Kills:**
  - **Zero-try count, at the end of development, before any price:** closed if fewer than 60 triggered windows have a two-sided R6 quote.
  - **Development:** closed if fewer than 60 bets, a cash PF under 1.0, or a half under 1.2.
  - With fewer than 30 bets: "no evidence at n = x".
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46 (clustered by US Central day), one try.
- **Windows (by window close time, date constants):**
  - calibration of H = liquidation sizes 2026-11-10 to before 2026-11-17, no outcomes;
  - development = closes 2026-11-17T00:00:00Z to before 2026-11-30T00:00:00Z, halves split at 2026-11-23T12:00:00Z;
  - **held-out = closes 2026-11-30T00:00:00Z to before 2027-01-01T00:00:00Z**, the end of R6's and the OKX recorder's recording, read once on or after 2027-01-02 on the Head's go.
  - These are forward days, so no earlier test can have read them. Rule (h) is still for the Head to check against CFRTI-K, CFRTI1-BTC and W-SPOTLEAD1, which use the same series in November.
- **Held-out line for HELDOUT_REGISTRY.md:** `| LIQREV | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/LIQREV_CARD.md | KXBTC15M (R6 book15r6) with OKX liquidations (oklq) | Calibration H from liquidation sizes 2026-11-10 to before 2026-11-17 (no outcomes); development = closes 2026-11-17 to before 2026-11-30; held-out = closes 2026-11-30 to before 2027-01-01, read once on or after 2027-01-02 on the Head's go | 2026-11-17; 2026-11-30; 2027-01-01 | NOT READ | card text | card only, not registered; PAPER AND SHADOW ONLY; rule 17 per card in Amendment 2 |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a different source and field.**
   - Forced-liquidation flow on another venue. This is NOT a first read of the field: LIQ1-INFO (information only), SNAPBACK1 (FALSIFIED) and SPIKE1 (FALSIFIED) read liquidations before (see Amendment 2). Lifecycle 7f lists "OKX liquidation cascades" as an idea.
   - Closest: W-SPOTLEAD1 (Kalshi lags spot, betting WITH the move) and OICORE (Kalshi open interest, cheap side). LIQREV bets AGAINST the move, from a different field, in the mid band.
   - Self-score: unique, medium confidence.
2. **Entry and exit:** 12 to 3 minutes before the close, hold to settlement. That is the 15 minute crypto grid, shared with OICORE and gold L1's timing; it stays out of OICORE's opposite side by the conflict rule.
3. **Correlation:** it trades OICORE's market (Bitcoin 15 minute), so correlation with OICORE must be measured in shadow (r under 0.3 over 20 days, lifecycle 7d check 3). Flagged, not assumed.
4. **Declined list:**
   - **Taker order flow on the 15 minute tape:** that row covers Kalshi's own tape. OKX liquidations are another venue's forced fills, a new data source.
   - **Cheap-side grammar on the 15 minute series without a new data source:** this is a new source, and it trades the mid band.
   - **Favourite-late:** excluded by the 20c to 80c band.
   - **Not** a lock, market making, spot lead (opposite direction) or a 15 minute model sweep.
   - The Verification Analyst decides whether "15 minute crypto plus a new outside feed" escapes the closed 15 minute crypto rows.

## Amendment 1 (Nov 13, 2026, before any data): LIQREV is the OKX recorder's own question (OKXLIQ1)

- **Naming.** The OKX recorder was built to ask "does a liquidation cascade move Bitcoin's 15 minute market", and nobody registered that question. The Head of R&D asked for it as a card named OKXLIQ1. This card is that registration. OKXLIQ1 and LIQREV are one card, one try; the name used in the registry is LIQREV (OKXLIQ1).
- **Why it is not the closed spot-lead family:**
  - Spot-lead (W-SPOTLEAD1 and its relatives) uses the index or exchange spot PRICE and bets that Kalshi follows it.
  - This card uses a different field: forced-liquidation FILLS on a derivatives venue, which no closed test read. It bets that part of the spot move REVERSES, the opposite direction.
  - A move with no liquidations never triggers it.
- **Why it is not the closed 15 minute crypto families:**
  - The closed rows are Kalshi's own tape flow (FLOW1, TAPEFLOW1, RESIL1), and cheap-side price, time and regime grammars on the same series "without a new data source" (GEN12, GEN13, LEADLAG1 and the rest).
  - OKX liquidations are a new outside data source. The rule is one pre-stated trigger, not a sweep, and it buys the mid band, not the cheap side.
  - What it shares with them is only the market: KXBTC15M at 12 to 3 minutes before the close.
- **Read timing (the Head's ruling):**
  - forward only;
  - the development read is on or after 2026-11-30;
  - **the held-out read is on or after 2027-01-01**, after the OKX recorder stops on 2026-12-31, on the Head's written go.
  - (Superseded by Amendment 2: R6 runs to 2026-12-31 on main, so the held-out window is closes 2026-11-30 to before 2027-01-01.)
- **H is not computed** until the Verification Analyst has scored this card and Auditor B has checked the text (the Head, Nov 13, 18:56Z). Then H is computed from liquidation sizes only, as written above.

## Amendment 2 (Nov 13, 2026, before any data): the Verification Analyst's score and the Head of R&D's rulings

- **(a) Family status and the third test.**
  - The liquidation-fade mechanism has been read three times:
    - LIQ1-INFO, information only, not a test;
    - SNAPBACK1, FALSIFIED;
    - SPIKE1, FALSIFIED.
  - That is 2 falsified of the 3 the owner's rule needs, so the family is NOT on the declined list.
  - **LIQREV is the family's third test. If LIQREV is FALSIFIED, the liquidation-fade family closes for good.** "No evidence at n = x" does not close it.
  - Uniqueness check 1 above is corrected to name LIQ1-INFO, SNAPBACK1 and SPIKE1. What is new here is the source (OKX's own forced fills, recorded forward) and the pre-stated trigger. The mechanism, fading a liquidation move, is the same family.
- **(b) Interference.**
  - LIQREV enters 12 to 3 minutes before the close, so on KXBTC15M it can take a window before OICORE (3 to 2 minutes before the close). It could also take one before CFRTI-K, which is live at trial size on the owner's exception and buys the cheap side of the same market about 3 minutes before the close.
  - Through the direction lock it could then block either of them.
  - **LIQREV is PAPER AND SHADOW ONLY.** It gets no live seat unless a new interference rule is written and approved later.
  - The conflict rule above (no bet where OICORE took the opposite side) stays for the paper record, and is extended to CFRTI-K.
- **(c) Windows: rule 17, card by card.** LIQREV reads no Kalshi row before its development read on or after 2026-11-30. Auditor B checks each status and hash below before that read.

| Card on KXBTC15M | Its unread window | Frozen with scorer and registration hashes? | LIQREV's treatment |
|---|---|---|---|
| CFRTI1-BTC (and its Kraken line) | from 2026-11-09, one read from 2026-11-20 | Yes: Auditor B verified the CFRTI hashes on Nov 13 (cfrti1.py cd54a75c at 79724f00, unchanged since d5964adb) | Reads the shared windows under the frozen-read clause |
| CFRTI-B | from 2026-11-09, same sitting | Yes, same verification | Frozen-read clause |
| CFRTI-K (and CFRTI-K-TX) | from 2026-11-14, its frozen read once on Nov 14 | To be checked by Auditor B: whether its scorer and registration hashes are recorded as frozen | If frozen: frozen-read clause. If not: CFRTI-K's windows from 2026-11-17 that LIQREV reads are labelled "not blind" for CFRTI-K. LIQREV's dates cannot move earlier, because the data is forward only |
| BOOKCH1 | windows closing after 2026-11-04, read by 2026-11-14 at the latest | V2 file at 79724f00 (bookch1_fwd.py and the registration); Auditor B to record the sha256s | No date overlap: BOOKCH1's forward period ends by 2026-11-14 and LIQREV's first Kalshi row closes on 2026-11-17. If BOOKCH1's read slips past Nov 17, its overlapped dates are labelled "not blind" unless it is frozen |
| W-SPOTLEAD1, its unseen block | not found in HELDOUT_REGISTRY under that name; Auditor B to name the dates | To be checked by Auditor B | If frozen: frozen-read clause. If not: the overlapped dates are labelled "not blind" for W-SPOTLEAD1 |

- **(d) The held-out end.** R6 runs to 2026-12-31 on main (the Verification Analyst; `END_UTC = "2026-12-31T23:59:00Z"` in `scripts/record_15m_book.py`), and so does the OKX recorder. The held-out is closes 2026-11-30T00:00:00Z to before 2027-01-01T00:00:00Z, a date constant. It is read once on or after 2027-01-02 on the Head's go. Every earlier mention of Dec 15 and Dec 16 in this card is corrected in place; Amendment 1's sentence on the end is marked superseded.

## Amendment 3 (Nov 13, 2026, before any data): readings R1 to R15, ruled by the Head of R&D

Scorer build 1 (`liqrev/liqrev_score.py`, 32a1d7fa) had to fix fifteen points this card left open. The Head of R&D ruled on Nov 13 (about 21:08Z):
- R1, R2, R5, R7 and R15 are accepted as written;
- R9 is option (c);
- the others stand as written.
Where this amendment and the text above differ, this amendment is right. The Testing Desk writes build 2 from this card alone.

**R9 in plain words:** the conflict rule (no bet in a window where OICORE or CFRTI-K took the opposite side) is DROPPED for the PAPER read. No money is at risk, and the bot's live order log may not enter this public repo. It stays a HARD CONDITION for any future live seat: LIQREV gets no live seat without it, and without the new interference rule of Amendment 2 (b).

**Readings that change the bet beyond the card's text, flagged:**
- **R5b:** both sides at H in the same minute means no bet in that window.
- **R6:** no R6 poll within 10 s after the trigger minute means no bet.
- **R15:** a window without OKX coverage is skipped.
All three only REMOVE bets; none adds or changes one.

- **R1, side:** in OKX's liquidation feed, `side` is the side of the liquidation ORDER. `sell` means a long position was liquidated (forced selling, so bet YES); `buy` means a short was liquidated (forced buying, so bet NO). `pos_side` is not used, because net-mode rows carry `net`.
- **R2, size in BTC:** BTC-USDT-SWAP is `sz` x 0.01 BTC. BTC-USD-SWAP is `sz` x 100 USD / `bk_px`. Contract values are from OKX's instrument spec, to be confirmed by the probe or the recorder's notes. Any other instrument is refused.
- **R3, L(t):** the BTC of one side with `ts_ms` in [t - 180 s, t), where t is a whole-minute boundary.
- **R4, trigger minutes:** the whole-minute boundaries t with close minus t from 720 s to 180 s inclusive, so 10 checks a window, in time order.
- **R5, H:**
  - the 99th percentile, nearest rank (ceil(0.99 x n)), over BOTH sides' L(t) pooled, two values a minute, for every whole minute from 2026-11-10T00:00Z to before 2026-11-17T00:00Z;
  - minutes outside the OKX recorder's coverage are left out;
  - H is a frozen input to the scorer and is not computed until Auditor B is CLEAN.
- **R5b, both sides at once:** if both sides reach H at the same minute, there is no bet in that window (counted as "both_sides").
- **R6, the quote:** the first R6 poll with `t_recv_ms` in (t, t + 10 s]; none means "no_quote". YES ask = 1 - `no_bid_px_1`; NO ask = 1 - `yes_bid_px_1`; spread = YES ask - `yes_bid_px_1` for both sides. It is usable only if 0 < yes bid < YES ask < 1.
- **R7, band and spread:** ask 0.20 to 0.80 and spread 0.04 or less, inclusive, with a 1e-9 tolerance, on the ask seen. If the first trigger minute fails them, the window is USED: no later minute is tried.
- **R8, fill and fee:** at the ask seen with no +1c, plus the fee 0.07 x p x (1 - p) rounded up to the cent. A void is a fee-only loss counted as a bet. Results other than yes, no or void are refused, and so is a duplicate window.
- **R9, the conflict rule:** RULED option (c): dropped for the paper read; a hard condition for any live seat (above).
- **R10, results:** from public settled results, joined by ticker.
- **R11, statistics:**
  - PF = gross gain / gross loss;
  - z is clustered by the US Central date of the close, using the sample standard deviation over days with at least one bet;
  - all bar tests are on unrounded values.
- **R12, duplicates:** OKX rows are de-duplicated on the recorder's own key (inst_id, ts_ms, side, pos_side, bk_px, sz).
- **R13, read guards:**
  - development read refused before 2026-11-30T00:00Z;
  - held-out read refused before 2027-01-02T00:00Z, and it runs once (a marker file);
  - development mode ignores and counts held-out windows.
- **R14, kills:**
  - zero-try count: fewer than 60 triggered windows with a two-sided quote closes it, where triggered = bets plus band or spread failures;
  - development: fewer than 60 bets, PF under 1.0, or a half under 1.2;
  - with fewer than 30 bets: "no evidence at n = x";
  - held-out: PASS only if development CONTINUEs, PF is 1.5 or better in development half 1, half 2 and the held-out, and the held-out z is 5.46 or more; otherwise FALSIFIED, which closes the liquidation-fade family.
- **R15, coverage:** a window is scored only if one OKX recorder coverage interval contains [close - 720 s - 180 s, close - 180 s). Otherwise it is "no_liq_coverage", because a missing feed would read as no liquidations. Coverage intervals come from the recorder's coverage.csv. How they are built belongs to the row builder (a separate file, written later and audited).

## Amendment 4 (Nov 14, 2026, 02:35Z, before H is computed and before any OKX or R6 row is read; Auditor B's NOT YET CLEAN on d2822839)

1. **R2, size unit (replaced).** H and L(t) are counted in raw contracts (`sz`) of **BTC-USDT-SWAP only**. BTC-USD-SWAP rows are still recorded, but are not used.
   - Why: the recorder stores no contract value (`ROW_COLS` in `scripts/record_oklq.py` has `sz` and `bk_px` but no ctVal), and this desk has no confirmed source for one.
   - Counting one instrument in its own raw contracts needs no conversion, so no unconfirmed unit can move H or a trigger.
   - Mixing the inverse swap would need a USD-to-BTC conversion that is not confirmed. Dropping it can only remove triggers, never add a mis-sized one.
   - R3 is unchanged otherwise: L(t) is the summed `sz` of one side of BTC-USDT-SWAP with `ts_ms` in [t - 180 s, t). H is the 99th percentile of that per-minute L over the calibration minutes, as R4 and R5 say.
2. **The bar's z.** z is computed on the **held-out window alone**: day-clustered by US Central date, at least 5.46, as R14 says. The development halves are checked by PF only (each half 1.0 or better at the 1c haircut and at 2c, per C7). Build 1 and build 2 must both read it this way.
3. **R6 clock.** The poll time is `t_recv_ms` **plus the run's offset**: the median, over the run's polls, of (the Date header + 0.5 s) - `t_recv_ms`, as in DEPTH1 and OIVER. The first poll with corrected time in (t, t + 10 s] is the quote.
4. **Information at t.** L(t) uses OKX rows by **`ts_ms` alone**, the exchange's own event time. This is accepted knowingly:
   - The OKX recorder runs a few times a day and fetches the last hours of the feed, so a row's `t_recv_ms` is hours after its `ts_ms`. A receive-time rule would remove every trigger.
   - So this card measures whether the information existing at exchange time t predicts the Kalshi move. It does not test whether a live bot could have seen it.
   - A live version would need a real-time liquidation feed and its own registration. Paper and shadow only, as before.
5. **Rule 17 table (Amendment 2 c).** Auditor B's checks (CFRTI-K frozen hashes, BOOKCH1 sha256s, W-SPOTLEAD1's unseen block) are due before the 2026-11-30 development read, not before H.
