# NEWH12 result (V2 worker NEWH12, 2026-10-30, research only)

Registration `workers/NEWH12_REGISTRATION.md` (commit 6aeaa8b, pushed before any fill quote after a signal or any outcome was
read). Code `src/scalper/newh12.py` (`counts` reads signal quotes only; `dv` scored once; `holdout` never run). Printout
`studies/newh12_result_2026-10-30.txt` (aggregates only). Nothing was changed after the score. Fees rounded up per order (C = 10
and C = 1, x1.2 at C = 10). Fill at the next candle's ask of the lagging book (660 s to 420 s before the close), 20c to 80c, held.

**No rule passed discovery, so no validation gate was applied and the frozen holdout (Oct 18 to Oct 30) was NOT read.**
Validation is printed for the record, as registered.

## Step 1: the cross-asset families against the ledger (the untested list)

- Gold against Bitcoin inside one window (lead, lag, laggard catch-up, pair, "dollar move" coherence): TESTED (**S01, S02, S03,
  BK4, NEWH8 R3**, co-loss information: gold's losses are independent of the coins'). No counterparty can be named for a shared
  factor that the record says does not exist. No try.
- One asset's previous window carrying into another's next: TESTED (**S04, S05, XLEAD1**). No try.
- Bitcoin and Ethereum pairs and divergence at the open: TESTED (**BK3, BK5**). Ethereum lagging a Bitcoin LEVEL extreme
  mid-window: **BK7** (18 entries). The CHANGE-based lead and lag, one leg on the book that did not move, minutes 3 to 7, 20c to
  80c: UNTESTED, this round (H1 to H4).
- The other coins' lean as a filter on L1 or on a price-band rule: TESTED (**CONC1, CROWD1, P3, slot `pair` filter**) and
  banned ground now. No try.
- 15 minute book against the hourly ladder at the shared close: TESTED on Bitcoin AND Ethereum (**XM1**, Ethereum z -4.20;
  **BLADX, LOCK2H, ARB4, CONF1/2, CORR1, GLADH**). No try.
- The ladder's lean at the 15 minute open: **LADLEAN, LADFADE** (Bitcoin, FALSIFIED). The Ethereum copy (KXETHD against
  KXETH15M) was DECLINED, no try: a copy of a falsified rule, XM1 already covers Ethereum's ladder, and local KXETHD minute
  candles span Sep 29 to Oct 13 only, so the fixed discovery window is empty (NOT_RUNNABLE on the registered split).
- Cross-venue and macro leaders (**PM1, PM2, COINPREM, XMAC1**), silver against gold (**GSILV**): TESTED. No try.

## Verdicts (PF at C = 10; fill at the next candle's ask, held)

| Rule | Counterparty named | Discovery n / PF10 / PF1 / PF x1.2 / win vs cost / day z | Validation n / PF10 / PF x1.2 / win vs cost / day z | Verdict |
|---|---|---|---|---|
| H1 XLAG-ETH (Bitcoin's book moved 15c+ in 2 minutes, Ethereum's 5c or less; buy Ethereum in Bitcoin's direction) | slower Ethereum quoters and resting orders | 312 (46 d) / 0.89 / 0.88 / 0.88 / 47.1% vs 48.0c / -1.11 | 157 (27 d) / 0.95 / 0.94 / 47.8% vs 47.3c / -0.30 | **FALSIFIED** |
| H2 XLAG-DOGE (same, Dogecoin lagging) | slower Dogecoin quoters, a thinner book | 537 (46 d) / 0.92 / 0.90 / 0.91 / 47.9% vs 48.1c / -0.86 | 239 (27 d) / 0.82 / 0.81 / 44.4% vs 47.3c / -1.51 | **FALSIFIED** |
| H3 XLAG2-DOGE (Bitcoin AND Ethereum each moved 10c+ the same way, Dogecoin 5c or less) | as H2 | 633 (46 d) / 0.96 / 0.94 / 0.95 / 49.8% vs 49.1c / -0.43 | 272 (27 d) / 0.84 / 0.83 / 46.0% vs 48.1c / -1.05 | **FALSIFIED** |
| H4 XLAG-BTC (control: Ethereum's book moved, Bitcoin's did not; buy Bitcoin) | none expected | 453 (46 d) / 0.90 / 0.88 / 0.89 / 48.3% vs 49.1c / -1.08 | 258 (27 d) / 0.84 / 0.83 / 48.8% vs 51.2c / -1.24 | **FALSIFIED** |

Net at C = 10, fees x1.2: discovery -$85.50, -$112.97, -$75.80, -$120.28; validation -$22.15, -$114.94, -$109.85, -$109.18.
YES share 0.47 to 0.54 in every cell, so no direction carries it. Trades spread evenly over the five signal candles.

**Funnels (all three stages).** XLAG-ETH 8,053 paired windows, 648 first triggers, 136 out of band, 512 trades. XLAG-DOGE
1,179 triggers, 312 band, 867 trades. XLAG2-DOGE 1,378 triggers (73 windows where the two majors disagreed were skipped), 346
band, 1,032 trades. XLAG-BTC 911 triggers, 135 band, 776 trades. The out-of-band cases are a "flat" book that was already past
80c or under 20c, not a stale one.

**Zero volume both ways.** No signal or fill candle used had volume 0 in any rule; every PF is the same with and without.

## Information looks (counted in N)

- **I1 same-window outcome agreement** (share of paired windows settled the same way): Bitcoin/Ethereum 80.6% (discovery,
  4,357) and 83.0% (validation, 2,560); Bitcoin/Dogecoin 76.1% and 77.6%; Ethereum/Dogecoin 77.3% and 79.8%. So the three
  coins share most of a 15 minute window's direction, which is what the lag story needs; the books already price it.
- **I2 catch-up** (the lagging book's side mid after the signal, signed in the leader's direction; discovery plus validation):
  Ethereum after a Bitcoin move +0.5c at 60 s and +1.0c at 180 s (595 triggers); Dogecoin after Bitcoin -0.2c and +0.1c
  (1,049); Dogecoin after both majors -0.1c and -0.2c (1,206); Bitcoin after an Ethereum move +0.8c and +1.7c (839). The
  leader itself gives back 0.2c to 0.5c. The largest drift toward the leader is on BITCOIN's book after Ethereum moved, the
  opposite of a "slower Ethereum quoters" story, and even that 1.7c is below the fee at these prices (about 1.75c on a 50c
  contract) and did not show in the outcome (XLAG-BTC won 48.3% at 49.1c).

## What it says

- A 15 minute crypto book that stayed flat while the other coin's book moved 15c is not stale: the flat book's side won at
  or below the price paid in all eight cells (win rate minus price between -2.9 and +0.7 points, every day z negative). With
  I1 at 76% to 83% agreement, the shared factor is real and already in the quotes; a flat book is reporting that its own spot
  has not moved against its own strike.
- The control earned the same as the hypothesis (H4 0.90 against H1 0.89 in discovery), so even had H1 cleared a bar its
  counterparty line would have failed under the registered rule.
- The whole mid-window cross-asset lead and lag among Bitcoin, Ethereum and Dogecoin is now closed on 1 minute candles, from
  the two directions and with the two-leader condition; with BK3, BK5, BK7 (the open and the level extreme), S01 to S03 and
  BK4 (gold), XM1 and BLADX (the ladders), the cross-asset family among these markets has no untested shape left that candle
  data can read. A sub-minute version would need the quote recorder's Bitcoin, Ethereum and Dogecoin rows (RECORD1's data,
  the last 150 s only, which is inside the banned late window for a held side above 50c), so none is proposed.

## Count

**N added: 6** (4 tries: XLAG-ETH, XLAG-DOGE, XLAG2-DOGE, XLAG-BTC; 2 information looks: I1, I2). Running count about
678,923 (after GEN9) + 6 = **about 678,929**. Deflated one-sided z bar 5.26.

## Proposed README section (for the lead to merge)

## Result: NEWH12 (cross-asset lead and lag among the 15 minute crypto books in the same window), 2026-10-30

Registered first (`workers/NEWH12_REGISTRATION.md`, commit 6aeaa8b), result `workers/NEWH12_RESULT.md`, code
`src/scalper/newh12.py`, local candles only (Bitcoin, Ethereum and Dogecoin share 8,053 settled closes, Aug 6 to Oct 30);
discovery to Sep 21, validation to Oct 18, holdout to Oct 30 NOT read because nothing passed. Family check first: gold against
Bitcoin in one window is S01 to S03, BK4 and NEWH8 R3 (and the co-loss read says the two share no 15 minute factor), pairs and
divergence at the open are BK3 and BK5, the level extreme is BK7, the ladders at the shared close are XM1 (Bitcoin and Ethereum)
and BLADX, and an Ethereum copy of LADLEAN was declined (a copy of a falsified rule, XM1 covers it, and local KXETHD candles start
Sep 29), so no try was spent there. The one untested shape: a lead and lag read from the CHANGE of two books over the same two
minutes (minutes 3 to 7), one leg on the book that did not move, bought at the next candle's ask 20c to 80c and held.
**XLAG-ETH** (Bitcoin moved 15c+, Ethereum 5c or less, buy Ethereum Bitcoin's way): PF 0.89 on 312 then 0.95 on 157,
**FALSIFIED**. **XLAG-DOGE** (Dogecoin lagging Bitcoin): 0.92 on 537 then 0.82 on 239, **FALSIFIED**. **XLAG2-DOGE** (both
majors moved 10c+ the same way, Dogecoin flat): 0.96 on 633 then 0.84 on 272, **FALSIFIED**. **XLAG-BTC** (the control, Bitcoin
lagging Ethereum): 0.90 on 453 then 0.84 on 258, **FALSIFIED**, and equal to the hypothesis, so the lag story fails on its own
terms. Information: the coins settle the same way in 76% to 83% of windows (I1), yet the flat book won at or below its price in
every cell; after a trigger the lagging book drifts 0c to 1.7c toward the leader over 3 minutes (I2), the largest drift being
Bitcoin's after Ethereum, below one fee and absent from the outcome. The mid-window cross-asset family among these markets is
closed on 1 minute candles. N +6; running count about 678,929 (z bar 5.26).
