# MECH1 screen spec (Desk A, Nov 17, 2026): DRAFT text for the Testing Desk's blind build, written before any code or data read

Built to MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4). Pure functions of (a signature, a data window); no search over thresholds. A signature is one row of the six fields (market, signal, clock, entry, exit, side) from mech_schema.py (vocabularies in that file). The registry (MECH_REGISTRY.json) decides what is NEW before anything is scored.

## 1. What the generator emits (one canonical setting per signature)
For each (market family, signal, clock, entry, exit, side) in the data we hold (inventory section 2) that classify() calls NEW (and, if the Head rules option B, a new market family counts as NEW unless a declined pattern names it): one record with these settings, nothing else:
- **Threshold:** the SEARCH-half 10% tail of the signal value on that market family. "Follow" side takes the tail in the direction of the signal's sign (top 10% of a positive-going field); "fade" and "cheap" the opposite tail; "favourite" and "cheap" are choices of side on a binary market and use the tail as a trigger only. The 10% tail cut is computed on SEARCH rows only, once, and written to a cuts file with its sha before any other window is read.
- **Hold (exit time), one fixed value per exit type:** fixed_time = 60 s before the close on 15 minute markets and 15 minutes after entry on perps; take_profit_multiple = 2 x the price paid, cap 0.99; stop = half of the price paid; hold_to_settle = settlement; next_print = the next funding print.
- **Entry:** taker at the ask of the next observation after the signal bar; maker_touch fills only on a later opposite-side taker print at least one tick through (a lower bound on fills, as lanes 1 and 6).
- **Cost:** 15 minute markets: the ceil-rounded per order Kalshi fee at entry and at any early exit, plus a 1c haircut against us on each leg. Perps: 12 bp taker and 5 bp maker per side (placeholders, as lanes 1 and 6) plus the funding actually booked.
- **At most 3 settings per signature, all counted.** The generator emits ONE; a second or third setting is a separate record and counts as a separate try.

## 2. Data inventory the first run may use (already held; Nov 18)
15 minute books R6 (Bitcoin, Ethereum, gold, XRP, Dogecoin) and NC15 (11 non-crypto series): best 5 YES and 5 NO bids with sizes about every 2 or 5 seconds, public trade tape, results. Perps: minute candles (bid and ask) for the four stock and index names already extracted, the 30 second and Sunday recorders, funding prints. The 60-day trade tape (columns trade_id, ticker, count, price, created_time, taker_side, is_block_trade) joins when the back-pull lands; see PERPS_TAPE60_AMENDMENT_NOV17.md. A signal field "tape" on gold, US 500, US Tech 100 and BTC counts as unread (the Head, Nov 17) only if the field is trade size, taker side, a sweep or a run of same-side prints, not a price or candle field.
Fast clocks first: fixed_time_to_close, any_minute, print (funding).

## 3. Signal field definitions (per market family; each is a number at the signal time t)
- price_level: the entry side's ask (15 minute) or the mid (perps).
- price_change: mid(t) minus mid(t - 180 s) on 15 minute markets; mid(t) over mid(t - 15 min) minus 1 on perps.
- spread: ask - bid at t, in cents (15 minute) or in bp of mid (perps).
- book_depth_imbalance: (sum of the best 5 bid sizes - sum of the best 5 ask sizes) / their sum, YES book, at t.
- open_interest: oi(t) - oi(t - 180 s) (15 minute candles); the perp's open interest change over 15 minutes (perps).
- volume: volume of the minute ending at t over the mean of the five earlier minutes.
- funding_rate: the last printed funding rate for the perp, at t.
- tape_flow: (contracts bought by takers - contracts sold) / total, every non-block print, over the 180 s before t; needs at least 5 prints.
- spot_elsewhere and cross_market_residual and settlement_mark and event_calendar: defined per record in the generator's output (the data source, the reference and the lag are named in the record); a record without them is not emitted.
A missing input (absent or not two sided quote, fewer than 5 prints, a null field) means NO SIGNAL at t (missing is never zero).

## 4. Screen 1, cheap
Per signature on SEARCH only: trades a day = fired signals / calendar days of the SEARCH window (at least 3); mean gross edge per contract after the fee and haircut must be above 0. A signature that fails either is dropped and counted as tried.
## 5. Screen 2
Net profit factor at the 1c haircut (15 minute) or at 12 bp a side (perps) in BOTH halves of SEARCH+VALIDATE (the window split in time, not by trade), at least 100 trades in total; one-sided day-clustered p as ENGINE1 (day_z, trade_days at least 10).
## 6. Multiplicity, held-out, shadow
BH at 5% over the number of SIGNATURES tried, carried into the ledger: m = the Head's carried m on the run day plus 1 to 3 per signature (the settings counted). The held-out window is read ONCE, after the BH survivors are printed and committed; windows are date constants in the registration (crypto perps: PERPS_TAPE60_AMENDMENT_NOV17.md section 3). A survivor that holds goes to forward shadow automatically (logging only); the usual CANDIDATE rule (100 forward trades, PF 1.3 at 1c, 1.0 at 2c, both halves) and the owner's popup follow.

## 7. Output (the daily table, spec section 4)
Per row: signature id, market, signal, clock, exit, side, stage, held-out n and days, signals a day, net edge at 1c in cents per contract, income a week = signals a day x edge x 5 x 7, forward n, and the date of forward n 100 at that rate.

## 8. Open points for the Head (the build cannot start the NEW step until decided)
(a) Option A or B for a new market family (strict spec versus a family counts as NEW). (b) Whether a second or third setting per signature is ever allowed on the first run (default: no, one each). (c) The carried m for the header.

## 9. Output format of each build (v1, Nov 17, 2026; both builds print exactly this)
One JSON object per line, one line per signature tried, UTF-8, keys sorted, separators "," and ":" with no spaces, lines sorted by `sig_id`. Floats are printed with Python's "%.17g" (counts and flags are integers or true/false; a missing value is null, never 0 or NaN). The file ends with one summary line `{"summary": ...}`. The print's sha256 is committed BEFORE it is opened (the usual rule), by whichever desk ran it.
Fields per signature line:
- `sig_id`: first 16 hex of sha256 of "market|signal|clock|entry|exit|side" (the six values joined by "|").
- `market`, `signal`, `clock`, `entry`, `exit`, `side`: the six values.
- `class`: the matcher's verdict (NEW, VERSION_NEW_MARKET, DUPLICATE, DECLINED), `class_ref`: the registry id it matched or null. Only NEW and, labelled, VERSION_NEW_MARKET are scored; the others print with `scored` false.
- `scored`: true or false. `data`: the named data file group read (e.g. "R6", "NC15", "perps_candles").
- `setting`: {`threshold_value` (the SEARCH 10% tail cut, float), `tail` ("high" or "low"), `hold_s` (seconds or null), `tp_mult` (or null), `stop_mult` (or null)}.
- `search`: {`n` (trades), `trade_days`, `calendar_days`, `trades_per_day`, `gross_edge_c` (cents per contract), `net_edge_c`, `pf_1c`, `pf_2c` (null where not defined), `pf_half1`, `pf_half2`, `day_z`, `p`} on the SEARCH window; `validate`: the same on VALIDATE.
- `screen1`, `screen2`: true or false; `m`: the BH family size for this line (the carried m plus the settings counted so far, an integer); `bh_survivor`: true or false.
- `heldout_read`: false. The held-out window is never read by the screen.
Summary line: `tried` (signatures scored), `settings_counted`, `m_carried`, `m_total`, `screen1_pass`, `screen2_pass`, `bh_survivors`, `windows` (the date constants as strings), `rule_hashes` (sha256 of every code file used), `data_file_shas` (sha256 of every data file read), `holds_file_sha256`.
Rounding: none inside the computation; printing only. A comparison is at 1e-9 relative for floats and exact for counts, flags and strings.

## 10. Data and holds the screen reads (Nov 17 inventory, Desk C's FAST_CLOCK_SIGNAL_FIELDS.md at 48c10c8bb on claude/idea-desk-c, read for file names only)
First run (Nov 18): R6 15 minute books (Bitcoin, Ethereum, XRP, Dogecoin, gold; 2026-10-29 to 11-16), NC15 (12 non-crypto series; 2026-11-11 to 11-16), perps minute candles (bid, ask, open interest, volume; indices, gold, BTC and ETH from Sep 2, stocks from Nov 5), funding and the 30 second recorder. Open interest, funding rate and settlement mark exist only on perps and the Deribit-linked Bitcoin feed; R6 and NC15 have none of them. HOLDS.json is applied by the generator at a pinned sha256 (the file is the Head's; this spec does not copy it): R6 gold, Bitcoin, Ethereum, XRP and Dogecoin are under hold H20 and the eight NC15 series of H21 are held; a held market-window is excluded from every window of the screen and its rows are counted in `summary.holds_excluded`. Where a hold and a window conflict the hold wins. Dogecoin is excluded under 7e whatever the hold says. The perps tape joins when the back-pull lands (PERPS_TAPE60_AMENDMENT_NOV17.md, settled readings in its section 6).
