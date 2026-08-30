---
name: health-check
description: Run the weekly strategy health review for shwoopnet — reads the live trading metrics (exit-type mix, profit factor, drawdown, trade count) against written thresholds and returns a single verdict on whether the strategy is working. Use when the user asks for a weekly review, a strategy health check, "how is the strategy doing", or invokes /health-check.
---

# Weekly strategy health check

A single verdict on whether the trading strategy is actually working,
read against thresholds decided in advance.

## Why thresholds are written down here

The numbers are easy to get and hard to read honestly. On a losing week
the temptation is to find the metric that looks least bad and lead with
it; on a winning week, to declare victory on a sample far too small to
support it. Both are normal, and both are why the thresholds live in this
file — decided when nobody was looking at a P&L — rather than being
judged fresh each time.

**If a number misses its threshold, that is the finding.** Do not soften
it, do not average it against something healthier, and do not go looking
for a subgroup where it passes.

## Step 1 — collect the numbers

These live in Firestore behind auth, so they can't be fetched from a
Claude Code session. Ask the user for them, naming exactly where each one
is. Six numbers, all visible in under a minute:

**Journal page:**
1. **Reached Trail/Breakeven** — the % and the "N of M tracked trades" underneath
2. **Profit Factor** — the card value
3. **Win Rate** — the % and total trade count
4. **Account Growth chart** — the *Max drawdown* figure in its legend

**Labs page:**
5. **Live so far** — the profit factor and closed-trade count, under both
   the equities and crypto Method sections

**Trade Overview:**
6. **Needs You** — anything sitting unacknowledged (e.g. a pending profit
   sweep)

Also ask: **how many of those trades are post-fix?** Trades from before
2026-08-29 predate the market-order chase fix and the weekend's
refinements, and mixing them in makes the strategy look worse than it
currently is. If the user isn't sure, treat the whole sample as suspect
and say so rather than guessing.

## Step 2 — apply the thresholds

Work through these in order. The first one that fails is the headline.

### Sample size — gate everything else
- **< 20 post-fix closed trades → INSUFFICIENT DATA. Stop here.**
  Report the numbers, but state plainly that no verdict is possible yet
  and that acting on them is noise-chasing. This threshold is the app's
  own `LABS_MIN_TRADES_FOR_CONFIDENCE`, not an invented one.
- ≥ 20 → continue.

### Exit-type mix (`Reached Trail/Breakeven`) — the primary metric
This is the leading indicator, ahead of profit factor, because it measures
whether entries produce genuine follow-through rather than whether a small
sample happened to land well.

- **< 30%** — the entry signal is not producing follow-through. The
  problem is upstream in what triggers an entry; no amount of exit tuning
  fixes it. This is the finding, even if profit factor looks fine.
- **30–50%** — marginal. Watch another week before concluding.
- **> 50%** — the mechanism is working. This was ~6% (2 of 32) pre-fix,
  so a jump here is the first real evidence the chase bug was the whole
  problem.

### Profit factor
- **< 1.0** — losing money. Nothing else matters this week.
- **1.0–1.5** — marginally profitable; costs and slippage could erase it.
- **> 1.5** — genuinely working.

**There is no backtest baseline to compare against. That is the most
important line in this file, and it is a deliberate absence.**

Every figure this section used to carry has been withdrawn:

| Figure | Withdrawn because |
|---|---|
| equities 2.71 | frozen number that did not reproduce |
| crypto 2.35 / 4.08 | crypto charged equities' trading costs |
| equities 1.24 / 1.48 / 0.96 | never corrected for the `rangeHigh` entry lookahead; the strategy is withdrawn entirely |
| crypto 1.93 → 1.94 → 1.20 | measured before the entry-pricing fix |
| crypto 1.05 | measured before the engine-parity fix (no early breakeven, trailing from the intrabar high) |

So do **not** judge live performance against a backtest number. There
isn't one, and inventing a comparison is worse than having none — that
substitution is the specific failure this skill exists to prevent, and it
was sitting in this file's own instructions until Aug 2026.

Judge on the thresholds above (< 1.0, 1.0–1.5, > 1.5) and on the
absolute arithmetic: does the per-trade edge exceed the round-trip cost,
measured rather than assumed? Crypto's measured spread is 0.200% median,
so its real round trip is 0.700%, not the 0.50% the backtest deducts.

If a corrected backtest figure is ever produced, it goes in
`CLAUDE.md` first and here second — never only here.

Both remain upper bounds. The crypto 25bps is the taker fee and excludes
spread, which is widest on the alts producing most of its signals, and it
is one 60-day window on a long-only trend strategy — in crypto that
measures the window at least as much as the strategy.

Compare live against backtest explicitly. A large gap that persists past
20 trades means the backtest is not describing reality, and the backtest
is the thing that's wrong.

### Max drawdown
- Judge against the account size, not in isolation. **A drawdown greater
  than ~20% of the account** means position sizing is too aggressive
  regardless of whether the strategy is net profitable.

### Both strategies have failed the gate
The rule set in advance was **1.5 across three windows**. Neither has
cleared it, and both decline monotonically as the window lengthens:

| | 30d | 60d | 180d | 365d |
|---|---|---|---|---|
| Equities | 1.48 | 1.24 | — | 0.96 (6 of 16) |
| Crypto | — | 1.94 | **1.20** | **1.20** (1,843 signals) |

Equities was also measured with a failed-breakout exit at 60 days: 1.12,
worse than without it.

Equities keeps degrading with window length. Crypto does not: 1.20 at both
180 and 365 days, identical across 801 and 1,843 signals, so that estimate
has converged. 1.94 was the recent window flattering it.

**Crypto's failure is a cost failure, and that distinction matters for what
to do next.** Its gross edge is +0.62% a trade and cost takes 81% of it,
leaving +0.12% against a 0.50% round trip that still excludes spread. The
signal is real and stable; it does not survive paying a taker fee on both
sides. Equities is not the same case — gross +0.19% against a 0.10% cost,
so cost takes half, and it degrades with window length regardless.

If a future review is asked whether either is worth restarting, the honest
answer for crypto turns on execution cost, not on signal quality.

**This is the finding, and no weekly figure changes it.** A good week on
twenty trades is not evidence against a 799-signal measurement. If a review
is being run in the hope that live results overturn this, say so plainly
instead.

### Per-symbol expectancy — do not act on it
The Labs per-symbol table looks like it identifies which names the
strategy works on. It does not. Delaying entry by a single bar reverses
the sign on roughly half the universe (MARA −0.30% → +0.54%, COIN −0.24% →
+0.24%, LCID +0.03% → −0.39%, DKNG +0.15% → −0.20%). A ranking that
unstable under a one-bar change is sampling noise, and trimming the
universe to its top rows is fitting that noise.

### Regression check
Compare against last week's numbers if the user has them. **A metric
moving materially in the wrong direction is a finding even if it's still
inside its threshold** — that's the early warning the absolute levels miss.

## Step 3 — deliver one verdict

Lead with a single sentence: is the strategy working, not working, or is
it too early to say. Then the supporting numbers. Then at most **one**
recommended action.

One action, not a list. A weekly review that produces five action items
produces zero, because none of them get done.

## What this check cannot tell you

- **Whether the edge is real or luck.** Twenty trades is enough to stop
  guessing, not enough to be confident. Several months is confidence.
- **Whether it survives a regime change.** Every post-fix trade so far
  comes from one market environment.
- **Anything about capacity.** These strategies trade deliberately
  volatile, retail-heavy small caps. Returns at $4k say little about
  returns at $400k, where your own orders start moving the tape.

Say so when it matters. A verdict that overstates its own confidence is
worse than no verdict.

## Related decisions this feeds

- **The 50/50 profit sweep split** (`shwoop-server/src/profitSweep.js`) is
  explicitly flagged for revisit once 20+ post-fix trades give a measured
  return. If the exit mix and profit factor both clear their thresholds
  with a real sample, that's the trigger — reconsider the split
  deliberately, with data.
- **Going live with real money** was gated on watching the first 5–10 real
  signals post-fix. That gate is no longer sufficient on its own: 5–10
  trades cannot distinguish a 1.24 profit factor from a 1.0, and 1.24 is
  what the corrected backtest actually measures. The gate should be a
  demonstrated edge larger than the cost model's own uncertainty, which
  needs a real sample, not a handful of signals.
