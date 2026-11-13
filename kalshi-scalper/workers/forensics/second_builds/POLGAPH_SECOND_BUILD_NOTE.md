# POLGAPH: independent second build (Forensics desk)

**Written Nov 13, 2026, about 01:32Z, on the Head of R&D's order (second, after VOIDSNAP).** Built from Desk B's registration with Amendments 1 and 2 alone
(`claude/idea-desk-b`, `kalshi-scalper/workers/polgap/POLGAPH_REGISTRATION.md`, sha256 `69eec8d6...`, unchanged at `a0cdeebe`) and `POLGAPH_SERIES.json` (`9f3886e7...`).
Desk B's `polgaph.py` was not read. Nothing of this card has been requested or read by anyone; no Kalshi request was made for this build.

## Files

| File | What it is |
|---|---|
| `polgaph_second.py` | the second build: lists, hourly candles and minute candles in, counts first, the cost line, and results only after the cost line passes |
| `make_polgaph_fixture.py` | invented lists, hourly and minute candles in the pull-run shape for all 69 series names; an `edge` argument plants or removes an effect |
| `POLGAPH_SECOND_OUTPUT_fixture_seed5_{no_edge,edge035}_MADE_UP_DATA.{txt,json}` | my build's figures on the two fixtures |

Commands:

```
python3 -I make_polgaph_fixture.py <dir> <POLGAPH_SERIES.json> 5 0.0       (and: 5 0.35)
python3 -I polgaph_second.py <POLGAPH_SERIES.json> --lists <dir>/lists --hourly <dir>/hourly --minute <dir>/minute
```

## Figures on the two made-up fixtures (mine only so far)

| Fixture | Market-mornings | Gap of 5c or more | The event's pick | Blocked | Fired | Filled (present, unchanged) | Verdict |
|---|---|---|---|---|---|---|---|
| seed 5, no edge | 12,865 | 3,999 | 601 | 162 | 439 | 344 (166, 178) | FALSIFIED (pooled), PF 0.61 |
| seed 5, edge 0.35 | 12,865 | 3,712 | 434 | 88 | 346 | 281 (140, 141) | the pooled pass does not count (one family supplies more than half the net); that family alone survives development |

These are invented rows; the figures mean nothing about the market. The comparison with Desk B's build on the same rows is still to come.

## Places where the registration leaves a choice

The build prints its readings with the output (`ambiguities`). The ones most likely to move a figure:

1. **The count "left after step 7".** I count the event's pick (one per event and morning) as step 7, then "blocked", then "fired". The text can also be read with the block inside step 7.
2. **"No fill data".** A market and morning has fill data if some answered minute request names the ticker and its time range contains the minute ending 07:01.
3. **The optimistic figure** books every fired decision at its limit: filled, not filled and no fill data alike.
4. **The family rule.** If the pooled read would survive and one family's net is more than half the pooled net, the verdict is that family's own read against the same minimums.
5. **A void** is any result that is neither yes nor no; the "settlement value paid" figure uses the listed settlement value and is left as the fee-only loss when none is listed.
6. **A market closing on or after 2026-11-13** is counted as refused and dropped; its result is never stored. The fixtures hold none.
7. **Largest number open at once** is taken at each filled bet's look.

## Limits

- Not yet compared with the first build. Nothing here is a verdict of any kind.
- The fixtures do not hold a held-out market, a list page that failed, or an hourly request that failed; those shapes are untested.
