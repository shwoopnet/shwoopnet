# FAV10-X build 1: spec and hand case (History Miner, written Nov 15, 2026, before any code)

Owner order via the Head of R&D (18:34Z): run XRPFAV10's rule FROZEN on every other 15 minute series in the research-data archive.

## Rule (frozen, from exits3.fav_entry, which copies research branch src/scalper/regime_b2.py rows 4 and 5)
- The LAST candle whose end is 570 to 640 s before the close (inclusive). None: no trade.
- That candle must be two-sided (C1: 0 < yes_bid < yes_ask < 1), else "not two-sided", no trade.
- No spread cap. Favourite = YES if yes_ask >= 1 - yes_bid, else NO at 1 - yes_bid.
- Trade only if the favourite's ask is 0.88 to 0.92 inclusive. 1 contract, held to settlement.
- Net per contract (exits3.net): entry min(0.99, e + h); fee per order ceil(round(100 x 0.07 x c x p(1-p), 9))/100, divided by c; win pays 1; void refunds the price and keeps the fee.
- Printed at h 0, 1c, 2c, at c = 1 (the rule's size) and c = 10.

## Universe and tries
- underdog2x's 19 series, sources, Oct 3 cut and SOL cut (before 1790760600). Thirds 1, 2 AND 3 kept (frozen rule, no fit; Auditor B to confirm).
- XRP is excluded: it is the rule's home market, already read. 18 tries, one per series, printed as tries = 18.
- Candles after the close dropped; first source wins on duplicate tickers.

## Per market print
n, wins, voids, PF at each h and c, halves by close order floor(n/2) (half 1 = first floor(n/2) trades), pass flag at c = 1.
- Bar: non-NC15: PF(1c) >= 1.3, both halves at 1c >= 1.0, and PF(2c) >= 1.0. NC15 series: PF(2c) >= 1.3 and both halves at 2c >= 1.0.
- n < 100: "no evidence at n = x", no pass flag.
- KXGOLD15M flagged: a pass there is a version of L1, not a new strategy.

## Hand case (invented)
H1 YES favourite e 0.90 wins, c 1: h0 +0.09 (fee 0.01), h1 +0.08, h2 +0.07. c 10, h0: fee 0.07 per order, +0.093.
H2 NO side: last candle in window bid 0.11 ask 0.13, yes_ask 0.13 < 1 - 0.11 = 0.89, so NO at 0.89; result no: h0 +0.10.
H3 e 0.88 loses, c 1, h0: fee ceil(0.7392) = 0.01, net -0.89.
H4 void, e 0.90, c 1, h0: -0.01.
H5 two candles at left 640 and 570: the 570 one is used. A candle at left 560 only: no trade. 0.93 favourite: no trade. Bid 0: not two-sided.
H6 pass flag: non-NC15 PF1c 1.3, halves 1.0 and 1.2, PF2c 1.0 passes; PF1c 1.29 fails. NC15 judged at 2c only. n 99 gives "no evidence at n = 99".
