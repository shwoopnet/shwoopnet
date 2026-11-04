# MECH1S registration (the structural-mechanism worker; its assigned ID was MECH1, which the Bitcoin tape worker already used, so files and code are named MECH1S / mech1_struct.py; 2026-11-04)

Registered BEFORE any outcome (win, loss, result, net) was joined to any treated row of any mechanism below. Cheap side only (ask 3c to 30c, a hard limit of 0.30 asserted in code); no favourite-side result is computed or printed; no 15 minute crypto or gold candle trigger. No new Kalshi fetch; no live code, no functions/, no L1, no OICORE; no promote verb.

## Question
Do any of 12 model-free structural mechanisms, each with a named counterparty, pick cheap-side rows that win more than they cost, after the fee, on the existing development caches? Prior: under 5% LEAD each. The pooled cheap side loses about 6c a contract (CALIB1 -6.0c, LIQ1 control -6.0c, NEWLIST1 PF 0.36 to 0.64), so a filter has to remove most of that to matter; the honest expected result is FALSIFIED for all three scored.

## Data (cached development only, frozen third excluded)
CALIB1 / LIQ1 pooled development table rebuilt from USWEEP1, USWEEP2, USWEEP3 caches and `data/newlist1.sqlite` (cut at `newlist1_cuts.json` t2) with `src/scalper/mech1_struct.py extract`: **16,201 cheap rows, 3,558 events, 12,530 markets**, identical to LIQ1's pool. Fields added from the same caches (no outcome): look timestamp, bid, spread, candle volume, the market's own earlier candles (price an hour before, path high, first quoted price), and for candle sources the event's sibling quotes at the same look and its ladder position from the census (numeric strike suffix, at least 5 markets, all suffixes numeric and distinct). newlist1 rows have no ladder (10 markets per family sampled). Entry: taker at the ask, held to settlement, fee 7% x C x p x (1-p) rounded up, C = 10 (`calib1.net_per_contract`).

## The 15 proposed mechanisms (3 dropped as duplicates, 12 in the ranked table)
Duplicates, dropped before the census (nearest ledger item):
- LASTTRADE (time since the last trade vs the quote, stale quote): LIQ1 (`workers/LIQ1_RESULT.md`), LOWV (volume 0 candle) was -7.1c, HIGHV -4.7c.
- AGE (days or hours since listing, fraction of life elapsed): NEWLIST1 (`workers/NEWLIST1_RESULT.md`), looks at 1, 3, 6 hours of life and the late control, PF 0.36 to 0.64.
- CHEAPCOUNT (number of cheap rungs in the same event, crowded tail): OVERROUND1 (ladder ask sum) and NHLROUND1 (under-round ladders).
Also noted as partly covered, kept as new angles: SPREADM follows up LIQ1 caveat 1 (no price control); WEEKEND: nearest S13 (Bitcoin favourite, weekend quiet, FALSIFIED), different side and universe; OFFHOURS and the 15-minute time-of-day blocks of IDEAS100 are favourite-side; PATH_FALL: nearest BOUNCE1 and MOM_FADE (Bitcoin 15 minute, spot moves), not hourly cheap price paths across categories; INTERIOR / SHOULDER / VOLRANK: nearest WXENS1 (cheap tail brackets of one temperature ladder with an ensemble model), no model-free ladder-position test exists in the ledger; NONROUND / FEE_WASTE: nearest O7 (resting bids at round prices, NEW, books) and CALIB1's ask buckets; none tests the cent itself.

## The ranked table (rank = eligible treated rows in the score set x story strength, strengths fixed BEFORE the census)
Score set = first two thirds of development events by earliest close time (D1 = first half of those events, D2 = second half); TEST = last third of development events. Counts are after the cap of 2 qualifying rows per event (md5 order). Census output `workers/MECH1S_CENSUS.txt` (features only; the one exception is YDAY, see Disclosure).

| rank | id | counterparty story (who loses and why) | fixed rule (treated) | placebo arm | strength | score-set rows (events) | test rows | rank score |
|---|---|---|---|---|---|---|---|---|
| 1 | INTERIOR | lottery buyers overpay the end brackets of a ladder (open-ended tails, the furthest strike); interior cheap brackets are priced by probability | cheap row whose strike is not the first or last of its event's numeric ladder (>= 5 markets) | the first or last strike | 4 | 2,629 (1,552) | 1,588 | 10,516 |
| 2 | NONROUND | sellers and bidders anchor on round numbers (5c, 10c, 15c ...), so round asks are stale and rich; a non-round ask was set by something that repriced | ask in cents not a multiple of 5 | ask a multiple of 5 | 2 | 3,761 (2,222) | 2,039 | 7,522 |
| 3 | PEAK_COLLAPSE | holders of a cheap side that already collapsed sell it down to the bid in a panic, past fair; buyers of the collapse pay less than the hazard | >= 2 earlier candles, earlier path high >= 2 x ask and >= 5c above it | earlier path high < 1.25 x ask | 3 | 2,483 (1,578) | 897 | 7,449 |
| 4 | PATH_FALL | momentum buyers chase a cheap side that rose in the last hour and overpay; a side that fell is not chased | ask <= 0.8 x its price about an hour earlier (candle 30 to 90 minutes before the look nearest 60) and >= 2c lower | ask >= 1.25 x and >= 2c higher | 3 | 1,472 (1,044) | 1,281 | 4,416 |
| 5 | VS_OPEN | the listing price was set by an anchored opening quote and the side has since decayed to a fair price (partial: NEWLIST1) | >= 2 earlier candles and first quoted price >= 2 x ask | ask >= first quoted price | 2 | 2,109 (1,426) | 760 | 4,218 |
| 6 | WEEKEND | weekend retail lottery flow is thin and informed makers are away, so asks are not padded by sellers (nearest S13) | look on Saturday or Sunday (US Eastern) | Tuesday to Thursday | 2 | 1,534 (914) | 741 | 3,068 |
| 7 | SHOULDER | a cheap rung next to the mass of its ladder is priced from the neighbours, a far-tail rung is a lottery ticket | max price of the adjacent rungs (same side) >= 0.30, >= 4 sibling quotes | adjacent rungs all <= 0.10 | 3 | 882 (545) | 916 | 2,646 |
| 8 | SPREADM | tight books at a higher cheap price have no stale padding (follow-up to LIQ1 caveat 1) | spread <= 1c and ask >= 10c | spread >= 5c and ask >= 10c | 2 | 817 (584) | 408 | 1,634 |
| 9 | FEE_WASTE | the fee rounds up to the cent; at C = 10 some prices waste almost nothing (cost, not a counterparty) | rounded fee minus exact fee <= 0.02c a contract | >= 0.08c | 1 | 1,194 (905) | 984 | 1,194 |
| 10 | VOLRANK | volume draws lottery buyers; the quiet nonzero rung among its siblings is not crowded | candle volume > 0 and the lowest among siblings with volume > 0 (>= 3 of them) | the highest | 2 | 524 (485) | 252 | 1,048 |
| 11 | OFFHOURS | overnight (00:00 to 06:00 US Eastern) retail is absent so the retail lottery premium is absent | look 00:00 to 05:59 ET | weekday 12:00 to 17:59 ET | 2 | 217 (145) | 74 | 434 |
| 12 | YDAY | autocorrelated series (weather, prices) repeat yesterday's winning bracket more than a flat ladder prices it | cheap row whose strike equals the strike of the single YES market of the same series' previous-day event | any other strike of an eligible series | 2 | 175 (153) | 65 | 350 |

Unscored rows 4 to 12 stay open for later workers (they are not tested here and carry no verdict).

## Scored: the top 3 by rank, ONCE
**INTERIOR, NONROUND, PEAK_COLLAPSE**, each with its placebo arm reported beside it (the opposite arm of the same hypothesis, not a separate search). Net per contract after fee, taker at the ask, held to settlement, C = 10. Event-clustered bootstrap 95% interval (2,000 resamples, seed 20261104) of the mean per contract. Parts: D1, D2 (halves of the score-set events), TEST (last third), and ALL (D1 + D2 + TEST; development only, the frozen third stays unread).
**LEAD only if** net > 0 in D1 AND D2 AND TEST AND the ALL lower bound > 0 AND at least 150 trades in ALL and at least 30 in each of D1, D2, TEST. Otherwise FALSIFIED (enough trades, bar failed) or NOT_ENOUGH_DATA (too few). A LEAD would not be a trade: only a forward pre-registered read of new events after 2026-11-04 could promote it, and no promote verb exists here.
Nothing is fitted: every cut above is a number written here; the only tuned object is the split by event order.

## Predictions (written before the join)
INTERIOR about -4c to -6c (FALSIFIED; the pooled cheap side is -6c and interior rows are most of it). NONROUND -5c to -7c (FALSIFIED; the cents it removes are few and not the bad ones). PEAK_COLLAPSE -4c to -7c (FALSIFIED; collapse often means the event is going the other way). P(any LEAD) under 10%.

## N accounting
+2 per mechanism scored: 3 scored = **N +6** (placebos are the other arm of the same mechanism and not counted separately). The 9 unscored mechanisms and the 3 dropped duplicates add 0 (no outcome was looked at). Coordinator total before this worker about 730,399; z bar 5.27.

## Disclosure
1. The assigned ID MECH1 was already used (Bitcoin tape counterparty worker, `workers/MECH1_*`, `src/scalper/mech1.py`); this worker's files are MECH1S so nothing of that record is overwritten.
2. The census is features only except YDAY, whose treated arm needs the previous-day event's winning strike; the census used the winner's strike label of OTHER (earlier) events to count eligible rows, never the outcome of the row itself. YDAY is rank 12 and not scored.
3. Pool, cap, split and net are the LIQ1 / CALIB1 definitions; no candle price or Kalshi result of a scored row has been aggregated before this file is committed.
