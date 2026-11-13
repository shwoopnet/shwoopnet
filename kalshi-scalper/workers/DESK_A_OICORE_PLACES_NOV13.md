# OICORE's mechanism as separate wheel places (Desk A, Nov 13, 2026; written only; nothing read, nothing registered)
The Head's order of 21:05Z (item 1, the owner's shadow list: 15 against a target of 20 to 30). Lane 0.6: a rule that runs on several markets holds a separate place, record, seat and kill on each, each admitted with its own spec line. Each place below is OICORE's mechanism on one market: a **7g VERSION in research** (the same logic on a new market: not unique, takes no research slot, one try counted per place, labelled **"no evidence"**). Lane section 3 item 3 still holds: one rule, the same parameters on every market ("markets differ, parameters do not"); the only number that differs by market is the open-interest threshold, and it comes from ONE fixed rule, below, not from tuning.

## The one rule every place shares (so the places differ only by market)
- **Entry:** at the decision poll, the last poll at or before close - 180 s (no more than 10 s earlier; exchange time by the rolling median of the Date header, the NC15 convention); fire only if the market's open interest at the candle ending at close - 180 s minus its open interest at the candle ending at close - 360 s is at least **T**.
- **T, per market, fixed by rule:** the 90th percentile (nearest rank) of THAT market's own 3-minute open-interest rises over its previous 20 trading days of windows (no outcome, no price, no result read; the SPXOI1 threshold rule). **A place is NOT SEATED until 20 trading days of its open interest exist; before that no number is guessed.** Open interest comes from the market's public one-minute candles in the after-the-day pull; the NC15 book polls do not carry it, so each place also needs that candle pull to cover its series (a recorder or pull request for the Head and Main, not something I build).
- **Side and price:** the cheaper side by ask (ties to YES), ask 0.08 to 0.50 inclusive (OICORE's live 8c floor, `SLOT_SKIP_BELOW`, and its 50c ceiling).
- **Limit:** the ask SEEN (+0.00; OICORE's slip was switched off in PR 895). Fill check on the NC15 convention: the next poll within 6 s at which the limit still meets the size; the worse of the signal poll and that poll prices the fill.
- **Exit and size:** held to settlement; 1 contract in shadow; fee quadratic, multiplier 1, rounded up to the cent per order.
- **Classification (7f):** family = cheap-side open-interest surge, hold to settlement; risk class small fixed; stage Idea (a version of a live probe); counterparty "none named" (as OICORE's MECH1). Kill: the lane's own per-place rules (section 6 of the lane text), and a place follows its parent: if OICORE is closed for cause, every place closes with it.
- **Held-out and tries:** development reads (history candles, if the Head orders them) use HELDOUT_FIRST = 2026-12-01T00:00:00Z as for SPXOI1; each place counts one try and none is unique. Forward signals count only after this file's registration commit.

## The places (one line each: series, recorder, what it needs before it can be seated)
| Place | Series | Book source | Needs before seating |
|---|---|---|---|
| OICORE-XRP | KXXRP15M | R6 (2 s polls; fill check: the next poll within 6 s) | open-interest candles for KXXRP15M; 20 trading days |
| OICORE-SILVER | KXSILVER15M | NC15 (5 s polls) | open-interest candles; 20 trading days; the candles must actually carry open interest |
| OICORE-COPPER | KXCOPPER15M | NC15 | same |
| OICORE-WTI | KXWTI15M | NC15 | same |
| OICORE-EURUSD | KXEURUSD15M | NC15 | same |
| OICORE-GBPUSD | KXGBPUSD15M | NC15 | same |
| OICORE-USDJPY | KXUSDJPY15M | NC15 | same |
| OICORE-HYPE | KXHYPE15M | NC15 | same |
| OICORE-BNB | KXBNB15M | NC15 | same |
"Enough open interest" is a gate 0 for each NC15 place, not something I can assert without reading data: a market whose candles carry no open interest, or whose threshold T is 0 or a handful of contracts, is NOT seated (never guessed), and is reported as such.

## Not written, with the reason (so they are not re-proposed)
- **Ethereum (KXETH15M):** the research session scored the mechanism on Ethereum and it does not carry over (CLAUDE.md, the OICORE section: "Ethereum was scored by the research session and does not carry over"; the SLOTEX-ETH record). Skipped; I have not re-read that result file.
- **KXINX15M:** already SPXOI1 (its own seat).
- **Bitcoin:** is OICORE itself (the live probe), not a place.
- **Gold, AUD/USD, USD/CAD, natural gas:** not in the Head's list; no place written (USD/CAD and natural gas can be added by the same lines if the Head wants them).
- A place has no research value of its own: each is shadow only, "no evidence at n = x", and none can be promoted past what OICORE's own record earns.

## Dated line (Nov 13, 2026, the Head of R&D, 21:06Z): three more places, and gold stays out
Added by the same lines as above (the shared rule, T per market, gate 0, NC15, "not seated" until 20 trading days of open interest exist, no evidence, a 7g version each):
| Place | Series | Book source | Needs before seating |
|---|---|---|---|
| OICORE-AUDUSD | KXAUDUSD15M | NC15 (5 s polls) | open-interest candles; 20 trading days; the candles must carry open interest. (AUD/USD was KESTREL's market; KESTREL was favourite-late, so this is a different idea: the cheap side on an open-interest surge.) |
| OICORE-USDCAD | KXUSDCAD15M | NC15 | same |
| OICORE-NATGAS | KXNATGAS15M | NC15 | same |
**Gold stays out for now:** it is L1's market, and a cheap-side place there needs an interference ruling first (a shared stop or window budget with L1). The Head asked Desk B to write the open-interest candle jobs for the places. The count is now twelve places.

## Dated line (Nov 13, 2026, the Head of R&D, 21:17Z): OICORE-ETH added
| Place | Series | Book source | Needs before seating |
|---|---|---|---|
| OICORE-ETH | KXETH15M | R6 (2 s polls, to 2026-12-31 for the series R6 still records; R6 drops to Bitcoin and Ethereum only after 2026-11-13 23:59Z, so Ethereum stays on R6) | open-interest candles; 20 trading days; the candles must carry open interest |
Same frozen parameters as every other place (shared rule, T = the market's own 90th percentile of 3 minute open-interest rises over the previous 20 trading days, cheaper side 0.08 to 0.50, limit = ask seen, hold, 1 contract in shadow). Labelled **"research doubts carry-over"**: the research session scored the mechanism on Ethereum and found it did not carry over (the earlier note above stands); this place is versions-as-shadow, a forward record only, with no claim and "no evidence at n = x". The count is now thirteen places.
