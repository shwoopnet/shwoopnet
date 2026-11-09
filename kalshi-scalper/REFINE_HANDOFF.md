# Refinement handoff (Head of Live Strategy Performance), Nov 8, 2026, 1:30 PM CT

Short state so a fresh session or autocompact loses nothing. Newest detail is in REFINE_STATUS.md (newest first). Scratchpad paths below are session local (not in the repo); the repo has the logs, yardsticks (REFINE_YARDSTICKS.md), retractions (REFINE_RETRACTIONS.md) and checklist.

## Role and rules
Reports findings to main (session_01PYvNscv7toqH6sCw7ADjw2); the owner decides everything live. Never change an order, size, rule or deploy. Register every read before scoring; shadows before any live change; state the booking basis on every figure (limit-booked settledPnl before PR 741, cash-booked after: paid = avgFill YES, 1 - avgFill NO, fee avgFee per contract). Stored sizing base is 979.25 (owner read Nov 7). Check-in is hourly. No em dashes. US Central times.

## Live record (cash basis, Nov 8 12:19 PM CT)
OICORE 71 fills, net +27.15, streak 7 of 24 (kill is 24 since PR 741), peak 57.37, drawdown 30.2 vs $60 own-peak stop at size 12. EVENT830 5 fills, 0 wins. Gold L1 closed on weekends (reopens Sun about 6 PM CT); Dogecoin paused since Nov 3.

## Open forward reads (all wired in the scratchpad wake.sh)
- S-HALFSIZE1 (OICORE under 0.10 group): 18 of 40 fills, 0 wins. Owner deferred half size to the Nov 13 read.
- S-OIBANDS1 (forward window from 2026-11-08T12:44Z): group A (paid 0.07 or less) read at 40, group B (over 0.20) read at 20.
- S-HOLDVSSELL (gold early sells after 2026-11-07T20:24Z): 0 of 30; if hold beats the sell with the 90 percent interval above 0 it comes to the owner as an approval item; live hold test was SKIPPED by the owner.
- S-ESFEAT1 (gold early-sell leads: paid price lowest tercile, rise3 lowest tercile): 0 of 20 early sells.
- S-NOFILLADV: 0 of 20 no-fills.
- S-OICHEAPSKIP1: waits for the PR 742 deploy (OICORE skip under 8c, merged, not deployed; PR 743 carries side in report skips, needs deploy-report.sh). On deploy day main gives the UTC time: write it to S/w_oicheapskip/DEPLOY_TS; read at 40 signals (about 10 days): permanent skip if at most 1 win, drop if 4 or more, else extend to 80.
- Dated: Nov 10 EVENT830 CPI release (13:30Z); C9 silver 200 windows about Nov 11 1 AM CT (kill if lost share over 12 percent or net below -2.0c); R6 Nov 12 13:00Z (r6_final_fixed2.py, back up oi first); OICORE forward read Nov 13 15:00Z; EVENT830 interim Dec 7.

## Done and closed (do not re-run)
Gold exit line scan (hold to 40c), gold entry look and band scan, early-sell separation (nothing at entry), early-sell rate (market flat near 6 percent, not a regime), hold vs sell (+21.85, CI spans zero), OICORE big-loss price caps, OICORE streak size cut, OICORE side split, OICORE OI minimum sweep (86.3k to 130k: no), OICORE rate vs plan (about 10 a day, matches sim), gold weekend reopen slice, gold size caps (arithmetic), stop headroom at base 979.25, risk at 12 and 15 contracts, PR 741 cash-basis checks.

## Standing queue (start the next when one finishes)
1 Nightly every-trade review from the latest report (about 12:17 AM CT). 2 Watch worker each wake: kill rules, cash-formula mismatches, tracker counts. 3 New refinements: gold band edges (0.85 to 0.88 and 0.97 to 0.99) on history; EVENT830 pricing cushion (forward only); anything the nightly review shows. 4 Risk reductions on current loss sources only with an out-of-sample bar. Evidence bar: both halves, live consistent, try count stated; withdrawn claims count against me.

## Known data traps
settledPnl before PR 741 is limit-booked; stop_headroom.py prints UTC though labelled CT; dash.sh DOGE ladder line retired; report drops skip note (PR 743 fixes); sim window counts differ by script (491 triggers vs 3,514 windows).

## Update Nov 8, 9:55 PM CT (overnight directive from main, owner asleep)
Keep working all night; never idle; nothing live, no merges, no deploys, no spend; do not ask the owner anything; urgent live-trading issues go to main at once, the rest one line each via main. A send_later reminder fires at 6:45 AM CT Nov 9: send main 3 lines (what ran overnight, approval-ready item, blocked). Queue overnight: nightly every-trade review (about 12:17 AM CT), hourly watch worker (kill rules on cash basis, cheap-skip signals, trackers), EVENT830 fills (CPI release is Nov 10 13:30Z), deploy-stamp and exit-watch health checks, hold-vs-sell tracker. New since the last handoff: PR 742 (OICORE skip under 8c) live since 2026-11-08T18:57:10Z (DEPLOY_TS written; S-OICHEAPSKIP1: 3 signals, 2 settled both would have lost; read at 40, keep skip at 1 win or fewer, drop at 4 or more, else 80); PR 743 (skip side in report) not yet deployed; S-OIBANDS1 and S-ESFEAT1 forward trackers; W-OIEXIT1, W-OIPARTIAL1 (profit-take and partial close fail), W-OISWEEP1 (OI minimum: no), W-OI-RATE (about 10 a day is the sim's own rate), W-GOLDEDGES1 (nothing), retraction 16 (S-LIM1-LIVE was a script bug: NO avgFill must be flipped). Live state: OICORE cash net +31.05 on 74 settled, streak 1 of 24, drawdown 30.9 vs $60 own-peak stop; gold reopened Sun about 5 PM CT (17 contracts incl +3 add-on); stop headroom about $110 at base 979.25. Pitfall: watch workers must pass the report path to the tracker scripts.
