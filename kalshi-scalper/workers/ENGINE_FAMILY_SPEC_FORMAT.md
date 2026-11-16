# FAMILY SPEC format (Desk A, Nov 16, 2026; the owner's "make research quicker"). A desk writes an idea as a SPEC, not a scorer. The audited engine does the rest.

**What a desk writes:** one file `workers/specs/<ID>.spec.json` (fields below) and a short card (the question, the mechanism, the uniqueness note against 7d and 7e). Commit both BEFORE any run. Auditor B checks the SPEC (data, cuts, look-ahead, the held-out map), not new code.

**What stays audited and shared (never rewritten per idea):** the loaders (each with its wall and an allow line from Auditor B), the scorer core (`engine1_core.py`, per-order rounded fee, haircuts, exits), the rule enumerator (`engine1_enum.py`), the perps block (`engine1_perps.py`), the driver (SEARCH, VALIDATE, Benjamini-Hochberg, `engine1_driver.py`), the printed report (counts first, m printed before any result, the disclosure line).

## Kinds of family (field `kind`)
1. `grid15m`: the 15 minute binary grid on candles (archive or NC15 extracts): you choose subsets of the engine's grid (buckets, bands, side rules, filters, exits); no new code.
2. `perps_grid`: the perps grid (filters, sides, hold exits to the cash close and next open, funding booked); no new code.
3. `event_rule`: a one-rule-per-event idea on any data with a loader (HOURBRIDGE1 is the example). Needs ONE small scorer plugin (event builder plus decision plus cash), written once with a hand case and audited by Auditor B; after that the spec is data only.
A family that needs a new loader, a new exit or a new feature is a spec PLUS a loader or library entry, each audited once; say so in `needs_new_code`.

## The fields (JSON object; every field is required unless marked optional)
- `id` (2 to 16 capitals or digits), `desk`, `date_registered` (ISO), `kind`, `card` (path of the card file), `needs_new_code` (list, empty for a pure spec).
- `uniqueness`: `closest_existing` (ids), `declined_list_rows_checked` (list), `difference` (one sentence), `family_flag` (favourite-late, OI, lead-lag, parity, maker, none).
- `data`: `loader` (the audited loader's file name), `loader_sha256` (the hash named in its allow line), `extracts` (names and sha256 of every extract or the dated recorder directories), `ticker_wall` (series or tickers), `window` (first and last close or candle date, UTC), `held_out_map_checked_by` (Auditor B and the date), `independence_note` (which other cards used the same days).
- `split`: `mode` (`fixed_dates` or `forward_only`), for `fixed_dates` the SEARCH last date and the VALIDATE first date per market as constants copied from `engine1_split.py` (a dated note adds a market), for `forward_only` the first close of the read and the release rule.
- `grid` (kinds 1 and 2 only): `buckets` (seconds left: 120 to 840 step 60; perps: none), `bands` (5 cent bands 1 to 18), `side_rules` (yes, no, cheap, favourite; perps: long, short), `filters` (names from the library: none, oi3, oi6, vol3, mom1, mom3, mom5, spread with their classes; perps: mom1, mom3, mom5, mom15, spread, tod, orb, sess), `exits` (H, T, S, B, M180, M60; perps: T3, T10, T15, T30, TS15, TS30, T60, T240, TC, TO). A subset of the library is a spec; a new entry in any list is `needs_new_code`.
- `event` (kind 3 only): the scorer plugin file name and hash, the decision instant, the signal threshold, the entry rule, the exit (usually hold).
- `costs`: `contracts` (10), `haircuts_primary` (cents or relative for perps, two numbers: the PF 1.3 line and the PF 1.0 line), `haircuts_stress` (optional), `fee_taker`, `fee_maker` (perps; both ASSUMED until Kalshi's schedule is read).
- `gates`: `min_n` (100), `pf_primary` (1.3), `pf_secondary` (1.0), `min_trade_days` (10 for perps), `bh_alpha` (0.05).
- `tries`: `rules_this_spec` (computed by the engine and checked against this number), `prior_m` (read from the TALLY, never typed).
- `prediction` (numeric, written before any read), `kill` (numeric), `kill_fast`: `true` (the engine drops the family when the first read has PF under 1.0 at the primary haircut, one line in the tally).
- `outputs`: `survivor_line` (market, rule, PF 1c and 2c, n, days) and `family_flag`.

## The run (what the pipeline does with a spec)
1. `spec_check.py <spec>` checks every field is present and consistent (grid values in the library, hashes shaped, dates sorted) and prints the number of rules the spec will try. A failing check stops the run.
2. Auditor B signs the spec (one message: the data, the cuts, the held-out map, the look-ahead), by its sha256.
3. The auto-run (a daily job) scores every signed spec on the data that landed since its last run; the print's sha256 is committed before it is read; a family is dropped when its first read has PF under 1.0 at the primary haircut ("kill fast"); BH counts every cell ever tried across families (the TALLY file holds counts of tries only, never a figure).
4. The report to the Head and the desk: counts first, m, SEARCH passes, VALIDATE passes after BH, survivors with the family flag.

## Rules that do not change
Hand case before code; one build only (a survivor needs a second build and rule 16b); a read of a held-out or a forward window follows the hold map; figures by message only; no account size or leverage until a survivor exists; the declined list (7e) and 7g (a variant is a version) apply to a spec like to any idea.
