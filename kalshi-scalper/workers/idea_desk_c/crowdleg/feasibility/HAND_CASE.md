# CROWDLEG/NOTAKER feasibility count: hand case (Nov 14, 2026, written before the reader code)

**Input.** The invented files in `hand/combo/`. They are not real data.

**Rule.** Fixed before the run, on the Head of R&D's ruling of Nov 14, 02:31Z.

- **Two-sided (rule 18):** 0 < yes_bid < yes_ask < 1, with a tolerance of 1e-9. A locked or crossed quote is not two-sided.
- **Qualifying:** two-sided, with the NO ask (1 - yes_bid) between 0.20 and 0.50 inclusive, and the spread (yes_ask - yes_bid) at most 0.04, inclusive. Both edges use the 1e-9 tolerance.
- **Counts are distinct combo tickers per UTC day.** A ticker counts as "with legs" if any of its qualifying rows that day has a non-empty `leg_tickers`. An 18-column file has no `leg_tickers`, which counts as empty.
- **Guard:**
  - files dated 2026-11-26 or later are refused, because S3's held-out window may start there (rule 17);
  - any path part beginning HELDOUT is refused;
  - only the columns ticker, yes_bid, yes_ask and leg_tickers are read, never a result, volume or other price.
- **Complete day:** a UTC day with 40 or more polls.
- **The verdict uses complete days only.** The average of qualifying distinct combos per complete day: under 5 means CLOSE ("no evidence: combos cannot be priced"); 5 or more means put the fix to the owner. With no complete day, the verdict is "no complete day".

**Expected on the hand files**, run with `--complete-polls 2` so that the two hand polls make one complete day. The 2026-11-26 folder is refused and listed, never read.

- **2026-11-13:**
  - polls 2, rows 9, distinct listed 8 (A to H);
  - two-sided distinct 6 (A, B, E, F, G, H);
  - qualifying distinct 4 (A, F, G, H);
  - qualifying with legs 1 (A).
- **Average qualifying per complete day:** 4.0, so the verdict is CLOSE.
