# R&D operating charter (DRAFT for the owner's review)

**Status: DRAFT (Nov 11, 2026). It binds nobody until the owner merges it.** Once merged it binds the research chat (V2) and the live-performance chat (Refinement). It sits under `docs/CHARTER.md`, which only the owner changes; where they differ, the Charter wins. The owner made four decisions in a popup on Nov 11, 2026 (pace, concurrency, closing a family, the owner gate); they are written in below. Written at the owner's request: "i think we need to define stuff for the R&D team otherwise they're going to get carried away."

## 1. Mission

Find strategies that clear the owner's bar, not variants of what we already run.

## 2. Scope

**May:** research on public data; shadow rules; pre-registered tests; recorders that stay inside the Charter's 250 runner minutes a month.

**Out of bounds, without the owner:**
- any live change (rule, size, stop, market), even a 1 contract probe;
- any new spend;
- any new venue, or any new recorder or anything that would take the month over the Charter limit of 250 runner minutes;
- any account, key or credential;
- any edit to trading code;
- anything on the DECLINED list (lifecycle section 7d).

## 3. Intake gate

Before any work, every idea passes the four uniqueness checks of `docs/STRATEGY_LIFECYCLE.md` section 7d:
1. The SIGNAL is different: a different data source or a different market type. Timing structure or price zone alone does not make it different.
2. The EXIT is different: time-based, a target or scaling, or paired within its own position; hold to settlement also counts when the entry rules are different and the strategy will not hedge or interfere with another market or strategy. Signal and exit must both differ, and the entry rules too (this replaces "2 of 4 axes").
3. Correlation under 0.3 with EVERY live strategy on the cash basis: daily cash P&L, Pearson r, at least 20 overlapping days, applied at the first read.
4. Not on the DECLINED list.

Then ONE LINE of registration, with the pre-registered bar, before anything is tested. No line, no test.

### What counts as "on the shadow list"

The owner's pace (Nov 11, 2026): "5 must make it onto the shadow list per week." That means five UNIQUE candidates, each passing the four checks above and not on the declined list. A candidate counts only when ALL of these hold:
- (a) it is pre-registered: the four checks passed, the bar and N written down;
- (b) a named data source is ALREADY collecting for it: a registry shadow rule, a recorder, or a read-time join on data we hold (candles, order documents, recorder branches);
- (c) it has a read date and an N target.

A bare idea does not count. A favourite-late variant never counts.

**Honest limits.** The shadow registry (`functions/kalshiShadowLib.js`) only carries Kalshi price rules (yes, no, favourite or cheap side, a band, a look window, a spread cap) on the bot's four quoted markets. So most unique candidates are recorder-backed or read-time joins. Five a week is supported in the first week by recorders already running (rain and weather forecast, Deribit options, OKX liquidations, in-game lag, perps carry). After that it needs a new recorder (runner minutes, an owner popup) or a build of a generic external-signal shadow logger (proposed, needs an owner popup). If fewer than five unique candidates exist in a week, the report says so and names the missing data or venue. It never pads with variants.

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

## 7. Escalation

An owner popup is REQUIRED (owner, Nov 11, 2026) for: any strategy going live, even a 1 contract probe; any exception to a ban or a rule; any spend or new recorder (anything over the Charter's 250 runner minutes a month); any account or key; any change to this charter or to the Charter. Everything else is decided inside the team and logged.

## 8. What "carried away" looks like, and the automatic stop

| What happens | Automatic result |
|---|---|
| A same-family variant of something run or closed | Rejected at intake as a duplicate. |
| Chasing the best cell of many | The result is void unless deflated for all the cells. |
| A test extended past its registered budget or N | Stopped and logged; a new registration is needed. |
| Re-running a closed family without new data | Stopped; the family stays closed (3 falsified tests means declined for good). |
| Padding the weekly five with variants | Not counted; the report names the missing data or venue instead. |
| Repeating a withdrawn figure | Stopped; counts against the chat that repeated it. |
| Spending usage on a test whose only possible answer is NOT_ENOUGH_DATA | Stopped; the cut is amended before any read, or the test is dropped. |

Each stop is applied by the COO (`.claude/agents/ops-coo.md`) or the head of the chat, and reported once.

## Numbers the owner may change

2 concurrent tests (was 3); at most 1 test per family; 3 favourite-late shadow rules (1 per underlying); 8 shadow rules in total for other mechanisms; 3 falsified tests to decline a family for good, and 2 NOT_ENOUGH_DATA from one source to close it; 20 overlapping days and Pearson under 0.3 for the correlation check; 5 unique candidates a week on the shadow list; 250 runner minutes a month (the Charter's).
