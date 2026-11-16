# Research audit log

Independent weekly audit of the research chats' results (read only; the audit never edits research branches). One line per result: id, date, verdict (VERIFIED, MISMATCH, COULD_NOT_VERIFY), why.

## 2026-11-09 (first audit; raw sqlite files and scan ledgers are not on any branch)
- W-OIBIGLOSS1 / OICORE net since Nov 1: VERIFIED as of Nov 8 01:33Z: 56 fills, 9 wins, fill-booked +22.77, limit-booked +9.61. STALE now: through Nov 9 00:50Z it is 65 fills, 10 wins, fill-booked +14.86, limit-booked +1.70.
- W-WEEKPNL1: VERIFIED for the limit-booked figures (OICORE 7d 51 fills +8.05; since the Nov 6 deploy 13 fills -19.54; EVENT830 5 fills -1.46); fill-booked 21.00 vs their 20.21 (small, same sign).
- W-OIPARTIAL1, W-OIEXIT1, W-OISWEEP1, W-ESRATE1: COULD_NOT_VERIFY (candle and recorder data and sim trigger files are not committed); registration order and internal arithmetic only.
- Fee rescore at 10 contracts (V2 harness finding): COULD_NOT_VERIFY (no rescore file committed); direction is right; "no verdict changes" is plausible, not proven (COMBO3 1.398 + 0.07 is about 1.47, thin).
- HISTBTC1, HISTETH1, COINRACE1, COMBO1 to 3, BINPATH, SERIESLAG1: counts and profit factors COULD_NOT_VERIFY (raw data absent); N and z arithmetic VERIFIED (1,290,505 gives z 5.373; 1,450,505 gives z 5.394); SERIESLAG1 NOT_ENOUGH_DATA is correct by its own rule (n 44 under 150).
- Discrepancies: HISTBTC1 registered 22,502 development rows, result says 22,605 (unexplained); registration and result commits are 24 to 123 seconds apart and the scan ledgers are not on the branch, so registration-before-result is not provable from git; HISTBTC1 and HISTETH1 both report exactly 2,079 held-out markets (recount).
- Stronger than the evidence: "family closed" on the Jun to Aug 2026 feed (a quote-regime caveat V2 states itself); OICORE live 16% vs 28% sim is p about 0.03 to 0.04 unadjusted across several looks.

## 2026-11-09 follow-up (V2's answers, V2 commit 861f41d, workers/DATA_CHECKSUMS.txt)
- 22,502 vs 22,605 dev rows: PLAUSIBLE, not proven: the fetch loop was still growing the table between the protocol (6,023 markets) and the scans; verdicts do not hinge on it (best PF 1.384 vs bar 1.5). Fix agreed: freeze the table (row count and hash) in the protocol.
- 2,079 held-out markets in both HISTBTC1 and HISTETH1: RECOUNTED by V2 (each 22 dates, close from 2026-07-15, same windows in both series); accepted.
- Registration order: agreed fix: push the registration commit alone and cite its hash and the ledger file in the result; ledgers for HISTBTC1 and HISTETH1 are now on the branch.
- 10-contract rescore: V2 will commit a script and rows (still open); COMBO3 about 1.47 stays "thin, not a survivor either way".
- Wording: "closes the family" becomes "not found on this feed (Jun to Aug 2026 quote regime)".

## 2026-11-16 (covers Nov 9 to Nov 15; about 2,000 research commits across 8 branches, so sampled by newest committed scorer; raw quote-data and kalshi-pull-data files were not pulled)
- UNDERDOG2X (History Miner): VERIFIED on sign and size. Order of events good: registration 94f4d88a 15:59Z, hand case 16:00Z, reader 16:01Z, print 16:03Z, all Nov 15; cuts are date constants; Amendment 2 (SOL cut) came before the read. Own reproduction from the research-data archive (variant b, 2x or hold, thirds 1 and 2, 1c haircut, own code, no rep.sqlite source): PF 0.63 (theirs 0.63), n 13,348 vs their 15,244 entries pooled over three variants (counts not like for like); 0c 0.70, 2c 0.57. 0 of 60 passes is credible. Open from the queue: Auditor B clearance of the pre Oct 3 held-out list is stated, not shown.
- MMSIM1 FALSIFIED on development, DEPTH1 held-out FALSIFIED: COULD_NOT_VERIFY figures (quote-data book and trade files too large to unpack here); process VERIFIED from the queue and git: DEPTH1 scorer and 10 features frozen Oct 30 (5334c171), read Nov 14 once; two independent builds equal on 334 of 360 figures, the f7 difference fixed and re-run, verdict independent of it (best z 2.74 vs bar 5.27). MMSIM1: two builds equal to 1e-15 on 168 events; verdict rests on a rule choice (Rule P vs registered Rule Q: PF 0.18 vs 1.41, same data), recorded by the Head as a reading.
- OICORE proven-bar 100 read (refine-live f7b63a4f): process finding. At 17:27Z Nov 14 an hourly dry run in report mode consumed the real read-once marker for the 100 read; only the verdict word was seen. Disclosed in the commit, fixed (f101f01a, e5099fbf), Head ruled the canonical path decides. Not a mismatch, but a one-shot read was spent by accident.
- Not reached: ENGINE1, ADJWIN1, S3 scorer, SIBHIT, IGFADE1/IGUNDER1, FAV10-X, CALIB1/2 (registered, no result yet or newer than this pass). Their registration-before-data order is committed first per commit titles, not independently timed.
