---
name: health-check
description: Run the weekly health review of the Kalshi bot (strategy L1) for shwoopnet. Reads the live record (Data page figures or the Copy all orders export) against thresholds written down in advance, and returns one verdict on whether the bot is working, plus the status of the forward tests. Use when the user asks for a weekly review, a health check, "how is the bot doing", or invokes /health-check.
---

# Weekly health check of the Kalshi bot

A single verdict on whether the bot is working, read against thresholds that
were written down before anyone looked at this week's profit and loss.

(The old version of this skill reviewed the equities strategy and read a
journal that no longer exists on the site. That strategy lives in the
`shwoop-server` repo and has its own copy of the skill there. This one is
only about the Kalshi bot, `functions/kalshiLiveLib.js`.)

## Why the thresholds are written here

The numbers are easy to get and hard to read honestly. On a losing week the
temptation is to lead with whichever metric looks least bad; on a winning
week, to declare victory on a sample far too small to carry it. This file is
the answer decided in advance.

**If a number misses its threshold, that is the finding.** Do not soften it,
do not average it against something healthier, and do not go looking for a
subgroup where it passes. Gold being positive does not excuse the bot being
negative, and the bot being negative does not excuse a market that is fine.

Rules that always hold:
- **Live and research figures never share a column.** Quote forward tests
  and backtests only as information, labelled as research.
- **There is no baseline figure to compare against.** Backtest numbers have
  been withdrawn again and again, and every withdrawal moved them down. Live
  is the measurement.
- **This check only reads.** A change to a size, a series or an entry time is
  a reviewed code edit the owner decides on. Recommend it, never apply it.
- **Never ask for credentials, keys or sign-in codes.**

## Step 1: collect the numbers

The orders live in Firestore behind auth, so a Claude Code session cannot
fetch them. Ask the owner for one of these, and say exactly where it is:

1. **Best:** Bot page, Tools, **Copy all orders** (the full export, not capped
   at 150 rows; it carries series, entry time, size, price, fill, fee, result
   and what the book showed), pasted into the chat.
2. **Quick:** the Data page: the five tiles (settled trades, result, won,
   average trade, worst trade), the **By market** table, the **Entry timing
   test** card, and the growth line's low and high.

If the export is available, compute everything below from it. If only the
Data page is, say which figures could not be computed (peak-to-trough
drawdown, halves, win and loss sizes) rather than estimating them.

Also read, from the repo, the research README (`kalshi-scalper/README.md`)
for the **read dates** of the forward tests, and `CLAUDE.md` for the rules
quoted below.

## Step 2: apply the thresholds, in this order

The first one that fails is the headline.

### Sample size (gate)
- **Fewer than 100 settled bot trades since the last change to the bot's
  rule, size or markets: no verdict on the bot as a whole.** Report the
  numbers and say so. Changes to count from: gold-first sizing (2026-10-21),
  the 10 minute entry for Bitcoin, XRP and natural gas (2026-10-21, about
  19:15 UTC), and anything newer in `CLAUDE.md`.
- **Fewer than 30 settled trades in a market: that market is a count, not a
  result.** Say "too few" and do not rank it.
- **Fewer than 150 settled trades at one contract: no decision about giving
  a market a larger size** (the gold-first rule).

### Break-even
- Win rate must beat `average loss / (average win + average loss)`, computed
  from the actual trades (about 94% at today's prices). A bot below its own
  break-even win rate is losing, whatever the average trade looks like.

### Result per contract, by market (never pooled)
- **Negative net over 30 or more settled trades: losing market.** State the
  per-contract figure in cents.
- **A market that is capped at one contract** (`CAPPED_SERIES`) earns the
  size ladder back only with **150 settled trades at one contract and a result
  above +0.5c per contract in both halves** (first half and second half of its
  trades by time). Report how close each is. Never move it from this check.
- **The ladder-sized market (gold)** is flagged if its **last 100 trades net
  negative**. That is a recommendation for a reviewed code edit, not an
  automatic change.
- **Probe markets** (`PROBE_SERIES`): report the record's state, how many of
  the 200 entries the drop rule has seen, and whether it has dropped.

### Loss stop headroom
- Worst rolling 24 hours of the bot's own trades against the stop (12% of the
  base at the last review). Within **half** of the stop is a finding.

### Drawdown
- Peak-to-trough on the growth line, against the account, not alone.
  **More than about 20% of the account** means sizing is too aggressive
  whether or not the bot is net positive. A single trade that costs more than
  10% of the account is a finding about the size that placed it.

### The exit at 25c
- Report how many positions fell to 25c, how many it sold, the realised
  result, and what holding would have done where the market result is known
  (Copy all stats carries this). It is a risk tool, not an earner; the
  research has found the line barely matters on the 10 minute markets, so
  only flag it if sells lose clearly more than holding over 20 or more
  touches.

### Regression
- Compare with last week's figures if the owner has them. **A metric moving
  materially the wrong way is a finding even inside its threshold.**

## Step 3: forward tests (information, never a verdict before its date)

List each forward test that is open, its read date, and how far along it is.
Today's set, from the research README: FWD5 (probe markets), FWD6 (best hours),
FWD7 and FWD8 (the 10 minute entry), FWD9 (spread filter on natural gas),
FWD10 (crowded windows), FWD2, FWD3 and GOLD1-F. **Do not judge one before its
read date**; they state their small samples up front and may end as
`NOT_ENOUGH_DATA`. The Entry timing test card on the Data page is a view of
the 10 minute entries, not a verdict: its two groups are not the same markets.

## Step 4: deliver one verdict

Lead with one sentence: working, not working, or too early to say. Then the
supporting numbers, by market. Then **one** recommended action. One action,
not a list: a review that produces five action items produces none.

## What this check cannot tell you

- **Whether an edge is real or luck.** Thirty trades stops guessing; only many
  weeks gives confidence. Wins here are about 6c and losses about 90c, so one
  loss erases about 14 wins and a short run can say almost anything.
- **Whether it survives a change of market conditions.** Every trade so far is
  from a few weeks of one environment.
- **Capacity.** The account is small on purpose.

Say so when it matters. A verdict that overstates its own confidence is worse
than no verdict.
