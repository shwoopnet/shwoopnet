# W-CALENDAR1: what is due next (written Nov 6, 2026 11:10 AM CT, 17:10Z; CT = UTC minus 6 since Nov 1)
Read only. Sources: kalshi-scalper/REFINE_STATUS.md (top entries, newest first), scratchpad interim_40.md, TOOLBOX.md.
Scratchpad root (S) = /tmp/claude-0/-home-user-shwoopnet/76de750d-5e48-584f-a0fa-77e7d05b9163/scratchpad
Resume recipe: export KALSHI_REPORT_TOKEN (never print it), cd S, run ./wake.sh (dash.sh fetches the report; fwd_all.py, wake_shadows.py, trackers run). Log with logentry.py. Always python3 -I.
Trigger ids are listed under "Scheduled triggers" near the end of this file. Items below say "wake.sh flag/tracker" or "note" where no trigger exists.

## Dated list (US Central, with Z)
1. PAST (Fri Nov 6, 12:24 PM CT, 18:24Z): oldest big loss (-11.18, gold 26NOV051330-30) left the rolling 24h window. The headroom figure (-$44.45 at 16:53Z vs stop line -55.9 to -62.2) was a Nov 6 snapshot and is stale; rerun `stop_room.py` (in wake.sh as STOP ROOM) on a fresh report. Note W-STOPCODE1: L1 does not pre-test an order against the stop; one more gold early sell (about -$10 to -$11) could trip it before 18:24Z. Only the owner can Stop or hold gold.
2. PAST (Fri Nov 6, 1:09 PM CT, 19:09Z): second loss (-10.45) and -1.17 at 19:27Z left the window, as did -3.25 at 02:12Z and -10.76 at 04:39Z (Nov 7). Still ahead: -11.25 at 07:24Z and -10.31 at 12:09Z Nov 7. Rerun stop_room.py after each.
3. Sat Nov 7, about 9:00 AM CT (15:00Z): OICORE interim rerun trigger (47 fills at Nov 6 16:57Z, later counts in the report; code kills: streak 18, net under -$6 after 40 fills, and the ladder's own-peak stop of $50 at 10 contracts; none hit; wording per interim_40.md). Also the 40-fill yardstick looks for S-JUMP1 and S-SDIR1 (wake_shadows.py), C2 (c2_fwd.py; dead if losses <=1 or net > +$2 at 40). Information only, no filters, no size change.
4. About Nov 10 CT (script projection; interim_40 says Nov 14 to 16): S-BUCKET1 B5 reaches 40 fills (8 on Nov 6, 0 wins, -$6.10; registered note says Nov 14 to 16, the script's Nov 10 is optimistic, it needs 8 fills a day). Flag: net per contract <= +1c at 40. Judge vs B10 and sim win 7.0% (2.8 wins expected; 0 wins in 40 is surprising, p about 5%). Fires by luck about 70% even if sim is right.
5. Tue Nov 10, about 9:00 AM CT (15:00Z): C9 (Silver shadow, KXSILVER15M, c9_start 1793656800, c9_fwd.py, network) reaches 200 windows. Registered kill at 200: lost share > 12% or net < -2.0c. At 97 windows: net -2.71c, lost 10 (10.3%); P(net below -2.0c at 200) 0.67 resampled, 0.18 from history; P(lost > 12%) 0.11. No interim look registered. 400-window read Nov 18 (Nov 25 at 18/day). wake.sh flag "C9 200".
6. Thu Nov 12, 7:00 AM CT (13:00Z): R6 run `r6_final_fixed2.py --live` (fetches quote-data into mirror.git). The recorder's last data arrives Nov 13 to 14, so Nov 12 is partial. Recorder self-stops after 2026-11-13 23:59Z. Caveats in TOOLBOX (gold depth sum rebuilt; ok:false rows need --retry-only). Forward reads FLOOR1 and THIN1 (XRP, a paused market) also settle Nov 12 per CLAUDE.md.
7. Fri Nov 13: OICORE forward read (`oicore_nov13.py dash_report.json` on a fresh report; kill streak 18, net -$6 after 40; PF under 1.0 needs 100 fills, net under 0 needs 150; neither reachable; these are Nov 13 read rules, not code kills). Streak odds: kill 18 hits 14.5% by Nov 13, 44% by Nov 30 (W-OICORE-NOV13PREP1). The Ethereum smooth-climb rules are moot (Ethereum paused Oct 30).
8. Sat Nov 14: R6 rerun after the recorder ends (final data).
9. About Nov 15: S-LIM1-LIVE review at 20 tagged fills (28 tagged already on Nov 6, net +17.62; rule: revert the +1c slip if tagged net < 0; lim_review.py < dash_report.json).
10. About Nov 18: extended OICORE read at 100 fills; C9 400 windows. About Nov 19: C1 (gold+Dogecoin 90 to 92c, 80 settled).
11. About Nov 19 to 25: EVENT830 reaches about 15 fills. Report mean price paid (use avgFill) vs registered 14c to 18c (16.3c at real fills on 5 fills, Nov 7; the 27.6c was inferred and retracted). Ask the owner about ADDING a note (not moving the bar) only if the real mean exceeds about 20c. Do NOT rewrite the registration.
12. Dec 7: EVENT830 INTERIM read only (fills, wins, net, price paid vs 14c to 18c, releases left; no pass/fail unless a kill fired). 40 fills not reachable by Dec 7 (Dec 10 at best, probably 2027). Kills: net under 0 at 40 fills, 20 loss streak, reviewedAt 2026-11-05.

## Open-ended trackers (no date; need fill counts)
- goldfwd (since 2026-11-05T16:27:35Z, w_goldfwd_bkt): 20 fills Nov 6, 5 losses, -$40.36, PF 0.25, break even 8.32%. Flag at 100 fills (none yet). Rate of 13 to 20 a day means about Nov 10 to 12.
- S-GPB1 (gold fills < 0.90 since Nov 4 09Z): UNRECONCILED, 4 fills here (17:10Z) vs 6 in REFINE_YARDSTICKS.md (16:58Z); flag at 40 (PF < 1.0). Far off.
- S-GOLDEXIT180 (cutoff 2026-11-06T17:00Z, goldexit180_fwd.py, wired into wake.sh): empty on Nov 6. Prints at 40 and 100 gold fills; adopt only if the shadow beats actual by > 0.5c per contract in both halves at 100 settled fills, else drop. Caveat: sale price is the candle bid. (W-GOLDEXIT180-AUDIT1: with realistic slippage the edge over hold is gone.)
- S-RISEFWD (cutoff 17:00Z Nov 6): read at 40 settled OICORE fills with rise >= 150,000 (probably months). Matters only if > +5c per contract above the 86.3k to 150k group, both halves positive.
- S-EDGEFWD (cutoff 17:00Z Nov 6): read at 20 settled edge fills (raw c-180 price strictly between 0.04 and 0.05). Matters only if >= 5c per contract below the others and negative in both halves.
- floor05: flag at 20 settled floor fills (13 A, 19 B so far), c per contract under 0.
- S-FLOW2 (needs 150 windows; diff -0.77c vs +2c pass bar) and S-FLOWL1 (gold, read at 20 early sells, earliest about Dec 1) kept until their registered reads.

## Report fix #729 follow ups (deployed: deploy-latest.sh ran Nov 6, Nov 7 data carries avgFill; rerun now)
On a fresh ?orders=1 report carrying avgFill and avgFee: (1) rerun w_costgap/run.py and w_event830_fee/fee.py (gold gap 0.33c, OICORE 0.62c; separate slip from fee rate); (2) rerun w_realpnl/real_pnl.py; (3) rerun W-GOLDSLIP1 with real fills; (4) recheck exit sale prices (W-GOLDEXIT-DEPTH1 used the order price: 15 of 16 gold exits sold below 25c, 11% extra loss). #733 adds exitAt, exitAvg and exitBid to the report, so redo it with the real exit price once #733 is deployed.

## Standing rules
Nothing here changes trading code, sizes or rules; Stop/hold decisions are the owner's. Interim reads: no new filters, no new splits, say "interim, not the Nov 13 read".

## Scheduled triggers (ids, from the refine session, Nov 6 2026)
- OICORE interim look Nov 7 15:00Z: trig_015tTohBPyF9B78WCsodgg2K
- R6 `r6_final_fixed2.py --live` Nov 12 13:00Z: trig_01K8HM7RsYAPmiDEEuqfvTcu
- OICORE Nov 13 read 15:00Z: trig_014htjG1o4wNqh61d6TgB4Wt
- EVENT830 Dec 7 14:00 CT (an INTERIM read; 40 fills will not be reached by then): trig_01AEWCMLQEdqT6R4bP1tgQY4
- Hourly routine (cron 32 * * * *): trig_017HTDZNKWfyBephf72bqcaG
The scratchpad scripts named above live in the refine session's scratchpad, not in this repo.

## deploy-latest.sh status (Nov 6 2026)
- Ran Nov 6 per main (main said about 12:15 PM CT, but the machine clock then read about 11:20 AM CT, so the time is unconfirmed: read the report deploys stamps). Live: skip reasons (kalshiSlotSkips, report skips section), #729 (avgFill, avgFee) and the #699 OICORE ladder.
- To do: read skips byReason for new OICORE triggers with no order (W-OICORE-SKIP1; the 16 earlier gaps cannot be explained); rerun cost gap, fee and slip checks on orders carrying avgFill and avgFee; treat OICORE dollar figures after the deploy as the ladder, not 10 contracts.

## Gold quiet hours
Not live: QUIET_HOURS_CT is empty (lifted Oct 30). No block review is due; S-GQH1 is history only.
