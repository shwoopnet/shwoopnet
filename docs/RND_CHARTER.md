# R&D operating charter (DRAFT for the owner's review)

**Status: DRAFT (Nov 11, 2026). It binds nobody until the owner merges it.** Once merged it binds the research chat (V2) and the live-performance chat (Refinement). It sits under `docs/CHARTER.md`, which only the owner changes; where they differ, the Charter wins. Written at the owner's request: "i think we need to define stuff for the R&D team otherwise they're going to get carried away."

## 1. Mission

Find strategies that clear the owner's bar, not variants of what we already run.

## 2. Scope

**May:** research on public data; shadow rules; pre-registered tests; recorders that stay inside the Charter's 250 runner minutes a month.

**Out of bounds, without the owner:**
- any live change (rule, size, stop, market);
- any new spend;
- any new venue, or any recorder that would take the month over 250 runner minutes;
- any account, key or credential;
- any edit to trading code;
- anything on the DECLINED list (lifecycle section 7d).

## 3. Intake gate

Before any work, every idea passes the four uniqueness checks of `docs/STRATEGY_LIFECYCLE.md` section 7d:
1. A different information source from the live strategies.
2. At least 2 of 4 axes differ: signal source, market type, timing structure, exit logic.
3. Low correlation with the live strategies on the cash basis: daily cash P&L, Pearson under 0.3, at least 20 overlapping days, applied at the first read.
4. Not on the DECLINED list.

Then ONE LINE of registration, with the pre-registered bar, before anything is tested. No line, no test.

## 4. Limits

- At most 3 analysts or concurrent tests at once (as the Charter).
- At most ONE test per mechanism family at a time.
- Shadow rules: at most 3 favourite-late and at most one per underlying (lifecycle section 7c); other mechanisms at most 8 shadow rules in total.
- Runner minutes stay inside the Charter limit.
- Usage: pace work around the five hour limit; stop everything at overage; start no new workers at a warning.
- Effort stop: a family is closed after 2 FALSIFIED tests from different cuts, or 2 NOT_ENOUGH_DATA from the same source (the Charter's rule).
  - **FALSIFIED** means it fails its pre-registered bar on the held-out read, or its cash profit factor is under 1.0 on the development read after fees.
  - **NOT_ENOUGH_DATA** means fewer treated events than the registered minimum.

## 5. Outputs

- **Monday morning, US Central, Refinement:** the weekly rotation report (lifecycle section 7b): keep, watch, size step, kill, return, promote. Every strategy is listed with its mechanism family, profit factor first, on the cash basis.
- **Monday morning, V2:** a weekly research note of verdicts and the backlog.
- **Each week, each chat:** five NEW unique ideas, each with the four intake checks filled in.
- **Otherwise:** ONE short note, and only on a stage pass or a big fail.
- Never "menu empty". Say what data or venue would be needed, and the cost.

## 6. Definition of done for a test

1. The bar and the number tried (N) are registered before any result is read.
2. A held-out final third, read once.
3. Deflation for the number tried.
4. Cash basis, after fees.
5. A verdict of FALSIFIED, NOT_YET_FALSIFIED or NOT_ENOUGH_DATA, with the numbers.
6. The fact checker confirms every figure before it reaches the owner.

## 7. Escalation

An owner popup is needed for: any candidate going live; any exception to a rule or a ban; any spend; any account or key; any change to this charter or to the Charter. Everything else is decided inside the team and logged.

## 8. What "carried away" looks like, and the automatic stop

| What happens | Automatic result |
|---|---|
| A same-family variant of something run or closed | Rejected at intake as a duplicate. |
| Chasing the best cell of many | The result is void unless deflated for all the cells. |
| A test extended past its registered budget or N | Stopped and logged; a new registration is needed. |
| Re-running a closed family without new data | Stopped; the family stays closed. |
| Repeating a withdrawn figure | Stopped; counts against the chat that repeated it. |
| Spending usage on a test whose only possible answer is NOT_ENOUGH_DATA | Stopped; the cut is amended before any read, or the test is dropped. |

Each stop is applied by the COO (`.claude/agents/ops-coo.md`) or the head of the chat, and reported once.

## Numbers the owner may change

At most 3 concurrent tests or analysts; at most 1 test per family; 3 favourite-late shadow rules (1 per underlying); 8 shadow rules in total for other mechanisms; 2 falsified tests or 2 NOT_ENOUGH_DATA to close a family; 20 overlapping days and Pearson under 0.3 for the correlation check; 5 new ideas a week per chat; 250 runner minutes a month (the Charter's).
