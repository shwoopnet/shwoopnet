# Audit of Nov 11 refinement FAILs (offline, read only)

Scope: the 8 files in refine_tools plus the five scratch dirs. Reran only local scorers on existing local files (w_sweep summary.py on a copy of cells.csv, w_pol_census cnt.py and score.py). No held-out file touched, no heldout.py run, no network.

Bottom line: no look-ahead leak and no false pass found. No FAIL flips to a pass. Three verdicts are worded stronger than the data supports (UNDERPOWERED or DATA_LIMITED would be the honest label), and one sports cell family is cut off by a sampling cap, not by the data.

## 1. W-SWEEP-EXT1 (external signal sweep): CONFIRMED FAIL
- Checked: spot read at the minute ending at the look (no peek), tercile cuts from TRAIN only, side from the sign of a pre-look feature, window result never used to pick a row, fee 0.07*p*(1-p) applied to the slipped price (slightly harsher than +0c), day-clustered z, held-out frozen at 17:57 and read once at 17:58.
- Grid count: 15 x 3 x 2 x 3 x 3 x 4 = 3,240 is right. The registered 1,512 and 1,728 were half the true grid (14 features is 3,024), already corrected in the RESULT. N = 5,319 + 900 + 3,240 = 9,459, Bonferroni z 4.55. Reproduced: 1,460 cells with validation n >= 60, 8 at naive z 2, 0 at 4.5, 33 expected by chance.
- Shortlist rule reproduces: 4 cells pass, the top 3 by validation lower bound were frozen (2362, 330, 2277). [live figure removed, ask Main] That is rule-compliant, not leakage.
- Held-out: all three PF 0.75 to 0.87 at +1c, mean negative. Cell 2362 had pooled z 3.75, still under 4.55. So the held-out did its job.
- Minor, not verdict changing: (a) the "Jun to Jul Bitcoin independent check" in the registration was never run; (b) feature `gb5` is "gold return" for BTC, ETH, XRP and "BTC return" for gold, fine but the label "gold-versus-BTC" hides that; (c) cfrti rows are kept only when the index result equals the Kalshi result (consistency filter, tiny n, no effect on the FAIL); (d) results missing in the candle file are inferred from the final bid or ask (0.98 rule), a few rows, no bias direction; (e) day clusters are about 16 per third, so cluster z is rough; the conclusion is a FAIL either way.

## 2. W-POL-APPR1 (approval and generic ballot calibration): CONFIRMED no edge, BUT label should be UNDERPOWERED / DATA_LIMITED, not FAIL
- No leakage: strikes picked by nearest-to-0.5 mid at the quote, quote is the last candle ending at or before the look, thirds by close date, held-out not scored. Fee and slip as registered (unrounded, +1c); live-3 replay uses the rounded fee, as registered.
- The registered rule says a cell with n < 30 per third is "underpowered, not passed". The result: 81 cells have train and validate obs, 0 reach n >= 30 in both. So the pass bar could not be tested at all. A cell with real negative evidence exists (ALL_APPR 6h 0.10 to 0.25 YES, z -2.7), which is a rule-out of buying cheap YES, not a FAIL of an edge.
- Coverage gap, undisclosed in the verdict line: events with usable quotes are APPR_DAILY 65, GCB 48, APPR_OTHER 11, APPR_RCP 8. KX538APPROVE got 0 events and KXAPRPOTUS 8 of 263 (the pull was stopped; historical RCP and 538 candles were never started). So APPR_RCP, APPR_538 and the "ALL_APPR" pool are effectively unscored. ALL_APPR is just DAILY + OTHER + 8 RCP events.
- [live figure removed, ask Main] (exploratory):" prints nothing (script ends before the loop). Cosmetic bug.
- Calibration header says "meanYESask" but prints the mid. Cosmetic. The calibration (YES overpriced at 10 to 25c: realized 0.111 to 0.127 vs mid 0.16 daily, 0.093 vs 0.164 GCB 1d) is descriptive only, n 54 to 212, same-week correlated; it is the only lead and it is not tradable after spread (the NO cells at 0.75 to 0.90 lose).
- Stale ledger: uses N about 8,190, now 9,459 (z 4.55). Does not matter, nothing passed.
- [live figure removed, ask Main] Finishing the historical pull (about 400 RCP and 1,278 538 requests) is the only way to test it.

## 3. W-CAT-SPORTS1 (sports calibration): CONFIRMED for ML and TOTAL; POSSIBLE FALSE NEGATIVE for SPREAD cheap longshots from a sampling cap
- Leak check: the original SPREAD and TOTAL pull kept the top 3 markets by FINAL volume per event, which leaks the outcome. The code already voids it (score.py skips SPREAD and TOTAL from the volume-picked files; candles_sp.jsonl redraws all strikes of random events; the VOID hist file is excluded). CONFIRMED correct. ML picks top 2 of 2 or top 3 of 3 markets, so the volume rule drops nothing there. The only residual is "volume > 0 at settlement" on events, mild and disclosed.
- Not recorded in PLAN.md or the result: the spread and total sample was cut from the plan's 120 events per series to 60 (`step2b.py`, by[s][:60]) and hist events cover only the 8 big ML series. This is why SPREAD cells have n 56 or 57 per third, 3 to 4 short of the n >= 60 floor.
- Pass-like cell that is NOT leakage: SPREAD 0.05 to 0.15, 1 to 6 h, YES, PF 1.62 train and 1.45 validate, but n 57 and 56 and lower 90 bound -3.6c, so it fails twice. The pooled calibration (SPREAD cheap bucket bias +8.7c, n 271) is counted across 3 looks of the same events, so the effective n is about a third. It is a lead for a larger SPREAD pull, nothing more.
- Mislabelled thirds: none. Cuts are over all events pulled (3,266), ML-heavy.
- Missing in SPORTS_CAL_RESULT.txt: a one-line verdict and event counts per type and third. Add before relaying.
- Verdict: FAIL stands for ML (n large, PF about 1.0, bias under 2c) and TOTAL; SPREAD is UNDERPOWERED by the cap, not tested to the registered n. Cheapest follow-up: pull all SPREAD events, not 60 per series.

## 4. Card 74 WXDAYEND (post-day-end window): CONFIRMED in substance, rule wording overreaches
- [live figure removed, ask Main] So buying costs 1.00 and there is nothing to earn. The close-time arithmetic (UTC day end 05:00Z NYC etc.) checks out, DST end Nov 1 handled.
- Bug in the argument, not the result: the registered rule is "fewer than 3 of 40 city-days". Only 20 were pulled (NYC 9, LAX 9, DEN 2, DAL 0), 0 of 20 qualified, and the text says the rest "could not change the verdict". They could (20 unpulled could still give 3). Call it FAIL on 0 of 20, DAL and most of DEN not read. The structural 0.99 / 1.00 book makes a pass very unlikely.

## 5. Card 84 MENTION-PERSIST (earnings mention persistence): CONFIRMED FAIL
- No outcome leak: candidates are chosen from the two prior calls only, the 50% subsample is an md5 of the ticker, the held-out third (by call) was never pulled, the 3-per-call cap picks the cheapest price. Fee unrounded, slip +0 and +1c, call-clustered bootstrap (seed 7).
- Close times of the markets are the call end (all strikes within seconds), so A minus 3 h is before the call for a normal one hour call. Not verified per call; a late-starting call would make the price post-call, but that would make the rule look better, not worse.
- Numbers reproduce: TRAIN 36 entries (29 calls) PF 0.58, VALIDATE 44 (36) PF 0.36, intervals -0.0014 upper and -0.0873 upper. Both n are under 60, so the registered kill bar and the DATA_LIMITED line both apply; the kill bar (PF below 1 and upper bound below 0) is met on its own. FAIL for the rule as written. The idea that the history sign is a weak fade is untested and would be a second try.

## 6. POLITICS_STEP2 (POL-c1, c2, k1; calibration): CONFIRMED DATA_LIMITED, nothing to flip
- No outcome-based selection: events kept by market life of 14 days or more from open and close times, strikes by every n-th sorted ticker, entry nearest 0.5, quote the last daily candle ending 14 days before close and at most 4 days older. Fee unrounded, +0c, matches the plan.
- Counts in PLAN.md are stale. The plan says c1 18, c2 42 (35), k1 17 (16); current cnt.py on the final 235-series pull says c1 99 (30 with 14 days; the regex also catches the generic-ballot and Vote series that belong to the approval test), c2 58 (47), k1 26 (24). The scored cand.jsonl covers c2 44 events and k1 19 (23 and 7 with an entry after the candle gap and price filters). It was pulled before the historical series list finished (cand.jsonl 19:29, hdone.txt 20:07), so the scored c2 and k1 sets are a subset. Still tiny (n 7 per third), so a larger set would not change DATA_LIMITED, but the plan numbers should be corrected.
- The 7 of 7 NO arm train and the YES arm 5 losses in a row are noise at n 7. The calibration step was never run (stated).
- [live figure removed, ask Main] Different bases in two files; do not compare their net dollars.

## Cross-cutting
- [live figure removed, ask Main] All FAILs are therefore FAILs a fortiori; no pass-like cell exists to be hurt by it. The +1c slip roughly covers the rounding.
- Ledger N: the sweep corrected itself to 9,459 (z 4.55). The politics, sports and cards files still quote 7,950 to 8,190 (z 4.5). Harmless today, update the common number before any future pass is judged.
- Pre-registered bars were not lowered anywhere.

## One-line verdicts
1. W-SWEEP-EXT1: CONFIRMED FAIL (held-out read once, all three negative).
2. W-POL-APPR1: CONFIRMED no edge, relabel as UNDERPOWERED (no cell reaches n 30; RCP 8 of 263 and 538 0 of 143 events pulled).
3. W-CAT-SPORTS1: CONFIRMED for ML and TOTAL; SPREAD is cut off by the 60-event cap (n 56 and 57 vs the 60 floor), so a possible false negative until more events are pulled.
4. Card 74: CONFIRMED (book sits at 0.99 bid and 1.00 ask), but the stop at 20 of 40 city-days is not licensed by the registered rule; word it as 0 of 20.
5. Card 84: CONFIRMED FAIL (kill bar met in TRAIN and VALIDATE, n under the floor).
6. Politics step 2: CONFIRMED DATA_LIMITED; plan counts stale, scored sets are a subset.
