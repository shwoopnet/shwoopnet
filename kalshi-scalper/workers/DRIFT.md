# DRIFT: the bot's live orders against L1's history rule on the same markets and minutes (newest first; aggregates only; `python -m scalper.drift run`)

## 2026-10-29 15:46 CT (report window 2026-09-29 13:17 CT to now; history candles up to 2026-10-29 15:45 CT)

**1. Coverage.** Live orders sent (filled or not) against the history rule at the order's own look; history entries at the bot's look the bot did not take, by reason.

| Window | Market | Live orders | Match | History: no entry | History: other side | No candle | Mismatch share (of those with a candle) | History entries | Taken | Not live yet | Paused (XRP) | Bot not trading | One crypto per window | Smooth gate | Other | Other share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7d | gold | 116 | 105 | 11 | 0 | 0 | 9.5% | 118 | 105 | 0 | 0 | 0 | 0 | 0 | 13 | 11.0% |
| 7d | Bitcoin | 15 | 15 | 0 | 0 | 0 | 0.0% | 151 | 15 | 0 | 0 | 1 | 61 | 73 | 1 | 0.7% |
| 7d | Ethereum | 22 | 19 | 3 | 0 | 0 | 13.6% | 159 | 19 | 0 | 0 | 4 | 58 | 76 | 2 | 1.3% |
| 7d | Dogecoin | 144 | 132 | 12 | 0 | 0 | 8.3% | 192 | 132 | 0 | 0 | 4 | 32 | 0 | 24 | 12.5% |
| 7d | XRP | 81 | 66 | 15 | 0 | 0 | 18.5% | 105 | 66 | 0 | 27 | 2 | 5 | 0 | 5 | 4.8% |
| 30d | gold | 316 | 291 | 25 | 0 | 0 | 7.9% | 568 | 291 | 161 | 0 | 85 | 0 | 0 | 31 | 5.5% |
| 30d | Bitcoin | 249 | 231 | 18 | 0 | 0 | 7.2% | 657 | 231 | 93 | 0 | 161 | 65 | 73 | 34 | 5.2% |
| 30d | Ethereum | 175 | 163 | 12 | 0 | 0 | 6.9% | 796 | 163 | 304 | 0 | 151 | 65 | 76 | 37 | 4.6% |
| 30d | Dogecoin | 174 | 159 | 15 | 0 | 0 | 8.6% | 810 | 159 | 573 | 0 | 4 | 41 | 0 | 33 | 4.1% |
| 30d | XRP | 117 | 99 | 18 | 0 | 0 | 15.4% | 752 | 99 | 607 | 27 | 2 | 8 | 0 | 9 | 1.2% |

**2. Slippage** (held filled orders: price paid minus the history candle's closing ask of the same side at the decision minute, cents; positive = paid more).

| Window | Market | Priced | Mean | Median | 10th / 90th pct | <=-2c | -1c | 0c | +1c | +2c | >=+3c |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7d | gold | 73 | +0.53 | +0.4 | -0.8 / +2.1 | 4 | 4 | 34 | 19 | 8 | 4 |
| 7d | Bitcoin | 9 | +0.61 | +0.7 | n/a | 0 | 1 | 1 | 6 | 1 | 0 |
| 7d | Ethereum | 13 | +1.07 | +0.8 | +0.0 / +3.2 | 0 | 0 | 5 | 5 | 2 | 1 |
| 7d | Dogecoin | 101 | +0.82 | +0.5 | -0.2 / +2.2 | 1 | 7 | 43 | 30 | 12 | 8 |
| 7d | XRP | 52 | +0.98 | +1.0 | -0.2 / +2.7 | 1 | 1 | 18 | 16 | 10 | 6 |
| 30d | gold | 193 | +0.60 | +0.5 | -0.5 / +2.0 | 10 | 8 | 83 | 66 | 16 | 10 |
| 30d | Bitcoin | 146 | +0.44 | +0.4 | -0.3 / +1.4 | 7 | 6 | 70 | 50 | 10 | 3 |
| 30d | Ethereum | 103 | +0.87 | +0.7 | -0.1 / +2.0 | 1 | 4 | 44 | 36 | 11 | 7 |
| 30d | Dogecoin | 123 | +0.86 | +0.6 | -0.2 / +2.2 | 2 | 8 | 51 | 37 | 16 | 9 |
| 30d | XRP | 76 | +1.76 | +1.0 | -0.1 / +4.0 | 2 | 2 | 25 | 21 | 14 | 12 |

**3. Result drift.** Live loss rate (filled, settled; an exit counts as a loss) against the history rule at the bot's look on the same market and the same US Central days; and on matched orders, live against the history rule's own outcome for the same markets.

| Window | Market | Live settled | Live losses | Days | History entries those days | History losses | Matched | Live loss rate (matched) | History loss rate (matched) | Live orders the history rule would not take: settled, losses |
|---|---|---|---|---|---|---|---|---|---|---|
| 7d | gold | 76 | 4 (5.3%) | 7 | 118 | 6 (5.1%) | 66 | 6.1% | 6.1% | 10, 0 (0.0%) |
| 7d | Bitcoin | 9 | 0 (0.0%) | 4 | 80 | 2 (2.5%) | 9 | 0.0% | 0.0% | 0, 0 (n/a) |
| 7d | Ethereum | 15 | 2 (13.3%) | 4 | 76 | 10 (13.2%) | 12 | 16.7% | 16.7% | 3, 0 (0.0%) |
| 7d | Dogecoin | 105 | 4 (3.8%) | 8 | 192 | 9 (4.7%) | 95 | 3.2% | 2.1% | 10, 1 (10.0%) |
| 7d | XRP | 60 | 9 (15.0%) | 6 | 79 | 4 (5.1%) | 49 | 6.1% | 4.1% | 11, 6 (54.5%) |
| 30d | gold | 200 | 9 (4.5%) | 17 | 380 | 19 (5.0%) | 180 | 4.4% | 4.4% | 20, 1 (5.0%) |
| 30d | Bitcoin | 155 | 11 (7.1%) | 15 | 392 | 26 (6.6%) | 147 | 6.1% | 5.4% | 8, 2 (25.0%) |
| 30d | Ethereum | 113 | 9 (8.0%) | 12 | 325 | 27 (8.3%) | 104 | 8.7% | 5.8% | 9, 0 (0.0%) |
| 30d | Dogecoin | 129 | 6 (4.7%) | 10 | 248 | 13 (5.2%) | 116 | 3.4% | 2.6% | 13, 2 (15.4%) |
| 30d | XRP | 86 | 12 (14.0%) | 8 | 129 | 8 (6.2%) | 72 | 8.3% | 6.9% | 14, 6 (42.9%) |

**Flags:** XRP 30d: slippage mean +1.76c on 76 held orders (above 1c)

Aggregates only; raw rows stay in the scratchpad. A live order the history rule would not take is usually a quote that moved between the candle's close and the send a few seconds later; the bot reads the market object, the history reads the minute candle. Information only; nothing here changes a live rule.

