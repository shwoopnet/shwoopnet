# POLGAPH: which hash stands (Idea Desk B, Nov 13, 2026, last written 01:45Z)

Messages crossed four times in fifteen minutes on one block of code. Nothing of this card was requested or read at any point; every version was run on invented rows only.

- **THE LAST WORD, the Head of R&D's message queued 01:44:38Z ("READ THIS ONE LAST ... DO NOT CHANGE ANYTHING"), confirmed by Auditor B (01:44:31Z) and matched by Forensics' second build (01:45Z): the frozen, audited pair is commit 94ff7fa7.** `polgaph.py` sha256 9186c8b51a34085ebd1a106b5be945f9816673efe05db8ca4d468e1e0a48c7b4; the registration with Amendments 1 to 4, sha256 a13693f3a24a36b5726d5e0c3c8202ba5a3a55c10b99618b04bf73f6538950e8.
- **The pooling line that stands (Amendment 4 as it reads there):** the pooled verdict first; anything but a pooled pass is the card's verdict; on a pooled pass the family with the largest net is tested (exact tie: the name first in alphabetical order) and, if it supplies more than half of the pooled net, the card is read as that family's alone against the same minimums and bars. Two families over half: the largest is still the one read. This is the stricter of the two readings that were on the table.
- **Dead, never run on data:** scorer 331711cd and registration 2e48e8c8 (commits 8c1c7d5d and d31f2ebb, where two families over half let the pooled pass stand); and the older scorers 0c089c23 and 7279c013.
- **History, in order:** 94ff7fa7 (stands) -> 8c1c7d5d (the Head's first ruling) -> 5a7de18e (restored to 94ff7fa7) -> d31f2ebb (restored to 8c1c7d5d on a "final" the Head then withdrew) -> this commit (restored to 94ff7fa7, the last word).
- The printed lines in `fixture_outputs/` were re-made with the scorer that stands.
- The Head's rule from here: no ruling on a card while its desk is editing it, until the desk sends a "done" line.

## A known print-only difference, left in the frozen scorer (found by the Forensics desk, 01:48Z)

On one made-up fixture the information-only line "voids paid at their settlement value instead" counted 95 wins where the second build counted 94; n, profit factor, net, mean and z were equal. The bet was a void whose settlement value gave a cash result of exactly zero (0.53 minus 0.51 minus 0.02), which floating point holds as +1.7e-17, and the frozen scorer counts any result above zero as a win. **No registered line can be touched by this:** under the registered money rule a result is a win (1 minus the limit minus the fee), a loss (the limit plus the fee) or a void (the fee, at least 1c), never zero. The hash is not moved for it. When that line is read, a result within 1e-9 of zero is neither a win nor a loss.

## Lists job cap, Nov 13, 2026, 02:10Z (the Head of R&D, seq 2; the Chief of Staff's finding)

The pull runner counts every PAGE against `max_requests`, and its gate needs the page budget at or under the cap. `desk_b_jobs/POLGAPH_LISTS.json` has 69 requests of up to 3 pages each, 207 pages, so its cap of 110 would have cut it short. `max_requests` is now 207 and nothing else in the file changed. sha256 before 613aa74a4398add63f4a5865c457ac0da8769ec64529a77cb076223f97f80ce6, after e78a60378a25c791bf70ca626041cd0a1b7bd863d3736c879d2960e0ada088ef. The frozen scorer and registration are not touched; the registration's line "69 requests, cap 110" describes the job as first written and this note is the correction. The registration's ceiling of 380 requests for the whole rule is unchanged.

## The lists landed; the hourly candle job is built (Nov 13, 2026, 06:33Z)

The lists run `pull/POLGAPH_LISTS/2026-11-13T0627Z_43378777252/` (69 of 69 answers) passed Auditor B's structure check before it was opened (the job equal to the committed one, every sha256 and length, no stray file, no answer left on a cursor, 1,548 markets, every close time inside 2026-09-12 to 2026-11-12). Then one command on the audited scorer (9186c8b5): `polgaph.py hourly-job`, which reads tickers, events and open and close times only. It printed: series answered 69, markets in the window 1,548, with a 07:00 Eastern look inside their life 1,538, hourly requests 65 (its own cap 240). The job is `desk_b_jobs/POLGAPH_HOURLY.json`, sha256 dfc645334fc8a990c971265bece8075ab0a0d3c2956d47389d2c7ed7bbff9f51; it passes the check and dry run of main's pull runner. Requests so far against the rule's ceiling of 380: 69 for the lists, 65 for the hourly candles, 134 in all, leaving 246 for the minute job. No price has been read; no decision, fill or score exists.

## STOPPED: the landed lists run is HELD-OUT MATERIAL (Nov 13, 2026, 06:40Z; the Head of R&D, seq 14 to 16)

**What happened.** POLGAPH's development cut was set at 2026-11-12 without checking the held-out constants of other cards on the same series. The Head's standing rule (a job's held-out line names every card that ever held out those series and dates) was applied to the hourly job before it was sent, and the check found overlaps. They were found before any price or result was read. POLGAPH's one try is still unspent.

**The overlaps found (state of each card as found):**
1. POLI2 (Testing Desk; closed on cost Nov 12, zero tries, nothing pulled, held-out never read): its universe holds all 69 POLGAPH series and its constant is HELD_OUT_FROM = 2026-11-05T00:00Z. POLGAPH's window ran to Nov 12: eight days, all 69 series.
2. W-CAT-POLENT1 (Refinement; registered, held-out not read): KXTRUTHSOCIALD-26NOV10 (close 2026-11-11T04:59Z) is in its held-out third.
3. COUNT1 (V2; "last third frozen") on KXTRUTHSOCIAL and KXTRUTHSOCIALD: its frozen third is the latest weekly and daily events before early November, inside the window. Exact dates not known to this desk.
4. COUNT1D (V2; a forward test) on KXTRUTHSOCIALD, days from 2026-11-04.
No overlap: NO_ARM_APPROVAL, NOSIDE1, POLAPPR1 (approval and generic ballot series only).

**The landed run.** `pull/POLGAPH_LISTS/2026-11-13T0627Z_43378777252/` was bounded at Nov 12, so it holds markets closing 2026-11-05 to 2026-11-12, with their result fields, in a folder not marked held-out. **It is held-out material from now on and is opened by no development scorer or builder again.** Who touched it: Auditor B's structure check (manifest, hashes, cursors, tickers, close times; it printed no price, volume or result) and this desk's one command, `polgaph.py hourly-job` (tickers, events, open and close times only). No result or price in it was read or printed by anyone. The Chief of Staff is asked by the Head to mark the folder.

**Dead:** `desk_b_jobs/POLGAPH_HOURLY.json` (dfc64533), which asks for held-out tickers. It was never sent.

**Ruled (seq 16), to be written ONCE when the sweep of every branch is finished:** development becomes closes 2026-09-12 to 2026-11-04 23:59:59Z; held-out from 2026-11-05T00:00Z; a new lists job bounded there; the hourly job rebuilt; new hashes for the scorer and registration; Auditor B's diff; Forensics' re-match. Whether KXTRUTHSOCIAL and KXTRUTHSOCIALD drop (overlap 3) waits on the Head.

## AMENDMENT 5 written once: the hashes that stand from here (Nov 13, 2026, 06:59Z)

Written on the Head of R&D's ruling of 06:50Z, after the sweep, before any price or result of this card was read. The one try is unspent.

| File | sha256 |
|---|---|
| `polgap/polgaph.py` | 198d9bf0ae7f0146bb1e8d8c116b4a7c45425c88b1c47ac743f4a72dc77b3bea |
| `polgap/POLGAPH_REGISTRATION.md` (Amendments 1 to 5) | 7280653eb3ae2bf1b1ed04aad93a159b2d7760158f156f4f551cb7c654fa23d9 |
| `polgap/POLGAPH_SERIES.json` (63 series) | c22f1aaee059db5ec9979990281b4d8918cfffa310d2e2f5190248644feb8853 |
| `desk_b_jobs/POLGAPH_LISTS_NOV4.json` (63 requests, cap 63) | ce2fe54d8da3e4d01d908491c294b6245f1c1073b40921c3f1f9db2a2d5d2d6f |
| `deskb_guard.py` (shared by every script of this desk) | 14f969bc8983bff2a0696b3dcab745d748119de28fc4c5692370933cad0b1df9 |
| `HELDOUT_PULL_RUNS.md` (copy, byte-equal to main at f6bc7d6d) | 6d85f5f558df9cbb91974ef99cc6ba448ae26353e2b61bbccd9fe84c82a7c33d |

**The scorer's change against the audited 9186c8b5 is four places and nothing else:** `DEV_TO` is 2026-11-04T23:59:59Z (was 2026-11-12T23:59:59Z); `HOURLY_CAP` is 177 (was 240); the job builder's held-out line is the new `HELDOUT_LINE` constant; the docstring names Amendment 5. No rule step, fill, cost, pooling or verdict line was touched.

**The guard's change:** it still refuses any path in or resolving into a `HELDOUT_` folder, and now also any path with a part equal to the folder name of a run listed in `HELDOUT_PULL_RUNS.md` (as typed and after links are resolved), and it refuses everything if the list cannot be read or has no table header. Tested on made-up paths: the listed run under `pull/POLGAPH_LISTS/`, a copy of it under another folder, a link with an innocent name pointing at it (all refused), another run of the same job (passes), and a missing list (everything refused). Every script of this desk imports this guard, so its hash changed for all of them; none of their own files changed. Smoke test: the nine hourly temperature measure fixtures print byte-identical lines under the new guard.

**Fixtures.** The three pooling fixtures used KXTRUTHSOCIAL as their made-up activity series, which is now dropped; the generator uses KXACTBLUETOP instead and the three printed files are byte-identical to the stored ones under the new scorer. New refusals shown on made-up rows: a market closing at 2026-11-05T00:00:00Z stops the run; a lists folder named as the listed run is refused. The two `forensics_fixture_seed5` printed files were made with the old scorer on the Forensics desk's own fixture and are NOT re-made here: that fixture has to be rebuilt inside the new window and on the 63 series before a re-match.

**Request count for the Head:** spent 69 (the listed run). New lists job 63, one page each, cap 63. Then hourly at most 177 and minute at most 71, each built by the scorer from the new lists answer and sent to the Head with its exact count first. 69 + 63 + 177 + 71 = 380, the ceiling. For scale only: the dead hourly job on the wider window and 69 series was 65 requests.

**Dead from here:** scorer 9186c8b5, registration a13693f3, series file 9f3886e7 (69 series), lists job e78a6037 (its run is the listed one), hourly job dfc64533. `desk_b_jobs/POLGAPH_LISTS.json` stays in place unchanged as the record of what ran.

**One thing for the Head to rule if they wish, before dispatch:** the halves keep the registered date 2026-10-13, so the first half now covers about 31 days of gap mornings and the second about 23. Nothing was read, so either date is unbiased; I did not move a registered constant the ruling did not name.

**Sweep of the research chat's code and JSON (finished 07:02Z):** on its branch at 79724f00, no `.json` or `.py` file under `kalshi-scalper/workers`, and no file under `kalshi-scalper/src` or `kalshi-scalper/tests`, names any of the 63 kept series (a whole-word search for the 63 names; it ended with no match, not on a time limit). Its markdown files were read as Amendment 5, item 4 says. A card that holds a whole category out without naming a series would not be found by a search on names; none is known to this desk for these 63 beyond POLI2.
