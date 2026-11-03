# BOOKIMB1 registration: a static five-level book DEPTH IMBALANCE on the cheap tail contract of the hourly Bitcoin ladder (KXBTCD), 25 minutes before the close, taker at the ask, held to settlement (V2 worker, 2026-11-03, research only)

Written and committed BEFORE any outcome was joined to a book row. What was looked at to write it: the README ledger and the registrations/results of MAKERTAIL1, BOOKCH1, DEPTH1 (text only), `src/scalper/makertail1.py` (the loader, schema and fee code I reuse), the recorder file list. No `result` value and no ask, bid or depth number of the KXBTCD book was opened for this card. Disclosure: the coordinator has seen the DEV outcomes of MAKERTAIL1 (resting buys in the 1c to 15c band, same instrument, same 25 minute look, same DEV days); that is a different order type, band and feature, but the DEV days are not fresh to the person who proposed this idea. I have not seen them beyond the README lines (a post hoc YES versus NO side split, NO tails better), and nothing here uses a side rule.

## Duplicate check

- **BOOKCH1** (15 minute markets, relative imbalance as a TRIGGER on the cheaper side, trailing 24 hour rank, forward only): not the same market (R6 15 minute Bitcoin and XRP), look (180 s), feature (relative to its own history) or data (R6). This card uses the hourly ladder book and an ABSOLUTE zero split.
- **DEPTH1** (five level imbalance, `KXGOLD15M` and `KXBTC15M`, look 480 s, sign of the feature picks the SIDE, ten features): different series, a feature that picks the side, not a filter on a given cheap contract. Closest cousin; the definition below is a different construction (3 tick window, own versus complement of the cheap contract).
- **MAKERTAIL1**: a resting buy at the best bid in the 1c to 15c band, same instrument and look; no depth feature. Its taker comparison (buy at the ask, same strikes) is the nearest baseline; this card's OFF group is the plain taker tail.
- **MAKERMID1, QUOTE2B/MM1**: mid band, flat before the close, quoting; not a held tail.
- **FLOWHR1** (running): uses the trade tape for flow. This card uses the BOOK only and never reads `trades.csv.gz`.
- **LADLONG1, HRSEAS1, VOLGAP1, OIHR1, G3H1**: the taker tail without a book feature (PF 0.64 to 0.78); the base rate this card's OFF group should resemble. `workers/OICORE_SHAPE_INVENTORY.md` has no book-depth feature on the hourly ladder.

**New:** a book depth imbalance, measured at one fixed look, as the filter on the cheap tail taker trade on KXBTCD.

## Data

`origin/quote-data`, `book/<date>/<run>/book.csv.gz`, read through git history exactly as `makertail1.load()` does (each row: ticker, `close_time`, server Date header, five YES bid levels and five NO bid levels with sizes, price in dollars). Outcome: `market.result` in `data/conf2_lad.sqlite`. Exchange time is the server Date header (1 second). The tape is not read.

## Definition (frozen, with the sign)

For each hourly close T and each recorded KXBTCD strike at that close, the **look poll** is the last book poll of that ticker whose Date-header time is at or before T-1500 s and not more than 20 s before it (as MAKERTAIL1). No look poll = NoData.

**The trade.** Each contract has two sides, YES and NO. For the side S of a strike, its **ask** = 1 - the best bid of the opposite side at the look poll. A candidate is a (strike, side) with ask in [0.03, 0.30] at the look. **Per close and per side, take the candidate with the highest ask** (nearest the money; ties by the lower ticker string): at most one YES and one NO trade per close. Entry: a taker buy of 1 contract at the ask of the **fill poll** = the first poll at or after look + 1.0 s and within 20 s of it; hard limit 0.30 (no trade if that ask is above 0.30 or below 0.03 or its displayed size is under 10, counted as NoFill and reported); held to settlement. Net = (1 if the side won else 0) - ask - fee, fee = 7% x C x p x (1 - p) rounded UP to the cent with C = 10, reported per contract, and x1.2 as stress. Cheap side only: this card computes no favourite-side or ask-above-0.30 result.

**The feature (computed at the LOOK poll, five recorded levels, never after).** Let `own` be the bids for side S (YES bids for a YES contract, NO bids for a NO contract) and `opp` the bids for the other side. With ticks of 0.01:

- `D_own` = the sum of displayed sizes on `own` levels whose price is within 3 ticks of the best own bid (price >= best_own - 0.03 + 1e-9), from the five recorded levels.
- `D_opp` = the same for `opp`, within 3 ticks of the best opp bid.
- `imb = (D_own - D_opp) / (D_own + D_opp)`, in [-1, 1]. If either side has no bid the contract has no ask or the candidate is dropped (an own side with no bid, `D_own = 0`, is allowed when the opposite side has bids: imb = -1).

Plain reading: D_own is resting demand for the tail contract itself; D_opp is resting demand for its complement (which is, equivalently, the supply offered at our ask). `imb > 0` means more resting size supports the tail than supports the favourite.

**SIGN CONVENTION, FIXED NOW: the feature is ON when imb > 0 (strictly). OFF otherwise (imb <= 0, including 0).** No threshold, no tuning, no second sign, no tertiles. The ON group is the trade under test; the OFF group is its registered complement.

## Frozen split

DEV = closes in [2026-10-29 00:00Z, 2026-11-02 00:00Z), split into HALF1 and HALF2 at the median close (as MAKERTAIL1). **HOLDOUT = closes 2026-11-02 00:00Z to 2026-11-03 16:00Z, not opened** unless DEV passes the full bar. FORWARD = closes from 2026-11-03 16:00Z.

## Numeric prediction (before any count)

Candidates per close: 0 to 2 (the 7 recorded strikes sit close to the money, so an ask under 30c on a given side exists in most closes). About 70 to 120 trades in DEV, of which ON about 30 to 60. Win rate below the price paid (the tail taker lost at PF 0.64 to 0.78 elsewhere): ON PF about 0.75 (0.3 to 1.3), OFF PF about 0.75; ON minus OFF per trade about 0c (range -4c to +4c); I expect no sign. Verdict expected NOT_ENOUGH_DATA on DEV (ON trades under 150), then FALSIFIED or NOT_ENOUGH_DATA forward. Prior of a pass: under 3%.

## Counterparty (stated, not assumed)

The seller of the tail at the ask is a resting maker; resting demand for the complement within 3 ticks (a thick opposite book) would mean makers are more willing to sell the tail, which could mean informed supply, and a thick own book would mean more buyers of the tail than sellers, the same crowd that pays the tail's usual negative edge. If the result cannot name this, the entry reads "no counterparty named".

## Kill rules and verdicts

- **NOT_ENOUGH_DATA:** under 150 ON trades in DEV (checked first). The report then gives ON trades per day and the days to 150 at that rate.
- **FALSIFIED:** the ON group's PF after fees (C = 10, fee x1.0) is under 1.5 in either DEV half, OR (ON per-trade mean minus OFF per-trade mean) is not above 0 in both DEV halves.
- **NOT_YET_FALSIFIED** is the best word: a pass needs day-clustered z above the deflated bar (about 5.27), a named counterparty, the holdout positive and the forward read. Nothing promotes; there is no promote verb.
- **Forward:** the same rule on closes from 2026-11-03 16:00Z, read ONCE, on the first moment 150 settled ON trades exist in the forward set, or on 2026-12-15 if fewer by then (`bookimb1_fwd.py`, fwdread guard like `makertail1_fwd.py`: refuses a second read, refuses before the condition, prints the README line). Forward kill rules are the DEV ones applied to the forward halves; with fewer than 150 ON trades at 2026-12-15 the read says NOT_ENOUGH_DATA and gives the days to 150.

## Tries and N

One rule (one feature, one fixed sign, ON versus its complement; the complement is not a second try). **N +2** (one rule at +2), running count about 730,215, z bar about 5.27.

Code `src/scalper/bookimb1.py`, `src/scalper/bookimb1_fwd.py`, tests `tests/test_bookimb1.py` (synthetic books), result `workers/BOOKIMB1_RESULT.md`.
