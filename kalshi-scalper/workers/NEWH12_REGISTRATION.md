# NEWH12 registration (Strategy Research V2 worker NEWH12, 2026-10-30, research only)

Written and pushed BEFORE any NEWH12 rule was joined to a fill quote after its signal or to any outcome. Code
`src/scalper/newh12.py` (committed with this file); result `workers/NEWH12_RESULT.md`. Markets: Kalshi `KXBTC15M`, `KXETH15M`
and `KXDOGE15M` (local 1 minute candles: `l1b`, `book`, `fresh` for Bitcoin and Ethereum; `e3b`, `alts2`, `fresh` for Dogecoin;
first file wins per close, the order every NEWH worker used). Public data only, nothing fetched. Times are UTC in the code and
US Central (CDT, UTC-5, the whole sample) in words.

## Step 1: which cross-asset families are already in the ledger (grep of README to GEN9)

| Cross-asset family | Ledger | Status |
|---|---|---|
| Gold and Bitcoin lead and lag inside one window (gold leads Bitcoin, Bitcoin leads gold, "laggard catch-up" when both move the same way, buy the slower) | **S01, S02, S03** (40 strategy screen, js 5, FALSIFIED); **BK4** (Bitcoin YES plus gold NO pair, FALSIFIED); **NEWH8 R3** (gold's cheap side when Bitcoin's core fires, FALSIFIED); co-loss information 2026-10-29 (gold's L1 losses independent of the coins', 3% to 10% against 30% to 63% coin with coin) | TESTED; the "dollar move" story has no counterparty to name because gold and the coins do not share a 15 minute factor on this record. No try. |
| Previous window of one asset carrying into the next window of another | **S04, S05** (Bitcoin and gold outcomes crossing over, FALSIFIED); **XLEAD1** (a Bitcoin L1 loss predicting the other coins' next window, NOT_ENOUGH_DATA, 293) | TESTED. No try. |
| Bitcoin and Ethereum pairs and divergence at the OPEN | **BK3** (Bitcoin YES plus Ethereum NO every window), **BK5** (mids differ by 10c in the first minute, YES on the lower, NO on the higher, 453 pairs), both FALSIFIED | TESTED at the open, as a two-leg pair, by LEVEL. |
| Ethereum lagging Bitcoin's extreme mid-window | **BK7** (Bitcoin mid at or above 0.95 or at or below 0.05 at 480 s, buy Ethereum's same side under 90c): 18 entries, NOT_ENOUGH_DATA; "Ethereum is usually priced in by the time Bitcoin is at an extreme" | TESTED only as a LEVEL extreme at one minute. A lead and lag by the CHANGE of the two books over the same two minutes, trading the book that did not move, one leg, 20c to 80c, from minutes 3 to 7, has not been run: **H1, H2, H3, H4** (disclosed as adjacent to BK7 and S03). |
| The other coins' lean as a FILTER on L1 or on a price-band rule | **CONC1** (agree versus disagree on L1, FALSIFIED, the sign reversed), **CROWD1**, **P3 breadth**, the slot search's `pair` filter | TESTED as filters on L1-shaped entries; banned ground now (L1 filters). Not what this round does. |
| 15 minute book against the hourly ladder at the shared close (Bitcoin and Ethereum) | **XM1** (Bitcoin AND Ethereum: trade toward the ladder, Ethereum -7.45c z -4.20, FALSIFIED), **BLADX**, **LOCK2H**, **ARB4**, **CONF1/CONF2**, **CORR1**, **GLADH** (gold) | TESTED on both coins. No try. |
| The hourly ladder's lean at the 15 minute open (windows opening :15 and :30) | **LADLEAN** (Bitcoin, FALSIFIED), **LADFADE** (Bitcoin, FALSIFIED on the holdout) | Bitcoin only. **An Ethereum copy (KXETHD against KXETH15M) is declined, no try:** it would be the Ethereum copy of a falsified Bitcoin rule; XM1 already found the Ethereum ladder the worse price at the shared close; and the local KXETHD minute candles cover Sep 29 to Oct 13 only (`ladders.sqlite`; the `ladl1_KXETHD` files are fixed-look snapshots), so the discovery window (to Sep 21) is empty and it is NOT_RUNNABLE on the fixed three-window split. |
| Cross-venue (Polymarket, Coinbase premium, Upbit) and macro leaders (S&P future, dollar, 10 year) | **PM1, PM2, COINPREM, XMAC1** (all FALSIFIED) | TESTED. No try. |
| Silver moved, gold did not | **GSILV** (NOT_ENOUGH_DATA) | TESTED. No try. |

So the one cross-asset shape the ledger lacks among these markets is a within-window lead and lag read from the CHANGE of two
books over the same minutes, one leg on the book that has not moved. That is the whole round.

## What this is NOT

No 88c to 97c favourite (L1); no L1 exit, size, filter, hour or throttle test; nothing bought in the last 6 minutes (every fill
candle ends 660 s to 420 s before the close); no cheap side chosen by a price band (the side is the direction the OTHER market's
book moved; the fill can be anywhere from 20c to 80c and a flat book usually sits near 50c); not a round trip (held to
settlement); not a two-leg pair (BK3, BK5); not a level extreme (BK7).

## What was looked at before this was written (disclosure)

The ledger sections above, NEWH9 and NEWH11 code, and `python -m scalper.newh12 counts`, which reads the SIGNAL candles only
(quotes at and before the signal: the two-minute move of each book), no fill quote, no quote after the signal and no result. It
was run so that the group is counted before the bar is set (the XLEAD1 lesson). Thresholds (15c, 10c, 5c, 10c spread, 20c to
80c) were written in the code before the count and were not changed after it. All three series share the same 8,053 settled
closes (discovery 4,357, validation 2,560, holdout 1,136).

| Rule | First-trigger windows: discovery | validation | holdout (frozen) |
|---|---|---|---|
| H1 XLAG-ETH | 394 | 201 | 53 |
| H2 XLAG-DOGE | 697 | 353 | 129 |
| H3 XLAG2-DOGE | 806 | 400 | 172 |
| H4 XLAG-BTC (control) | 528 | 311 | 72 |

Triggers spread evenly over the five signal candles. Fills, band and outcomes were not read.

## Common to every rule (fixed now)

- **Universe (time only):** every settled window (close time) 2026-08-06 to 2026-10-30 where the lagging series and every
  leader series have a settled market with the SAME close. **Windows:** DISCOVERY closes before 2026-09-21; VALIDATION
  2026-09-21 to 2026-10-18; HOLDOUT 2026-10-18 to 2026-10-30 (frozen; read once, only after a pass in both, after that result
  is pushed).
- **Mid:** YES mid of a candle's closing quote, readable only if 0 <= bid <= ask <= 1, ask above 0, bid below 1 and the spread
  at most 10c (a cost filter, visible before the trade). **Move** of a book at signal candle s: mid(s) minus mid(s - 120 s).
- **Signal candles:** s ending 720, 660, 600, 540 and 480 s before the close (minutes 3 to 7). The FIRST candle that triggers
  decides the window; a window is traded at most once and a first trigger whose fill is missing or out of band is "no fill" or
  "band", never retried at a later candle.
- **Side:** the direction the leader's book moved (YES if its mid rose, NO if it fell). **Fill:** the lagging book's side ask on
  the NEXT candle (s + 60), inside [0.20, 0.80]; missing or outside the band counted. Held to settlement, nothing sold.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle had volume 0.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, net positive at fees x1.2 in each, at least
  100 / 50 / 30 trades (discovery / validation / holdout), a named counterparty, and pooled day-clustered z at least the
  deflated bar (about 5.26).

## H1 XLAG-ETH (1 try): Bitcoin's book moved, Ethereum's did not

- **Trigger:** |Bitcoin move| at least 0.15 and |Ethereum move| at most 0.05 over the same two minutes. Trade Ethereum.
- **Counterparty:** the Ethereum 15 minute quoters whose bots refresh more slowly than the Bitcoin quoters', and the resting
  Ethereum orders and takers who have not yet seen a spot move that both coins share (their 15 minute returns are strongly
  correlated, so a 15c repricing of Bitcoin's window is usually a repricing of Ethereum's too).
- **Honest alternative:** BK7 found Ethereum priced in by the time Bitcoin is at an extreme; the quoters read the same spot
  feeds for both coins; a book that stayed flat while Bitcoin's moved is usually reporting a real divergence of the two spots
  against their own strikes (the correlation is far from 1), so the flat book is right and the one minute delay to the fill
  gives back any lag that did exist.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.10 at C = 10, win rate within 3 points of the price paid.

## H2 XLAG-DOGE (1 try): Bitcoin's book moved, Dogecoin's did not

- **Trigger:** as H1 with Dogecoin as the lagging book. Trade Dogecoin.
- **Counterparty:** as H1, on a thinner book quoted by fewer makers, so if a refresh lag exists anywhere it should be largest
  here. The honest alternative is the same as H1's.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.15.

## H3 XLAG2-DOGE (1 try): both majors moved the same way, Dogecoin did not

- **Trigger:** |Bitcoin move| and |Ethereum move| each at least 0.10 with the SAME sign, |Dogecoin move| at most 0.05. Trade
  Dogecoin in the majors' direction. Two leaders agreeing is the crypto factor rather than one coin's own move, which is the
  case the lag story needs most.
- **Counterparty:** as H2.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.15. If H3 clears discovery and H2 does not, the two-leader condition is doing
  the work and the result is read with that in mind; nothing is tuned either way.

## H4 XLAG-BTC (1 try, the control): Ethereum's book moved, Bitcoin's did not

- **Trigger:** as H1 with the roles swapped. Trade Bitcoin in Ethereum's direction.
- **Why it is here:** Bitcoin's book is the most quoted of the three, so a refresh-lag story predicts H4 earns LESS than H1. If
  H4 earns as much as H1, whatever H1 shows is a shared-factor effect, not a lag, and the counterparty line of H1 is not met.
- **Counterparty, if any:** Bitcoin quoters slower than Ethereum's, which is not expected.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.10, no better than H1.

## Information looks (counted in N, not rules)

- **I1 same-window outcome agreement:** the share of paired windows in which the two coins settled the same way, for
  Bitcoin/Ethereum, Bitcoin/Dogecoin and Ethereum/Dogecoin, discovery and validation. Says how much shared factor there is to
  be mispriced.
- **I2 catch-up (quotes only, no result):** at the trigger windows, the lagging book's side mid change from the signal candle to
  +60 s and +180 s, signed in the leader's direction, beside the leader's own further move. If the lagging book does not move
  toward the leader after the signal, there was no lag to trade.

## Kill criteria (each try, no parameter changes after any score)

- Discovery: fewer than 100 trades NOT_ENOUGH_DATA (validation printed for the record). PF at C = 10 under 1.5, or net at
  fees x1.2 at or below 0: FALSIFIED.
- Validation (after a discovery pass): fewer than 50 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0:
  FALSIFIED.
- Holdout (after both passes, read once): fewer than 30 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0:
  FALSIFIED. All PF gates met but pooled day z under the deflated bar: NOT_ENOUGH_DATA. All gates met: NOT_YET_FALSIFIED
  (forward registration only).
- H1 passing with H4 matching it (H4 discovery PF within 0.2 of H1's): the counterparty line fails and H1 is at most
  NOT_ENOUGH_DATA whatever its PF.

## Count

N tried: **4** (XLAG-ETH, XLAG-DOGE, XLAG2-DOGE, XLAG-BTC) + 2 information looks (I1, I2) = **6**. Running count about 678,923
(after GEN9) + 6 = **about 678,929**. One-sided Bonferroni z bar at 0.05: **5.26**.
