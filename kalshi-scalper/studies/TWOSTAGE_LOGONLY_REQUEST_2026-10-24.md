# Two-stage entry log-only request for the build session (the owner said "go" in the research session on 2026-10-24)

Logging only. **No order, size, entry-time, cap or series change; nothing on the page.** The goal is a live record of what a "earliest of 10, 8 or 6 minutes where the favourite is in the band" entry would have been, so the registered forward read (TS1, public candles, on or after 2026-11-12) can also be checked on the bot's own markets.

## What to write
For every market of the series the bot looks at (gold, XRP, Bitcoin, Dogecoin, Ethereum, natural gas and the probes), once, at the 6 minute look, using the 1 minute candles the bot has already read (the 2 hour candle read starts at the market's first candle, so the earlier looks are in it):
- `ask10`, `side10`, `inBand10`: the favourite at the candle ending 600 s before the close: the side whose ask is inside the entry band (0.88 to 0.97), its ask, and whether one exists.
- `ask8`, `side8`, `inBand8`: the same for the candle ending 480 s before the close.
- `ask6`, `side6`, `inBand6`: the same at the 6 minute look (360 s).
- `twoStageLeft`: 600, 480 or 360 for the earliest look with `inBand` true, or null if none.
Write it on the order record when an order is placed, and, if cheap, as a small record for each market where `twoStageLeft` is not null and no order was placed. Candle times are the exact ones used in the backtest: the candle whose end is exactly 600, 480 or 360 seconds before the close (no substitution of a neighbouring candle; a missing candle means no value).

## What I do with it
After settlement, score the two-stage entry (the first in-band look, one entry per market, held) against the 6 minute entry on the same markets, per series, on days no earlier test has seen. The public-candle read TS1 on or after 2026-11-12 stays the registered one; this is the live cross-check. Any live two-stage rule would be a separate, reviewed change the owner asks for.
