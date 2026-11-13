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
| `POLGAPH_SECOND_OUTPUT_fixture_seed5_{no_edge,edge035}_MADE_UP_DATA.{txt,json}` | my build's figures on the two fixtures |

Commands:

```
python3 -I make_polgaph_fixture.py <dir> <POLGAPH_SERIES.json> 5 0.0       (and: 5 0.35)
python3 -I polgaph_second.py <POLGAPH_SERIES.json> --lists <dir>/lists --hourly <dir>/hourly --minute <dir>/minute
```

## SAME OUTPUT as Desk B's build on two made-up fixtures (Nov 13, about 01:45Z)

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

## Places where the registration leaves a choice

The build prints its readings with the output (`ambiguities`). The ones most likely to move a figure:

1. **The count "left after step 7"**: SETTLED by Amendment 3, item 2. A decision is the event's pick; fired is decisions less blocked.
2. **"No fill data".** A market and morning has fill data if some answered minute request names the ticker and its time range contains the minute ending 07:01.
3. **The optimistic figure**: SETTLED by Amendment 3, item 3. Every decision is booked at its limit, no block, no fill test.
4. **The family rule.** If the pooled read would survive and one family's net is more than half the pooled net, the verdict is that family's own read against the same minimums.
5. **A void** is any result that is neither yes nor no; the "settlement value paid" figure uses the listed settlement value and is left as the fee-only loss when none is listed.
6. **A market closing on or after 2026-11-13**: SETTLED by Amendment 3, item 4. It stops the whole run.
7. **Largest number open at once** is taken at each filled bet's look.

## Limits

- Agreement on invented rows shows the two builds read the text the same way on the planted cases. Nothing here is a verdict of any kind.
- The fixtures do not hold a held-out market, a list page that failed, or an hourly request that failed; those shapes are untested.
