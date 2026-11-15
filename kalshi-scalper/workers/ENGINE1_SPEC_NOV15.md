# ENGINE1: one automated rule-search engine (Desk A and Testing Desk, Nov 15, 2026; the owner's order, relayed by the Head). Spec fixed before any read.

Two independent scorer cores (Desk A's `desk_a_verify/engine1_core.py`, the Testing Desk's own); they must agree to 1e-9 on a shared invented fixture (rule 16b) before any real run. Auditor B checks look-ahead. No data is read until this spec, the fixture, both cores and Auditor B's CLEAN exist. Figures by message only.

## Data and cuts (each printed by the loader)
- Archive 15 minute series (19), closes before 2026-10-03T16:00Z; NC15 runs under the ADJWIN1 allow line (11 series, same cut, same loader order); stock perps SPY, QQQ, NVDA, AAPL from 2026-11-06 (kalshi1m), not the EVM4 names. Perps and the other two sources have different cuts and bid/ask fields; one loader per source, each printing its cut and drop counts. Raw data stays off branches; reads go through the heldout guard and its allow lines, which need the Head's and Main's written acceptance for any new reader.
- SPLIT by fixed dates per market, written as constants BEFORE any read: sort a market's distinct close dates; SEARCH = the first floor(D/2) dates, VALIDATE = the rest. The archive's third 3 is spent, so VALIDATE is the last in-history gate; the forward shadow is the true held-out.

## Entry, features, rule space
- A rule is (market, time-left bucket, entry price band of 5c, side rule, exit, at most ONE filter). Time-left buckets: seconds left at the entry candle, in 60 s buckets from 120 to 840. Side rule: cheap, favourite, YES, NO (by the quote at the entry candle). One entry per window per rule: the first candle in the bucket whose ask for the side is inside the band and passes the filter.
- Features come from candles ending AT or BEFORE the entry candle only: OI change over 3 and 6 minutes, volume change over 3 minutes, price (mid) momentum over 1, 3 and 5 minutes, spread. A filter is (feature, sign of the move or tercile); tercile cut points come from the SEARCH half only and are frozen constants for VALIDATE. Missing feature = no entry (counted).
- Exits: hold to settlement; target (exit when the bid reaches min(2 x price paid, 0.99)); stop (bid at or below half the price paid); time exit at 180 s and at 60 s before the close (the candle ending then, at the bid). Target and stop are tested on candle closes after the entry candle, whichever comes first; a candle ending after the close is dropped (C8).

## Scoring
Cash PF per order (net per contract after the per-order rounded fee, at 1 contract and at 10; ceil(round(x, 9))), entry ask + h, exit bid - h, h = 0, 1c, 2c. 2c is primary where an exit can fall in the last 2 minutes and on NC15 (C11). Day-clustered z (sum per day, mean over the sample sd / sqrt(days)); day-clustered p from z (two-sided normal; for a one-sided "PF above 1" claim use the upper tail, stated). n per rule, trade days.

## Gates
SEARCH: 1c PF 1.3 or more, 2c PF 1.0 or more, n 100 or more. VALIDATE (the survivors of SEARCH only): the same bar on the VALIDATE half, plus Benjamini-Hochberg at 5% on the day-clustered p over ALL combos tried (every rule scored in SEARCH, whether it passed or not; the count printed first). The total combos tried is printed before any result. The rule space is capped so that the count is declared as a constant: state it here after the grid is frozen, before the first read: COMBOS_TRIED = (to be filled by the shared fixture builder, not by the result).

## Output (one block)
Combos tried, SEARCH passes, VALIDATE passes, each survivor in one line (market, rule, PF 1c / 2c, n, days), and a note on which closed family it belongs to (favourite-late, OI, lead-lag, none) for the Head to flag duplicates. Under the owner's order survivors are shown even if they sit in a closed family; a survivor is information for the forward shadow, not a pass.

## Open points for the Head, Testing Desk and Auditor B (before any build)
1. Price paid for the target and stop: ask + h at the entry candle, as above. Agree?
2. The count of rules is large (series x 7 buckets x ~10 bands x 4 sides x 5 exits x ~15 filters is on the order of 10^6 per source); BH on p over that many tests is heavy and most cells have n under 100. Propose capping SEARCH to cells with n at least 100 before counting, with the count of DROPPED cells printed as part of COMBOS_TRIED (they were still tried). Agree?
3. The perps have no settlement result; hold to settlement is not defined there (perps have no 15 minute close). Propose perps use only time exits at fixed minutes after entry (3, 10, 15, 30) and the target and stop, and are scored in a separate block with the 12 bps fee ASSUMED (not confirmed). The 15 minute series use the rules above.
4. 48 hour first full run: the loaders for the archive (Forensics is the single extractor) and the perps need allow lines and a data hand-off. Who delivers the archive's candles to the loader, and in what shape?
