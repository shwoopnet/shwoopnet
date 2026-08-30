---
name: strategy-audit
description: Interrogate a trading-strategy number before acting on it — audit the backtest code for the defects that inflate results, run the arithmetic that exposes an edge too thin to trade, then give a go/no-go with a decision rule committed in advance. Use whenever a backtest figure, profit factor, expectancy or win rate is quoted, whenever the user asks whether to trade a strategy, go live, fund a real account, change position sizing, or add a filter, and whenever a strategy change needs verifying — even if they only mention the number in passing and don't ask for an audit.
---

# Strategy audit

A number is a claim, not a fact. This is how the claim gets tested before
money moves.

## Why this exists

In a single weekend, four backtest figures for these strategies turned out
to be wrong. **Every one of them was wrong in the flattering direction:**

| Claimed | Actual | Cause |
|---|---|---|
| PF 13.26, all 16 symbols positive | 0.94 | Entry booked at a price you couldn't have got |
| PF 2.71 "across 5 windows" | 1.24 | Frozen number nobody re-ran; doesn't reproduce |
| PF 4.08, all 12 pairs positive | 1.93 | Crypto charged equities' trading costs |
| Live PF looked like the strategy | risk was 2x | Duplicate orders; real size ≠ intended size |

None of them looked wrong. That is the whole problem — a broken backtest
does not announce itself, it produces a plausible number, and plausible
numbers get acted on.

So the working assumption here is inverted: **a favourable number is
evidence of a bug until it survives an audit.** That sounds paranoid until
you notice that the four errors above were found by looking, and zero of
them were found by the numbers looking suspicious.

## Step 1 — establish what was actually measured

Before analysing anything, pin down what produced it. Ask, or read it out
of the code:

- Which **configuration**? Optional filters and checkboxes change the
  result and are easy to leave on. The 13.26 came from an option that has
  never run live.
- Which **window**, and how many? One window is one regime.
- Which **universe**, and has it changed since the number was set?
- Is this a **live measurement or a stored constant**? `LABS_BACKTEST_PF`
  in `index.html` is hardcoded. A stored number that can't be reproduced
  right now is not a measurement, it is a memory.

If the answer to any of these is "not sure", stop and find out. An audit of
a number whose provenance is unknown is theatre.

## Step 2 — run the arithmetic

```bash
node .claude/skills/strategy-audit/scripts/strategy-arithmetic.js \
  --pf 1.93 --wins 125 --losses 155 --expectancy 0.44 --cost 0.50
```

`--cost` is the round-trip cost already deducted, in percentage points
(`ORB_SLIPPAGE_BPS` and `CRYPTO_SLIPPAGE_BPS` in `index.html`, × 2 legs,
÷ 100).

A backtest summary shows profit factor, win rate and expectancy but not
average win and average loss — and those are exactly where defects show.
The script recovers them, because profit factor and expectancy are two
equations in two unknowns.

To verify a change did what it claimed, use `--compare`. A per-trade cost
change should move expectancy by *exactly* that amount:

```bash
node .../strategy-arithmetic.js --compare \
  --before-pf 4.08 --before-expectancy 0.84 --before-wins 153 --before-losses 127 \
  --after-pf 1.93  --after-expectancy 0.44  --after-wins 125 --after-losses 155 \
  --cost 0.50 --cost-change 0.40
```

An exact match is strong evidence the change did one thing and only that
thing. A mismatch means something else moved too — find out what before
trusting either number.

## Step 3 — read the code for these five defects

The arithmetic narrows where to look; it does not prove anything. Open the
source. Each of these has already happened here.

**1. A fill price you could not have got.**
The single most productive check. Trace the entry price back to the bar
that produced it: could it have been known at the moment of the decision?
The confirmation-bar option in `runIntradayBacktestSimulationAsync`
(`index.html`) waited for the next bar to close beyond the range — thereby
selecting for a favourable move — and then booked the fill at the *original*
breakout level, handing every trade that move for free. PF 13.26. The tell
was an average loss barely above slippage: a trade entered below its real
fill price rarely reaches its stop.

**2. A cost model borrowed from the wrong market.**
`applyCryptoBacktestSlippage` deducted `ORB_SLIPPAGE_BPS` — 5bps, the
*equities* number. Alpaca crypto charges a percentage taker fee per side
plus a far wider spread. Not an approximation, the wrong quantity. Check
that each market has its own constant and that it traces to a published fee
schedule rather than to whatever made the output look good.

**3. An edge smaller than its own cost assumption.**
Equities measures +0.09% expectancy against a 0.10% modeled round trip. The
edge is contained inside the error bar of a single assumption, so being
modestly wrong about fills erases it. The script flags this. **Under ~2x
cost, re-run with the cost raised 50%** — if the edge doesn't survive, what
was measured was the assumption.

**4. One window mistaken for evidence.**
Every figure above came from a single ~60-day window. For a long-only trend
strategy in crypto this is close to meaningless on its own: a trending
window makes any breakout system look good. Three non-overlapping windows
(the lookback selector goes to 365) or the number is provisional.

**5. Live exposure that isn't the intended exposure.**
Fifteen trades ran at double the intended size because the same signal was
submitted twice, and that was discovered from a journal banner rather than a
risk alert. Before comparing live against backtest, confirm the live sample
is what you think: check the broker's own order history, not just the
journal.

### Two tells worth internalising

- **Every symbol positive.** 16 of 16 and 12 of 12 both turned out to be
  bugs. A real strategy has names it doesn't work on. A clean sweep is a
  finding about the tool.
- **A per-symbol table is not a ranking.** Delaying entry by one bar
  reversed the sign on half the universe (MARA −0.30% → +0.54%, LCID
  +0.03% → −0.39%). Never trim a universe from that table; it is noise with
  decimal places.

## Step 4 — sample size, honestly

Trade count flatters. 406 signals across 16 correlated small caps in one
regime is closer to **60 independent days** than 406 independent trades,
because a market-wide move produces many of them at once. Divide by
symbols, then ask how many genuinely independent periods remain. The 20-
trade gate (`LABS_MIN_TRADES_FOR_CONFIDENCE`) is a floor for noticing, not
for concluding.

## Step 5 — deliver a verdict and a rule

Lead with one sentence: **trade it, don't trade it, or not yet.** Then the
evidence. Then — and this is the part that does the work — **a decision rule
written before the next run**, naming a threshold and what happens on each
side of it.

The demonstrated failure mode here isn't bad arithmetic, it's plausible
numbers surviving unexamined and then getting defended. A threshold
committed to in advance is the only real defence, because after a result
arrives there is always a reason to keep going.

**There are currently no baselines to judge against.** Every figure this
line used to carry has been withdrawn: 2.71, 2.35 and 4.08 first, then
1.24 / 1.48 / 0.96 for equities (never corrected for the `rangeHigh`
entry lookahead, and the strategy is withdrawn entirely), then 1.93 /
1.94 / 1.20 for crypto (measured before the entry-pricing fix), then 1.05
(measured before the engine-parity fix).

That is six withdrawals, and the honest state is an empty baseline rather
than the most recent survivor. If you need a number to compare against,
re-measure it — and put it in `CLAUDE.md` first, so this file cannot be
the only place a stale figure lives.

This line itself carried 1.24 and 1.93 as "current" for weeks after both
were withdrawn. A skill that quotes a number is a skill that goes stale,
which is why the rule is to point at the source rather than restate it.

## What this cannot tell you

Say so plainly when it applies, rather than letting a clean audit imply
more than it earned:

- **Whether the edge is real.** A backtest that survives every check above
  is a backtest that isn't obviously broken. That is not the same as an
  edge, and only forward performance settles it.
- **Whether it survives a regime change.** Every measurement here comes
  from one market environment.
- **Anything about capacity.** These strategies trade deliberately volatile,
  retail-heavy names. Returns at $4k say nothing about $400k, where your own
  orders move the tape.
