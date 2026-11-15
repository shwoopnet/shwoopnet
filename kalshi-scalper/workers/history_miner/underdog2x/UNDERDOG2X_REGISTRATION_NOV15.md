# UNDERDOG2X: the owner's manual underdog scalp, generalised to every 15 minute series in the research-data archive (History Miner, registered 2026-11-15 ~16:20Z, BEFORE any price, quote or result is read; the Head's brief of 15:56Z, owner directive item 1)

**What has been read so far:**
- the archive's integrity (research-data branch, Oct 29 archive, WHOLE sha256 15788a025e39d48725...);
- only the market table's ticker, series and close_ts columns, to list the series and fix the date constants below.

No candle, bid, ask, volume, open interest or result has been read.

## 1. Universe and held-out cuts
- **Source databases, in this order, first source wins on a duplicate ticker:** l1b, book, e3b, alts4, alts2, alts3, rep (`.sqlite` from the archive). Every series ending 15M. Candles ending after a market's close are dropped.
- **Global cut (conservative, "when in doubt, cut it"):** only markets closing BEFORE 2026-10-03T00:00:00Z (epoch 1790985600).
  - It covers XOI1's W3 (Oct 3 to Oct 27; Bitcoin, XRP, HYPE, NEAR, Zcash, BNB), FXREF1 (from 2026-10-03T16:00Z; WTI and the FX pairs), the Oct 5 cuts (gold, silver, copper, natural gas, platinum, palladium: QSTALE1/TSLM1, TIECOND1) and FLIPS0-X's forward (from Oct 24).
  - The VA's 28 nc-data windows are November, outside the archive.
- **Not in the universe:** every market closing on or after Oct 3. That removes KX10YRRATE15M, KX2YRRATE15M, KX30YRRATE15M, KX5YRRATE15M, KXAUDUSD15M, KXUSDCAD15M and KXBRENT15M entirely, since their archive data starts after Oct 3.
- **To be confirmed before any run (Auditor B with Desk A's HELDOUT_REGISTRY):** no OPEN card holds a window BEFORE Oct 3 on these 19 series. If one does, that window is cut by a dated line here before the run. Forensics' check found none on Bitcoin, Ethereum and XRP (INX1, RO1, OVN2, WXDEAD1, SLOTEX-ETH); the other series are unchecked.

## 2. The 19 series and their fixed-date thirds (constants; UTC dates at 00:00Z)

| series | markets kept | first close | third 1 | third 2 | third 3 (HELD-OUT, read once) |
|---|---|---|---|---|---|
| KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M, KXNEAR15M, KXZEC15M | 5,493 each | 2026-08-06 | to 08-25 | 08-25 to 09-13 | 09-13 to 10-03 |
| KXBNB15M, KXHYPE15M | 5,489 each | 2026-08-06 | to 08-25 | 08-25 to 09-13 | 09-13 to 10-03 |
| KXGOLD15M | 4,121 | 2026-08-06 | to 08-25 | 08-25 to 09-13 | 09-13 to 10-03 |
| KXSILVER15M | 4,085 | 2026-08-06 | to 08-25 | 08-25 to 09-13 | 09-13 to 10-03 |
| KXWTI15M | 4,129 | 2026-08-06 | to 08-25 | 08-25 to 09-13 | 09-13 to 10-03 |
| KXSOL15M | 4,455 | 2026-08-17 | to 09-01 | 09-01 to 09-17 | 09-17 to 10-03 |
| KXCOPPER15M | 2,545 | 2026-08-27 | to 09-08 | 09-08 to 09-20 | 09-20 to 10-03 |
| KXNATGAS15M | 2,589 | 2026-08-27 | to 09-08 | 09-08 to 09-20 | 09-20 to 10-03 |
| KXPALLADIUM15M, KXPLATINUM15M | 984 each | 2026-09-17 | to 09-22 | 09-22 to 09-27 | 09-27 to 10-03 |
| KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M | 649 each | 2026-09-23 | to 09-26 | 09-26 to 09-29 | 09-29 to 10-03 |

- Thirds are by close time against these dates, not by count.
- Rule: T1 = first close + (cut - first close)/3, T2 = first close + 2(cut - first close)/3, each floored to 00:00Z of its UTC day.
- The FX pairs, platinum and palladium have only 10 to 15 days, so their thirds are thin. They are reported; under 30 trades in any read is "no evidence at n = x".

## 3. Entry (fixed)
- For each market, scan its 1 minute candles in end time order. Take the FIRST candle that:
  - has at least 600 s left (end_ts <= close - 600);
  - is two-sided (0 < yes_bid < yes_ask < 1, rule 18 / C1);
  - has one side's ask from 0.20 to 0.25 inclusive (YES ask = yes_ask; NO ask = 1 - yes_bid).
- Two-sided quotes cannot have both asks at or under 0.25, so the side is unique.
- Buy that side, ONE contract. e = that ask (raw). One entry per market at most.

## 4. Exits: three variants, each a try
Marks are the candles after the entry candle, at or before close - 60. Side bid: YES = yes_bid; NO = 1 - yes_ask. A mark is sellable if 0 < side bid < 1. A sale waits for the first sellable mark at or after its trigger.
- **(a) 2x or 3 minutes:**
  - Sell at the first mark at or before close - 180 whose side bid >= 2e.
  - If none, sell at the mark ending close - 180, or the first sellable mark after it.
  - If none is sellable, hold to settlement (counted).
- **(b) 2x or hold:** sell at the first mark (to close - 60) with side bid >= 2e; else hold to settlement.
- **(c) half at 2x, rest to 0.80:** half the position sells at the first mark (to close - 60) with side bid >= 2e. The other half sells at the first mark at or after that one with side bid >= 0.80, else it is held. If 2x never comes, all is held.
  - **One contract cannot be halved.** Proposed for the Head's ruling: (c) is scored as a 2 contract position (one 2-contract buy order; one 1-contract sale at 2x; one 1-contract sale at 0.80 or settlement), net reported per contract, so it stays comparable. Until ruled, (c) is not run.

## 5. Prices, fees, haircut (RND_QUEUE C1 to C11)
- Entry e + h (cap 0.99). Sale side bid - h (floor 0.01). h = 0, 1c, 2c are all printed.
- Taker fee on every leg at the haircut price, rounded up to the cent per order at the order's contract count, divided per contract (C4).
- A void (no yes or no result) refunds the price and keeps the entry fee, counted (C10).
- Upper bound, not fill-checked (C5, C9).
- **Primary haircut:**
  - 2c on NC15 series at every mark (C11): silver, copper, WTI, natural gas, EUR/USD, GBP/USD, USD/JPY, HYPE, BNB.
  - On the other 10 series, 2c for variants (b) and (c), whose exits can fall in the last 2 minutes (C8), and 1c for (a), whose exits are at 3 minutes or earlier, unless held.

## 6. Read and bar (fixed)
- **Development read:** thirds 1 and 2. Per variant: pooled over all 19 series, and per series. Printed:
  - n; cash PF; PF of third 1 and of third 2; PF of the halves by count floor(n/2) in close order;
  - mean cents; day-clustered z (UTC close day);
  - at h 0, 1c, 2c, with the exits by reason.
- **Bar (the Head's):** PF 1.3 or better at 1c, with both halves 1.0 or better, AND PF 1.0 or better at 2c, on thirds 1 and 2.
  - **Reading flagged for the Head:** "both halves" = third 1 and third 2 each PF 1.0+ at 1c. The floor(n/2) halves are also printed.
  - On NC15 series the 1.3 and both-halves tests are read at 2c (C11).
  - Under 30 development trades: "no evidence at n = x".
- **Held-out:** third 3, read ONCE, for any variant (pooled or per series) that met the bar, on the Head's go after the development print is committed and reported.

## 7. Tries (for deflation)
- 3 variants x (pooled + 19 series) = **60 tries**, counted whether or not a series has enough trades.
- Variant (c) counts only if the Head rules it runnable.

## 8. Gate
- One build (this desk), Auditor B's CLEAN of the code and input list, the Testing Desk's input list, and the held-out confirmation in section 1, before any read.
- Development print committed blind; figures by message only. The held-out is read once on the Head's go.

## Amendment 1 (2026-11-15 ~16:05Z, the Head's rulings of 15:59Z, before any price or result is read)
1. **Variant (c) runs as a 2-contract position:**
   - one 2-lot buy at e + h (fee rounded per order at 2 contracts);
   - one 1-lot sale at the first side bid >= 2e (fee at 1 contract);
   - the other 1-lot sold at the first later side bid >= 0.80 (fee at 1 contract), else held to settlement.
   - If 2x never comes, both are held. Net is reported per contract (divided by 2).
2. **Bar:** thirds 1 and 2 are the halves. Each needs PF 1.0+ at the primary haircut, and PF 1.3+ pooled over thirds 1 and 2 at the primary haircut, AND PF 1.0+ at 2c. The floor(n/2) halves are printed as information. NC15 series are read at 2c (C11). Variants (b) and (c) on the other series have 2c as primary (C8), so their bar is read at 2c too. (a) on the other series is read at 1c.
3. **Pre-Oct 3 held-outs:** Auditor B confirms against Desk A's HELDOUT_REGISTRY for all 19 series before any price or result is read. Any window an OPEN card holds is cut, and the cut is listed here by a dated line before the run.
4. **Thin series:** the FX pairs, platinum and palladium stay in, with n reported per series. A series under 30 entries in any third is "no evidence at n = x" for that series, never a pass on its own.
