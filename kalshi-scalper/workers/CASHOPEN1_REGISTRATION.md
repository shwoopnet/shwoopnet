# CASHOPEN1 registration: do perp quotes lag the cash tape in the first minutes after the 09:30 New York open (written 2026-11-06, before any perps30 file or Yahoo bar of this study was read)

Discovery only. No live code, no promote verb.

## Mechanism and counterparty
At the 09:30 cash open the opening auction prints a price that the perp's market maker has only estimated; during the first minutes cash moves fast and the perp quote (a maker reacting to the cash tape, with a mark and a funding reference) can sit behind it. Counterparty: the maker whose resting quote is stale. Honest alternative: the maker reprices within one 30 second sample, or widens, so the lag is below one sample and below the round-trip cost.

## Data (not yet existing)
perps30/<date>/open.csv.gz, one sample per 30 seconds from 09:10 to 10:30 New York (same columns as the hourly files). No such file exists on origin/perp-data as of 2026-11-06 16:00 UTC. Cash reference: Yahoo chart API, keyless, 1 minute bars. **Yahoo keeps only about 7 days of 1 minute bars, so a cache of the cash bars of every universe ticker must be fetched at least once a week starting by 2026-11-13** (5 minute bars last 60 days but are too coarse for this test). Equity perps are `inactive` (bid 0) outside US hours: a perp-day with no active quote at 09:30 to 09:35 is counted and skipped.

## Rule (fixed, no tuning)
Universe, on cost: Equities and Indices perps whose median relative spread in 09:30 to 10:30 over dev files is at most 25 bps; the 15 cheapest; mapped to the cash ticker (single names to the stock; SPY, QQQ; US Tech 100 to QQQ as the liquid proxy). Slots: sample at the first 30 second sample at or after 09:31:00 and 09:33:00. At a slot, cash_ret = (close of the last complete 1 minute bar ending at or before the slot) / (open of the 09:30 bar) - 1; perp_ret = mid at the slot / mid at the first active sample at or after 09:30:00 - 1. Gap g = cash_ret - perp_ret in bps. If |g| >= 10 bps, trade the perp in the sign of g (buy at the recorded ask if g > 0, sell at the recorded bid if g < 0), exit 120 seconds later at the first sample at or after the exit time (bid for a long, ask for a short). One contract-equivalent, returns in bps of the entry price. Cost = the recorded spread crossing (in the entry and exit prices) plus a fee of 12 bps a side (the PERP1 placeholder; Kalshi's real perp fee is unverified), reported at x1.0 and x1.2. Control: same slots, |g| < 10 bps, same direction rule.

## Windows and cut
Dev perps30 open files dated 2026-11-06 to 2026-11-30; **files on or after 2026-12-01 are held out and never read**. Halves: odd and even dev trading days (D1 = first 8 files, D2 = the rest). z is day clustered (cluster = trading date).

## Numeric prediction
About 30 to 60 triggered trades in dev (10 perps x 16 days x 2 slots x about 15%), gross +3 to +10 bps, net after about 24 bps of fee plus 3 to 10 bps of spread = -15 to -30 bps, PF 0.1 to 0.5. Verdict probabilities: NOT_ENOUGH_DATA 55%, FALSIFIED 43%, LEAD 2%.

## Verdict rules
NOT_ENOUGH_DATA: under 150 triggered dev trades or under 12 dev trading days or no perps30 files (the months-to-150 at the observed rate is reported). FALSIFIED: with at least 150 trades, PF under 1.5 in either half, or net per trade not above 0 in both halves, or PF under 1.2 at fees x1.2, or trigger minus control not positive, or day clustered z under 5.27. LEAD only if all pass; then the held-out files are read once and PF under 1.5 there is FALSIFIED.
**Read date: 2026-12-01** (dev complete). The 150 trade bar at about 2 trades a dev day needs about 75 days of perps30 (about 2027-02-26) if the recorder is extended; today the test is NOT_ENOUGH_DATA by construction.

## Count
N +1. Running before about 730,455, after about 730,457 with CASHSPREAD1 (coordinator keeps the total).
