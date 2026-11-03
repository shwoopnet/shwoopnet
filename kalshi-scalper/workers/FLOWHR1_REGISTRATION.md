# FLOWHR1 registration: does signed taker flow on the contract separate winning from losing cheap tails of the HOURLY Bitcoin ladder (KXBTCD), bought as a TAKER at the ask? (V2 worker, 2026-11-03, research only)

Written and committed BEFORE any flow value, win rate, or P/L was computed for this card. What was looked at to write it: the README ledger, `src/scalper/makertail1.py` and `makertail1_fwd.py` (loaders and guard pattern), `src/scalper/fwdread.py`, `scripts/record_book.py` (tape columns), and the registrations of MAKERTAIL1, MAKERMID1, BOOKCH1. No flow, ask-by-flow, outcome or fill was computed for this card.

**Owner rule (strict, 2026-11-03): cheap side only. This card buys only the cheap side (ask 3c to 30c). No favourite-side result is computed or printed anywhere in the code (asserted by a test: the ask band is the only price filter and an ask above 0.30 is never scored).**

## Duplicate check

- **S-FLOW1** (the refinement chat's lead, Bitcoin 15 MINUTE markets, cheaper side, taker flow in the 3 minutes before the decision, threshold -0.036; the FLOW1 worker tests it on history): different series, different look, different window. This card does not touch 15 minute markets and cites -0.036 as fitted elsewhere, NOT tuned or re-fitted here. No FLOW1 or S-FLOW1 registration was in the repo when this was written (grep of README and workers/).
- **FLOW1 (2026-10-27, README line 6891) and PERPFLOW1:** order flow on the UNDERLYING (Binance) and on the perpetual, as a filter on L1 entries or as a trade on the perp. Different instrument: here the flow is Kalshi's own contract tape.
- **MAKERTAIL1 / MAKERMID1:** RESTING bids on the hourly ladder (adverse selection). This card is the TAKER at the ask on the same book and tape, with a flow filter. MAKERTAIL1's taker comparison (all tails, no filter, bid band 1c to 15c, ask size >= 10) was an information row, PF 0.86 in DEV.
- **BOOKCH1:** book SIZES as a trigger on 15 minute markets. Not flow, not hourly.
- **QUOTE2B / MM1:** two-sided quotes. **LADLONG1, HRSEAS1, VOLGAP1, OIHR1, LADLOCK, LOCK2H:** cheap-tail taker trades without a flow feature (PF 0.64 to 0.78). **OICORE_SHAPE_INVENTORY:** no signed-tape-flow feature on KXBTCD.

**New:** signed taker flow on the contract itself, from the full public tape, as a filter on a cheap-tail taker buy on the hourly Bitcoin ladder.

## Disclosure of what the coordinator saw

The coordinator saw MAKERTAIL1's DEV outcomes for resting bids in the 1c to 15c band (fill and win rates by price bucket, by side, and the taker comparison PF 0.86). No flow was seen. The DEV window below is therefore NOT virgin for the tail band; that is why the forward read, not DEV, carries the claim. The threshold -0.036 comes from the S-FLOW1 lead on 15 minute markets and is fixed; nothing here is tuned.

## Data

`origin/quote-data` `book/` (git history, 3 second books for the 7 strikes nearest the money and the public tape every 30 s with trade ids de-duplicated), loaders reused from `makertail1.py`. Outcomes from `data/conf2_lad.sqlite` (`market.result`). Exchange time = the server Date header (books) and `created_time` (trades). Closes from 2026-10-29.

## Definitions (frozen)

- **Look:** the last book poll of a ticker at or before T-1500 s (25 minutes before the close), not older than 20 s; none = NoData.
- **Entry (taker):** the book poll at or after look + 1 s (within 20 s). For side S in {yes, no}, ask(S) = 1 - best bid of the OTHER side, ask size = displayed size at that bid. Eligible when ask in [0.03, 0.30] (hard limit 0.30) and ask size >= 10. Buy 1 contract at the ask, held to settlement.
- **One per close per side:** among the strikes of a close whose side S is eligible, take the one with the HIGHEST ask (nearest the money, still under 0.30). So at most one YES-side tail and one NO-side tail per close. (YES-side = strike above spot, NO-side = strike below.)
- **Signed taker flow on that contract (side S):** over trades of the ticker with `created_time` in (look - 600 s, look], bought_S = contracts with `taker_outcome_side == S`, sold_S = contracts with `taker_outcome_side != S` (a taker buying the other side is a taker selling S). flow_S = (bought_S - sold_S) / (bought_S + sold_S). The YES and NO flows of one strike are exact mirrors. Zero contracts in the window = **NoFlow** (reported, in neither set). If the recorded tape polls have a hole longer than 90 s inside the window (or none cover it) = **NoData** (counted, excluded).
- **Low-flow set:** flow_S <= -0.036. **High-flow set (complement):** flow_S > -0.036 (defined flow only). **All-flow control:** every eligible tail, including NoFlow and NoData-free rows only (NoData rows excluded everywhere).
- **Fee:** 7% x C x p x (1 - p) rounded UP to the cent, C = 10, p = ask; per contract = that / 10. Net per contract = (1 if the side won else 0) - ask - fee. Also reported at fee x1.2. PF = gross wins / gross losses of the nets.
- **Readouts (not claims):** low-flow by side (YES / NO), by ask bucket (3-9c, 10-19c, 20-30c), win rate against mean price paid, high-flow the same.

## Frozen split

DEV = closes 2026-10-29 00:00Z to 2026-11-02 00:00Z (the two halves split at the median close among selected DEV tails). HOLDOUT = closes 2026-11-02 00:00Z to 2026-11-03 16:00Z, opened only if DEV passes every bar below. **FORWARD = closes from 2026-11-03 16:00Z.**

## Numeric prediction (before any count)

About 1.9 selected tails a close, so about 100 DEV tails; flow defined for 60% to 80% of them; low-flow about 40% to 50% of the defined: roughly 25 to 45 low-flow trades in DEV (NOT_ENOUGH_DATA expected). Mean ask about 17c; win rate about 0.8 x the price paid; low-flow net per contract about -2c (range -6c to +3c), PF about 0.7 (0.3 to 1.6); low-minus-high difference positive with probability about 45%, so no more than a hypothesis. Prior of FALSIFIED by the numbers 85%, of NOT_ENOUGH_DATA on DEV 90%.

## Kill rules and verdicts

- **NOT_ENOUGH_DATA:** under 150 low-flow trades with a result in the window. The report gives low-flow trades per day and the days to 150 at that rate. Numbers are still printed as information (with signs), but a verdict word needs 150.
- **FALSIFIED:** (low-flow PF under 1.5 after the fee in EITHER half) OR (mean net per contract of the low-flow set minus that of the high-flow set not above 0). Applied at 150 or more low-flow trades, and on DEV at any n as a "sign check only" line (the verdict word on DEV is still NOT_ENOUGH_DATA below 150).
- **NOT_YET_FALSIFIED** is the best word: a pass would need day-clustered z above the deflated bar (about 5.27), a named counterparty and the holdout; no promote verb.

## Forward plan

`src/scalper/flowhr1_fwd.py` (fwdread guard: prints the registered rule, refuses a second read, writes a started marker, prints the README line, never appends). Closes from 2026-11-03 16:00Z, read ONCE when 150 low-flow trades with a result exist or on 2026-12-15, whichever comes first; the same definitions and kill rules, DEV and HOLDOUT never touched (asserted). Reports by side as readouts.

## Tries and N

Two (the low-flow rule and the all-flow control). N +4 (+2 per rule); coordinator keeps the total (about 730,215 + this, z bar about 5.27).

Code `src/scalper/flowhr1.py`, `src/scalper/flowhr1_fwd.py`, tests `tests/test_flowhr1.py` (synthetic trades and books), result `workers/FLOWHR1_RESULT.md`.
