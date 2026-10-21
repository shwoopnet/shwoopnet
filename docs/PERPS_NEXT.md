# Perps: a leverage test and a going-live checklist (design only, nothing built or applied for; 2026-10-21)

Perps are **not live and nothing is wired**. Three earlier tests (PERP1 to PERP3, `kalshi-scalper/README.md`) found no edge that survives costs after 2022. Leverage does not create an edge, it multiplies the result and adds a way to lose everything (liquidation). So the test below is about survival, and it only matters if an unlevered edge exists first.

## Part 1: the leverage test (PERP4, to be registered in the research README BEFORE any code runs)

**Question.** If PERP1's daily trend rule has an edge, how much leverage can it carry without being liquidated, and does leverage turn the thin post-2022 result positive after funding?

**Fixed before running:**
- Rule: PERP1 exactly (same four markets, same entries, same stop), no new parameter.
- Leverage 1x, 2x, 3x, 5x. Liquidation when the position loses `1 / leverage - 0.5%` of its value (a 0.5% maintenance margin, adjusted to the real figure once Kalshi's margin article is read).
- A trade that touches liquidation inside a day is closed there, at a loss of the whole margin; intraday highs and lows are used, not closes.
- Costs: PERP1's (0.12% a side fee, 0.01% slippage, 0.02% a day funding), charged on the leveraged notional.
- Primary window: **entries from 2022 on** (the early crypto years carried PERP1; they are reported as information only).
- Reported per leverage: mean net per trade on margin, share of trades liquidated, worst run of losses, and the month-clustered z against the placebo draws PERP1 used.

**Bar (stated now).** At least 150 trades in the primary window; mean net above zero with month-clustered z of at least 2.4 (one more try); above the placebo 95th percentile; positive in both halves; positive with costs x1.2; and **liquidated on under 5% of trades at the leverage called best**. No leverage can pass if 1x does not.

**Prediction.** 1x is about 0.0% a trade (PERP1's own post-2022 reading), so every leverage is `FALSIFIED`, with liquidations on 10% to 25% of trades at 5x (about 80% confident). Recorded first so a pass counts as a surprise.

## Part 2: going live, in the order it would have to happen (each step needs your go)

1. **Read, no code.** Kalshi's perps eligibility, fee, margin and liquidation articles end to end. Stop if fees or rules differ from `docs/PERPS_THEORY.md`.
2. **Apply for access** (you, with your own details; I never see credentials). Perps use a separate margin balance, so fund only an amount you can lose.
3. **Wait for a passed test.** Nothing below starts unless PERP4 (or a better idea) returns `NOT_YET_FALSIFIED` on recorded data, and then it only earns a small slot.
4. **Hard limits in code, not settings** (the same rule as `L1_SERIES`): one named market, a leverage ceiling of 2x, a fixed dollar cap per position, a daily loss stop, and a liquidation buffer check before any order (refuse if the stop is farther than the liquidation price).
5. **A separate trade-only API key** for the margin account (no withdrawal permission), stored as a Firebase secret like the existing key.
6. **Its own kill switch and an exit watch that only reduces exposure**, built to the same invariants as the L1 exit watch (reads the live position first, never opens the opposite side, fixed client order ids, never retries a lost answer).
7. **It must not overlap L1** (CLAUDE.md "L1 is the only strategy"): a separate account satisfies the position rule, and the review must show why it is a different bet, not a different lane of the same one.
8. **First live period at the smallest size**, read against the pre-registered prediction at a fixed date, with a promotion and demotion rule written before it starts.

Nothing in this file is applied. Do not treat the numbers in Part 1 as results: it is a design.
