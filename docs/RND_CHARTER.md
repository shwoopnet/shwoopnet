# R&D operating charter (DRAFT for the owner's review)

**Status: DRAFT (Nov 11, 2026). It binds nobody until the owner merges it.** Once merged it binds the research chat (V2) and the live-performance chat (Refinement). It sits under `docs/CHARTER.md`, which only the owner changes; where they differ, the Charter wins. The owner made four decisions in a popup on Nov 11, 2026 (pace, concurrency, closing a family, the owner gate); they are written in below. Written at the owner's request: "i think we need to define stuff for the R&D team otherwise they're going to get carried away."

**Politics and parlays:** the owner's Nov 11, 2026 answers (probe sizes, loss caps, kill and return rules, the 14 day cap) are in `docs/POLITICS_RULES.md`.

## 1. Mission

Find strategies that clear the owner's bar, not variants of what we already run.

## 2. Scope

**May:** research on public data; shadow rules; pre-registered tests; recorders that stay inside the Charter's 250 runner minutes a month.

**Out of bounds, without the owner:**
- any live change (rule, size, stop, market), even a 1 contract probe;
- any new spend;
- any new venue, or any new recorder or anything that would take the month over the Charter limit of 250 runner minutes;
- any account, key or credential;
- committing live trading figures (results, order details, balances, sizing figures of our real account) to the repo or any branch, in a doc, a comment, a changelog line, a test fixture or a research file; live numbers go in messages and on the owner's private pages (owner rule, Nov 12, 2026; `test/noLiveFiguresGates.test.js`). Research results on public data are fine;
- any edit to trading code;
- anything on the DECLINED list (lifecycle section 7d).

## 3. Intake gate

Before any work, every idea passes the four uniqueness checks of `docs/STRATEGY_LIFECYCLE.md` section 7d:
1. The SIGNAL is different: a different data source or a different market type. Timing structure or price zone alone does not make it different. Kalshi's own data counts as a different source from price only if it is a different FIELD with different logic (open interest, book depth, trade flow count); the same price band at a different time does not (owner, Nov 11, 2026).
2. The EXIT is different: time-based, a target or scaling, or paired within its own position (the same strategy's own legs only, never a hedge against another strategy or market; decided, owner, Nov 11, 2026); hold to settlement also counts when the entry rules are different and the strategy will not hedge or interfere with another market or strategy. Signal and exit must both differ, and the entry rules too (this replaces "2 of 4 axes").
3. Correlation under 0.3 with EVERY live strategy on the cash basis: daily cash P&L, Pearson r, at least 20 overlapping days, applied at the first read. A correlation of 0.3 or more is a FAIL: the candidate is REJECTED as a duplicate and put on the declined list with the correlation number, the live strategy it matched and the dates of the window (owner, Nov 11, 2026).
4. Not on the DECLINED list.

**Who judges (owner, Nov 11, 2026).** An independent check, the Verification Analyst (the fact-checker agent), scores the four checks. A candidate is added to the shadow list only when that check says it passes all four AND the owner approves the entry. The proposing chat never scores its own candidate.

**Liquidity provision (owner, Nov 11, 2026, popup: YES).** A no-signal liquidity-provision family (market making: P&L from the spread and queue position, time-flatten exit) counts as unique, classified by entry mechanism and exit style; its signal check is NOT APPLICABLE. It must still pass correlation under 0.3 against every live strategy, the declined list and the cash PF 1.3 bar, and any live version needs its own owner popup (section 7). See lifecycle 7f rule 6.

Then ONE LINE of registration, with the pre-registered bar, before anything is tested. No line, no test.

### What counts as "on the shadow list"

The owner's pace (Nov 11, 2026): "5 must make it onto the shadow list per week." That means five UNIQUE candidates, each passing the four checks above and not on the declined list. A candidate counts only when ALL of these hold:
- (a) it is pre-registered, scored by the Verification Analyst and approved by the owner: the four checks passed, the bar and N written down;
- (b) a named data source is ALREADY collecting for it: a registry shadow rule, a recorder, or a read-time join on data we hold (candles, order documents, recorder branches);
- (c) it has a read date and an N target.

A bare idea does not count. A favourite-late variant never counts.

**Honest limits.** The shadow registry (`functions/kalshiShadowLib.js`) only carries Kalshi price rules (yes, no, favourite or cheap side, a band, a look window, a spread cap) on the bot's four quoted markets. So most unique candidates are recorder-backed or read-time joins. Five a week is supported in the first week by recorders already running (rain and weather forecast, Deribit options, OKX liquidations, in-game lag, perps carry). After that it needs a new recorder (runner minutes, an owner popup) or a build of a generic external-signal shadow logger (proposed, needs an owner popup). If fewer than five unique candidates exist in a week, the report says so and names the missing data or venue. It never pads with variants.

### Versions and regime strategies (lifecycle 7g, Nov 11, 2026)

Refinements and parameter tweaks are VERSIONS, not new strategies. A filter or improvement to an existing strategy (a gold spot-gap filter, the Polymarket lead on OICORE) and a tweak (price band, look time, size, the same logic on another market) are each a v2 that REPLACES its parent, which is retired with its record kept. A version never counts toward the weekly five or the cap on favourite-late shadows (that cap counts distinct strategies), never needs the uniqueness check, and still needs the declined-list check and a named parent. It is tested beside the parent as `NAME v2` on the same days and signals, and takes over only on the test in 7g (cash PF better by 0.10, net dollars per contract-week not lower, second half not worse, at least 60 signals); otherwise the owner decides by popup. A regime-only strategy is its OWN strategy with a regime tag: it counts as unique if signal and exit differ, its correlation is measured on its ON days, its regime signal is a registered input, and it is off when the reading is missing.

### Classification and stages (lifecycle 7f, Nov 11, 2026)

Strategies move through five stages: Idea, Shadow, Probe, Live, Retired. Family is the entry mechanism plus the exit style; risk class is the win-rate class, loss shape, dollars per order, dollars per day and correlation group. The proven bar, cash PF 1.3 or better over 100 fills in 2 of 3 windows, is the Probe to Live bar. Every candidate registration includes its one-line classification card: `NAME | family | risk class | stage`.

## 4. Limits

- At most 2 concurrent tests at once (owner, Nov 11, 2026; it was 3).
- At most ONE test per mechanism family at a time.
- Shadow rules: at most 3 favourite-late and at most one per underlying (lifecycle section 7c); other mechanisms at most 8 shadow rules in total.
- Runner minutes stay inside the Charter limit.
- Usage: pace work around the five hour limit; stop everything at overage; start no new workers at a warning.
- Effort stop (owner, Nov 11, 2026): after 3 FALSIFIED pre-registered tests a mechanism family goes on the DECLINED list for good. Two NOT_ENOUGH_DATA from the same source close that source (the Charter's rule).
  - **FALSIFIED** means it fails its pre-registered bar on the held-out read, or its cash profit factor is under 1.0 on the development read after fees.
  - **NOT_ENOUGH_DATA** means fewer treated events than the registered minimum.

## 5. Outputs

- **Top priority (owner, Nov 11, 2026): a replacement for gold L1**, which is a Probe under review and keeps trading under its existing kill (lifecycle 7f). Both Monday reports LEAD with progress on it, naming the candidates that pass the four uniqueness checks and how close each is to the proven bar.
- **Monday morning, US Central, Refinement:** the weekly rotation report (lifecycle section 7b): keep, watch, size step, kill, return, promote. Every strategy is listed with its mechanism family, profit factor first, on the cash basis.
- **Monday morning, V2:** a weekly research note of verdicts and the backlog.
- **Each week:** five unique candidates on the shadow list (see section 3 for what counts), each with the four intake checks filled in. A short week is reported as short.
- **Otherwise:** ONE short note, and only on a stage pass or a big fail.
- Never "menu empty". Say what data or venue would be needed, and the cost.

## 6. Definition of done for a test

1. The bar and the number tried (N) are registered before any result is read.
2. A held-out final third, read once.
3. Deflation for the number tried.
4. Cash basis, after fees.
5. A verdict of FALSIFIED, NOT_YET_FALSIFIED or NOT_ENOUGH_DATA, with the numbers.
6. The fact checker confirms every figure before it reaches the owner.
7. **The cutoff is a constant (Nov 12, 2026, after Desk A's held-out audit).** The registration states the held-out cutoff as a date or timestamp, the script carries that same constant, and the read-once marker is a line committed to the repo (not a scratch or git-ignored file). A cutoff computed as "the last third of whatever data exists when the script runs" is not allowed: on data that keeps growing it silently turns held-out into development. A test whose held-out was touched is reported with and without the touched part. The audit found nine such cases among open tests; they are being pinned.
8. **Slow families have a separate, lower screen (Nov 12, 2026, owner).** A family that produces fewer than about 52 independent events a year (owner, Nov 12: the line was moved from 26 to 52 so weekly families qualify) cannot reach the bar above for years. For those, `docs/POLITICS_RULES.md` section 8 sets a screen for a PAPER LIST only (cash PF 1.3 on at least 30 independent events, both halves positive, pinned cutoff, read once; below 30 the label is "no evidence at n = x"). It permits no live order, and the false-positive share it lets through is stated there.

## 7. Escalation

An owner popup is REQUIRED (owner, Nov 11, 2026) for: any strategy going live, even a 1 contract probe; any exception to a ban or a rule; any spend or new recorder (anything over the Charter's 250 runner minutes a month); any account or key; any change to this charter or to the Charter; and the owner's approval of EACH candidate's entry onto the shadow list, after the Verification Analyst has scored the four checks (section 3). Everything else is decided inside the team and logged.

## 8. What "carried away" looks like, and the automatic stop

| What happens | Automatic result |
|---|---|
| A same-family variant of something run or closed | Rejected at intake as a duplicate. |
| Chasing the best cell of many | The result is void unless deflated for all the cells. |
| A test extended past its registered budget or N | Stopped and logged; a new registration is needed. |
| Re-running a closed family without new data | Stopped; the family stays closed (3 falsified tests means declined for good). |
| A candidate with a correlation of 0.3 or more with a live strategy | Rejected as a duplicate and put on the declined list with the correlation number. |
| Padding the weekly five with variants | Not counted; the report names the missing data or venue instead. |
| Repeating a withdrawn figure | Stopped; counts against the chat that repeated it. |
| Spending usage on a test whose only possible answer is NOT_ENOUGH_DATA | Stopped; the cut is amended before any read, or the test is dropped. |

Each stop is applied by the COO (`.claude/agents/ops-coo.md`) or the head of the chat, and reported once.

## 9. Roster and division of labour (owner, Nov 11, 2026: "more productive, more work, better results"; reorganised Nov 12, 2026 with a Head of R&D)

| Role | Does | Never does |
|---|---|---|
| **Owner** | Decides every popup in section 7 and anything live, types "merge N", does every deploy. | |
| **EA** | Relays the owner's decisions and questions, keeps the Team Roster and Desk artifacts. | Edits trading code or merges. |
| **Main (Chief of Staff and Head of Engineering)** | Keeps engineering, merges (only on the owner's typed word), pull requests, security reviews with the security agent, recorders, kalshi-pull, deploy guidance and everything live. Agrees the research split of the Kalshi request budget with the Head of R&D. Arranges the Verification Analyst for any claimed pass or uniqueness score. Writes the throughput line. | Deploys, places orders, merges without the owner's word, or runs research. |
| **Head of R&D** (session_01PSWvZopXkxCcgaNUnhG9nM) | Runs all research. Owns the ranked queue (`RND_QUEUE.md` on the branch `rnd-queue`), the deflation log, the research split of the Kalshi read budget (agreed with Main), the probe pipeline, the paper and shadow list, and the desks below. | Merges, deploys, places orders, changes a live rule, or verifies its own passes. |
| **Strategy Research V2** (session_01PSWvZpN1MLodfM5W2dqtii) | RETIRED Nov 12, 2026 (its pending reads were moved to the Head of R&D; the owner ruled its closing-buy forward reads retired unread). | |
| **Refinement** (session_01PSWvZpZPD3ULyjU4sQhPcX) | Keeps live monitoring and the rotation report; runs the RESEARCH tests (calibration and event cards) from the queue. | Change a live rule. |
| **Idea Desk A** (fresh session session_01PSWvZn6mGV21Lppbpapybi from Nov 12, 2026; the earlier session_01PSWvZpRsGYgz8k99mrZJ8V is archived; structure and cross-market) and **Idea Desk B** (session_01PSWvZpwmrFdTUNmT36ngYQ; events and information, incl. politics, clinical, weather, combos) | WRITE cards and protocols: at least 12 pre-registered cards each, then the top 3 deepened into ready-to-run protocols. | Run tests, call Kalshi (unless the budget split gives them part), open pull requests (unless Main asks), place orders. |
| **Probe Engineering desk** (session_01PSWvZnv28Wm8fCqua9FMzq; stopped Nov 12, 2026, its three deliverables accepted, handoff in docs/probes/HANDOFF_PROBE_DESK_NOV12.md) | Writes build-ready specs and off-by-default code for live probes. | Run anything live, or merge. Its code is never live until the owner decides. |
| **Live-Data Forensics desk** (session_01PSWvZn9mqpQ8DM1QEXpyVo) | Studies the bot's own behaviour and the recorded books. | Touch the live account. It gets live figures by message only, and none go in the repo. |
| **Verification Analyst** (session_01PSWvZqX5pfCnCJfvqJpDCL, created Nov 12, 2026) | Re-checks any pass (every figure) and scores the four intake checks, from its own implementation written from the registration text, never from the author's script. Stays independent of the Head of R&D; reports to Main. | Merge, push to main, edit trading code, or open a held-out block. |
| **Testing Desk** (session_01PSWvZoWZGK1VYgdMTA25vo, created Nov 12, 2026) | TESTS registered cards (re-scores of stale-quote results, re-opened cards, dated reads); sends job files to Main for kalshi-pull. Reports to the Head of R&D for direction and to Main for engineering. | Invent strategies, place orders, make Kalshi requests from its own address. |
| **Stocks Desk** (session_01PSWvZm6Fiw2pwNzcbUhudN, created Nov 12, 2026; replaces session_01PSWvZkxSgedtJBD4vHPwcs, which could not push) | Researches US equities and ETFs under the same bars; owner-approved $25 total Databento cap. Reports to the Head of R&D for direction and to Main for engineering. | Place an order, open or change an account, spend beyond the cap, put Databento-derived data in the public repo. |
| **Security agent** | Reviews every pull request that touches `functions/`, workflows, recorders, rules or sign-in code. | Merges or deploys. |

**One ranked queue.** The Head of R&D keeps `RND_QUEUE.md` on the branch `rnd-queue` (not main, so it changes without a pull request): cards ready to test in rank order (by speed to a verdict), cards waiting on data with the date they unblock, and who holds each. A tester that finishes takes the top ready card at once; a desk never waits on a tester and a tester never waits on a desk. A card enters the queue only with its pre-registration complete (source and terms clause, family, uniqueness result, cheapest test, prediction, kill criteria, counterparty, time to verdict, lock-up per dollar-year).

**Kalshi request budget.** The shared bucket is 12 requests a minute. The Head of R&D and Main agree the split by priority each hour; the research share is the Head of R&D's to divide among the desks and testers, and the split is recorded at the top of `RND_QUEUE.md`. Nobody exceeds their share, and a 429 is never retried in a loop. The Idea Desks hold zero.

**Throughput line.** Every 6 hour report from Main carries: cards written, tests finished, tests waiting, and desks or workers idle and why. The Head of R&D supplies the research figures.

Section 4's limits (2 concurrent tests, one per family) are the default. The owner has authorised extra workers for the Friday sweep (Nov 11, 2026); that is recorded here, not a change to section 4.

## Standing permission: Main may merge docs-only pull requests (owner, Nov 12, 2026)

The owner gave Main a standing permission to merge, WITHOUT a typed "merge N", any pull request that changes ONLY documentation: markdown under `docs/`, `CLAUDE.md`, changelog text, and rulebook or charter text other than the owner-only `docs/CHARTER.md`. The owner confirmed it directly in their own words ("Main may merge docs-only PRs without my typed merge. Anything touching code, workflows, recorders, job files, the site or the bot still needs my typed merge N"). Conditions: Main first runs its usual checks (the full test suite, the frontend check, the no-live-figures gate); every such merge is listed in the next 6 hour report with its number and one line of what it recorded. The owner's typed "merge N" is STILL REQUIRED for anything that touches code, tests that gate behaviour, workflows, recorders, job files, the site pages, `functions/`, firestore rules, or any config a recorder or the bot reads. A docs pull request that records a NEW decision the owner has not made is not docs-only for this purpose: Main asks first. This replaces "merges only on the owner's typed word" in section 9 for docs-only pull requests.

## Numbers the owner may change

2 concurrent tests (was 3); the version takeover test in lifecycle 7g (0.10 profit factor margin, 60 signals); at most 1 test per family; 3 favourite-late shadow rules (1 per underlying); 8 shadow rules in total for other mechanisms; 3 falsified tests to decline a family for good, and 2 NOT_ENOUGH_DATA from one source to close it; 20 overlapping days and Pearson under 0.3 for the correlation check; 5 unique candidates a week on the shadow list; 250 runner minutes a month (the Charter's).
