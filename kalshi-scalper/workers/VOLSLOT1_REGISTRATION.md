# VOLSLOT1 registration: the favourite in the quietest clock slots (Strategy Research V2, worker VOLSLOT1, research only)

Written 2026-11-03 BEFORE any win, loss, profit factor or result of any favourite trade was computed. Only outcome-free counts (eligible favourite
trades per volatility class and third, from quotes alone; `python -m scalper.volslot1 counts`: quiet W1 156 / W2 448, loud 127 / 432, mid 278 / 852,
all 1,282 / 2,615, 1,604 trades unclassified for lack of trailing history) and TODSEAS1's result file were read. Code `src/scalper/volslot1.py`, tests
`tests/test_volslot1.py` (5 ok). Touches no live code, `functions/`, L1 or OICORE. No promote verb. Crypto and gold excluded (owner's ban on 15 minute L1).

**Plain statement.** Likeliest outcome: FALSIFIED. A favourite at 85c to 97c pays 3c to 15c to win and 85c to 97c to lose; PF 1.5 needs the win rate to beat the
price by about 3 points after the fee. EVENT-style reads of this family (Bitcoin favourite PF 0.77 at 180 s; USWEEP1 scoring favourites 85c to 97c across ALL
non-15-minute series, not duplicated here) say the favourite is not underpriced on average. This try is only the slot-volatility CONDITION.

## Question and mechanism
TODSEAS1 (unregistered post hoc observation, S9 NY_MIDDAY, 1 win in 79 at 8.7% paid, diff -11.6c, z -2.95) suggests the maker quotes the 15 minute book at about
one volatility while realised volatility depends on the clock slot. **Mechanism:** in quiet slots the tails are overpriced, so the favourite is underpriced.
**Counterparty:** the maker selling the 85c to 97c side's complement (buying the tail) at a price set for an average slot. Honest prior of a survivor: 2%.
**Duplicate check (done before registering):** TODSEAS1 (cheap side by NAMED clock slot, ask 5c-30c; not this), USWEEP1 (favourite 85-97c across all non-15-minute
series at fixed times to expiry; its result had not landed at registration, noted in the result if it has), COMM1, TAIL1, UNDER1 (cheap side), E3, PUB20 (P02 VOLEXP
is volatility clustering on cheap sides). Not covered: favourite on the non-crypto 15 minute series conditioned on trailing slot realised move.

## Universe (fixed on metadata)
KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXSILVER15M, KXCOPPER15M, KXWTI15M, KXNATGAS15M, KXPLATINUM15M, KXPALLADIUM15M (same as TODSEAS1). AUD/USD and USD/CAD
have candles only inside the frozen W3, so they are left out (stated). FX candles start 2026-09-23 (no W1), platinum and palladium 2026-09-18.

## Quiet slot definition (chosen before outcomes; quotes only)
- **Realised move of a window** = sum of |change of the YES mid| over consecutive 1 minute candles from the window open to the look (end_ts in (close-900, close-180]),
  at least 8 consecutive pairs, else the window has no value. No outside spot price exists for these series on file; this is Kalshi's own quote path, a
  contract-implied proxy, disclosed. It uses no result.
- **Slot** = the window CLOSE as a US Eastern quarter hour (96 slots) x weekday class (Mon-Fri vs Sat-Sun, ET).
- **Trailing 30 days:** for a window on ET date d, the slot's value = mean realised move of the same series, same slot, same weekday class over windows with
  close in [d - 30 days, d) (strictly earlier dates), at least 8 windows. Only windows closing before 2026-10-05 (the first two thirds) are ever loaded.
- **Quartile:** the slot's value is ranked (mid rank for ties) among the series' slots that have a value on that date (at least 8 slots). **Quiet = rank in the
  bottom quartile, loud = top quartile**, mid = the rest; windows without a classification are unclassified (in the all-slots control only).

## Trade rule (one rule, every class)
Window with close `c`. At the candle ending 180 s before the close require 0 < bid < ask < 1 and ask - bid <= 0.10. The favourite is YES if its ask is 0.85 to 0.97, else
NO if 1 - YES bid is 0.85 to 0.97, else no trade. **Fill at that side's ask on the candle ending 120 s before the close with a HARD LIMIT at 0.97** (a fill ask above
0.97 is no trade, never filled higher). Held to settlement, 1 order per series per window, C = 10, taker at the ask, **fee 7% x C x p x (1-p) rounded up to the cent
per order** (`gen6.fee`; x1.2 also reported). No event filter (stated: events are not removed; same in all three classes).
**Worst single loss at 10 contracts: $9.73** (970c + 3c fee at 97c; $0.97 at 1 contract). At 92c paid one win nets about 7c per contract, so **one loss costs about
14 wins**: the payoff ratio (average win over average loss) is about 0.07 to 0.10 and is reported next to PF.

## Windows
W1 2026-08-06 to 09-04, W2 09-05 to 10-04, **W3 2026-10-05 on is the FROZEN HOLDOUT, never loaded by the scoring command** (`hi_ts` is the start of W3 in both `counts` and
`score`). W3 is read only if the quiet class passes W1 and W2 (code for that is not written; it needs a new amendment).

## Three tries (N)
1. QUIET (bottom quartile) = the treated class. 2. LOUD (top quartile) control. 3. ALL slots control. **N: +6** (+2 per try, 3 tries). Per-series and per-month tables are reports.

## Numeric prediction (recorded first)
Quiet W1+W2 trades about 600 (156 + 448 by outcome-free counts). **Win rate about 91.5% against about 92% paid; payoff ratio about 0.08; PF 0.90 (0.60 to 1.25); mean -0.6c
per contract (-2.5c to +1c).** Quiet minus loud mean net +0.5c (-2c to +3c), quiet minus all +0.3c. Chance the quiet class shows PF 1.5 or better in both W1 and W2: 3%.
Streaks (`streaks.py`, independence): at a 92% win rate the longest losing run in 100 trades has mean about 1.5 and 95th percentile 2 to 3; but 8 losses in 100 are normal
(the typical bad stretch costs 8 x $9.2 = $74 against 92 x $0.7 = $64 won), so streak length is not the risk, the loss COUNT is.

## Kill rules (decided now)
On trades with a settled result, class QUIET:
1. **NOT_ENOUGH_DATA** if pooled W1+W2 trades < 150 or either half < 30 (reported with n, win, fill, PF; nothing widened).
2. **FALSIFIED** if PF < 1.5 in W1 or in W2 after fees, OR quiet-minus-loud (mean net, cents per contract) is not positive in BOTH halves, OR PF at fees x1.2 is at or under 1.0.
3. Else W3 may be read once under a written amendment; PF < 1.5 or difference not positive in W3 = FALSIFIED. A z below the deflated bar (about 5.27 at N about 728,780) is never a pass:
   at best NOT_YET_FALSIFIED.
4. **Probe flag** (information only): quiet mean net positive after fees AND quiet-minus-loud positive in both W1 and W2. Spec if it fires: 1 contract, hard limit 0.97, one order per
   series per window, kill at 40 fills with net below -$3 or PF below 1.2, worst day = 9 series x 1 contract x 0.97 about $8.7, 40 fills about 2 to 3 weeks (about 5 to 8 quiet trades per day).
5. Run once; `data/volslot1_score.json` makes a second run refuse. No slot, definition, limit or class changes after any outcome is seen.

## Expected read date
2026-11-03 (candles on file to 2026-11-03 for all nine series; W1 and W2 only).
