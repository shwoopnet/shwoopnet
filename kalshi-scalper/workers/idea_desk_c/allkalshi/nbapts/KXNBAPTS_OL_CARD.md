# KXNBAPTS (O) and (L): two VERSION cards for a paper record (Idea Desk C, Nov 15, 2026, written before any data for this card is pulled)

**Status:** VERSION, not NEW (the Verification Analyst, Nov 15, 14:45Z). The Head of R&D's go (14:46Z) is a paper record under the lighter gate: one build plus Auditor B's quick check. These cards count toward the owner's 5 at PF 1.3+, never toward the unique list. Nothing here is live, places an order or changes the bot.

## Parents and priors, said plainly

- **(O) fade a large pre-game move.**
  - Parent: the displacement-fade family (SNAPBACK1 and SPIKE1 falsified; LIQREV is the third test; SWING1, SCALP2, LADFADE and the S17, S27, S29, S37 and S40 fades all lost).
  - The prior is that it fails here too. The only new thing is the market (NBA player points rungs, pre-game).
- **(L) follow the last pre-game hour's move.**
  - Parent: PREMOVE (Desk B, esports and e-soccer, registered) and the momentum-follow family (M1, INPLAYJUMP's follow arm).
  - Same prior. The only new thing is the market.
- **Why the market might differ (a reason, not evidence).** Player props reprice on injury and lineup news in the last hours before tip-off, and are heavily traded (on Nov 10, 389 markets in 8 events, about 6.0 million contracts; Desk B's listing). Neither parent ran on a market whose late information is lineup news.
- **Not a ban shape.** The side is picked by a move, never by a price band. The band (40c to 60c) is the mid-strike region. So it is not favourite-and-hold, not the 7e cheap-side row, not market making and not a short round trip held for seconds.

## Data and windows (the Head's dates, Nov 15, 14:44Z; constants in the scorer)

- **Series:** `KXNBAPTS` only. Not `KXNBAPTSPROT`, not `KXNBAPTSLEADER`, and not the rebounds or assists series.
- **Development:** markets with close_time from 2026-10-21T00:00Z to before 2026-11-06T00:00Z.
- **Cut, never pulled:** closes from 2026-11-06T00:00Z to before 2026-11-13T00:00Z (PROPUNDER's reserve, rule 17).
- **Held-out:** closes from 2026-11-13T00:00Z to before 2026-12-04T00:00Z.
  - Read once, on the Head's go.
  - Pulled as its own small job after Dec 4.
  - It can be checked against the in-game recorder's books.
- **Disclosure: PROPS1.** PROPS1 (V2) read this series' cheap side with a frozen cut of 2026-10-03T16:00Z. That is last season, so it shares no closes with this card.
- **Disclosure: PROPUNDER.** PROPUNDER (mine, closed unread, 0 tries) reserves the week above. Its development block (closes Oct 15 to before Nov 6) overlaps this card's development block, so stage A makes it read-exposed (Auditor B, Nov 15). Its reserve is used for nothing else.
- **Exposure inside the reserve, times and counts only (Auditor B's note (b), Nov 15).** Two reads touched the reserve week (Nov 6 to Nov 13) before this card; neither read a price, volume or result.
  - Desk B's Nov 10 listing counts quoted in this card: 389 markets, 8 events, about 6.0 million contracts.
  - My own read of Nov 9 KXNBAPTS, KXNBAPTSPROT and KXNBAPTSLEADER markets in the CENSUS_LISTING run (Nov 15, about 14:40Z), to design the tip proxy. Fields read: the key names of one market; for each market, ticker, event_ticker, open_time, close_time, occurrence_datetime, expected_expiration_time and can_close_early; and for one KXNBAPTSPROT market also created_time, expiration_time, latest_expiration_time, updated_time, settlement_timer_seconds and rules_primary.
- **Truncation (Auditor B's note (3)).** If the last stored page of the stage A list still has a cursor, the list is not whole. The scorer stops before any result read and says so (`truncated_lists`).
- **Raw files (Auditor B's note (a)).** The raw list and candle files carry price and result fields. Nobody opens them for a rule. Only `ol_score.py`, once frozen and CLEAN, reads them, in the order its docstring states.
- **Stage A:** the job `KXNBAPTS_LISTS_A` lists settled KXNBAPTS markets with close-time bounds of the development block only, plus one series read.
  - The scorer keeps: ticker, event_ticker, open_time, close_time, occurrence_datetime, can_close_early, result.
  - Stage B is sized from stage A's real count: one-minute candles, batched, files under 470 requests at 5 s.

## The clock (the list carries no tip-off time)

- **Tip proxy.** `occurrence_datetime` looks like a scheduled game end: 3 hours after the usual tip-off, on the Nov 9 times seen (time fields only, no price or result read). The tip proxy is P = occurrence_datetime - 3 h.
- **Last pre-game mark** G = P - 30 min (a buffer for an early tip or a wrong proxy).
- **Check.** Before scoring, the scorer prints the share of markets whose first in-game sign (close_time before occurrence_datetime, meaning closed early on a hit threshold) comes before G. If more than 2% do, the proxy is wrong and the card stops before any result is read.
- **Decision time** D = G - 60 min, on the 1 minute candle ending at D.

## The rules (each side bought is 1 contract)

- **Mid.** On a candle, the mid is (yes_bid close + yes_ask close) / 2, only when the candle is two-sided under rule 18: 0 < yes_bid < yes_ask < 1, with 1e-9.
- **Move.**
  - m3 = mid(D) - mid(D - 180 min). This is (O)'s window.
  - m1 = mid(D) - mid(D - 60 min). This is (L)'s window.
  - Both ends must be two-sided. A missing candle is never carried forward.
- **(O):** if |m3| >= 0.10, buy the side that FELL. That is NO if m3 > 0 (NO ask = 1 - yes_bid), else YES (ask = yes_ask). The side's raw ask at D must be 0.40 to 0.60 inclusive.
- **(L):** if |m1| >= 0.06, buy the side that ROSE, with the same 0.40 to 0.60 band on the side's raw ask at D.
- **Removed:** a market whose close_time is at or before D (closed early, for example a player ruled out with an early close). It is counted and printed.

## Exits: EXITS3 (History Miner, Nov 15), one adaptation stated

- **Hold:** settle at 1 or 0. This is the baseline.
- **T:** take profit, first mark with side bid >= min(2e, 0.90).
- **S:** stop, first mark with side bid <= e / 2.
- Marks are 1 minute candles after D. T and S may trigger to the candle ending 60 s before close_time, in-game included, as EXITS3 says.
- **M (adapted):** EXITS3's time exit sells 180 s before the close. For a pre-game rule the matching time is the end of the pre-game period, so M sells at the mark ending at G (60 minutes after entry). Written now, before any read.
- **Sellable mark:** the side's bid is above 0 and below 1.
- **Tries:** (O) hold, T, S, M and (L) hold, T, S, M. That is **8 tries**, all added to the deflation ledger.

**Stated before any read (Auditor B, Nov 15):**
- **M exit.** It sells at the mark ending exactly at the M time. If that candle is missing or not sellable, it sells at the first sellable mark up to 4 minutes later, printed as `M_late` with its count. With no such mark the trade is held. 4 minutes keeps the NBA M exit pre-game (G is 30 minutes before the tip proxy) and the MENT M exit before the speech (O - 5 min + 4 min).
- **e is the raw ask at D,** before any haircut. T's level min(2e, 0.90) and S's level e/2 use raw e, so every haircut line exits at the same mark (EXITS3).
- **Bars** are judged on unrounded figures with no tolerance: exactly 1.3 or 1.0 passes.

## Costs, printing and the bar

- **Haircut d3b5f24e (C1 to C10).** Entry = raw ask + h; a sale = bid - h, never below 0.01; h = 0, 1c and 2c all printed. The primary is 1c, but 2c when the entry or exit mark is within the last 2 minutes before close_time (C8).
- **Fee:** per order, rounded up: ceil(7% x p x (1-p) x 100) / 100. Taker on every leg.
- **Void:** a void refunds the price and keeps the fees.
- **Label:** "upper bound, not fill-checked".
- **Printed for each try:**
  - n, cash PF, halves at floor(n/2) in entry order, mean cents a trade, and day-clustered z;
  - exits by reason;
  - the **two-sided share** at D and at each move anchor (C1: prop candles are often one-sided);
  - the drop counts.
- **Bar (paper, as ruled):** PF 1.3+ at 1c with both halves 1.0+, AND PF 1.0+ at 2c, judged unrounded.
- **Kill:** any try under the bar on development is closed. A try that passes starts a paper record. Its held-out read is one read after Dec 4, on the Head's go.
- **Figures** go by message only. No live figure is in any file.

## Order of work

1. This card.
2. Stage A list job, to Auditor B, then to Main.
3. Scorer, plus a hand case with expected outputs.
4. Auditor B's quick check, then sized stage B candles to Main.
5. Run once, commit blind, figures by message.
