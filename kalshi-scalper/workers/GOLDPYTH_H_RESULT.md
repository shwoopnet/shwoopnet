# GOLDPYTH-H result (V2 worker, 2026-10-30): NOT_RUNNABLE, no try spent (N +0, running count unchanged)

**Brief.** History version of the director's Brief A (`workers/DIRECTOR_2026-10-30.md`): fetch Pyth gold, the settlement source of
KXGOLD15M (`Metal.Index.1OZGOLD/USD`, feed id `7fd2c870...c387`, see `studies/SETTLEMENT_MECHANICS_2026-10-29.md`), at every minute
mark of the last 10 minutes of each gold window Aug 6 to Oct 27, check it reproduces Kalshi's results, then register and score a
Pyth fair-value rule. The forward recorder (Brief A proper) was not in scope and was not touched.

**Why it stops at step 1.** Pyth's price data is no longer keyless. Checked 2026-10-30 07:20 UTC with plain GETs, no key
(`src/scalper/goldpyth.py`, re-runnable):

| Endpoint | Answer |
|---|---|
| Benchmarks `/v1/updates/price/{ts}` (1oz gold, XAU/USD, and Bitcoin as a control) | 401 unauthorized |
| Benchmarks TradingView shim `/v1/shims/tradingview/history` (several symbol spellings, 1 and 60 minute) | 404 |
| Hermes `/v2/updates/price/{ts}` and `/latest` (gold and Bitcoin), Hermes beta | 401 unauthorized |
| Hermes `/v2/price_feeds` (metadata only) | 200 |
| Pyth Lazer history service (OpenAPI lists only `/live`, `/update-batches`, `/feeds` and token-gated publisher routes; `/history/v1/symbols` is metadata) | no price route |

The 401 comes from Pyth's own server (Cloudflare headers), not the agent proxy. Bitcoin answers the same, so it is not a gold
restriction. This matches what GOLDFV1 already recorded on 2026-10-29 ("Pyth's history now answers 401 without a key") and the
settlement study ("Pyth's history needs a key"); the brief's premise that Benchmarks is public and keyless is out of date. Note
also that Hermes LATEST now answers 401, so Brief A's forward recorder as drafted ("live Pyth prices are public") would need a
key too; the director's brief should be corrected before it goes to the owner.

**What is keyless, and why it is not enough.** Kalshi's own market objects carry Pyth at each quarter hour: a settled
KXGOLD15M market has `expiration_value` (Pyth at the close, e.g. 3982.83) and the next window's `floor_strike` is that same number.
That is one Pyth price per 15 minutes, at the open and the close of each window, nothing inside it. The registered design needs
Pyth at minute marks 10 to 1 minutes before the close; at the open the distance to the strike is zero by construction, so the
quarter-hour series cannot give a fair value at any decision minute. Not run, not counted. The 20-window match check was not run
either, since no Pyth price at the close instant could be read (Kalshi's `expiration_value` IS the settlement value, so comparing
it with the result would be circular).

**How this differs from GOLDFV1 and XMAC1 (what has and has not been tested).** GOLDFV1 used Yahoo's 1 minute COMEX gold future
bars (`GC=F`), a different instrument from Pyth's 24/7 1oz gold index: it carries a futures basis and a roll, trades on the CME
schedule, and Yahoo stamps bars by minute start, so its information is a minute old at best. XMAC1 used Yahoo 1 minute S&P future,
dollar index and 10 year yield bars as leaders, not gold's price at all. Both found Kalshi already prices the latest minute of
those feeds. Neither used the settlement source, and neither saw anything below one minute. So "does Kalshi gold lag Pyth itself"
remains untested; it is answerable only with a Pyth key (history) or a recorder that has one (forward).

**Registration.** None written: registration comes before any Pyth price is joined to Kalshi data, and no Pyth price could be
read, so there was nothing to register and no variant was tried. N +0.

**Verdict: NOT_RUNNABLE.** Paths that would make it runnable, all needing the owner: a Pyth API key placed in the Claude
environment's secrets (never in chat), or a paid historical export. Nothing else in this repo was changed.

Files: `kalshi-scalper/src/scalper/goldpyth.py` (access probe, no key, no environment read), this file.
