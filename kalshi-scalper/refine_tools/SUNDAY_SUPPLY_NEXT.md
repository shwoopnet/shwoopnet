# Sunday supply next (for Sun Nov 15, 7:17 PM CT), DRAFT from verified results only, 2026-11-10

PF first: live cash PF is 1.20 over 14 days (249 orders, +$44.23, 81% of bootstrap weeks positive) and 1.24 over 28 days (358, +$61.97); last 7 days below 1 (-$16.2). Gold 1.14 (157 orders), OICORE 1.30 (81 orders, 14 wins). Research bar is 1.5 in each of three windows after fee and after deflation (N tried about 890, Bonferroni z about 5.2). Nothing is at the bar.
Honest summary: 0 new rules, 0 new candidates this week. No idea passed an independent window except the already registered shadow rules (section 2). Basis: cash, PF per contract, unrounded fee, hold to settlement.

## 1. Ideas tested this week (backlog rows 1 to 61, Nov 10 dispositions); N tried about 890
- FAIL: row 4 silver L1 (PF 1.15, n1255, 0.98 at +1c); 5 volume surge (V1 0.98 n62, V2 0.81 n126); 7 gold vs hourly ladder (0.83 / 0.63); 9 fee batching (uplift -0.001); 13 8:45 ET window (0.68 vs control 0.66, n143); 17 gold vol-by-session (no negative cell); 18 OICORE 120 s entry (P3 n5, only +0.17 over base; re-test forward); 19 adaptive OI (n under 40); 21 equal-dollar sizing (two-half bar missed); 24 grind vs gap (76 of 77 are gaps); 25 loss clustering (9.1% vs 7.4%, p 0.49); 28 OI burst (interval spans zero); 29 XRP spot gap (0.97 n37); 40 XRPYES10 on hourly ladder (0.53, n135); 41 perp premium (diff -1.92c, spans zero); 53 weather nowcast (0.72, n136); maker replay W-MAKERREPLAY1 (taker 1.27, maker-filled 1.16, fill 66.9%); band floors 0.945 and 0.93 (KILL).
- Not runnable or repeat: 15 stale quote (0 of 558 fire); 37 fee audit (all series multiplier 1, no cheaper series); 38 gold resting entry (closed with maker replay); 42 and 47 (repeats); 50 (0 of 2000 strikes match); 61 dropped (no box office series).
- Not enough data: 14 thin-bid skip (kept 1.55 n275 vs skipped 1.02 n45); 20 OICORE book imbalance (kept PF 1.90 vs 1.11, H1 spans zero); 22, 23 (12 touches); 26, 30, 31, 39, 43, 44, 45, 46 (P1 1.27 n31), 48 (holiday 0.95 n58), 58.
- Passed its own bar, stress-testing: row 3 gold spot gap S1 (3.15 / 4.20 at +0c; only 876 of 1,679 favourites had PAXG data). Row 16 is S1 with a noisier sigma, not independent evidence.

## 2. Shadow candidates (registered, PR 753; none is a pass)
- GOLDALL: independent Aug 13 to Sep 1 PF 1.60 (439) / 1.36 at +1c. Also the forward test for S1. Forward read 2026-12-14.
- GOLDHI6S: 1.68 (265) / 1.35 at +1c. Needs deploy-latest.sh (PR 753). Read 2026-12-14.
- XRPFAV6: 1.645 (137) / 1.46. Prior low (live XRP 0.49 over 65 fills, paused). Read 2026-12-14.
- XRPYES10: 1.91 (70) / 1.66. On main. Read 2026-12-14.
- Common bar: 150 forward signals, PF at least 1.3, second half at least 1.2, 14 days, no day above 30 percent of net. Not offered: Bitcoin, Ethereum, silver, longshots, ladders, 54-series scan.
- Caveats: gold net is thin (+1.5c GOLDALL, +1.0c GOLDHI6S at +1c); the independent gold window is 3 weeks; shadow rows assume a fill at the touch. OICORE gap check (W-OIGAP1): model PF 1.69 became live 1.30, mostly period (1.80 before Oct 30, 1.21 since), not execution; live win rate 17.3% vs 26.7%.

## 3. Owner approval items pending (nothing live, nothing built without a yes)
- Forward logs, log-only PRs (FORWARD_LOG_PACKET), build order 32 plus 35, then 34, then 33: row 32 book snapshot on orders (one public read per order); row 35 spot stamp on orders (adds an outside host, flag for the scan and host gate); row 34 qualified-but-no-order rows (new collection plus rules deploy); row 33 exit watch bid reads (touches safety code, strictest gates).
- Public-data recorders (FORWARD_LOGGERS_PACKET), recommended yes on 55 (OKX liquidations vs Bitcoin 15 minute) and 52 (rain vs NWS PoP); 56 (ESPN lines) only if the terms risk is accepted; 60 and 54 as a tiny add-on for the Dec 8 to 9 FOMC; 57 drop. First read of 55 or 52 is about January 2027.
- Row 36: extend R6 for gold only past Nov 13 (28 days, same public endpoints). Decision needed before the R6 auto-stop at 2026-11-13 23:59 UTC.
- Income (DEC 9 page): about $70 to $100 a month today; $2,000 a month needs 21x to 30x the size. Size is not the lever until PF is well above 1.2 with a named counterparty.

## 4. Dated reads calendar
- Nov 11: weather row 49 scoring (registered Nov 10, not yet run).
- Nov 12 13:00Z: R6 read (r6_final_fixed2.py --live, back up oi/ first); also the research FLOOR1 and THIN1 forward reads for XRP (from CLAUDE.md).
- Nov 13: OICORE forward read; R6 recorder stops 23:59 UTC.
- Nov 14: maker replay on the full R6 set (15:00Z); the 13 day gold replay already FAILED.
- Nov 17: EVENT830 re-read after the release (row 30); Nov 20: OICORE night split at n 50 (row 10).
- Dec 1: ETH-scaled OICORE (row 8); Dec 3: row 27 ETH confirmation; Dec 7: EVENT830 read (first result 0 wins in 10 orders, -$1.30, an anecdote).
- Dec 9: income checkpoint. Dec 14: shadow candidates forward read. Later: row 23 about Feb, row 39 about mid Feb 2027.
