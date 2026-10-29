# Handoff to "Strategy Research V2" (written 2026-10-29 by the first research session)

Research branch: `claude/epic-ptolemy-0amjd9`. Data branch: `research-data` (see section 4). Research only: nothing here trades, deploys or changes the bot.

## 1. State in plain words

About **438,666 things tried** (every pre-registered variant, generator strategy and filter counted). **Nothing has passed a forward read.** The one strategy that cleared every backtest gate (G3H1, 2026-10-29) was withdrawn the same day: its data file kept strikes chosen from quotes AFTER the entry time (a universe look-ahead), and on a corrected file it lost (PF 0.43 / 0.60 / 0.60).

**Deflation bar:** Bonferroni one-sided 5% over N tried: z about **5.17** at N about 438,700 (use `scalper.gen1._norm_ppf(1 - 0.05 / N)`). **Success bar (owner's, unchanged):** profit factor at least 1.5 in each of three windows (discovery, validation, frozen holdout read once) after per-order rounded fees, positive at fees x1.2, independent n counted (days or closes, never trades), a named counterparty, and a deflated z at the bar. A pass earns a forward paper read only.

### Verdicts of the last two days (older ones: `studies/SCOREBOARD_2026-10-28.md` and every `## Result:` section of `README.md`)

| ID | What | Verdict | Key numbers |
|---|---|---|---|
| SCALP1 / SCALP2 | 15 min scalps (spot lag; overshoot bounce) | FALSIFIED | PF 0.59 / 0.57 |
| HIST1 | 576-cell scalp grid | FALSIFIED | best confirm PF 0.89 |
| AUTO1 to AUTO3 | 176,640 decision trees | FALSIFIED | 0 admissible holdout passes (AUTO1's 2 were 95c+ favourite buys) |
| MAKER4 | two-sided maker quoting, 12 to 4 min left | FALSIFIED | PF 0.00 (strict fills), 0.64 (optimistic, zero maker fee) |
| DAYCUT1 | L1 daily profit target / time cutoff | FALSIFIED | history net falls; live only 16 days |
| SIZE1 / SIZE2 | size and per-order fee rounding | no verdict change | PF size-invariant except rounding at 1 contract |
| ARB2 / ARB3 / ARB4 / ARB5 | full-set, crossed-ladder, deadline, bracket-vs-ladder, sports-totals locks | FALSIFIED | best +1.4c (a trap), +0.6c, +0.1c, -0.4c |
| RULES1 / FEE1 | rules review of flagged locks; size and rounding | closed | USCLIMATE is a trap; size reveals no edge |
| GEN1S / GEN1 / GEN2 | 17,500 distinct generated full strategies (15 min, 18 series) | NO_WINNER | 0 past discovery; best discovery PF 1.25 / 1.25 / 1.14 |
| GEN3 | 5,000 distinct on the hourly Bitcoin ladder | NO_WINNER after CORR1 | 21 discovery survivors, 2 validation, 1 holdout pass, all collapse to PF 0.27 to 0.83 on the corrected file |
| CORR1 / AUD1 | corrected re-read; independent re-implementation | FALSIFIED | G3H1 0.43 / 0.60 / 0.60; G3H2 0.77 / 0.83 / 0.59 |
| THETA1 | favourite drift sold before settlement, long-dated markets | FALSIFIED | 27 cells, PF 0.03 to 0.34 (0.15 to 0.48 with missing exits dropped) |
| EXIT1 | new exit shapes on L1 | FALSIFIED | hold beats every shape (hold 0.961 / 0.928 / 0.898 at 1 contract) |
| REGIME1 | 5 stand-down filters on L1 | FALSIFIED | spread >= 2c skip lifts PF about 0.09 in every window (information) |
| GOLD1D | gold stability | claim FAILS | 6 min PF 1.20 (halves 1.33 / 1.08); 10 min 0.89 |
| CONF1 | confluence filters on L1 | TWIN, TAPE FALSIFIED; LADDER NOT_ENOUGH_DATA | LADDER holdout kept PF 1.79 on 116 closes (one window, information) |
| MM1 | gold market making | NOT_ENOUGH_DATA / NOT_RUNNABLE | 48 gold windows recorded vs 300 needed; mid-window needs recorder R2 |
| LOOK1 / BAND1 / ROUND1 | per-market look time, sub-band, fee-minimising size | FALSIFIED | discovery picks fall back; ROUND1 +0.05c a contract (upkeep note) |
| LIVELOSS | where live L1 loses | information | BTC -$22.46, XRP -$11.31, gold +$33.83; 10 min lead PF 0.64 |
| LADL1 | L1's rule on gold daily/weekly and BTC/ETH hourly ladders | PENDING (download running) | gold: only 38 daily and 9 weekly closes on record |

## 2. Where the ledger is

- `kalshi-scalper/README.md`: every pre-registration and result, in order (about 8,600 lines). Search `## Pre-registration:` and `### Result` / `## Result:`.
- `studies/SCOREBOARD_2026-10-28.md` (families tested), `studies/NOVIEW_MECHANISMS_2026-10-28.md` (no-view mechanisms; there is no `research/MECHANISMS.md` in the repo), `studies/RECORDER_SPECS_2026-10-29.md` (R1 to R5 data plans), `studies/*_result_*.txt` (copies of result files), `studies/gen3_survivors_FROZEN_2026-10-29.json` (sha256 e73c1af9...).
- `forward_candidates.json`: the owner's file of ranked candidates; currently every entry is a FAILED or FALSIFIED label (no valid candidate).

**Discipline rules:** register rule, counterparty, numeric prediction and kill criteria in the README and push BEFORE any scoring; run once; verdict words only FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE; count every try; no promote verb; nothing live; owner decides everything that ships. Owner style: no em dashes, they/them, short, numbers first (profit factor first, with window, n and cost), numbered options plus a one-line recommendation at the end of owner-facing messages.

## 3. Pending work, in order

1. **LADL1** (registered): download `python -m scalper.ladl1 fetch` (resumable) writing `data/ladl1.sqlite`; started 2026-10-29 about 15:00 UTC after CORR1; gold done (38 daily closes, 9 weekly), Bitcoin and Ethereum hourly in progress (about 1 to 2 hours). Then `python -m scalper.ladl1 run` (once). Expect NOT_ENOUGH_DATA for gold (under 30 closes per window).
2. **CONF1 LADDER** needs the ladder for the WHOLE L1 history (Aug to Oct) built with the before-entry universe; register as CONF2 if the owner wants it.
3. **MM1**: re-check when the recorder holds 300 gold windows (about 9 days from 2026-10-29); mid-window needs R2 (not approved).
4. **Self-guide next round, not yet registered:** none of these survived the "is it already tested" check: calibration by time to close (THETA1, GEN1S), tennis post-set reversion (NOT_RUNNABLE, no score markers), settlement-time quotes (T1 to T5, QUOTE1), cross-series lead-lag (GEN2). Ideas worth a registration if data allows: CONF2 (ladder confluence on the full history); an L1 upkeep note bundle (skip spread >= 2c; size picked to minimise rounding) for the owner, not a strategy.

## 4. Rebuilding `kalshi-scalper/data`

Pushed to branch `research-data` (commit after d35cbcf; the older 2026-10-20 archive with `restore.sh` and `*.xz` files is kept beside it) as one gzipped tar, 278 MB, split into six 45 MiB chunks, with `MANIFEST.txt` (sha256 per chunk and the reassembly command): every source database except the very large or quick-to-rebuild ones. Reassemble: `git fetch origin research-data && git worktree add ../rd origin/research-data && cd ../rd && sha256sum -c MANIFEST.txt --ignore-missing && cat research-data.tar.gz.part-* | tar xzf - -C <repo>/kalshi-scalper/data` (whole-archive sha256 15788a02... in MANIFEST.txt). Contents: 161 files listed in FILES.txt (every source sqlite except sc1, fp3*, sweep1_*; the binance, binance_carry, cpi1, ment1, quote1 and maker4 folders; small json bar files; result files). `ladl1.sqlite` was still downloading and is not in it.

Not pushed (rebuild commands, from `kalshi-scalper/` with `PYTHONPATH=src`):
- Derived arrays (minutes each, from the pushed sqlite files): `python -m scalper.gen1 build` (40 s), `gen1s build` (5 min), `gen2 build` (about 1 h, 2 GB), `gen3 build` (5 min), `auto1/2/3 build` (10 to 20 min each).
- `sc1.sqlite` (787 MB, tennis candles): `python -m scalper.sc1 fetch` (several hours).
- `fp3*.sqlite` (tennis tapes, about 300 MB): `python -m scalper.fp3 fetch K N` sharded (hours).
- `lag2_*.json` (280 MB): the LAG2 fetcher (hours); only needed to re-read LAG2.
- 15 minute candles refresh: `python -m scalper.fresh_update` (resumable, 10 to 40 min per few days of new windows).
- Corrected hourly ladder: `python -m scalper.corr1 fetch 0 4` ... `fetch 3 4` in parallel then `python -m scalper.corr1 merge` (about 1 hour with 4 shards; strikes chosen 55 to 52 min before each close).
- Recorder files: `git fetch origin quote-data` (quotes/ and book/ folders; gzipped CSV; QUOTE2B order book under book/ since 2026-10-29 03:50 UTC).
- Slow ones to know: `sc1` (hours), `fp3` (hours), `maker4` tapes (about 1 hour with 12 shards; pushed), THETA1 (about 2 hours; pushed), LADL1 (1 to 2 hours).
- **Not pushed on purpose:** the owner's live order exports (`orders_export*.csv`, kept in the session scratchpad). They are the owner's private account record, not public market data, and branches of this repository can be public; ask the owner for a fresh "Copy all orders" export instead.

## 5. Gotchas learned (each one cost a result)

- **Universe look-ahead:** never choose strikes, markets or windows from quotes after the earliest entry time (G3H1: PF 3.48 became 0.43). Write the selection time into every registration.
- **Truncated scans:** an API listing that returns exactly the requested limit is truncated, not complete (the Alpaca 10,000-trade trap, CLAUDE.md); follow cursors and report a truncated scan as its own verdict.
- **Entry fills:** price an entry at the quote you could actually hit; the signal candle's closing quote is the earliest; a next-candle fill is the conservative check (AUD1 shows both).
- **Zero-volume candles:** a closing bid on a minute with no volume may not be fillable; report the share and the result with them dropped and treated as unfillable.
- **Fees:** Kalshi charges 7% x C x p x (1-p) rounded UP to the cent PER ORDER; at 1 contract a 0.46c fee becomes 1c (L1 history PF 0.927 at 1 contract vs 1.006 at 10).
- **Same-day holdout reuse:** a holdout read more than once is spent; the AUTO runs read one three times.
- **Process kills:** `pkill -f <pattern>` matches its own shell; kill by pid after checking `ps -o args`.
- **Memory:** passing large Python lists between pool workers exhausted 15 GB (GEN1 lost 2 hours); write numpy chunks to disk instead.
- **Git:** `data/` is ignored; never `git add -A`; never commit `data/` files to the research branch.

## 6. Registered future reads and what each waits for

| Read | Waits for | Date |
|---|---|---|
| GEN1 / GEN1S / GEN2 holdout | nothing frozen; empty read | on or after 2026-11-08 |
| GEN3-F1 | cancelled (G3H1 falsified by CORR1) | none |
| QUOTE2B | order-book recorder (book/ on quote-data), about 14 days from 2026-10-29 03:50 UTC; register before reading | about 2026-11-12 |
| LOCK2 | 25 hourly closes in the recorder's ladder.csv (1 file so far) | when available |
| MM1 | 300 gold windows in quotes.csv (48 now) | about 2026-11-07 |
| Recorder data check | trigger `trig_01S8xWT6V35hZu6gmf7TZYJy` (record1 look, 300 trades over 10 dates) | 2026-10-29 15:11 UTC, then daily |
| L1 forward reads (REV1, P6F, FLOOR1, THIN1, FLIP1, GAS1-F, ABSORB-F) | scheduled triggers; owner said not to run L1 research unless asked | 2026-11-05, 11-12, 11-17 |
