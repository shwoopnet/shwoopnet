# Career portfolio notes

Private working notes for résumé, interviews and a portfolio write-up. Last refreshed: 2026-10-08 (US Central). Everything below is checkable in the git history (PR numbers #300 and up) and the tests. Edit freely; keep it honest.

## One paragraph

I built and operate a small automated trading system end to end: a single-file web app, Firebase cloud functions that place real orders on Kalshi, and a research harness that tries to disprove every strategy before it is trusted. The work was done with AI assistance under my direction. The interesting parts are not the strategy (its edge is thin and unproven, and the project says so) but the safety engineering around real money, the research discipline, and how quickly it iterates from a user complaint to a tested, deployed change.

## Résumé bullets (pick what fits the role)

- Designed and shipped an automated trading bot for Kalshi 15 minute markets running 24/7 against a live account, with order idempotency across overlapping deploys, a rolling 24 hour loss stop, fail-closed behavior on any unreadable state, and an emergency "flatten all" that pauses before it sells.
- Built a research harness with a falsification-first process: every hypothesis registered with a counterparty, numeric prediction and kill criteria before any code runs; 2,582 variants tested, none passing the pre-set bar, and the result reported as such.
- Found and fixed a class of error in my own tooling: a skim rule that looked sensible but banked $150 on a net loss, caught by replaying it on 69 days of history before it shipped.
- Maintained a quality bar without a test framework: about 55 plain-node test files plus Python research tests, static checks of a 15,000 line single-file frontend, and a hand-run mutation check (66 mutants, 53 killed, 9 real gaps closed).
- Ran a security review of the frontend, rules and functions; fixed stored script injection, dependency advisories and input validation; documented what was left for the owner to decide.
- Turned vague product feedback ("simplify our UI a lot") into measured, reviewable changes: charts per market, a Running menu replacing a button panel, Central time throughout, and a page that fits one screen, with fixture-rendered screenshots for each change.
- Diagnosed and fixed production incidents quickly and wrote them down: duplicate orders from deploy overlap, missing losses on the performance page, and a GitHub Pages build that failed because a symlink was committed.

## Stories (situation, action, result)

**Money-safety under deploys.** Two server instances overlap for seconds on every deploy. A random order id only protected one call, so 15 duplicate orders once reached a real account. I keyed ids on the signal and wrote tests that state the consequence. Result: Kalshi refuses the second order, and the pattern is documented as a rule for every later change.

**A figure that was not what it claimed.** A simulated 89% win rate was quoted next to a live page that showed losses. I corrected it publicly in the project, separated live from research numbers, and added a settle sweep so every loss reaches the page. Lesson: label the source of every number.

**Say no to a good-looking idea.** The reinvest-and-skim idea sounded right. Replaying it showed the first version skimmed gross wins and drained the base. I rebuilt it to skim only new net highs, added a test for the failure, and recorded the mistake so it is not rebuilt.

**Public by accident.** While adding docs I checked what GitHub Pages publishes and found review notes and function source reachable on the public site. I excluded everything except the app and listed the cleanup caveat (already-crawled copies cannot be recalled).

## Numbers to quote (and their caveats)

| Claim | Number | Caveat |
|---|---|---|
| Variants tested | 2,582, none passing | Several are overlapping variants of the same idea |
| Backtest, L1 | about +0.9c per contract, z 1.45 | Failed its own bar; not evidence of an edge |
| Live record | 37 settled, 36 won, about +$3 | Tiny sample; one loss costs about 14 wins |
| Account size | about $344 | Real money, small amounts, by design |
| Tests | about 55 JS files, 1 Python file | Plain assert scripts, no framework |
| Mutation check | 66 mutants, 53 killed | Hand-run on the money code only |

## Skills shown

Product judgment under feedback; risk and failure-mode thinking for real money; statistical honesty (pre-registration, multiple-testing, clustering by day); Firebase (auth, Firestore rules, scheduled and callable functions); testing without a framework; static analysis of a single-file app; incident handling and write-ups; working with AI tools as a pair (scoping, reviewing, and refusing output that does not hold up).

## What I would do differently

Check what a public hosting platform publishes before the first document is added. Pre-register sizing changes as strictly as strategies. Keep live and simulated figures in separate columns from day one.

## Assets

Screenshots in `docs/mockups/` (fixture data): `kalshi-wide.png`, `kalshi-wide-menu.png`, `kalshi-phone.png`. Link to the repository history for the PR trail rather than copying code.
