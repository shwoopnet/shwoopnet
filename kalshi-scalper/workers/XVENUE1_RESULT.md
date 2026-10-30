# XVENUE1: do Kalshi and Polymarket resolve the same 15 minute window differently? (no trade, 2026-10-30)

Measurement only. No rule, no trade, no PF, 0 tries, N unchanged (about 728,658). Public data only. Nothing live touched, no recorder built.

## Data reachability
- Polymarket gamma API (`gamma-api.polymarket.com/events?slug=...`) and the CLOB price history (`clob.polymarket.com/prices-history`) were both reachable from this session. No allowlist change needed.
- Slug pattern: `btc-updown-15m-<start unix>` and `eth-updown-15m-<start unix>`, start = Kalshi close minus 900 s. Up/Down outcome from `outcomePrices` once `umaResolutionStatus` is `resolved`. All 16,222 requested windows existed and were resolved cleanly (0 missing, 0 unresolved).
- Rule text (market description, read from the API): "Up" if the Chainlink BTC/USD (ETH/USD) data stream price at the end of the range is greater than or equal to the price at the start. That is a point-in-time comparison, not a time-weighted average (the NEWH16 digest line saying "time weighted average" is wrong; corrected here). Kalshi settles on a different index (CF Benchmarks, 60 second averages), so the sources and the averaging both differ.
- Kalshi side: `l1b`, `book` and `fresh` sqlite files, 2026-08-06 to 2026-10-30. The settled `result` was read ONLY for the agreement count. Spot: Coinbase public 1 minute candles.

## 1. Agreement (all Kalshi windows with a Polymarket twin: 16,222)
| Asset | Joined | Agree | Disagree | Share | Kalshi YES / PM Down | Kalshi NO / PM Up |
|---|---|---|---|---|---|---|
| Bitcoin | 8,111 | 7,985 | 126 | 1.55% | 69 | 57 |
| Ethereum | 8,111 | 8,003 | 108 | 1.33% | 60 | 48 |
| All | 16,222 | 15,988 | 234 | 1.44% | 129 | 105 |

The split between the two directions is even, so there is no one-way bias.

## 2. Where the disagreements sit (Coinbase 1 minute close at the Kalshi close vs the Kalshi strike, basis points)
| Asset | Disagreement median | p90 | All windows median | Within 1 bp: share of disagreements / share of all windows / disagreement rate inside | Within 5 bp |
|---|---|---|---|---|---|
| Bitcoin | 1.20 | 3.52 | 7.76 | 41% / 8% / 8.2% | 92% / 36% / 3.9% |
| Ethereum | 1.41 | 4.25 | 10.07 | 35% / 6% / 8.5% | 92% / 28% / 4.4% |

Disagreements cluster at the strike as expected (99% within 10 bp), but even within 1 bp the venues disagree only about 8% of the time, and 92% of disagreements are within 5 bp, where the price of a side is rarely 80c.

## 3. Both venues 80c or higher on the same side, 6 minutes before the close
Kalshi: the 1 minute candle ending at close minus 360 s, YES ask 0.80 or higher or NO ask (1 minus YES bid) 0.80 or higher. Polymarket: the last price in the history for the Up token at or before that minute and within 150 s (a last-trade series at 1 minute fidelity, not a true book midpoint; this is a caveat).

| | Count |
|---|---|
| Windows with a Kalshi side at 0.80 or higher | 9,161 |
| Polymarket had no fresh price | 46 |
| Polymarket on that side under 0.80 (not both) | 2,179 |
| **Both 80c or higher** | **6,936** (Bitcoin 3,324, Ethereum 3,612) |
| Resolved differently | **37 = 0.53%** (Bitcoin 16, Ethereum 21) |

The 37 are listed by ticker in the scoring output (`src/scalper/xvenue1_score.py`). Their Kalshi prices run 0.80 to 0.96.

## Reading
Two venues, two indexes, disagree on about 1.4% of 15 minute windows, always within a few basis points of the strike. When both venues already price one side at 80c or higher at 6 minutes, they disagree on 0.53% of windows (37), well under the 2% gate, so the registered condition for describing a cross-venue structure is NOT met (share 0.53% is below 2%; n of 37 meets the 15 floor but the share does not). A 0.53% disagreement rate cannot pay a second venue's fee plus a leg that fills on only one venue. Nothing is proposed, and no Polymarket book recorder is needed on this evidence. Information only.

Caveats: Polymarket prices are last-trade history, not a quoted book; the 0.80 threshold uses Kalshi's candle ask and so is not a fill; one pass, no variants.

## Files
`src/scalper/xvenue1.py` (fetch and join), `src/scalper/xvenue1_score.py` (scoring). Data stays in `data/` (ignored).
