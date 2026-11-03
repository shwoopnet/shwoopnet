# STRADDLE1 data feasibility (2026-11-03, no purchase made)

ThetaData pricing page (thetadata.net/pricing) and v3 docs (thetadata.net/docs, Getting Started, Subscriptions), read today:
- Options Value $40/month: 1 minute data from 2020-01-01 ("6 years"), 2 concurrent requests, historical EOD, Quote, Open Interest, OHLC endpoints; no trade, no greeks. Standard $80 (tick, 2016, 4 concurrent). Pro $160. Individual plans are personal use only, no redistribution.
- FREE tier: options EOD from 2023-06-01, 1 day delay, 30 requests/minute, EOD endpoint only. The EOD report carries NBBO bid and ask (last NBBO at the close) plus OHLC. That is enough for this test from 2023-06 (about 3.4 years, roughly 13 earnings seasons).
- Access: the Java Theta Terminal is no longer required. The official Apache-2.0 `thetadata` Python package (1.0.17 on PyPI, installs via pip here) talks gRPC to mdds-01.thetadata.us:443 and authenticates at nexus-api.thetadata.us; both are reachable through this container's proxy (HTTP 415 and 405 answers, i.e. the services respond). Credentials: THETADATA_API_KEY env var, or email and password (first two lines of creds.txt / THETADATA_CREDENTIALS_FILE). Actual login NOT tested (no account). Java 21 is also installed here and the terminal JAR (41 MB) downloads from download-unstable.thetadata.us, as a fallback.
- Unverified: whether gRPC streaming survives the proxy for large responses; the EOD bid/ask at 16:00 can be stale or wide on thin names (the 3 percent filter handles it).

Cheaper or free alternatives: ThetaData free account first (pilot, $0). Others not tested for reachability beyond status: cboe.com datashop (reachable, priced per file, expensive), optionsdx.com and historicaloptiondata.com (reachable, EOD files, paid; coverage and bid/ask not checked).

Earnings calendar: SEC EDGAR data.sec.gov submissions (reachable keyless with a User-Agent; Apple shows 8-K items 2.02 on 2026-11-02, 2026-07-30, ...). The submissions JSON also has acceptanceDateTime, which gives before-open versus after-close. company_tickers.json gives the universe. Yahoo calendar page returns 200 but is HTML and unreliable; Nasdaq API is blocked (000).
