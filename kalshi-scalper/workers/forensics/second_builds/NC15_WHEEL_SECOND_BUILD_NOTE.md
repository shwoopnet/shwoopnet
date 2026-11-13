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
| `nc15_wheel_block_compare.py` | compares Desk A's printed block lines with mine, block by block and state by state |
| `make_nc15_wheel_fixture.py` | invented NC15 book and coverage rows for all 11 series over 40 days, with the awkward cases listed in its header |
| `NC15_WHEEL_SECOND_OUTPUT_fixture_<name>_MADE_UP_DATA.{txt,json}` | my figures on six fixture reads (seed6, seed7, seed6_confexp, seed6_ties, seed6_openexp read on Dec 26 and on Dec 30) |
| `NC15_WHEEL_FIRST_BUILD_BLOCKS_fixture_*_reader_2921a03a_run_by_forensics.txt` | Desk A's block reader output on the same fixtures, as run by me |

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

## Nov 13, about 02:12Z: the Head's rulings applied, and the block layer compared (SAME on both fixtures)

The Head of R&D ruled the open readings at 02:05Z and wrote them into `ROTATION_LANE.md` section 4 (`rnd-queue` 7c4c71d2): a block keeps growing until it holds 60
signals, 7 different days and 10 wins and 10 losses; a block not complete within 21 x 24 hours ends unread and is EXPIRED; a day is US Central from the signal poll's time;
halves are the first floor(n / 2); the 6 seconds are on estimated exchange time. Desk A built a block reader from that text (`desk_a_verify/wheel_block_reader.py`,
sha256 `aee149e7...` at `93a02b44`), and its signal scorer is now `nc15_wheel_replay.py` sha256 `8d1055df...` (the hash the note above names, `b44c1d8f...`, is the earlier one).
I rewrote my block layer to the rulings and ran Desk A's three commands myself, unread, from a checkout of `93a02b44`
(`nc15_wheel_replay_records.py`, `nc15_wheel_records_csv.py`, `wheel_block_reader.py --kind=either`); its block output reproduces its committed files byte for byte.

| Fixture | Records the same in status | Differ | Record figures | Differ | Per-series figures | Differ | Blocks (both builds) | Block figures | Differ | Place states | Differ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed 6 | 20,994 | 0 | 18,343 | 0 | 63 | 0 | 15 | 243 | 0 | 7 | 0 |
| seed 7 | 20,994 | 0 | 18,390 | 0 | 63 | 0 | 14 | 226 | 1 (print only) | 7 | 0 |

- **The scalar-result difference is gone** with Desk A's `8d1055df`: both builds now book a final value that is neither yes nor no as a void at once.
- **The one differing block figure is print rounding of an exact half cent.** Copper block 1 on seed 7 has a net of exactly $121.305; one build prints 121.31 and the
  other 121.30. Every other figure of that block is the same, and the net is not a bar. Printing the net in tenths of a cent would remove it.
- **Three conventions I took from Desk A's block reader, which the ruling text does not spell out** (put to the Head for a yes): a void counts as a loss when the block
  waits for 10 losses; once a place is QUALIFIED no further block is read for it; when a signal comes more than 21 x 24 hours after a block's first signal, the block is
  EXPIRED and that signal starts the next block.
- **A print convention only:** Desk A's waiting state counts the pending signal in its `block_n`; mine counts the signals before it. The comparison maps one to the other.
- **What the fixtures exercised:** cleared and QUALIFIED, cleared with a failed confirmation (one with a profit factor that prints 1.00 and is under 1.0 in both builds),
  blocks that grew to 191 and 206 signals to reach 7 days, an EXPIRED block, FAILED on the profit factor, on a half and on the 30 percent day rule, and places waiting on
  an open result.

## Nov 13, 02:21Z: the second round of rulings (items g to o), and same on three fixtures (SUPERSEDED by the next section)

**The block comparison in the section above is superseded.** It was made against the lane text at `7c4c71d2` and Desk A's first reader. While it ran, the Head ruled ten
more places (items (g) to (o), `ROTATION_LANE.md` section 4 at `rnd-queue` `bd7007cb`) and Desk A rebuilt its reader. I rebuilt my block layer from that text and compared again.

Builds compared: mine `nc15_wheel_second.py` sha256 `1e8ac8fb...`; Desk A's signal scorer `nc15_wheel_replay.py` `8d1055df...`, records file writer
`nc15_wheel_records_csv.py` `d3f89f57...` and block reader `wheel_block_reader.py` `66e729c8...` at `claude/idea-desk-a` `c36aa1e8`. I ran its commands unread
(`... nc15_wheel_records_csv.py <dir> 2026-12-23T00:00:00Z <out.csv>`, then `wheel_block_reader.py <out.csv> --now=2026-12-23T00:00:00Z --start=2026-11-13T00:23:49Z`);
on seeds 6 and 7 its block output reproduces its committed files byte for byte.

| Fixture | Records the same | Differ | Record figures | Differ | Per-series figures | Differ | Blocks (both builds) | Block figures | Differ | Place states | Differ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed 6 | 20,994 | 0 | 18,343 | 0 | 63 | 0 | 12 | 192 | 0 | 7 | 0 |
| seed 7 | 20,994 | 0 | 18,390 | 0 | 63 | 0 | 10 | 158 | 0 | 7 | 0 |
| seed 6, variant `confexp` | 20,994 | 0 | 17,731 | 0 | 63 | 0 | 11 | 175 | 0 | 7 | 0 |

- **What changed in my block layer for items (g) to (o):** money in whole cents with 10 x W >= 13 x L and W >= L and no float; the 30 percent rule on whole cents; signals
  with a limit of 88c or above skipped (about 200 a fixture); EXPIRED decided by the clock with the stated read time, and the next block starting at the first counted
  signal after the expiry time; the confirmation's own 21 day limit; a void in n and in the losses' money but neither a win nor a loss for the 10 and 10 count.
- **The new fixture variant** (`make_nc15_wheel_fixture.py <dir> 6 confexp`) makes one place's signals nearly stop after its first block clears: both builds print that
  block CLEARED with its confirmation EXPIRED, unread, and a new block not yet begun. The half-cent net print difference of the earlier comparison is gone (whole cents).
- **Where the text is silent and I took Desk A's choice** (each named in the scorer's printed readings): an open result inside a block makes it WAIT unless the clock is
  already past the block's 21 days, when it is EXPIRED before any wait; cash that is not whole cents (a size-weighted fill price) goes to the nearest cent, half up
  (361, 352 and 356 final fillable signals on the three fixtures, the same count in both builds); the 30 percent reason is listed only for a positive block net; once a
  place is QUALIFIED no further block is read.
- **Outcomes exercised across the three fixtures:** FAILED (18 blocks), CLEARED and QUALIFIED (7), CLEARED with a failed confirmation (2), CLEARED with the confirmation
  in progress, waiting on an open result, and EXPIRED (1 each), EXPIRED blocks (3), blocks grown to more than 160 signals to reach 7 days.

## Nov 13, 02:24Z: the third round of rulings (items p to t), and SAME on three fixtures. THIS is the standing comparison.

The lane text moved once more while the comparison above ran: items (p) to (t) and the round-down rule for cash that is not a whole cent (`rnd-queue` `77eeb93b`, with a
pointer added at `dbd2f4da`, which is the text I built to and the head of that file when I compared). Desk A's reader moved with it.

Builds compared at 02:24Z: mine `nc15_wheel_second.py` sha256 `ade91e30...`; Desk A's signal scorer `nc15_wheel_replay.py` `8d1055df...`, records writer
`nc15_wheel_records_csv.py` `38ec4c46...` and block reader `wheel_block_reader.py` `2921a03a...` at `claude/idea-desk-a` `4774933b`, run by me, unread, with
`--now=2026-12-23T00:00:00Z --start=2026-11-13T00:23:49Z`.

| Fixture | Records the same | Differ | Record figures | Differ | Per-series figures | Differ | Blocks (both builds) | Block figures | Differ | Place states | Differ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed 6 | 20,994 | 0 | 18,343 | 0 | 63 | 0 | 12 | 192 | 0 | 7 | 0 |
| seed 7 | 20,994 | 0 | 18,390 | 0 | 63 | 0 | 10 | 158 | 0 | 7 | 0 |
| seed 6, variant `confexp` | 20,994 | 0 | 17,731 | 0 | 63 | 0 | 11 | 175 | 0 | 7 | 0 |

- **What changed for items (p) to (t):** cash that is not a whole cent is rounded DOWN (`floor(100 x cash + 1e-6)`), where the round before had it to the nearest cent;
  an open result inside a block makes it wait with its expiry not yet decided, where Desk A's earlier choice had expired it first; the order of signals is decision time,
  then ticker, then side; nothing is read after QUALIFIED (now in the text).
- **One state I first had differently and fixed:** a confirmation still collecting inside its 21 days, with one result open, is "in progress" in both builds (I had
  printed it as waiting). It waits only once the read time is past its 21 days and a result is still open.
- **Not exercised by these fixtures, so agreed by reading only:** two signals of one place at the same decision time (the side tie of item (p)); a block past its 21 days
  that holds an open result (item (q)'s "expiry not yet decided" for a block); a rule in the favourites class (150 signals).
- The files `NC15_WHEEL_FIRST_BUILD_BLOCKS_fixture_*_reader_2921a03a_run_by_forensics.txt` are Desk A's block output from these runs.

## Nov 13, 02:40Z: the two plants the Head asked for, and A DIFFERENCE the ties plant found (the offset of polls received at the same instant)

The Head recorded the comparison above, wrote the places' start time (2026-11-13T02:24:00Z, `rnd-queue` `fb978196`), and asked for two more cases before any block is
read. Both builds are now run with `--start 2026-11-13T02:24:00Z`. Builds: mine `nc15_wheel_second.py` sha256 `ab3343b9...` plus the switch below; Desk A's unchanged
(`8d1055df`, `38ec4c46`, reader `2921a03a` at `4774933b`).

1. **A block past its 21 days that still holds an open result: SAME.** Fixture `make_nc15_wheel_fixture.py <dir> 6 openexp`. Read at `--now 2026-12-26T12:00:00Z`
   both builds print the slow place's second block as "waiting for results, expiry not yet decided"; read at `--now 2026-12-30T00:00:00Z`, when those results are 7 days
   old and so voids, both print it EXPIRED with the same 20 signals.
2. **Two counted signals at the same decision time: ONE DIFFERENCE.** Fixture `... 6 ties` gives two places a twin market in every third window, with the same polls.
   The two builds start one block with different members of a tied pair (first ticker `...-00` in mine, `...-01` in Desk A's); every other figure of that block is equal.

**The cause is not the order rule; it is the clock.** For two rows received at the same instant, Desk A's scorer gives DIFFERENT offsets: a poll's offset window is the
rows up to and including that poll's own row in the run's order, so the second row of an instant sees one more row than the first. Mine gives every row received at one
instant the same offset: all header rows with a receive time at or before the poll's. The sheet says "the 120 most recent rows of the same run folder (any ticker,
ordered by receive time, at or before that poll, rows with a readable header only)". Both readings fit those words.

| Read | Signal polls | Exchange time differs between the builds | Largest | Records or figures that differ | Blocks that differ |
|---|---|---|---|---|---|
| seed 6 | 3,099 | 18 | 0.011 s | 0 | 0 |
| seed 7 | 3,121 | 9 | 0.012 s | 0 | 0 |
| seed 6 confexp | 3,011 | 15 | 0.011 s | 0 | 0 |
| seed 6 ties | 3,262 | 122 | 0.040 s | 0 | 1 (the tied pair's order) |
| seed 6 openexp, read Dec 26 | 3,099 | 18 | 0.011 s | 0 | 0 |
| seed 6 openexp, read Dec 30 | 3,099 | 18 | 0.011 s | 0 | 0 |

With my build's switch set to Desk A's reading (`NC15_OFFSET_WINDOW=row`), all six reads are identical to Desk A's in every exchange time, record, figure, block and state.
So this one reading is the whole difference.

**Why it matters on the real log:** NC15 reads all 11 tickers in one batched poll, so every poll row shares its receive time with ten others; the choice touches every
poll. The size is hundredths of a second, which can move a poll across the decision instant, across the 6 second second-look limit or across a Central midnight, and it
decides the order of signals of one place decided at the same time (which the real places cannot have: one market a window).

**An honest note on my earlier "same":** my comparison tool did not compare exchange times until now, so the "same" of 02:24Z was true of every status, figure, block
and state, and silent about those hundredths of a second. The tool now compares them (`nc15_wheel_compare.py` with the first build's records file as third argument).
Put to the Head for a ruling at 02:40Z; my default stays the per-instant reading until then.

## Places where the sheet or the lane leaves a choice

The scorer prints its readings with its output. The ones most likely to move a figure:

1. **How the 6 seconds to the second poll are measured.** Now exchange time, as the first build (see above); I first used the recorder's clock.
2. **A ticker in two run folders.** The signal poll is the latest by exchange time over all run folders; the second poll is the next poll in the SAME run folder (Desk A's choice 1).
3. **What a block is when its 60 signals fall on fewer than 7 days, or span more than 21.** RULED by the Head (02:05Z): it keeps growing to 7 days; past 21 x 24 hours it is EXPIRED, unread. (I had read both as FAILED.)
4. **The rarer outcome for a rule that buys either side at 10c to 90c.** RULED: 10 wins AND 10 losses. A void counts as a loss (Desk A's reading, taken).
5. **The 30 percent day rule** is tested only when the block's net is positive. **A day** is the US Central date of the signal poll's time (RULED).
6. **Halves** of a block of n signals are the first n // 2 and the rest.
7. **Open results.** A block that holds an open signal waits, and so does everything after it. A signal is open until 7 days after its close, by the `--now` time.
8. **The confirmation's 30 signals** belong to no block; the next block starts after them.
9. **The offset** uses rows of the same run with a receive time at or before the poll's, all rows of the same instant included.
10. **Result from two run folders:** a yes or no in either wins over an empty value; two that disagree stop the run.

## Limits

- Records, per-series totals and block lines are all compared with the first build on invented rows. Nothing here is a verdict of any kind.
- The fixture's polls are regular; real NC15 runs have fallback reads and gaps that may hold shapes neither build has met.
- The later public result read (the Chief of Staff's list job) has no input in this build yet: results come from the coverage files only.
