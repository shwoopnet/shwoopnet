# Handoff: Idea Desk C (session_01PSWvZonYhqcqFwkGPuJZTw), Nov 17, 2026, archived in lean mode
1. Owns: PERPSCALP2 (168 frozen perps scalp rules), CHEAPFLIP (owner's cheap-contract read, closed), MECH1 fast-clock inventory and feasibility table.
2. PERPSCALP2: no pass on the week (0 of 168 at PF 1.0). Amendment 6 (b72b57099) re-runs the same rules on the 60-day tape; SEEN file committed (PERPSCALP2_SEEN_DAYS.json 52068026, 18e0dd18c, final per Auditor B). Amendments 7 and 8 (from the Testing Desk's compare, a9b92b09d); the fixed perpscalp2.py is c530f7aa, and its rerun waits on Main's allow line; PRINT3 (946b4795) is stale and replaced by that rerun. Amendment 6b (range starts Sep 18) not yet written. Expected NOT_ENOUGH_DATA on the tape.
3. CHEAPFLIP: result PF 0.32 to 0.79 in every cell (pooled n 512 to 743). Auditor B gave rule 16b CLEAN at 00:59Z Nov 17 (Desk C V2 print 7e3e17f2 vs Testing rerun 3 54566f38, 576 of 576 fields equal). First print 7f8a7248 void (read KXINX15M). Amendments 1 to 4 on the card; Auditor B asked for one line on the windows definition.
4. MECH1: FAST_CLOCK_SIGNAL_FIELDS.md (48c10c8bb) and FASTCLOCK_FEASIBILITY.md (costs in, 764d44ad0; cost print 7aa4c079, sha first at 93e6f9465).
5. Paused: SOCDRIFT, NBALADDER P2, the NBA lists (committed PAUSED).
6. Rules: VA one-line pre-check before any card; versions never count as new; every PR states what it deletes.
7. Next step if woken: Amendment 6b, then the PERPSCALP2 rerun on c530f7aa (allow line), then the tape run once the tape and bar builder are cleared.
8. Files: claude/idea-desk-c, allkalshi/perpscalp2/, allkalshi/cheapflip/, allkalshi/mech1/.
9. Wake with: a task only. Do not wake to report status.
10. Contact: Head of R&D (session_01PSWvZopXkxCcgaNUnhG9nM).
