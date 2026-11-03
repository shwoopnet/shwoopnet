# COST1 registration (Strategy Research V2 worker, 2026-11-03, written before any number below was computed)

Owner assignment via main. Measurement and desk research only. No live code, no functions/, no L1, no OICORE, no promote verb, no new try (N unchanged, about 728,700). Nothing here is scored as a strategy.

## What will be computed (no outcome claim is made here)

1. **Fee table.** Kalshi taker fee = ceil_to_cent(0.07 x C x p x (1-p)) per order, for C = 1, 5, 10, 50, 100 at every price 1c..99c: total fee in cents, fee per contract in cents, fee as a percent of price paid. Rounding effects at 1c..5c shown separately (a 1c contract pays 1c, i.e. 100% of price).
2. **Maker fee.** Look up Kalshi's published fee schedule (web), and any API fields (maker_fee, fee_waiver, fee_type, fee_multiplier on series). State what is confirmed and what is not. Where it cannot be fetched, the number is labelled unverified and a sensitivity (maker = 0, 0.25 x taker, taker) is shown.
3. **Spread by price band.** From candles already held (the same market list tstop1.load uses: history, fresh and replicated 15 minute data), the median (ask - bid) at the entry-style look, by price band of the YES mid and by series class (crypto, gold/commodity, FX, other 15 minute). Information only.
4. **Round-trip cost by band.** Hold-to-settlement = one fee. Buy then sell = two fees plus the spread crossed. Cheapest bands named.
5. **Break-even win-rate excess by band** (1-5c, 5-15c, 15-30c, 30-70c, 70-85c, 85-97c, 97-99c), at C = 1 and C = 10: the win rate minus the price paid that makes a held contract net zero, at (a) taker, (b) optimistic maker at the bid (maker fee, no spread crossed), (c) maker with a fill-probability haircut taken from the held MAKER/QUEUE evidence in the README (MAKER2, MAKER3, P2/bookmaker, L1Q1 and MAKER5 registered, not read). The haircut is a quoted README number, not a new estimate.
6. **Candidates that could flip.** A list of previously "falsified at taker cost" families (cited by README id) whose recorded net edge was within the taker-minus-maker fee gap, with the break-even they would need. They are NOT re-scored.

## Rules
- Code `src/scalper/cost1.py` and `tests/test_cost1.py` committed with this file or after, before the result file. Result `workers/COST1_RESULT.md` and a README ledger entry.
- Spread medians use only candles with a two-sided quote (bid > 0, ask < 1, ask >= bid).
- No em dashes. No outcome of any strategy is computed.
