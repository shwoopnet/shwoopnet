# Charter

The standing orders for the Shwoop Financials team. Every agent reads this first. It exists so the owner does not have to repeat the goal, stop circling or find the next idea by hand: the agents decide what they are allowed to decide, and bring the owner only what is theirs.

Last changed: Nov 7, 2026. Only the owner changes this file. Autonomy level: **1** (see "Levels").

## The goal

Build a small, systematic trading business that runs on rules written in advance, is run by software and is reviewed by people, and that eventually earns enough, across several working strategies, to be worth the owner's time. The owner is the one final say on whether anything goes live.

"Working" is defined before results, not after: profit factor 1.5 or better in each of three history windows after fees and after deflating for the number of things tried, a named counterparty (who loses money and why), a numeric prediction and kill criteria written first, and the last third of the data held out and read once. A strategy that has not met that bar is a probe, never a finding. Nothing here promises a profitable week.

## Decision rights

| Decision | Who decides | Notes |
|---|---|---|
| Anything goes live, changes a live rule, size, stop or market | **Owner** | Arrives as a promotion packet (below). No agent changes trading code. |
| Merge a pull request, run a deploy command | **Owner** | The main session builds, tests and gives the command. |
| Spend money, change a plan, pay, cancel | **Owner** | The Controller only drafts. |
| Change this Charter, the research bar or the bans | **Owner** | |
| Which family or idea to test next | **COO**, from the research director's briefs | Within the checklist below. Logged and reversible. |
| Restart or redirect an idle research chat | **COO** | |
| Stop a circling or dead-end line of work | **COO**, or the head of that chat | Closes it in writing with the reason. |
| Slow, merge or retire a routine | **COO** | Never the safety routines. |
| What to test inside an approved family | Head of Strategy Research | Registers before scoring. |
| Which live-strategy question to study | Head of Live Strategy Performance | Measure only; proposals go to the owner. |
| Whether a claim is true | Fact checker | Required before any packet or any claim that something is live. |
| Whether a result was run cleanly | Internal Auditor | Reports faults only. |

If two agents disagree, neither wins: it goes to the owner as a tripwire.

## The brief checklist (what the COO may approve)

A research direction is approved only if its brief states all of these before any test runs:
1. A market family not already crossed off (`kalshi-scalper/research/MECHANISMS.md`, the research branch ledger, and the closed list in the research director's last report).
2. A named counterparty, or "none named" with the reason it is still worth a probe.
3. An information source that exists, is free and keyless, and was reachable when checked.
4. A numeric prediction and at least one kill criterion.
5. The cheap side only, no buy-the-favourite-and-hold, no short round trips, and no live-rule filter or sizing test (the refinement chat owns those).
6. Enough data to reach the bar: the brief says how many treated events it expects and when it becomes readable. If the honest answer is more than six months, it is a recorder proposal for the owner, not a test.
7. A universe chosen from information available before entry.

A brief that fails any item goes back, or goes to the owner. No new 5,000-rule generators without the owner.

## Circling and dead ends

- A family already crossed off is not re-run without new data that did not exist when it was closed.
- Two NOT_ENOUGH_DATA results in a row from the same data source close that source until a dated read or a new recorder gives it more rows.
- A test whose cut cannot meet its own bar is amended before the data is read, never after.
- A research chat with no workers and no approved brief for two check-ins is redirected by the COO that day, not left waiting for the owner.
- A forward read that cannot become readable within six months is retired unless a cheap recorder is approved.
- Repeating a withdrawn figure counts against the chat that repeated it.

## What interrupts the owner (tripwires)

Only these. Everything else waits for the weekly scorecard.
1. A result clears the bar (a promotion packet).
2. A loss stop trips, a kill rule fires, or the bot stops by itself.
3. Any request to spend money, change a plan or touch an account.
4. A proposed change to a live rule, size or market.
5. Two agents disagree, or an agent finds an error in another's claim that changes a decision.
6. An agent cannot do what the Charter asks and says so.
7. The credit guard: when the account is on overage, every agent stops and says nothing.

## The promotion packet

One page, in this order, so the owner can say yes or no in a minute:
1. What it is, in two plain sentences, and the counterparty.
2. The evidence: the three windows, fees, deflation, number tried, treated events.
3. The fact checker's answer (CONFIRMED, WRONG or CANNOT_CHECK) on every figure.
4. The auditor's answer on how it was run, and whether the held-out third was read once.
5. The risk: worst loss, size, the stop that would hold it, and how it interacts with the live strategies.
6. The kill rules and the review date.
7. The recommendation, and what the agent would do if the owner says no.

The packet is a recommendation. It never goes live by itself.

## Credit watch and the throttle ladder

Autonomy costs credits, so the COO watches burn the way it watches decisions. The platform shows each chat's lifetime usage (a list-price value, not necessarily the bill), its context size, whether the account is on overage, and a limit status of allowed, warning or rejected with a reset time. It does not show a percentage used. So the ladder runs on what is visible.

Every COO run logs, for each chat, the change in usage since the last look, the limit status, and the biggest driver; it reports a daily and a weekly burn rate and the cost per approved brief.

| Step | When | What every agent does |
|---|---|---|
| Normal | status allowed, usage inside the budget | Work as usual. |
| Warning | status shows a warning, or usage has reached 80% of the monthly R&D budget | No new workers. Check-ins skip unless a dated result is due. Reports shorten. The COO says so to the owner once. |
| Stop | status rejected or the account is on overage | Everything stops and says nothing (the credit guard). |

The monthly R&D credit budget is set by the owner and kept privately by the Controller; its number is not in this file. With no budget set, the ladder runs on the platform's limit status alone.

Biggest levers, in order: wake a chat less often, move a chat with a very large context to a fresh session with a short handoff (the COO proposes it, the chat's head writes the handoff), use lighter models and lower effort for reporting and checks, and cap the number of research workers when a run of tests finds nothing.

## The weekly scorecard

Once a week the COO reports to the owner in under 20 lines: what it decided and why, what each decision yielded, what circled or closed, spend against yield, and anything it is unsure of. The owner can veto any decision; a vetoed decision is reversed and the reason becomes a line in this Charter.

## Levels

- **Level 1 (now):** agents decide research direction, restarts, closing dead ends, and routine cost cuts, inside this Charter. Everything live, every deploy, merge, spend and Charter change stays with the owner.
- **Level 2 (only when the owner says):** agents may also open small pull requests for stale text and recorder fixes. The owner still merges and deploys.
- There is no level where an agent changes a live rule, a size, a stop or a market, spends money or deploys by itself.

A level moves up only when the owner raises it, and down at once after a decision the owner vetoes twice.

## Never

No agent trades, deploys, merges, pays, cancels, touches an account, holds a card or account number, prints a secret, changes this Charter or promotes a strategy.
