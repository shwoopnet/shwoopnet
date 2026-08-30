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
- **> 1.5** — genuinely working. For context the backtest claimed 2.71
  (equities) / 2.35 (crypto), and live ran 0.55 pre-fix.

Compare live against backtest explicitly. A large gap that persists past
20 trades means the backtest is not describing reality, and the backtest
is the thing that's wrong.

### Max drawdown
- Judge against the account size, not in isolation. **A drawdown greater
  than ~20% of the account** means position sizing is too aggressive
  regardless of whether the strategy is net profitable.

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
  signals post-fix. This review is how that gate gets judged.
