# RECPLAN1 proposal: which forward recorders are worth building (2026-11-04)

**NOTHING IS BUILT BY THIS DOCUMENT.** It is a ranking for main and the owner to decide. No recorder, workflow or script was written or pushed, no Kalshi fetch was made, no outcome was read, N +0, no rule registered, no promote verb. Any recorder file would go on a separate branch cut from origin/main, and only on main's or the owner's go-ahead. Owner rule held throughout: cheap side only (ask 3c to 30c), no favourite-and-hold research, no 15 minute crypto or gold candle triggers.

Worker RECPLAN1, session "Strategy Research V2". Sources: `workers/*_RESULT.md`, `*_REGISTRATION.md`, `RECDAILY_NOTES.md`, `RECREF_NOTES.md`, `WXENS1_NOTES.md`, `FORWARD_CALENDAR.md`, `FORWARD_RUNBOOK.md`, the README ledger, and the recorders on `origin/main` (`.github/workflows/record-*.yml`, `scripts/record_*.py`). I did not fetch robots.txt or any terms page for any outside host; the compliance column comes from what the repo notes record plus general knowledge, and each "check" is flagged.

## 1. What already exists on origin/main (state at 2026-11-04 02:25 UTC, from the `quote-data` branch)

| Recorder | File | What it records | Status seen |
|---|---|---|---|
| RECDAILY | `scripts/record_daily.py`, `record-daily.yml` (cron 7,37 each hour), watchlist `workers/RECDAILY_WATCHLIST.json` | Kalshi quotes every 30 min of NOWCAST1 (KXCPI, KXCPICORE, KXPCECORE, KXGDP), FEDIMPL1 (KXFEDDECISION, KXFED), BARRIER1 (14 monthly one-touch series) and results | Running: 40 calls, 0 errors, 109 quote rows in the first run |
| RECREF | `scripts/record_ref.py` + `ref_adapters.py`, `record-ref.yml` (every 2 h), watchlist `workers/RECREF_WATCHLIST.json` | Quotes of KXRT, KXMC, KXTRUTHSOCIALD, KXTOPSONG, KXBBSINGLE, KXTOPALBUM, KXSTEAMTOPSELLER and others, with the current value of the public source (kworb, Rotten Tomatoes, Metacritic, Billboard, Steam, Polymarket xtracker) | Running: 3 parse failures in the first run (Billboard markup, as the notes predicted) |
| WXENS1 / WXLOW1 | `scripts/record_wxens.py`, `record-wxens.yml` (hourly, :12), watchlist `workers/WXENS1_WATCHLIST.json` | Open-Meteo ensemble members (highs and lows), NWS point forecast, Kalshi quotes of every bracket of 14 cities' KXHIGH and KXLOWT events at 07:00 and 10:00 local standard time, results, IEM observed max and min | Running, but the first run was a quiet slot (`cities_due` 0). **The Open-Meteo ensemble call (429 risk on a shared address) has not yet been exercised on a runner.** |
| RAINCAL, SPORTS-PRE, DERIBIT, R6 book, quotes, book, perps | `record-rain`, `-sportspre`, `-deribit`, `-15m-book`, `-quotes`, `-book`, `-perps` | Other registered tests | Out of scope here |

Actions minutes: the repo is public (Pages), where the notes say Actions minutes are free. I have not verified the billing plan; if the repo ever went private, RECDAILY alone (1,500 to 3,000 min/month by its own notes) would exceed the 2,000 free minutes. Minutes below are billed-minute estimates (1 to 2 per short run, rounded up per job), not measured.

## 2. Ranking (trades unlocked per Actions minute)

"Treated trades" = trades under the registered rule, not outcomes. Where the worker result gives no measurement, the figure is marked **guess** and the reasoning is shown. Minutes are per month. "Marginal" is the cost over what already runs.

| Rank | Candidate | Verdict | Treated trades per month | Marginal Actions min per month | Trades per marginal minute |
|---|---|---|---|---|---|
| 1 | **FXREF1 reference recorder** (Yahoo 1 minute for 7 symbols) | **GO** (new, small) | 50 to 200 (**guess**) | 30 to 60 | about 1 to 6 |
| 2 | **STRESSDAY1 ladders** added to RECDAILY | **GO** (config edit only) | about 340 entries, but the binding unit is stress DAYS (25 needed) | 0 to 720 | about 0.5 or more |
| 3 | **WXENS1 + WXLOW1** (and the overround filter) | **KEEP** (already running) | pooled about 215 (highs 120, lows 96) | 0 (sunk 720 to 1,440) | unbounded; about 0.2 on total cost |
| 4 | **COUNT1D** | **KEEP, no new build** (RECREF already lists KXTRUTHSOCIALD) | 3 to 18, median 9 | 0 | n/a |
| 5 | OVERROUND1 forward | **NO-GO as a recording** | 0 (falsified as a trade) | 0 | 0 |
| 6 | GOVCOUNT1 / whitehouse.gov post times | **NO-GO** | about 2 (**guess**) | 45 to 90 | about 0.03 |
| 7 | TENNIS1 (ATP/WTA) | **NO-GO for a recorder**, throttled fetch instead | about 35 (from the result) | 0 | n/a |
| 8 | SLOWSTAT1 | **NO-GO** (no recorder needed) | under 3 | 0 | n/a |
| 9 | INCENT1 | **NO-GO** (not a trade-count test) | 0 | n/a | n/a |
| 10 | PROPS1 / SCOUT1 (MLBKS1) | **WAIT** (not run yet, history is available) | unknown | 0 | n/a |
| 11 | WXOTHER1 | **CANNOT ASSESS** (no file in the repo) | unknown | n/a | n/a |
| 12 | COUNT2 / KXTORNADO | **DEAD** | 0.05 per year | n/a | 0 |

## 3. Per-candidate detail

### 1. FXREF1: keyless minute reference for FX, WTI, natural gas (GO, new)
- **(a) Unlocks.** FXREF1 (`FXREF1_RESULT.md`: NOT_RUNNABLE because Yahoo 1 minute reaches only about 7 days back and the pre-cut Kalshi history has no reference). The result's own forward plan: a daily keyless recorder to the `quote-data` branch and **one frozen read on or after 2026-12-15** under unchanged rules. Kalshi candles for the same days can be re-fetched later from the public API, so only the reference needs recording (registration, last paragraph).
- **(b) Volume and minutes.** 7 requests (`EURUSD=X GBPUSD=X JPY=X AUDUSD=X CAD=X CL=F NG=F`, `range=5d&interval=1m`) per run. Yahoo keeps about 7 days of minutes, so one run every 2 to 3 days leaves no gap, and the first run backfills the last 7 days at once. About 15 runs a month at 1 to 2 minutes is **30 to 60 min/month**; roughly 3 MB a month gzipped (my estimate). Folding the 7 requests into the existing `record-ref.yml` as one more adapter would cost about 0 extra minutes.
- **(c) Public and compliant.** Keyless, GET only. Caveat: the Yahoo chart endpoint is an unofficial, undocumented API, and Yahoo's terms are not friendly to automated use; the project's own `marketTapeTick` already reads the same endpoint (CLAUDE.md), so this is not a new exposure, but **check the terms, send at most 7 requests per run, and use a descriptive User-Agent**. The research sandbox got HTTP 429 from Yahoo; a GitHub runner address is shared too, so expect gaps and count them (never fill).
- **(d) Existing recorder.** Closest: `scripts/ref_adapters.py` (RECREF's adapter pattern: add a `yahoo` adapter and a watchlist entry, a few dozen lines, no new workflow). Alternative: a new `scripts/record_fxref.py` and workflow, about 60 lines. Either is a main/owner decision; I build neither.
- **(e) Expected treated trades.** **Unmeasured, a guess.** Markets per day before the cut: WTI about 71, gas about 70, FX about 65 each, so about 336 a day. Cheap-side quotes are about 45% of WTI and gas markets. The 3x rule (model at least 3x ask) fired on 14% of NOWCAST1 releases and on 1% of tennis events (`TENNIS1_RESULT.md`). At 0.5% to 2% of all markets that is 50 to 200 a month; at the tennis rate it is the bottom of that range or lower. FXREF1's own kill line is "under about 150 expected treated", so the first 4 to 6 weeks (to 2026-12-15) may still end NOT_ENOUGH_DATA. Thin AUD/USD and USD/CAD books (median 1,600 contracts) may also not fill.
- **(f) Recommendation: GO.** Best ratio of any unbuilt recorder, a tiny cost, and the only one whose missing input is perishable (the 7 day Yahoo window loses data every day it is not recorded). Start with a backfill, then every 2 days.

### 2. STRESSDAY1: daily-ladder quotes past 2026-10-02 (GO, a watchlist edit)
- **(a) Unlocks.** STRESSDAY1 forward score (`STRESSDAY1_RESULT.md`: NOT_ENOUGH_DATA, 10 stress days against 25 needed). Needs at least 25 stress days and 150 stress entries; about **55 trading days at a one-third stress rate**, so about **late January 2027** if the quotes start around 2026-11-05. The VIX reference needs no recorder (Yahoo daily `^VIX` has years of history); the FOMC/CPI/JOBS dates are in `EVENT1_CALENDAR.csv`.
- **(b) Volume and minutes.** No new workflow. RECDAILY polls the watchlist every 30 minutes with up to 6 pages per series at a 0.5 s gap. Adding about 10 ladder series adds roughly 30 to 60 seconds per run, so **0 to 720 min/month** more, and tens of MB a year.
- **(c) Public and compliant.** Kalshi public market data, GET only, same as RECDAILY today.
- **(d) Existing recorder.** `workers/RECDAILY_WATCHLIST.json` (config only; "add a test by editing this file and nothing else"). The series are the Financials, Commodities and Crypto daily ladders that STRESSDAY1's census used (names from the cached CALIB1 table, which I did not re-read). USWEEP1's favourite watch items were removed from this file on Nov 3 under the owner's ban; STRESSDAY1 is cheap side only, and the ask 3c to 30c filter must be applied by the READER, never the recorder, which stores every poll. It needs entry timestamps: RECDAILY rows carry `poll_ts` and `mins_to_close`, which is what the CALIB1 table lacked.
- **(e) Treated trades.** Development rate: 782 entries on 22 days (about 36 a day), 399 of them on 10 stress days. At the same rate, about 16 stress entries per trading day, about 340 a month. **The entries are not independent (several looks per ladder); the registered unit is the DAY**, so the binding constraint is 25 stress days, not trade count.
- **(f) Recommendation: GO.** One JSON edit on main, near zero marginal cost. Reason to hesitate: the prior is that cheap sides lose on stress days (predicted PF 0.3 to 0.8), so the likely verdict is FALSIFIED, which is still a result for the cost.

### 3. WXENS1 + WXLOW1 (and the OVERROUND1 filter): already running (KEEP)
- **(a) Unlocks.** WXENS1 read on **2027-02-28 23:59 UTC or at 300 trades**; WXLOW1-L and WXLOW1-P on the same dates (the pooled read comes about twice as early). Registered take-up: highs 0.5 trades per city-day (about 4 a day), lows 0.4 (about 3.2), pooled about 7.2 (range 2.8 to 15), so 300 pooled trades in about 42 days (about mid-December 2026 to January 2027 if the first look is 2026-11-05). `FORWARD_CALENDAR.md` row 42.
- **(b) Volume and minutes.** 24 runs a day, 720 a month, **720 to 1,440 min/month** (my estimate; already spent). Storage is not measured in the notes.
- **(c) Public and compliant.** Kalshi public, api.weather.gov (descriptive User-Agent, as it requires), Open-Meteo free API (non-commercial limits, per IP daily cap), IEM public daily JSON. All keyless. **Check** Open-Meteo's free-tier terms for a research script run hourly from a shared address.
- **(d) Existing.** `record-wxens.yml` is the recorder. Nothing to add.
- **(e) Treated.** About 120 highs plus 96 lows a month (registered, **unmeasured**; the reader module `wxens1.py` does not exist yet, calendar row 42).
- **(f) Recommendation: KEEP, and verify on the first look morning that the ensemble call is not 429.** If it is, the whole lane produces nothing, and the fallback is a run from a machine with its own address. The highest-value check in this document costs one look at `wxens/runs/<date>.csv` (`n429`, `ens_rows`).

### 4. COUNT1D (Truth Social daily): covered, no new build
- **(a)** COUNT1D forward read due **2027-03-01** or at 150 trades; expected NOT_ENOUGH_DATA (12 to 70 trades by then, reaching 150 before then under 3%).
- **(d)** RECREF already records KXTRUTHSOCIALD quotes every 2 hours beside the Polymarket xtracker count. The rule's own count source is the CNN archive (`ix.cnn.io/data/truth-social/truth_archive.json`), which carries post timestamps, so the count at the look is recomputable later and needs no recorder. Kalshi candles come later from the API. One optional insurance: a daily gzipped copy of the archive, if posts are ever deleted from it (about one request a day, as a RECREF adapter).
- **(e)** 0.1 to 0.6 trades a day (registered guess), about 9 a month.
- **(f) Recommendation: no new recorder.** The weekly series is not reconcilable (26 of 36 weeks) and stays out.

### 5. OVERROUND1: no-go as a recording
- Result: **FALSIFIED as a trade** (LOW overround net -1.58c, both halves negative, PF 0.85); only the ordering survived (LOW minus HIGH +5.9c). Its forward plan, "log overround at the 24 hour look on new temperature events", is already available from the WXENS1 recorder's `quotes` table (every bracket at 07:00 and 10:00 local). Those looks are about 39 hours (10:00 the day before) and about 18 hours (07:00 on the day) before close, **not** the registered T1440, so a faithful rerun would need a third look, a small change to `look_label` and `due_local_hours` in `scripts/record_wxens.py`. Not worth it: it is an observation, not a trade, and could only serve as a filter inside another registered rule. **No-go; use the existing quotes if a filter is ever registered.**

### 6. GOVCOUNT1 / COUNT2 count families, whitehouse.gov post times: no-go
- **(a)** Would make KXEOWEEK (about 54 events so far, 1 to 5 markets per event) mid-period observable. No forward read is registered; it would need a new registration.
- **(b)(c)** One page read every hour or two, 45 to 90 min/month. whitehouse.gov has no API; scraping a page is a robots/terms question I did not check, and **Federal Register publication lags signing by 3 to 7 days (median 5)**, so post times may not match the count that settles the market.
- **(e)** COUNT1's take-up was 0.42 trades per weekly period; at 4 events a month that is **about 2 trades a month (guess)**, so 150 trades is about 6 years. **No-go**: wrong order of magnitude. The other government families have 1 to 15 settled events each.

### 7. TENNIS1: no recorder; a throttled fetch is the way out
- Result: NOT_ENOUGH_DATA. The blocker was Kalshi's rate limit on the shared egress (about 4 requests a minute sustained), not missing history: candles stay on the public API. Treated about 74 pre-cut (34 to 114) plus about 8 a week forward (2 per 100 tour events), so **about 35 a month and 150 around mid-March 2027**, as the result computes.
- A recorder would be a new tennis module (ESPN scoreboard for ATP and WTA, Kalshi quotes at T-10 min), not a few lines of `record_sportspre.py`. **No-go.** Instead resume `python -m scalper.tennis1 fetch` only for events whose stored ask is already 3c to 30c (about 5 a day) at a polite pace. Challenger, ITF and darts stay NOT_RUNNABLE until a results source is allowed.

### 8. SLOWSTAT1: no-go (no recorder needed)
Monthly series; Kalshi history and FRED are retrievable later. The census gave 54 scoreable markets in total (an upper bound), and KXADP reaches 40 events around 2028. **Rerun the census on 2027-02-01** as registered, nothing before.

### 9. INCENT1: no-go (not a trade-count test)
Verdict VIABLE_SMALL_PROBE by the registered rule, but median net is negative under the fill-floor stress; it is a market-making lane with no treated-trade count and no registered forward read. A recorder of incentive programs and books would need a registration first, and the real evidence is a paid-reward probe, which is an owner decision.

### 10. PROPS1 and SCOUT1 / MLBKS1: wait
Both registered 2026-11-04 and not run. Their reference (ESPN box scores) and Kalshi candles are retrievable for past games, so a recorder is not the first move. If either ends NOT_ENOUGH_DATA, the forward answer is ESPN `summary` for upcoming games plus candles after settlement; revisit then. PROPS1 pre-cut events: NBA about 1,000 per series, NFL about 250, WNBA about 300.

### 11. WXOTHER1: cannot assess
No file, README line or registration named `WXOTHER1` exists in the repo. If it means other weather families, RAINCAL already records rain (`record-rain.yml`, to 2026-12-31).

### 12. COUNT2 / KXTORNADO: dead
12 events a year, 1 trade in 19 scored events, and a SOURCE_MISMATCH (daily-file sums higher than Kalshi's count in 16 of 26 months). About 60 years to 40 trades.

## 4. Dead, do not record (11 items)

1. KXTORNADO / COUNT2 forward freeze (0.6 trades a year; source mismatch).
2. Truth Social weekly count (26 of 36 weeks reconcile; not testable). The forward daily is already registered as COUNT1D.
3. Government count families other than KXEOWEEK (nominations 15 events, judges 11 and a key, pardons 11, bills 1 to 3, press briefings 3, CBP 9): too few events.
4. BARRIER1 monthly one-touch (14 series in RECDAILY): 40 fills needs 11 to 13 months and 150 needs 3 years. Candidate to REMOVE from `RECDAILY_WATCHLIST.json` (saves calls, not minutes).
5. FEDIMPL1 (KXFED, KXFEDDECISION in RECDAILY): 150 trades is 4 to 8 years. Same removal candidate.
6. FXREF1 on index 15 minute series (Dow, S&P 500, Nasdaq 100) and Brent: 0 settled markets, excluded by the registration.
7. SLOWSTAT1 zero-volume series (AMSAVO, DDR5, B200, USDNOK, 30 year hourly).
8. Challenger / ITF / darts tennis (no free results source reachable).
9. OVERROUND1 as a standalone entry (falsified).
10. WX1-style point-forecast weather (falsified at -4.70c, z -4.17); WXENS1 is the ensemble variant and is separate.
11. Favourite-side USWEEP1 watch items (owner ban, already removed from the RECDAILY watchlist on Nov 3). GAS1-F and ABSORB-F are favourite-and-hold reads and need an owner ruling, not a recorder.

## 5. What I would ask main or the owner to decide

1. **GO FXREF1 reference recorder** (rank 1): choose "adapter in `ref_adapters.py` / `record-ref.yml`" (about 0 min, touches an existing recorder) or "new small workflow" (30 to 60 min a month). It needs a backfill the day it starts.
2. **GO STRESSDAY1 ladders** (rank 2): a one-line-per-series edit of `RECDAILY_WATCHLIST.json`; I can list the exact series from the CALIB1 table when asked.
3. **Check WXENS1 now** (rank 3): `wxens/runs/<date>.csv` after the 13:12 UTC run on 2026-11-04 shows whether the Open-Meteo ensemble call returned rows.
4. Nothing else needs a build. Everything else is no-go, waiting for a result, or already covered.
