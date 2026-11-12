# UNRATEROUND against the slow-family paper screen (T2-3): proposed re-registration, scorer and job committed before any data (Testing Desk, Nov 12, 2026)

**PROPOSED, NOT YET REGISTERED.** The card as Desk B registered it does not qualify for the screen (below). Re-registering is a new try against the screen, so it needs the Head's word and a ledger row. Nothing was pulled, no Kalshi request was made, no outcome was read. No live account figure.

**Counts:** registered 1 (Desk B card 4, Nov 11, retired Nov 12 on the main bar); proposed re-registration 1 (this file); pulled 0; scored 0; closed 0. Waiting on: the Head's yes, then Main to dispatch stage 0.

## The registration as it stands (Desk B, `IDEA_DESK_B_NOV11.md` card 4, unchanged)

Official arithmetic prior: u0 = unemployed / labour force of the last release (BLS LNS13000000, LNS11000000); next unrounded rate = u0 + 0 drift + normal error (sd from monthly changes 2010 to 2019 and 2022 to 2025, frozen); three days before the Employment Situation release buy the threshold or bracket side whose ask is 8c or more under the model, price 10c to 80c, one per event, hold to settlement; January releases excluded. Expected 15 to 25 entries from 30 to 36 events. Desk B's own text says that reads "no evidence", and `PAPER_LIST.md` says it "does not qualify as registered" for the screen (an 8c-edge rule trades only some events, under 30 trades).

## The re-registration proposed (the minimal change Desk B's ranking names: one trade on every monthly release)

Everything above stays except: **one trade on EVERY non-January monthly release**, the (market, side) with the largest model-probability-minus-price among sides priced 10c to 80c, even when that edge is under 8c. The original 8c rule is reported as a subset, information only. Screen (POLITICS_RULES section 8, pending merge): cash PF 1.3 or better on at least 30 independent events at +0c on the unrounded fee 0.07 p (1 - p), 1 contract; both halves (events split by date at the median) net cash above zero; pinned cutoff; read once. Labels exactly: under 30 events "no evidence at n = x"; 30 or more and met "on the paper list (unproven)"; 30 or more and not met "off the list (failed the screen)". Never PASS. Multiplicity (the file's own table): about 15% of no-edge rules pass this screen at n = 30; this is try 2 against the screen for this card, and the Head states the running count of cards read next to any listing.

**Pins I declare (the card is silent):** (1) the rounding is half up to 0.1 and strike types come from the list answer's `strike_type`, `floor_strike`, `cap_strike` (greater: headline above the floor, so unrounded at least floor + 0.05; less: below the cap; between: inclusive); checked against the market rules text before the read. (2) "January" means reference month January (the annual population-control break), by the event ticker's month. (3) Entry = the last hourly candle ending within 6 hours at or before 3 days before the event's earliest market close (a proxy for the release time), priced from the candle's ask close (YES) or 1 minus bid close (NO). (4) Only markets whose strike lies within 0.35 of u0 are pulled (to bound requests; chosen from BLS data only, before any price). (5) u0 for event month M is the unrounded rate of month M minus 1, from a BLS levels file `bls_levels.csv` (year, month, unemployed, labor_force). (6) Cutoff: `CUTOFF = 2026-11-05T00:00Z` is a date constant in `unrateround.py` and here; events closing on or after it are never requested; the read-once marker line is committed in the script and becomes "READ ON <date>, commit <hash>" after the one read. (7) Stage-1 gate: if the settled non-January events before the cutoff number under 30, the answer is "no evidence at n = x", no candle is requested and nothing is scored.

**Taker line (required):** price comes from an hourly candle close, not an order book, and not yet cleared by Forensics' CANDLEVSBOOK1. The book-replay line cannot be produced (no book exists for past months). The haircut line is printed: after the 34 percent fill drop the expected n is 0.66 n against the screen's 30; with about 33 events that is about 22, so even a listing would rest on a count the haircut puts under 30. Say so in any report.

## Request count (all Kalshi, 1 a second)

| Stage | Job | Requests |
|---|---|---|
| 0 | `kalshi_pull_jobs/UNRATE_SERIES.json` (passes `--dry-run`): `GET /series/KXU3` and `/series/KXUE` (a 404 is an answer; I do not know which ticker is unemployment, so two checks) | **2** |
| 1 | built by `unrateround.py build-s1 <stage 0 folder>`: one live and one `/historical` list | **2** (at most 6 with paging) |
| gate | `unrateround.py events <stage 1 folder>`: under 30 events stops here | 0 |
| 2 | built by `build-s2 <stage 1 folder> <bls_levels.csv>`: one candle request per near-the-money market, about 7 per event | **about 230 (33 events x 7), at most about 350** |

**Total about 235 typical, at most about 360, against Desk B's 40 (that assumed one market per event; the all-events rule needs the near-the-money set).** Stage 2 is not placed in the order until stage 1 shows 30 or more events. Plus one non-Kalshi input: the BLS levels file (two public series, 2009 to 2026). A keyless BLS request from this session was refused today (the shared address has used the daily threshold), so someone else or a later hour must supply `bls_levels.csv`; it needs no Kalshi request and no key.

## Files

`unrateround.py` (build-s0, build-s1, events, build-s2, score), `test_unrateround.py` (made-up data: rounding probabilities sum to 1, January excluded, held-out cutoff, the under-30 stop, the sd, each built job passes the runner's `check_job`, half and haircut lines), `../kalshi_pull_jobs/UNRATE_SERIES.json`. Owner field `MAIN` (the runner has no Testing Desk entry). Score within the hour of the stage 2 pull: `python3 -W ignore kalshi-scalper/workers/testing/unrateround.py score <stage 1 folder> <stage 2 folder> <bls_levels.csv>`.
