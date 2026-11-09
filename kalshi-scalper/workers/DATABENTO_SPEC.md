# Databento historical pull for NQ and GC (owner on a Mac), Nov 9, 2026
Verified from Databento's public docs today: new accounts get $125 in free data credits; signing up gives an API key automatically (starts with db-, 32 characters, shown on the portal's API keys page); metadata, symbology and account calls are free and cost is checked with metadata.get_cost before any data request; billing is metered by uncompressed bytes of time series data. NOT verified (page is dynamic or silent): whether a card is required at sign-up, the 6 month expiry of the credits, and the price per GB for GLBX.MDP3 (see the data catalog page after login). Our sandbox CAN reach hist.databento.com (answers 401 without a key), so no network change is needed.

## What to request
- Dataset GLBX.MDP3 (CME Globex). Symbols NQ and GC; micros MNQ and MGC only if get_cost says the total still fits.
- Schemas ohlcv-1m (1-minute bars) and ohlcv-1d (daily). Timestamps are UTC; we convert to US Eastern in the loader.
- Continuous symbols, stype_in = continuous, stype_out = instrument_id (so every row carries the real contract id; a change in id marks a roll): NQ.c.0 and NQ.c.1 (calendar roll: .c.0 is the front month and moves to the next contract after expiry, as in NG.c.0 in their example) and GC.c.0, GC.c.1. Optional NQ.v.0 / GC.v.0 (rolls to the contract with the most prior-day volume, nearer the liquid month). Databento does NOT back-adjust: prices are the original unadjusted prices. That matches our registration (unadjusted front month with our own roll): we apply our roll rule on the contract id and use the .c.1 series for carry/roll cost.
- Date range: the longest that fits. Approximate size: an ohlcv bar is 56 bytes; 1-minute NQ is about 340,000 bars per year (about 19 MB), so 15 years of one 1-minute symbol is roughly 0.3 GB. Four series (NQ.c.0, NQ.c.1, GC.c.0, GC.c.1) for the full history is about 1 to 1.5 GB; the daily schema is negligible. Whether that fits the $125 depends on the per-GB price: get_cost gives the exact dollars for each request before anything is billed.

## How the key is used (never in chat)
The owner creates the account and copies nothing into chat. Main requests the secure credential form for host hist.databento.com; the owner enters the key there; the sandbox then calls metadata.get_cost for each planned request, reports the dollar figures, and fetches only requests the owner approves.

## Mac steps (paste-ready)
1. In Safari or Chrome go to databento.com and click Sign up (email or Google/GitHub). Note whether it asks for a card and tell us; if it does, a card is only needed to turn on pay-as-you-go, which you do NOT need: leave it off (Billing, usage-based access, leave "Enable pay as you go" off) so you cannot be charged beyond the free credits.
2. Log in, open the portal, click API keys (the left menu). Do not copy the key into chat. Wait for us to request the secure form, then paste it there only.
3. Optional, no code: Data catalog, GLBX.MDP3, Schema ohlcv-1m, Symbols NQ.c.0, Symbology type Continuous, date range, "Get cost" shows the price; do the same for the others and tell us the dollar figures (these numbers are not secret).
## If Databento does not fit (free, no card, Mac)
- Barchart: free account, historical download of daily and a limited number of intraday bars (usually capped at about 2 years of 1-minute for free).
- TradingView free: daily CSV export is not offered on the free plan; Premium exports chart data (1-minute depth capped by plan).
- Yahoo (ES=F, NQ=F, GC=F daily) is currently rate limiting our sandbox (429); the owner can download daily CSV from the Yahoo Finance history page in a browser (Max range, daily), usually from the 1990s, unadjusted continuous, fine for the daily trend tests.
- Stooq: daily CSV from the browser (es.f, nq.f, gc.f) works for a person even though our sandbox is blocked.
- FirstRate free sample is two weeks only (format check).
