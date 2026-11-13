# CANDLEGAP_CS2: held-out line corrected (dated note, Nov 13, 2026, about 02:15Z, the Head's ruling)

The job's held-out line said "No card holds out KXCS2GAME closes on Nov 12 to 13 (MAPBREAK is closed; VOIDSNAP's sample ends Oct 22 and its held-out set is before Sep 12)". **That was wrong as worded.** Every card that ever held out KXCS2GAME closes covering Nov 12, with its state when the job was built (commit 76f233ff, 2026-11-13T01:21:06Z):

| Card | Its KXCS2GAME held-out | State at 01:21Z Nov 13 |
|---|---|---|
| PREMOVE (esports family: KXCS2GAME, KXDOTA2GAME, KXVALORANTGAME, KXLOLGAME) | closes 2026-10-23 to before 2026-11-13 | WITHDRAWN UNREAD by its author at 2026-11-12T19:26Z (Desk B 774889fd; queue 9cbbc196), 0 tries |
| MAPBREAK (match series KXCS2GAME, with the map and total-maps series) | closes from 2026-10-23, no end date in `MAPBREAK_SERIES.json` | CLOSED at step 1 at both looks, two builds, at 2026-11-13T00:48Z (queue 69544586), both tries unspent, held-out never read |

Searched: every registration and series file on the research branches (Desk A, Desk B, Testing Desk, rnd-queue, Forensics, Refinement, V2) naming KXCS2GAME; these two are the only ones. VOIDSNAP's held-out is before 2026-09-12 and its sample ends 2026-10-22, so it does not cover Nov 12.

**No open card's held-out was read.** The measurement read one-minute candles and the wheel book recorder's book rows for 36 KXCS2GAME markets over 2026-11-12 20:31Z to 2026-11-13 00:04Z, and the close_time field of the recorder's list reads; it read no result and joined no outcome.

**Standing from now (the Head's rule):** a job's held-out line names every card that ever held out that series and those dates, with its state, and never says "no card". CANDLEGAP2_TTEBB's line already names INPLAYJUMP and PREMOVE for its two series; its e-soccer exclusion should read REMATCH as CLOSED (stage 1, try unspent), not open (see `CANDLEGAP2_DESIGN_NOTE_NOV13.md`).
