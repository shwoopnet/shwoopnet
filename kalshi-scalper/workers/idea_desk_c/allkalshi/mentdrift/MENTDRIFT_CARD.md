# MENTDRIFT: late drift on Trump mention markets, a VERSION card for a paper record (Idea Desk C, Nov 15, 2026, written before any data for this card is pulled)

**Status:** VERSION, not NEW. It counts toward the owner's 5 at PF 1.3+ and never toward the unique list. Paper only, under the lighter gate: one build plus Auditor B's quick check. Nothing here is live, places an order or changes the bot.

## Parent and prior, said plainly

- **Parent:** PREMOVE (Desk B: follow the last hour's pre-match move, esports and e-soccer, registered) and the momentum-follow family (M1, INPLAYJUMP's follow arm).
- **Neighbours on this market:** MENT1, MENTPERSIST1 (base rates), TRUMPTOPIC1 (post counts, cheap YES) and CAL1 or FLB1 (calibration by lead; Mentions -0.36c at 72 h as information).
- **No late-drift test exists on mention markets** (the VA's matrix, Nov 15).
- **The prior is that a follow rule fails here as it did elsewhere.** The only new thing is the market. A speech-word market reprices before the event on schedule and topic news, which none of the parents traded.
- **Not a ban shape.** The side is picked by a move, never by a price band. The band (0.30 to 0.70) keeps out the cheap side and the favourite side. It is not the 7e cheap-side row, not market making and not a short round trip.

## Data and windows (constants in the scorer)

- **Series:** KXTRUMPMENTION and KXTRUMPMENTIONB.
  - Only events with an `occurrence_datetime` (present from 2026-04-17, per TRUMPTOPIC1's registration).
  - The word "Event does not qualify" is skipped.
- **Development:** events with occurrence from 2026-04-17T00:00Z to before 2026-08-06T00:00Z.
  - This is TRUMPTOPIC1's fit third. Its outcomes were seen by that card, which is allowed for development.
  - Every market here is before the historical cutoff, so its candles come from the per-market historical endpoint.
- **Cut, never pulled:** occurrence from 2026-08-06 to before 2026-10-03.
  - This is TRUMPTOPIC1's held-out third (read, spent). Kept cut under rule 17.
- **Held-out (this card):** occurrence from 2026-10-03T00:00Z to before 2026-11-05T00:00Z.
  - TRUMPTOPIC1 marks this block "never used", so it is free.
  - Read once, on the Head's go, after development passes. Its lists and candles are their own job then.
- **Cut, never pulled:** occurrence from 2026-11-05T00:00Z on. That is TRUMPTOPIC1's forward read, open to 150 trades or 2027-06-30.
- **Disclosure:** MENTPERSIST1's held 500 markets are earnings-call word series. Before scoring, the scorer prints their overlap with this card's tickers; it is expected to be 0.
- **Exposure, LOADED not LOOKED AT (Auditor B, Nov 15).** The historical list stops at the Sep 13 cutoff, so this card's held-out and TRUMPTOPIC1's forward window are not in it. It does return the Aug 6 to Sep 12 part of TRUMPTOPIC1's spent held-out, with results, in the raw file. That file stays in scratch and nobody opens it except through `ol_score.py`. The scorer tests each market's OWN occurrence_datetime before parsing any other field; a missing or unparsable occurrence is dropped and counted. The result is read only for kept rows.
- **Truncation.** If page 10 (KXTRUMPMENTION) or page 5 (KXTRUMPMENTIONB) still has a cursor, the list is not whole and the scorer stops before any result read.
- **Stage A:** the job `MENTDRIFT_LISTS_A` asks for the historical market lists of the two series, which have no date filter, plus two series reads.
  - Before reading any other field, the scorer drops every market whose event occurrence is outside development.
  - It keeps ticker, event_ticker, close_time, occurrence_datetime, can_close_early and result, in that order of use. The result is read last, only for the development rows.

## The clock and the rule (1 contract a side)

- **O** is the event's occurrence time: the earliest occurrence_datetime of its markets.
- **D** is the decision time, O - 60 min, on the 1 minute candle ending at D.
- **Mid:** (yes_bid close + yes_ask close) / 2, only when the candle is two-sided under rule 18: 0 < yes_bid < yes_ask < 1, with 1e-9. A missing candle is never carried forward.
- **Move:** m = mid(D) - mid(D - 300 min). Both ends must be two-sided.
- **Trade:** if |m| >= 0.08, buy the side that ROSE. That is YES (ask = yes_ask) if m > 0, else NO (ask = 1 - yes_bid). The side's raw ask at D must be 0.30 to 0.70 inclusive.
- **Cap:** at most 3 trades an event, the largest |m| first, ties broken by ticker. Words inside one call move together.
- **Removed and counted:** a market whose close_time is at or before D.

## Exits: EXITS3 (History Miner, Nov 15), one adaptation stated

- **Hold:** settle at 1 or 0. This is the baseline.
- **T:** take profit, first mark with side bid >= min(2e, 0.90).
- **S:** stop, first mark with side bid <= e / 2.
- Marks are 1 minute candles after D. T and S may trigger to the candle ending 60 s before close_time.
- **M (adapted):** sell at the mark ending at O - 5 min, before the speech starts. EXITS3's 180 s before the close would be mid-speech, where the word itself settles the market.
- **Tries:** hold, T, S and M are **4 tries**, all added to the deflation ledger.

**Stated before any read (Auditor B, Nov 15):**
- **M exit (part of this card's rule; EXITS3 as written has no slip).** It sells at the mark ending exactly at the M time. If that candle is missing or not sellable, it sells at the first sellable mark up to 4 minutes later, printed as `M_late` with its count. M and M_late are printed separately for each try. With no such mark the trade is held. 4 minutes keeps the NBA M exit pre-game (G is 30 minutes before the tip proxy) and the MENT M exit before the speech (O - 5 min + 4 min).
- **e is the raw ask at D,** before any haircut. T's level min(2e, 0.90) and S's level e/2 use raw e, so every haircut line exits at the same mark (EXITS3).
- **Bars** are judged on unrounded figures with no tolerance: exactly 1.3 or 1.0 passes.

## Costs, printing and the bar

- **Haircut d3b5f24e (C1 to C10).** Entry = raw ask + h; a sale = bid - h, never below 0.01; h = 0, 1c and 2c all printed. The primary is 1c, but 2c when the entry or exit mark is within the last 2 minutes before close_time (C8).
- **Fee:** per order, rounded up: ceil(7% x p x (1-p) x 100) / 100. Taker on every leg.
- **Void:** a void refunds the price and keeps the fees.
- **Label:** "upper bound, not fill-checked".
- **Printed for each try:**
  - n, events, cash PF, halves at floor(n/2) in entry order, mean cents a trade;
  - z clustered by event (words in one call share an outcome tendency);
  - exits by reason;
  - the two-sided share at D and at D - 300;
  - drop counts.
- **Bar (paper, as ruled):** PF 1.3+ at 1c with both halves 1.0+, AND PF 1.0+ at 2c, judged unrounded.
- **Kill:** under the bar on development closes the try. A pass starts a paper record. The held-out block is read once, on the Head's go.
- **Figures** go by message only.

## Size and cost (estimate, set from stage A's real count)

- TRUMPTOPIC1 counted 179 events with an occurrence from Apr 17 to Nov 4. About 96 of them are in development, about 2,900 markets.
- **The historical candle endpoint is one request per market.** Each request covers D - 300 min to close_time, at most about 8 hours of 1 minute bars.
- So stage B is about 2,900 single requests: 7 files under 470 requests, about 4 hours at 12 a minute.
- If that is too heavy for the shared budget, stage B reads an md5(ticker) sample of 1,400 markets: ordered by md5 only, no price or result used, fixed before any candle.
- The Head picks which.

**Decided (the Head of R&D, Nov 15, 14:51Z, before stage A lands): the fixed sample of 1,400.**
- **Pool:** the development markets left after the time-window filter and the "Event does not qualify" drop. Only time fields and the word title are used; no price, volume or result.
- **Order:** sorted by the lowercase hex of md5(SEED + ticker), ascending, with ticker as the tie break. SEED is the ASCII text `MENTDRIFT-2026-11-15`.
- **Sample:** the first 1,400 in that order, or all of them if the pool is smaller.
- **Use:** stage B pulls candles for exactly these, in the same order. The scorer applies the same rule, and markets outside the sample are counted as `not_sampled`.
- **Later:** if the paper record shows anything, the rest can be pulled later as a second, disclosed sample (positions 1,401 onward in the same order).

## Order of work

1. This card.
2. Stage A list job, to Auditor B, then to Main.
3. Scorer, plus a hand case.
4. Auditor B's quick check, then stage B to Main.
5. Run once, commit blind, figures by message.
