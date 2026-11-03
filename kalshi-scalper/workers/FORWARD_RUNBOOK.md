# FORWARD RUNBOOK: what to do when a read date arrives, and how to recover a reclaimed container (FWDCAL, 2026-11-03)

Companion to `workers/FORWARD_CALENDAR.md` (the dated table). Research only, N +0. Nothing here promotes anything or touches live code.
All commands run from `/home/user/shwoopnet/kalshi-scalper` with `PYTHONPATH=src` (`export PYTHONPATH=src`). Times are UTC; Central is CST (UTC minus 6) from 2026-11-01.

## The five rules when a read date arrives

1. **Run it exactly once.** A registered read is spent when it runs, even if it crashes or the output looks thin. Most scorers write a started marker or a
   `data/<id>_result.txt` and refuse a second run. Do not delete either to "try again": a crashed run is the lead's decision (GF1/GF2/DEPTH1 refuse again on purpose).
   Before running, check that no verdict for the id is already logged in `README.md`, `workers/AUTO_LOG.md` or `workers/*_RESULT.md`. The result files live in
   `data/`, which is git-ignored and is lost when the container is reclaimed, so the README line is the durable proof that a read happened. Information looks
   (`look`, `count`, `readiness`) may be repeated; the registered read may not. A refusal (before the date, under the minimum count, gate not met) is not a run.
2. **Read the registration first.** Open `workers/<ID>_REGISTRATION.md` (and every `*_AMENDMENT*.md`, and the README section) and read the rule, the bar,
   the kill rules and the numeric prediction BEFORE running. Confirm the date, the data cut (freeze time, thirds, holdout) and the command match. If the
   command in the calendar and the registration disagree, stop and ask the coordinator; do not pick one.
3. **No re-definition.** Do not change a threshold, band, look time, fee, window, universe, split or bar after the data exist. A scorer bug found before the
   read is fixed by an amendment pushed BEFORE the run (no outcome seen, N unchanged); a bug found after is disclosed and the run stays spent
   (CPI1/MENT1 and the USWEEP1 de-duplication are the model: disclose, re-run only the corrected scorer on the same data, say so). Updating a hard-coded N
   or z constant to the coordinator's running count is hygiene, not a re-definition; print the registered bar beside it (the calendar lists which constants).
4. **Quote the window, n, cost and N.** Every verdict line in the README states: the date window and what it covers (discovery, validation, forward days, holdout),
   n (independent units: days, closes or events, never trades alone), the cost (fee 7% x C x p x (1-p) rounded up per order, at 1 and 10 contracts, and the
   x1.2 stress), the profit factor first, the day-clustered z against the bar at the running N, and the verdict word. Words: FALSIFIED, NOT_YET_FALSIFIED,
   NOT_ENOUGH_DATA, NOT_RUNNABLE. No promote verb; a pass earns only a falsifier read or a new registration. No em dashes; they/them.
5. **Holdout reads need the coordinator.** Any frozen third, holdout block or window C (GEN1 holdout, MAKERTAIL1 HOLDOUT, COUNT1/COUNT2/NEWLIST1 H, WXENS1 and
   the rest) is read only when the coordinator says so in writing, because it is read once and then spent. A scorer that starts a holdout by itself because a
   date passed is a defect: stop it and tell the coordinator.

Order on a read day: (a) check `ps` for the AUTO loop and any fetch; (b) `git branch --show-current` must print `claude/epic-ptolemy-0amjd9`; (c) run the
refresh the read names (usually `python3 -m scalper.fresh_update`, resumable, about 1 hour); (d) run the information look if one exists; (e) run the registered
read once and save the full output; (f) paste the printed text into the README with the five items of rule 4; (g) commit by file name and push.

## Items that are owner/main decisions, not worker decisions

Do not run these without a written go: the favourite-and-hold reads (USWEEP1 x5, GAS1-F, ABSORB-F, and the 2026-11-12 L1 reads, README "Owner instruction
(2026-10-28)"), FLIP1/FLOOR1/THIN1 (need the owner's export), STRADDLE1 (needs the owner's data key), any recorder extension (R6), any new trigger.

## Recovery after the container is reclaimed

The research container is ephemeral. Processes die, `/tmp` and the scratchpad are wiped, and `kalshi-scalper/data/` (git-ignored) may be gone or stale.
Do these in order and stop at the first surprise.

1. **Branch and tree.** `cd /home/user/shwoopnet && git status -sb && git branch --show-current`. The shared tree must stay on `claude/epic-ptolemy-0amjd9`; do
   not switch branches. `git pull -q --rebase --autostash origin claude/epic-ptolemy-0amjd9`. Never `git add -A`; never commit `data/`.
2. **Restart the autoscore loop.** `ps -eo pid,args | grep -c '^bash workers/autoscore_loop.sh'` (must be 1; more than 1 means a duplicate, kill the extra by
   pid after checking `ps -o args`, never `pkill -f`, which matches its own shell). To start it:
   `cd /home/user/shwoopnet/kalshi-scalper && nohup bash workers/autoscore_loop.sh >/dev/null 2>&1 &` then verify with the `ps` line above and
   `tail -5 data/autoscore_loop.log`. If the container was down for hours the first pass logs the recorder staleness (RECFEED); a read whose date passed while
   it was down runs on the first pass after it (MM1, QUOTE2B, MAKER5, L1Q1, GF1, GF2, DEPTH1, MKTTIME1-F), because each is gated by its own date and count, not by the clock of the pass. The loop needs `KALSHI_REPORT_TOKEN` in the environment only for the nightly live watcher; without it that step fails and nothing else stops.
3. **Rebuild `data/` if it is missing.** `git fetch origin research-data` then follow `HANDOFF_V2.md` section 4 (reassemble the split tar, check `MANIFEST.txt`
   sha256, extract into `kalshi-scalper/data`). Then `python3 -m scalper.fresh_update` (resumable) for the 15 minute candles, and `git fetch origin quote-data`
   for the recorders. Derived arrays and big databases have rebuild commands in the same section. **Do not trust a missing `data/*_result.txt` as
   "this read has not run":** the README and `workers/AUTO_LOG.md` are the record. If the README shows the verdict and the result file is gone, the read is
   done; do not run it again.
4. **Run fetches as tracked background commands.** Use the Bash tool with `run_in_background: true` (or `setsid nohup ... > data/<name>.log 2>&1 &`), never a
   foreground call that can time out and leave a half-written database. Record the pid, the log path and the start time in your report. Check with
   `ps -eo pid,args | grep scalper` and `tail data/<name>.log`. Resumable fetchers (`fresh_update`, `newlist1 fetch`, `count1 fetch`, `usweep1 fetch`,
   `ladl1 fetch`, `conf2 fetch`) skip what they already have: after a reclaim, just start them again with the same arguments (keep the same shard K and N). Two
   writers on the same sqlite file corrupt it: check `ps` before starting a second fetch on the same database. The AUTO loop already refreshes `fresh.sqlite`
   and `conf2_lad.sqlite` at most every 6 hours, one Kalshi stream at a time; do not start a manual `fresh_update` while its pass is running.
5. **The shared Kalshi rate limit (429).** Every worker, the AUTO loop and the recorders share one public read limit. Expect HTTP 429 in bursts (fetch
   rates seen: about 21 to 25 series a minute, 5 to 7 bulk pages a minute). Rules: one thread per fetcher; sleep between calls (0.5 s spacing in the
   recorders); on a 429 back off and retry (the scorers wait 2 s times the attempt, up to about 10 s, and retry up to 20 times); never run a second
   fetcher in parallel "to go faster"; a slow fetch is not a result. A prefix that is thin because of the limit reads NOT_ENOUGH_DATA or waits, never a pass
   (NEWLIST1 Amendment 2 is the model). If 429s persist for an hour, stop fetching and tell the coordinator; do not score a partial fetch except where the
   registration says to (NEWLIST1 rank prefix, COUNT1 complete events only).
6. **Recorders and branches.** `git fetch origin quote-data research-data perp-data`. The recorders (quotes, book, R6, deribit, sportspre, rain, perps) run on
   GitHub Actions from `main`; a quiet recorder is usually GitHub dropping a scheduled start, not a failure (4 to 5 hour gaps have happened). RECFEED prints
   it in `workers/AUTO_LOG.md`. Do not "fix" a recorder from the research branch; report the gap to main. R6 ends itself at 2026-11-13 23:59 UTC.
7. **Scheduled triggers.** The HANDOFF triggers fire into the old, archived research session. After a reclaim, do not assume any fired: read
   `workers/FORWARD_CALENDAR.md`, find the rows whose date is now past, and check each against the README for a logged verdict.
8. **Re-verify before the next read.** Import check: `for m in rev1 event830 makertail1 r6tests quote2b mm1 record1 gf12 depth1 gas1 mkttime1f newlist1 elect1 fedimpl1 raincal deribit_implied sportspre; do python3 -c "import scalper.$m" || echo FAIL $m; done`. Print a module's usage (no outcome is read) with
   `python3 -m scalper.<module>` with no argument where it has a `main(argv)`.
9. **Report.** Tell the coordinator: branch, loop pid, which data was rebuilt, which fetches are running (pid and log), the next five dated reads, and anything
   that ran while you were down.

## Forward read commands (built 2026-11-03, FWDTOOLS) and what is still missing

Built, each with `python -m scalper.<module> forward [--force-info]` and a synthetic test in `tests/test_fwd_<name>.py`: `makertail1_fwd` (also `makertail1 forward`), `bookch1_fwd`
(also `bookch1 forward`), `usweep1_fwd` (needs `--owner-asked`), `nowcast1_fwd`, `count1_fwd` (blocked, prints why), `count2_fwd`, `barrier1_fwd`. The table is at the end of
`workers/FORWARD_CALENDAR.md`. After a real read, paste the printed `FWD-READ <ID> ...` line into README.md yourself; that line (not data/) is what refuses the next attempt.
Still missing: the `scalper.wxens1` read command lives on `claude/v2-recorder-wxens` (not on this branch, do not duplicate it); `scalper.recdaily` is on the unmerged
`claude/v2-recorder-daily` branch, so `usweep1_fwd`, `nowcast1_fwd` and `barrier1_fwd` stop with a clear message until it is merged; there is no fetch for COUNT2's forward candles and nothing records the
nowcast values NOWCAST1 needs at each look (`--nowcast-file`).
