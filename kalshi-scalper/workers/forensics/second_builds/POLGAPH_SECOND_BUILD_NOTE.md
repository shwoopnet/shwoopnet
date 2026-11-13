# POLGAPH: independent second build (Forensics desk)

**Written Nov 13, 2026, about 01:32Z, on the Head of R&D's order (second, after VOIDSNAP).** Built from Desk B's registration with Amendments 1 and 2 alone
(`claude/idea-desk-b`, `kalshi-scalper/workers/polgap/POLGAPH_REGISTRATION.md`, sha256 `69eec8d6...`, unchanged at `a0cdeebe`) and `POLGAPH_SERIES.json` (`9f3886e7...`).
Desk B's `polgaph.py` was not read. Nothing of this card has been requested or read by anyone; no Kalshi request was made for this build.

## Files

| File | What it is |
|---|---|
| `polgaph_second.py` | the second build: lists, hourly candles and minute candles in, counts first, the cost line, and results only after the cost line passes |
| `polgaph_compare.py` | compares Desk B's printed lines with my output, figure by figure; reads printed output only |
| `make_polgaph_fixture.py` | invented lists, hourly and minute candles in the pull-run shape for all 69 series names; an `edge` argument plants or removes an effect |
| `POLGAPH_SECOND_OUTPUT_A5_fixture_<name>_MADE_UP_DATA.{txt,json}` | my build's figures on the six fixtures made after Amendment 5 (the earlier ones were removed, see the Amendment 5 section) |

Commands:

```
python3 -I make_polgaph_fixture.py <dir> <POLGAPH_SERIES.json> 5 0.0       (and: 5 0.35)
python3 -I polgaph_second.py <POLGAPH_SERIES.json> --lists <dir>/lists --hourly <dir>/hourly --minute <dir>/minute
```

## SAME OUTPUT as Desk B's build on two made-up fixtures (Nov 13, about 01:39Z)

Desk B ran its scorer on the same rows and committed its printed lines (`claude/idea-desk-b` at `93e2d076`, `polgap/fixture_outputs/`; scorer sha256 `0c089c23...`,
registration `b1ac127d...` with Amendments 1 to 3). `polgaph_compare.py` reads those lines and my output and compares every figure.

| Fixture | Figures compared | Differ | Decisions | Blocked | Fired | Filled (present, unchanged) | Verdict in both builds |
|---|---|---|---|---|---|---|---|
| seed 5, no edge | 155 | 0 | 601 | 162 | 439 | 344 (166, 178) | FALSIFIED (pooled), PF 0.61 |
| seed 5, edge 0.35 | 156 | 0 | 434 | 88 | 346 | 281 (140, 141) | the pooled pass does not count (one family supplies more than half the net); that family alone survives development |

These are invented rows; the figures mean nothing about the market.

**How it got there.** Each build had one thing to change, and both are now in the registration as Amendment 3:

1. **Desk B's scorer** first accepted a minute request only if it started exactly at 07:00, so on this fixture's requests (06:55 to 07:05) it called every decision
   "no fill data". The reading in this build (an answered request that names the ticker and whose range holds the minute ending 07:01) is now the text, and its scorer's
   hash moved from `7279c013...` to `0c089c23...`. The fixture found that before any real request.
2. **This build** first booked the optimistic, same-candle figure on fired decisions only. The text now says every decision is booked, with no block and no fill test, and
   this build does that.
3. **A listed market closing after 2026-11-12 23:59:59Z stops the whole run.** This build first dropped and counted it; it now stops. Checked on a copy of the fixture's
   lists with one such market added: the run refuses before any count.

Not compared: Desk B prints "candles without a volume field"; this build reads a missing volume as 0 and does not count them (0 on both fixtures).

## Nov 13, about 01:44Z: Amendment 4 (the pooling line read exactly) and a fixture that separates the two readings

Auditor B found that Desk B's scorer let one family rescue a FAILED pooled read. Amendment 4 (registration `a13693f3...`, scorer `9186c8b5...` at `94ff7fa7`) reads it
exactly: the pooled verdict first; anything but a pooled pass is the verdict; on a pooled pass the family with the largest net (tie: alphabetical) is read alone if it
supplies more than half of the pooled net.

- **This build already took the pooled verdict first.** One small change: it now picks the family with the largest net (it had picked the first family over half in file
  order, which differs only when two families are each over half).
- **A third fixture separates the readings:** `make_polgaph_fixture.py <dir> <series json> 5 0.32 -0.5` (edge 0.32 for activity counts, minus 0.5 for the other two
  families). Pooled: n 288, PF 1.07, net positive, FALSIFIED. Activity counts alone: n 230, PF 1.93, more than half of the pooled net. Read "pooled first", the verdict is
  FALSIFIED (pooled); under the old reading it would have been "activity counts: survives development".
- **Both builds print FALSIFIED (pooled) on it,** and the same 155 of 155 figures. I ran Desk B's scorer at `94ff7fa7` on this fixture myself, with the two commands Desk B
  gave, from a checkout of its branch, without reading it; its printed lines are saved here as
  `POLGAPH_FIRST_BUILD_OUTPUT_fixture_seed5_edge032_others_minus05_MADE_UP_DATA_run_by_forensics.txt`.
- The two earlier fixtures still agree against Desk B's refreshed lines at `94ff7fa7`: 155 of 155 and 156 of 156.

## Nov 13, about 01:47Z: the two-families fixture, and one information-only difference

The Head's last word (01:44Z): align to Desk B's `94ff7fa7` (scorer `9186c8b5...`, registration `a13693f3...`, restored byte for byte at `5a7de18e`); the later hashes
`331711cd` and `2e48e8c8` are dead. This build was already on that text. Fixtures asked for: pooled fail with a dominant family (above), and two families over half:

- `make_polgaph_fixture.py <dir> <series json> 5 0.35 -0.4 balanced`: 7 activity-count series, 7 shipping, 14 single questions; the two count families get the edge and
  single questions lose. Pooled: n 152, PF 1.74, a pass. Activity counts and shipping counts EACH supply more than half of the pooled net (the third family is negative).
  Both builds read the family with the largest net alone, and both print "no evidence at n = 66" for it (halves 35 and 31). I ran Desk B's scorer at `94ff7fa7` on it
  myself with its two commands, without reading it; its lines are saved as `POLGAPH_FIRST_BUILD_OUTPUT_fixture_seed5_balanced_edge035_single_minus04_MADE_UP_DATA_run_by_forensics.txt`.
- **155 of 156 figures the same. THE ONE DIFFERENCE, information only:** on the line "voids paid at their settlement value instead" Desk B's build prints wins 95 and
  mine 94; n, profit factor, net, mean and z are the same. The cause is one voided bet whose cash result at its settlement value is exactly zero (value 0.53, limit 0.51,
  fee 0.02). In floating point 0.53 - 0.51 - 0.02 is +1.7e-17, so a build that counts a win as "result above zero" with no tolerance counts it; mine uses the 1e-9
  tolerance and does not. The registration does not define a win on that line. No verdict line reads it. Sent to the Head and Desk B for a one-line pin.
- Desk B's three small pooling cases (`make_pool_fixture_MADE_UP_DATA.py`) start from a decisions file and exercise its score step only; this build has no such
  entry point (it always decides from the candles), so those three were not run here. The two whole-pipeline fixtures above cover the same two cases.
- The three earlier fixtures are unchanged in content under the changed generator (checked by hashing the decompressed answers).

## Nov 13, 01:48Z: the Head's ruling on the one difference, and where POLGAPH stands

- **Ruling: a sentence, no hash change.** Desk B's scorer stays frozen at `9186c8b5...` (branch head `cfb1eec0` holds it and registration `a13693f3...`, checked by
  hash). The Head's sentence: "On the information-only line for voids paid at settlement value, the first build's wins count uses a raw comparison and may count a cash
  result of exactly zero as a win; the second build applies 1e-9 and does not; the difference is at most the number of exactly-zero voids, and no verdict reads that count."
- **At the read:** if that count differs by more than the number of exactly-zero voids, it goes to the Head.
- **Standing:** text closed, scorer frozen, auditor clean, second build matched. This desk's POLGAPH work is closed until the lists land; nothing has been requested.

## Nov 13, about 07:35Z: re-match after Amendment 5 (development ends Nov 4, 63 series): SAME OUTPUT on six made-up fixtures

Desk B asked for a re-match at 07:03Z. Amendment 5 (registration sha256 `7280653e...`, series file `c22f1aae...`, scorer `198d9bf0...`, `claude/idea-desk-b` at `4b3c8aaf`;
the three hashes checked on the branch head `2e142312`) moves three things and no rule: development closes end 2026-11-04T23:59:59Z, six activity-count series leave
(63 remain, 42 in that family), and the landed lists run `pull/POLGAPH_LISTS/2026-11-13T0627Z_43378777252` is held-out material. I read the amendment's text and the series
file. I did not read `polgaph.py` and did not open the landed run. No price or result of this card has been read by this desk.

**What changed here (from the text):**

- `polgaph_second.py` (now sha256 `7ec18562...`): a listed market closing on or after 2026-11-05T00:00:00Z stops the whole run; the series come from the file given on
  the command line as before (63 names). New refusals: a path that is, or lies inside, the listed run (by its folder name), and a copy under another folder name whose
  manifest carries the same job and start minute.
- `make_polgaph_fixture.py` (`01acdbed...`): invented closes end 2026-11-04; the `balanced` variant uses the first 10 activity-count series (it was 7), because the
  shorter window left the 7-series variant under the 150-bet minimum and the two-families case would have gone untested.
- `polgaph_compare.py` is unchanged (`f66f5185...`).

**The earlier fixtures and their saved outputs are gone from this folder** (they held invented closes after Nov 4 and names of the six dropped series; git history keeps
them). The new ones are named `..._A5_...`. I ran Desk B's scorer at `198d9bf0...` on each myself, with its two commands (`decide`, then `score`), from a checkout of its
branch, without reading it; its printed lines are saved as `POLGAPH_FIRST_BUILD_OUTPUT_A5_fixture_<name>_MADE_UP_DATA_run_by_forensics.txt`.

| Fixture (generator arguments after the series file) | Figures compared | Differ | Case it exercises | Verdict in both builds |
|---|---|---|---|---|
| `5 0.0` | 155 | 0 | no effect | FALSIFIED (pooled) |
| `5 0.35` | 156 | 0 | pooled pass, one family over half, family under the minimum | activity counts alone: no evidence at n = 138 |
| `5 0.32 -0.5` | 155 | 0 | pooled read fails while one family is strongly positive | FALSIFIED (pooled) |
| `5 0.35 -0.4 balanced` | 156 | 0 | pooled pass, two families each over half, the alphabetically first has the largest net | activity counts alone: no evidence at n = 83 |
| `6 0.35` | 156 | 0 | pooled pass, one family over half and over the minimums | activity counts alone: survives development |
| `6 0.35 -0.4 balanced` | 156 | 0 | pooled pass, two families each over half, the largest net is NOT the alphabetically first | shipping counts alone: no evidence at n = 71 |

Invented rows; the figures mean nothing about the market. The win count on the "voids paid at their settlement value" line is the same in both builds on all six
(the Head's sentence of 01:48Z still covers a difference of at most the number of exactly-zero voids at the read).

**Refusals, tested on copies of the first fixture (both builds, from their behaviour alone):**

| Case | This build | Desk B's scorer (`decide`) |
|---|---|---|
| One market added closing 2026-11-04T23:59:59Z | runs, counts it (2,473 markets) | runs, counts it (2,473) |
| One market added closing 2026-11-05T00:00:00Z | REFUSED, whole run stops | REFUSED, whole run stops |
| One market of a dropped series (KXTRUTHSOCIAL) added, close inside the window | skipped, not counted | skipped, not counted |
| The same with a close of 2026-11-10 | skipped, run does NOT stop | skipped, run does NOT stop |
| Lists folder named `POLGAPH_LISTS/2026-11-13T0627Z_43378777252` | REFUSED | REFUSED |
| The same folder copied under another name, manifest with that job and start minute | REFUSED | runs |
| Lists inside a `HELDOUT_` folder | REFUSED | REFUSED |

Two things for Desk B and the Head, neither a figure:

1. **A copy of the listed run under another folder name is not refused by Desk B's guard** when only the name changes (its registration says "wherever it was copied").
   On the real run this cannot reach a count: that run holds markets closing after Nov 4, so the close-date stop fires in both builds. It is a wording or guard point.
2. **A held-out close on a series OUTSIDE the 63 does not stop either build**; both skip the market by its series and never read its result. The new lists job asks only
   the 63 series, so none should arrive. If rule (h) is meant to stop a run on any held-out row, whatever its series, that is a ruling.

**Standing:** second build re-matched on the amended text. Nothing of this card has been requested by this desk. The comparison is made again when the bounded lists
and the candles land.

## Places where the registration leaves a choice

The build prints its readings with the output (`ambiguities`). The ones most likely to move a figure:

1. **The count "left after step 7"**: SETTLED by Amendment 3, item 2. A decision is the event's pick; fired is decisions less blocked.
2. **"No fill data".** A market and morning has fill data if some answered minute request names the ticker and its time range contains the minute ending 07:01.
3. **The optimistic figure**: SETTLED by Amendment 3, item 3. Every decision is booked at its limit, no block, no fill test.
4. **The family rule**: SETTLED by Amendment 4. Pooled verdict first; only a pooled pass can hand the card to the family with the largest net.
5. **A void** is any result that is neither yes nor no; the "settlement value paid" figure uses the listed settlement value and is left as the fee-only loss when none is listed.
6. **A market closing on or after 2026-11-05** (it was 2026-11-13 before Amendment 5): SETTLED by Amendment 3, item 4. It stops the whole run.
7. **Largest number open at once** is taken at each filled bet's look.

## Limits

- Agreement on invented rows shows the two builds read the text the same way on the planted cases. Nothing here is a verdict of any kind.
- The fixtures do not hold a list page that failed or an hourly request that failed; those shapes are untested. A held-out market and the listed run were tested on copies (Amendment 5 section).
