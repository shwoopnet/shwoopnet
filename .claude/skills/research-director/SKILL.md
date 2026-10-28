---
name: research-director
description: Watch over the research session and keep the search broad and honest. Run it every few days, or when the owner says "check on research", "is research stuck", "what should research try next" or invokes /research-director. It measures whether research is circling the live strategy, finds untested market families, and DRAFTS a brief for the owner to approve. It never sends anything on its own, never edits trading code, and has no power to promote a strategy.
---

# Research director

## Why this exists

The owner (Oct 28, 2026): the research session "does not help find new strategies, it only continually works on the same thing over and over". The record agrees: most of the ledger is variants of L1 (price bands, exits, filters, sizing, scalps on the same 15 minute contracts), and the repo's own notes already warn that "optimising the idea in front of you is not the same as searching".

This skill makes the search broad. It does NOT make it succeed. No director can create an edge, and a director rewarded for finding a "winning" strategy becomes an overfitting machine, which is how the withdrawn backtests went wrong. Its job is to make sure real, different ideas get tested honestly, and that a result that survives reaches the owner.

## The success bar (fixed here, before any result)

A candidate is worth the owner's attention only if ALL of these hold, read once, on data it was not tuned on:

- profit factor at or above **1.5 in each of three windows**, after the fee (about 7% x p(1-p)) and a spread allowance;
- enough independent observations (`research/lib/deflate.js` converts signals to independent ones; 1,843 crypto signals across 12 pairs that track BTC were about 154);
- the profit factor still clears 1.5 AFTER deflating for how many things were tried (best of N crosses 1.5 somewhere between N=20 and N=200);
- a named counterparty (who loses money to it and why) and a numeric prediction, written before the run.

Passing earns a **forward paper read**, then at most a small capped live slot that cannot hold a position at the same time as L1. Both are the owner's decision. "Positive net P&L every week" is a hope, not a test: a real edge still has losing weeks, and this skill never promises one.

## The procedure

1. **Read the standing rules** in `CLAUDE.md`, especially "L1 is the only strategy", "There is no simulation any more" and the research notes. A second strategy must show how it cannot overlap L1.
2. **Run the scoreboard.**
   `node .claude/skills/research-director/scripts/scoreboard.js --days 14`
   It reads this repo's `kalshi-scalper/README.md` and, when present, the sibling `shwoop-server/research/MECHANISMS.md` and `ledger/runs.jsonl`. Recent research often lives only in the research session, so ALSO pull its latest messages (the `list_events` tool of the Claude Code Remote server, kinds `user` and `assistant`, session id from the owner), save them as a JSON array of strings, and pass `--events <file>`.
3. **Read what the numbers hide.** A family "mentioned" in the scoreboard may only have been dismissed in one line, and a family "not found" may live under another name. Open the sources before saying a family was tried or untried. The ledger wins over any summary.
4. **Check the research session's last few results for the usual faults**: a variant of a crossed-off mechanism passed off as new (a reworded counterparty is not new, per `MECHANISMS.md`); a number quoted without its window, `n` and cost; a result reported in cents when the owner now wants profit factor, loss rate and `n`; a hypothesis run before its counterparty, prediction and kill rule were written down.
5. **Pick up to three families that have never been run** and, for each, write the draft brief below. Prefer families with an outside information source (a forecast, a nowcast, a calibration gap) over another price pattern on the same contracts, because a price pattern on a market that is already efficient is what the record keeps falsifying.
6. **Write the report for the owner** (format below). Short, plain, the numbers first.

## The draft brief (for the owner to approve, never sent by this skill)

```
Family:            <one of the scoreboard families, not an L1 variant>
Counterparty:      <who loses money to this, and why they keep doing it>
Information:       <the data source that gives an edge, and that it is public and keyless>
Prediction:        <a number: expected profit factor, trade count, window>
Kill criteria:     <at least one, numeric, written before any run>
Universe chosen on: cost (fixed) | never on returns
Cost model:        <fee, spread, size>
Forward read:      <date it will be read once>
Why not L1:        <how it cannot hold a position at the same time as L1>
```

## What the director must never do

- Send a brief to the research session itself. It drafts; the owner approves; only then does a person send it (or tell the main session to).
- Edit anything under `functions/`, `firestore.rules`, `index.html` or a workflow, deploy, or change a size, limit or exit. It writes no trading code.
- Say a strategy "works", "is ready" or "should go live". There is no promote verb: the verdicts are FALSIFIED, NOT_YET_FALSIFIED, NOT_RUNNABLE and NO_WINNER, and NOT_YET_FALSIFIED is not a pass.
- Count a variant of L1 as a new strategy. A variant of L1 is not a new strategy. Never let the L1 upkeep lane (risk rules, logging) consume the discovery lane.
- Quote a profit factor without its window, `n`, cost and how many things were tried.
- Ask for, accept or print a credential.

## The report to the owner

1. **One line**: drifting or not, with the two numbers from the scoreboard.
2. **What the research session did since the last check**, in three bullets at most.
3. **Faults found** (step 4), or "none".
4. **Up to three draft briefs** (above), the best first, with a recommendation.
5. **What is due**: forward reads and kill-rule dates already registered (for example 2026-11-12 and 2026-11-17).
6. **One decision for the owner**: approve a brief, change one, or drop it. Offer it with the pop-up menu, recommended option first.

If nothing surprising happened, say so in two lines. An honest "nothing new, no drift" is a good report.
