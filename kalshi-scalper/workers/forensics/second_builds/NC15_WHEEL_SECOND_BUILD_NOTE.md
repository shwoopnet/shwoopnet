# NC15 depth-cell wheel replay: independent second scorer (Forensics desk)

**Written Nov 13, 2026, about 02:02Z, on the Head of R&D's order of 01:49Z.** Built from Desk A's frozen definition sheet v4 alone (`claude/idea-desk-a` at `8679f760`,
`DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md`, sha256 `c53d2b9f...`, sections 0, 2 and 3) and, for the block, `ROTATION_LANE.md` v1.2 section 4 on `rnd-queue`.
Desk A's `nc15_wheel_replay.py` (sha256 `b44c1d8f...` at `fc53341c`) was not read. No real NC15 row was opened: the scorer is default closed and ran on invented rows only.
Nothing here is a read of the registered NC15DEPTH1 cell, and no block data has been looked at.

## Files

| File | What it is |
|---|---|
| `nc15_wheel_second.py` | the second scorer: signal poll, cell, band, second look, walk and fill price, fee, result and void rule, then blocks and confirmation for the 7 places |
| `nc15_wheel_compare.py` | compares Desk A's printed records and per-series lines with my records file; reads printed output only |
| `make_nc15_wheel_fixture.py` | invented NC15 book and coverage rows for all 11 series over 40 days, with the awkward cases listed in its header |
| `NC15_WHEEL_SECOND_OUTPUT_fixture_seed{6,7}_MADE_UP_DATA.{txt,json}` | my figures on two fixtures |

Commands:

```
python3 -I make_nc15_wheel_fixture.py <dir> 6          (also seed 7)
python3 -I nc15_wheel_second.py <dir> --now 2026-12-23T00:00:00Z --records <records.csv>
```

`--records` writes one row a window (status, signal poll, exchange time, offset, imb5, side, ask, limit, second poll, sizes offered, walked prices, fill, fee, result, cash),
so the two builds can be compared signal by signal and not only on the block lines.

## What the two fixtures hold (mine only so far)

| Outcome | Seed 6 | Seed 7 |
|---|---|---|
| a block that clears and its confirmation QUALIFIES | copper, BNB | copper, BNB |
| a block that clears and its confirmation fails | USD/CAD | USD/CAD |
| a block that grows past 60 for want of 10 losses | BNB (67) | BNB (84, waiting) |
| a block that fails on the profit factor or on a half | WTI, silver, USD/CAD | WTI, silver, USD/CAD |
| a block that fails on "one day over 30 percent of the net" | copper block 1 | natural gas |
| 60 signals on fewer than 7 days | natural gas (every block) | natural gas |
| 60 signals spanning more than 21 days | HYPE (37.9 days) | none |
| a block that waits on an open result | none | natural gas, HYPE, BNB |

Invented rows; the figures mean nothing about any market. The comparison with Desk A's scorer on the same rows is the next step.

## Compared with Desk A's scorer, record by record (Nov 13, about 02:07Z)

Desk A's scorer (`nc15_wheel_replay.py`, sha256 `b44c1d8f...`) was run by me, unread, from a checkout of `claude/idea-desk-a` at `fc53341c`, through its record printer:
`python3 -I desk_a_verify/nc15_wheel_replay_records.py <dir> 2026-12-23T00:00:00Z`. `nc15_wheel_compare.py` reads its printed lines and my records file.
I read Desk A's build notes (`NC15_WHEEL_REPLAY_NOTES_NOV13.md`, text) only after my first build, and took its written choices 1, 2, 4 and 5.

| Fixture | Records the same in status | Status differs | Record figures compared (side, ask, limit, imb5, fill, fee, cash) | Differ | Per-series report figures | Differ |
|---|---|---|---|---|---|---|
| seed 6 | 20,994 | 0 | 18,343 | 0 | 63 | 0 |
| seed 7 | 20,993 | 1 | 18,383 | 0 | 63 | 4 (all from the one record) |

**THE FIRST DIFFERENCE (seed 7, one record):** a fillable signal whose coverage result is `scalar`, on a market that closed 2 days before the read. The sheet says a final
value that is neither yes nor no is booked under the void rule (fee-only loss, counted). My build books it as a void at once. Desk A's build prints it as PENDING, and books
it as a void only once 7 days have passed since the close. The cash in the end is the same; the difference is that a block holding such a signal would wait up to 7 days
longer than the sheet says. (On both fixtures, every such signal older than 7 days is a void in both builds.)

**Two readings I changed to match, each a legitimate reading of the sheet, both now switchable in my build:**

1. **The 6 seconds to the second poll are measured on exchange time** (each poll with its own offset). I had used the recorder's clock. With my first reading 54 records
   on seed 6 differed, all of them cases planted at 6.000 s and 6.001 s. A caution worth a line in Desk A's notes: the difference of two offset estimates adds up to about a
   second of estimation noise to a gap the recorder's own clock measures to the millisecond.
2. **A row with no readable Date header can be a poll**, with an offset from the earlier header-readable rows of its run. Desk A's note 3 says such a row "is never a poll";
   its code, like the sheet's text, does not exclude it. With note 3's reading 41 records on seed 6 differed. A caution: in a run with almost no readable headers those
   41 polls take their clock from a handful of rows carried over from another run folder.

**Two more things seen, neither a record difference:**

- **A counting gap in the first build's report:** windows whose polls have no clock at all (480 on seed 6) appear under no reason in its "no signal by reason" counts.
  The sheet says every missing item is counted by reason. My build counts them as "no signal: no clock".
- **The block bar has no first build.** Desk A's note 9: its scorer outputs records, per-series counts, cash and profit factor, and the pending list; the block bar
  (60 fillable signals, 1.3, halves, days, confirmation) "is the lane's" and is not built there. So the block lines in my output have nothing to be compared with yet,
  and three of their readings are open (below, 3 to 5).

## Places where the sheet or the lane leaves a choice

The scorer prints its readings with its output. The ones most likely to move a figure:

1. **How the 6 seconds to the second poll are measured.** Now exchange time, as the first build (see above); I first used the recorder's clock.
2. **A ticker in two run folders.** The signal poll is the latest by exchange time over all run folders; the second poll is the next poll in the SAME run folder (Desk A's choice 1).
3. **What a block is when its 60 signals fall on fewer than 7 days, or span more than 21.** I read both as FAILED, and the next block starts after it. The lane text can
   also be read as "the block keeps growing until it has 7 days".
4. **The rarer outcome for a rule that buys either side at 10c to 90c.** I need 10 wins AND 10 losses (a void is neither); the block grows one signal at a time until then.
5. **The 30 percent day rule** is tested only when the block's net is positive. **A day** is the US Central date of the decision instant.
6. **Halves** of a block of n signals are the first n // 2 and the rest.
7. **Open results.** A block that holds an open signal waits, and so does everything after it. A signal is open until 7 days after its close, by the `--now` time.
8. **The confirmation's 30 signals** belong to no block; the next block starts after them.
9. **The offset** uses rows of the same run with a receive time at or before the poll's, all rows of the same instant included.
10. **Result from two run folders:** a yes or no in either wins over an empty value; two that disagree stop the run.

## Limits

- Records and per-series totals are compared with the first build; the block lines are not (no first build of them exists). Nothing here is a verdict of any kind.
- The fixture's polls are regular; real NC15 runs have fallback reads and gaps that may hold shapes neither build has met.
- The later public result read (the Chief of Staff's list job) has no input in this build yet: results come from the coverage files only.
