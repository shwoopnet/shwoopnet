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
