# scorekit: the shared loader and scorer skeleton (T3, Testing Desk, Nov 12, 2026)

Written from Desk B's census first cut (`FAMILY_CENSUS_NOV12.md`, 7523154) and Forensics' cost table (`FAMILY_COSTS_NOV12.md`, af5fd4d). **No data was opened and no try was made**: `test_scorekit.py` uses made-up rows only. No Kalshi request. No live account figure.

## What a card writes, and what it gets for free

A card supplies ONE function from loaded rows to trades. `scorekit.py` does the rest.

```python
import scorekit as k
cs = k.candles([folder_a, folder_b])      # {ticker: [candle]}, prices in dollars, cents or dollars accepted
ms = k.markets(folder_lists)              # settled lists: close, result, strike type/floor/cap, volume
bk = k.books(folder_books)                # order book snapshots (SHAPE ASSUMED, see below)
trades = my_card_rule(cs, ms)             # [{event, cluster, ts, price, win, fee_mult?}]  or early-exit trades with `net`
k.Cutoff(CUTOFF_TS, "REGISTRATION.md", not_before=READ_TS).check(trades)   # date constant + committed marker line
print(k.score(trades, {"name": "...", "price_source": "...", "freshness": "...", "book_replay": "...", "slow": False}))
```

Outputs per read: n and cash PF by window (three chronological windows for the research bar, two for the slow-family screen), net, PF at +1c, event-clustered z (equal-weight cluster means over their standard error; needs 2+ clusters), the haircut line, the book-replay line, the price source and freshness (printed as NOT STATED if the card omits them), and the label.

## Rules built in (so no card can forget them)

- **Bar:** PASS (research bar) only if clustered z is at least 5.46 (N about 2,113,000) AND cash PF is at least 1.5 in EACH of three windows. A card's own looser bar is reported as "cleared its registered bar (NOT the research bar)".
- **Labels:** under 100 trades "no evidence at n = x" (30 for the slow screen); FALSIFIED only at 100 or more with cash PF under 1.0; slow screen: "on the paper list (unproven)" or "off the list (failed the screen)", never PASS.
- **Haircut line always printed:** 34 percent of orders at the ask seen do not fill at a live-like delay (Forensics: 59 percent to 73 percent fill at the ask, 76 percent to 86 percent at +1c on the 15 minute series; 25 percent at +1c here). The label is recomputed on the haircut n; if that falls under the minimum, that line says "no evidence at n = x" whatever the headline shows. Family-specific fill rates from `FAMILY_COSTS_NOV12.md` can be passed by a card that has a book; none is assumed for a family with no recorder.
- **Fee:** 0.07 x price x (1 - price) unrounded, once, settlement free, scaled by `fee_mult` (Desk B holds the fee class; the cost table says redo costs where a family's fee differs).
- **Price source:** a source that says "market list quote" prints the warning that a list quote is up to about 11 seconds old.
- **Guard:** `Cutoff` takes the cutoff as a date constant, refuses to run before the registered read date, refuses development trades in a held-out read and held-out trades in a development read, refuses if the marker line already says READ ON, and fails if the registration has no marker line. `mark_read` returns the replacement line for a human to commit; the kit never writes a file.

## T4: shapes checked against real landed files (Nov 12, shape only: no outcome column printed, nothing scored)

Checked: one R6 book file (`quote-data` book15r6), `kalshi-pull-data` answers of four kinds (SPREADCELL1 binary candles, PERPBTC1M perp candles, CFRTI_K_LISTS settled list, COMBO1_OPENBOOK list) and one perp-data day file (`kalshi1m`). **Verified and flag removed:** binary candles (`yes_bid` and `yes_ask` objects with `*_dollars` strings, int `end_period_ts`, `volume_fp`, `open_interest_fp`); settled lists (keys incl. `result`, `strike_type`, `floor_strike`, `volume_fp`, open and close times); R6 book CSV (5 levels a side, empty cells skipped, YES buys meet NO bids); perp-data CSV. **Found and fixed (real bugs):** (1) perp candles are `{'bid': {...}, 'ask': {...}}` with plain keys and ABSOLUTE price levels, so the loader's old cents rule would have turned a 6.83 perp price into 0.068: now `absolute=True` for perps; (2) perp CSV and R6 book files had no loader: `perp_csv`, `r6_book` added. **Still not verified:** `books()` for pull-answer order books (no such answer has landed; the shape is from the recorder's parser); `cap_strike` on `less` and `between` markets (the one list checked, KXBTC15M, has only `floor_strike`, so UNRATEROUND must confirm `cap_strike` on its first answer); the cents fallback for the /historical endpoint (no historical candle answer has landed).
**One replay rule:** `fill_ioc` is Desk A's convention (e1a034f9) copied exactly: 1 contract IOC, walk up to 5 levels at or below the limit, first poll within 4 s after t0 + delay, no poll is no trade, short size is no trade. **Haircut table where no book exists** (Forensics HOW_TO_PRICE_A_PAPER_TRADE.md, 722ef2d): cut the count a third at the price seen, 15 percent at +1c and 2 s, 23 percent at 6 s, about 34 / 25 percent for a slow 5 to 10 s arrival, and add 1c to the price paid on the rest; the missed trades lean toward winners, so random dropping may be generous.

## Honest limits

- `books()` is the one loader still unverified against a landed pull answer (see T4 above).
- Equal-weight cluster means are one choice of clustered z. A card with very unequal clusters should say so in its registration; the kit does not weight.
- A trade that exits early must supply `net` itself; the kit does not simulate exits or fills. The book-replay line is the card's to compute from `books()` and pass in.
- `unrateround.py` and `poli2_count.py` predate this kit and keep their own small scorers; they can move onto it without changing any rule.
