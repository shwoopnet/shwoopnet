# WXENS1 notes: the ensemble tail-bracket recorder (2026-11-03, research only)

Registration: `workers/WXENS1_REGISTRATION.md` (pushed before any recorded row; README ledger entry "Pre-registration: WXENS1"). Nothing is scored here. N +2.

## What it records (all public, GET only, no key, no secret, no order)

Hourly at minute 12 (cron `12 * * * *`, plus `workflow_dispatch`), only for cities whose LOCAL STANDARD hour is 7 or 10 at that moment (the market day is a standard time day):

| Look | Cities due | Target days recorded |
|---|---|---|
| 07:00 | `L0_07` and `L1_07` (information only) | the settlement day and the day after |
| 10:00 | `L1_10` (the one registered look) | the day after (the market opens 10:00 ET the day before) |

Per run, per source: `ens` (Open-Meteo ensemble API, every member `temperature_2m_max` in F of GFS, ECMWF IFS and ICON for the target day), `nws` (api.weather.gov point forecast daytime high), `quotes` (bid, ask, last, volume, close time of every open bracket of the target event), `events` (the event's rules text once, to confirm the station). Every six hours (UTC 01, 07, 13, 19): `results` (each newly settled market's result and `expiration_value`) and `obs` (the IEM daily `max_tmpf` as a cross-check). Files: `wxens/<table>/<date>/<HH>.csv.gz` on branch `quote-data`, plus `wxens/runs/<date>.csv` (counts of calls, 429s, errors, clock skew).

Watchlist (`workers/WXENS1_WATCHLIST.json`): New York `KXHIGHNY`, Los Angeles `KXHIGHLAX`, Miami `KXHIGHMIA`, Chicago `KXHIGHCHI`, Austin `KXHIGHAUS`, Denver `KXHIGHDEN`, Philadelphia `KXHIGHPHIL`, San Francisco `KXHIGHTSFO`, Phoenix `KXHIGHTPHX`, Seattle `KXHIGHTSEA`, Dallas `KXHIGHTDAL`, Atlanta `KXHIGHTATL`, Houston `KXHIGHTHOU`, Las Vegas `KXHIGHTLV`. The 8 tested are the highest median bracket volume over the first 7 target dates (`python -m scalper.wxens1 cities DATA`, refuses to overwrite). Station names for the non-WX1 cities (KDFW for Dallas, KHOU for Houston, KSFO, KPHX, KSEA, KATL, KLAS) are best guesses to be checked against each event's `rules_primary` in `wxens/events` after the first run; they affect only the IEM cross-check and the coordinates, not the traded settlement (the market's own result).

## Request counts and cost

Per hour: about 24 hours x (1 ensemble call batched for all due cities + 2 NWS calls and 1 to 2 Kalshi pages per due city). Each city is due 3 hours a day, 14 cities, so about 42 city-looks a day: roughly 24 ensemble calls, 84 NWS calls, 60 Kalshi calls a day, plus the results step (4 times a day, 14 settled listings and up to 14 IEM calls) = about 70 more Kalshi calls. Under 300 calls a day in total, spaced 0.5 s apart. Actions cost: one 1 to 2 minute job per hour, about 1,500 minutes a month; free on a public repo. Data: under 2 MB gzipped a month.

Risk: Open-Meteo's free tier is limited per IP and answered HTTP 429 ("Daily API request limit exceeded") to the research sandbox, which shares its address. A GitHub runner's address is shared too: if the ensemble call is refused, that run records a gap (counted in `runs`), never a made up row. If gaps are common, the fallback is the manual command from a machine with its own address.

## Reachability from the research sandbox (2026-11-03)

- Kalshi public API (`external-api.kalshi.com/trade-api/v2/markets`): reachable (strike layout, ticker form `KXHIGHNY-26NOV05-B64.5`, `strike_type` greater/less/between, `yes_ask_dollars`, `volume_fp`, `rules_primary`; sometimes 429 for a few seconds).
- NWS (`api.weather.gov/points/...` and the `forecast` URL it returns, needs a User-Agent): reachable.
- IEM (`mesonet.agron.iastate.edu/api/1/daily.json`): reachable, field `max_tmpf`.
- Open-Meteo ensemble API: reachable but HTTP 429 daily limit from this sandbox, so the live response shape was NOT seen. `parse_ensemble` accepts any daily key that starts with `temperature_2m_max` and treats `memberNN` as the member, the rest as the model; if the first real run shows another naming, a one line change in `parse_ensemble` fixes it and the raw key is stored in every row (`member_key`), so no data is lost.

## How to turn it off

Delete `.github/workflows/record-wxens.yml` on main (or Actions, record-wxens, Disable workflow). The branch `quote-data` keeps what was recorded.

## What main must do

1. Merge branch `claude/v2-recorder-wxens` into main (the workflow checks out `main` for the script and watchlist). The workflow is under `.github/workflows` and `scripts/`, both excluded from the Pages site; `test/wxensRecorderGates.test.js` pins that.
2. Make sure Actions is enabled for the repo and the workflow may write to `quote-data` (the same setup as `record-daily`, `record-quotes`, `record-rain`).
3. Run the workflow once by hand (`workflow_dispatch`) at 15:xx UTC to see the first files and check `runs` for 429s on the ensemble call.

## If Actions is not wanted: the manual snapshot

From `kalshi-scalper`: `cd src && python -m scalper.wxens1 snapshot ../data/wxens_manual --wide`, run at two times a day for the primary look: 11:30 ET (the Eastern cities are at 11:30 and the Central ones at 10:30) and 13:30 ET (Denver and Phoenix at 11:30, the four Pacific cities at 10:30), and `--results` once a day. The information looks (07:00) are optional by hand. `--wide` accepts local hours 7, 8, 10 and 11 as the two looks. A skipped day is a gap, not a problem. Copy the `wxens/` folder into a `quote-data` checkout if the reader should see it: the reader (`python -m scalper.wxens1 count DATA`) wants `DATA/wxens/...`.

## Reading it

`python -m scalper.wxens1 count DATA` prints the selected trade count and the date 150 would be reached. It reads no outcome. `cities DATA` freezes the 8 cities after 7 dates; `run DATA` is the one registered read (refused before 300 trades or 2027-02-28, and a second time).

## Time to 150 trades

Registered prediction: 0.5 trades per city-day over 8 cities, about 4 a day, so **150 trades about 38 days after the first primary look (range 19 to 94 days), 300 about 75 days (range 38 to 188)**. If the recorder starts on 2026-11-05, 150 trades is about 2026-12-13 (range 2026-11-24 to 2027-02-07) and 300 is about 2027-01-19 (range 2026-12-13 to 2027-05-12, so the 2027-02-28 stop date may come first). The `count` command replaces this guess with the measured rate after the first week.

## WXLOW1: the daily LOW extension (2026-11-03, branch `claude/v2-recorder-wxens-lows`, stacks on `claude/v2-recorder-wxens`)

Registration: `workers/WXLOW1_REGISTRATION.md` (README "Pre-registration: WXLOW1", pushed before any recorded row). The WXENS1 rule is NOT changed; this records the same inputs for the low and reads them with the same code. Nothing is scored by the recorder. N +2 (the lows claim and the pooled claim).

**What is recorded (same hourly run, same idempotent slot files, same `wxens/` folder, new tables with a `_low` suffix; the highs files are untouched):**

| Table | Content |
|---|---|
| `ens_low` | every member of Open-Meteo `temperature_2m_min` (column `tmin_f`) per model, in the SAME ensemble request as the highs (`daily=temperature_2m_max,temperature_2m_min`): no extra ensemble call |
| `nws_low` | the NWS night temperature from the SAME forecast body (no extra NWS call): `role` `prior` = the night that starts the evening before the target date (ends that morning, where the day's low usually falls), `same` = the night that starts on the target date |
| `quotes_low`, `events_low` | the `KXLOWT*` brackets of the target event (one extra Kalshi listing per due city), same columns as the highs |
| `results_low`, `obs_low` | settled low markets with `expiration_value`, and the IEM `min_tmpf` cross-check (`iem_min_tmpf`) |
| `runs` | five more counts appended at the end (`ens_low_rows` ... `obs_low_rows`); the first thirteen columns are unchanged |

Series (in `WXENS1_WATCHLIST.json` as `low_series`, one per city; the script names no ticker): `KXLOWTNYC`, `KXLOWTLAX`, `KXLOWTMIA`, `KXLOWTCHI`, `KXLOWTAUS`, `KXLOWTDEN`, `KXLOWTPHIL`, `KXLOWTSFO`, `KXLOWTPHX`, `KXLOWTSEA`, `KXLOWTDAL`, `KXLOWTATL`, `KXLOWTHOU`, `KXLOWTLV`. The older `KXLOWNY`-style tickers return no markets and are not used. `--highs-only` (command line) or `kinds=("high",)` records the highs alone.

**Cost:** per run one extra Kalshi listing per due city (about 42 city-looks a day, so about 42 more Kalshi calls) plus, on the results step, 14 more settled listings and up to 14 more IEM calls a day. Ensemble and NWS calls are unchanged in number (the response is larger: about 122 members per variable per city instead of 122 for the max alone, so the body roughly doubles). Still under 400 calls a day, still one job an hour.

**Shapes seen live (2026-11-03), and what was not:**
- Seen: Open-Meteo ensemble `temperature_2m_min` for ONE location answered 200 with keys `temperature_2m_min_ncep_gefs_seamless` (control) and `temperature_2m_min_memberNN_<model>`; the models answer as `ncep_gefs_seamless` (31 incl. control), `ecmwf_ifs025_ensemble` (51), `icon_seamless_eps` (40) although they are requested as `gfs_seamless`, `ecmwf_ifs025`, `icon_seamless`. `parse_ensemble` handles exactly this naming (this also settles the highs parser's open question: the max keys follow the same pattern). The `models` column in the ensemble rows therefore holds the response names. NWS: the same `forecast` body has `isDaytime: false` periods ("Tonight" 18:00 to 06:00). IEM daily JSON has `min_tmpf`. Kalshi `KXLOWT*` listings answer with the same market fields as the highs.
- NOT seen: a multi-location (comma separated latitudes) Open-Meteo request with both variables. It answered HTTP 429 (daily limit) later the same day from the sandbox, so the list-of-locations shape is still taken from the documentation (the highs recorder has the same assumption). A refused call is counted as a gap, never filled.
- `KXLOWTSFO`: an open-status series listing returned nothing on one pass while the event's markets were active; if the recorder shows empty San Francisco low quotes on its first runs, that is the cause and the city is dropped by data.

**Reader:** `python -m scalper.wxlow1 count|cities|run|pooled DATA` (`src/scalper/wxlow1.py`). It imports every constant, the probability model, the trade choice and the verdict from `scalper.wxens1` (`build` gained optional table/column arguments; the highs defaults are unchanged and `test_wxens1.py` still passes). `count` prints lows, highs and pooled selected counts and the dates 150 and 300 would be reached (no outcome read). `cities` freezes the low city set separately (`wxlow1_cities.json`). `run` is WXLOW1-L (one shot, `wxlow1_result.txt`). `pooled` is WXLOW1-P (one shot, `wxlow1_pooled_result.txt`, refused until both city sets are frozen, prints pooled numbers only, never a split). Manual fallback `snapshot` records both kinds.

**Tests:** `kalshi-scalper/tests/test_wxlow1.py` (live key shape parse, NWS night roles, a full fake run with one ensemble call and separate low files, the reader on the low tables, the pooled and lows-alone one-shot reads on crafted data), `test_wxens1.py` unchanged and passing, and in `test/wxensRecorderGates.test.js` gates W1 to W6 unchanged plus W7 (low series in the watchlist only, one ensemble call carrying both variables, `_low` tables, no rule constant of its own in the reader, count reads no outcome, pooled one shot with both sets frozen).

**Time to 150 trades (registered prediction, from the first low primary look):** lows alone about 47 days (range 21 to 125), pooled with the highs about 21 days (range 10 to 54), highs alone 38 (19 to 94). Only the pooled claim shortens the wait; its read comes before WXENS1's own, which the registration discloses.

**What main must do:** merge `claude/v2-recorder-wxens` first, then `claude/v2-recorder-wxens-lows` (it edits `scripts/record_wxens.py`, the watchlist, `wxens1.py` and the gate test, and adds `wxlow1.py` and its test). No workflow change is needed: `record-wxens.yml` already runs the script and stages `wxens/`. If the highs branch is merged and the recorder has already started, the lows start on the next run after the second merge (the `runs` file for that day gets five more columns mid file, harmless: read it by position or ignore the first lines).
