# Market tape sources: scoping (Nov 11, 2026)

Scoping only. No code was changed. Nothing here is legal advice; where a terms page could not be read the source is treated as barred. No request was sent to any Yahoo host. The strip and Brief keep running on Yahoo until the switch ships.

Why: Yahoo's terms (legal.yahoo.com/us/en/yahoo/terms/otos 2(d)(9), 2(e), 2(d)(10)) forbid automated access and building databases. The page needs a source whose terms allow an LLC to read by machine, store a snapshot and show it on its own site.

## 1. What the page needs today

From `SYMBOLS` and `NEWS_FEEDS` in `functions/marketTapeLib.js` (one quote read at 5 minutes over 1 day for price, previous close and session state, plus one read at 1 hour over 7 days for the Brief line, per symbol, every 15 minutes):

| Symbol | Name | In strip | Kind |
|---|---|---|---|
| ^GSPC | S&P 500 | yes | index |
| ^NDX | Nasdaq 100 | yes | index |
| ^DJI | Dow | yes | index |
| ^RUT | Russell 2000 | yes | index |
| ^TNX | 10Y yield | yes | yield |
| TLT | Long bonds | yes | ETF |
| ^VIX | VIX | yes | index |
| GC=F | Gold | yes | future |
| BTC-USD | Bitcoin | yes | crypto |
| ETH-USD | Ethereum | Brief only | crypto |
| CL=F | Crude oil | Brief only | future |
| SPY, QQQ, DIA | ETFs | Brief only | ETF |

Each quote needs: price, previous close, session state, the day's closes (`series`, `seriesT`), and the week's hourly line (`range: "7d"`). The Brief's three chart pairs are Bitcoin and Ethereum, SPY and QQQ, gold and crude. News: CNBC (two feeds), MarketWatch and WSJ World (Dow Jones RSS), CoinDesk, Cointelegraph. Mood: CNN stocks fear and greed, alternative.me crypto fear and greed.

## 2. Verdicts

Verdicts are for automated reads by a commercial LLC, plus caching and showing the data on its own site. "NOT READ" means the page failed to load and the source is treated as barred.

| Source | Verdict | Evidence (URL, clause) | Key | Delay / limits | Covers |
|---|---|---|---|---|---|
| Treasury FiscalData API | PERMITTED | fiscaldata.treasury.gov/api-documentation/: "The data is offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use" (continues to cover commercial use). No account or token needed. | No | No limit stated. Daily data. | Treasury datasets. Daily par yield endpoint was NOT confirmed on the page (only an example endpoint). |
| Treasury daily par yield curve (home.treasury.gov XML/CSV) | AMBIGUOUS | Rate statistics page has no terms of use text and the Site Policies page was not read. A "Developer Notice on changes to the XML data feeds" banner exists. US government work, but not confirmed on a page I read. | No | End of day only | 10Y, 30Y yield (daily close) |
| FRED API | PERMITTED for US government series, AMBIGUOUS or FORBIDDEN for third party ones | fred.stlouisfed.org/docs/api/terms_of_use.html: must "register for an API Key"; must show "This product uses the FRED(R) API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."; bans "any application that replicates or attempts to replace the essential user experience" of FRED. No caching clause. fred.stlouisfed.org/legal/: copyrighted series "Pre-approval required" need the owner's permission for commercial use; "Citation required" series are allowed for "internal commercial uses" and "reports to clients"; bans redistributing "any third party's proprietary content ... for commercial use" without written permission. | Yes, free | Daily series, one day behind. Bandwidth may be limited, no number stated. | DGS10, DGS30 (Treasury via Fed, public). VIXCLS (CBOE) and SP500 (S&P) are third party series: label not checked, treat as barred until the series page says otherwise. |
| Coinbase Exchange public market data | NOT READ, treat as barred | Docs say "Market Data APIs provide market data and are public" and name the terms at coinbase.com/legal/market_data. That page and coinbase.com/legal/market_data_terms both returned 403 to the fetch tool. | No (public endpoints) | Rate limit not stated on page read | BTC, ETH (would cover them, 24/7) |
| Kraken public API | NOT READ, treat as barred | support.kraken.com says "API keys are not required to call the market data (aka public) API endpoints". The API terms URL returned 404 and the legal index has no data clause. | No | Not stated | BTC, ETH |
| CoinGecko API | AMBIGUOUS | coingecko.com/en/api_terms: "You are entitled to charge for your services and products that incorporate or integrates our CoinGecko API." Must show "Powered by CoinGecko". "do[es] not encourage caching or storage"; if cached, refresh at least every 24 hours and protect it. Free Demo plan terms are on the pricing page, not read. | Yes (key), free tier unconfirmed | Limits on pricing page, not read | BTC, ETH |
| Alpha Vantage | FORBIDDEN on the free key | alphavantage.co/terms_of_service/: free key is for "personal, non-commercial use"; commercial includes use "as or on behalf of a corporation, firm, partnership ... and not as an individual". Free support page: 25 requests a day. | Yes | 25/day free | n/a |
| Finnhub | FORBIDDEN on free/personal | finnhub.io/terms-of-service: "All plan listed on Finnhub website is strictly for personal use unless explicitly stated otherwise." "Personal plan can't be used by any business even internally without a written approval." Also bars redistributing data or derived results. | Yes | 30 calls/second cap | n/a |
| Twelve Data | FORBIDDEN on free | twelvedata.com/terms: "Use Free Tier data for commercial purposes" is banned (2.3(l)); external display needs a Redistribution add-on (2.2(e)). | Yes | per plan | n/a |
| Polygon.io (now massive.com) | NOT READ, treat as barred | polygon.io/legal/terms redirects to massive.com/legal/terms, which is only an index: personal use under "Individuals" terms, business under "Businesses" terms. The actual clauses were not read. | Yes | not read | n/a |
| Tiingo | NOT READ, treat as barred | tiingo.com/about/terms returned 404. | Yes | not read | n/a |
| EODHD | FORBIDDEN on the terms read | eodhd.com terms: a "Professional User" is any entity using data "As part of a business activity"; the Non-Professional list bans "displaying, or granting access to the Information". Professional rights not set out, and no free plan on the page. | Yes | not read | n/a |
| Stooq | NOT READ, treat as barred | stooq.com returned 503. | No | n/a | n/a |
| Alpaca market data | EXCLUDED | Owner cut Alpaca from the site. Not checked. | | | |
| IEX Cloud | EXCLUDED | The service was shut down in 2024. Not checked. | | | |
| gold-api.com | AMBIGUOUS | Home page: "free to use, 24/7", "No Rate Limiting for real time prices", no key, shows gold (XAU), silver, platinum, palladium, copper, bitcoin, ethereum. It links to a Terms of Service that was NOT read, and does not state commercial use. Oil is not listed. | No | Real time, no stated limit | Gold, maybe BTC and ETH |
| CNBC RSS | AMBIGUOUS, lean barred | cnbc.com/terms/ covers only CNBC+/Pro/Investing Club: "You may not scrape, repackage, reproduce, republish, recirculate" content; no RSS-specific text. The footer links a /rss-feeds/ page that was not read. | No | | News |
| MarketWatch and WSJ (Dow Jones RSS) | NOT READ, treat as barred | dowjones.com/rss-feed-terms/ is blocked in this environment. | No | | News |
| CoinDesk, Cointelegraph RSS | NOT READ | Not fetched this round. Treat as barred until read. | No | | Crypto news |
| Federal Reserve press release RSS | AMBIGUOUS, likely permitted | Feeds exist, e.g. federalreserve.gov/feeds/press_all.xml and press_monetary.xml. The Website Policies page I read has no reuse or bot clause, only that third party copyrighted material needs the source's permission. No explicit permission sentence found. | No | | Official news (releases only, not market news) |
| alternative.me Fear and Greed API | PERMITTED | alternative.me/crypto/api/: "You are free to use our API and data from our API in any way you like, this includes commercial projects of any kind." Fear and greed page: "Commercial use is allowed as long as the attribution is given right next to the display of the data." Limit: "60 requests per minute enforced over a 10 minute window." They may "change or discontinue the API". | No | Updates about every 5 minutes | Crypto fear and greed (keep as is, add visible attribution next to it) |
| CNN Fear and Greed (production.dataviz.cnn.io) | NOT READ, treat as barred | cnn.com/terms returned HTTP 451. The endpoint is an undocumented site back end, the same kind of use as Yahoo's chart endpoint. | No | | Stocks fear and greed |

## 3. Recommended minimal set (PERMITTED only)

1. **alternative.me** for the crypto mood, unchanged, with the attribution shown next to it.
2. **Treasury FiscalData or Treasury's own yield curve** for the 10Y (and a 30Y in place of the TLT ETF). Daily close only. Needs one more read to confirm the exact endpoint and the Site Policies text before building.
3. **FRED** for DGS10 and DGS30 only if the Treasury endpoint is not usable. Free key, required notice text on the page, daily and a day behind.

That is all. On what was actually read, no source covers anything that moves during the day.

## 4. Gaps

- **Crypto (BTC, ETH):** no permitted live source confirmed. Coinbase and Kraken are the natural fit (public, keyless) but their terms could not be read. Next step is for the owner to open coinbase.com/legal/market_data in a browser and paste the display, caching and automated access clauses, or approve CoinGecko after its Demo plan terms are read.
- **Stock indices, S&P, Nasdaq 100, Dow, Russell 2000, SPY, QQQ, DIA, TLT:** no permitted free source. Free keyed APIs (Alpha Vantage, Finnhub, Twelve Data) forbid business use on the free key. Real-time US exchange data carries exchange licensing, so a paid plan with a display and redistribution licence is the realistic route.
- **VIX:** FRED VIXCLS is CBOE content (label unchecked), daily only.
- **Gold and crude oil futures:** gold-api.com is promising for gold but its terms are unread; oil has no candidate.
- **Intraday week line (1 hour bars):** none of the permitted sources gives it.
- **Fear and greed for stocks:** CNN not permitted as far as I could read.
- **News:** see section 6.

## 5. Proposed change design

**Functions.** `marketTapeLib.js`: replace `SYMBOLS` and `chartUrl` with a per source reader list; each symbol names its one permitted source or has `source: null`. Remove `parseChart` use for Yahoo. `marketTapeTick` keeps merging per symbol so one failing source never blanks the rest. The 7 day hourly read goes away for symbols whose source only has daily closes: the Brief then draws the daily closes it has, marked `range: "daily"`.

**Page.** A symbol with no source shows "No price" (strip and Brief), never a stale or invented number. The Brief chart pairs that lack data say so. Source credit lines go on the page: "Data from alternative.me" next to the crypto mood, and the FRED notice if FRED is used. Quote ages on the page come from each symbol's own `asOf`, so a daily source reads "close of <date>", not live.

**Key storage.** Any key (FRED, or a paid vendor) is a Firebase secret (`defineSecret`, Secret Manager), bound only to `marketTapeTick`. The owner enters it through the secure form (`request_credential` flow or `firebase functions:secrets:set` in the owner's own terminal), never in chat, the repo, `.env` committed files or the page. The page never sees the key.

**Tests.** (a) New gate in `test/marketTapeGates.test.js`: no file under `functions/` (comments stripped) contains `yahoo`, `query1.finance`, `query2.finance` or `finance.yahoo`, and no host outside a fixed allow list appears in the tape code. (b) A symbol with no source renders "No price" and writes no quote. (c) A failing source keeps the older quote with its own `asOf`. (d) The required attribution strings exist in `index.html` next to the data they credit. (e) `blankSlateGates` host list updated on purpose. (f) A secret name is referenced, no key value appears in the repo (security scan).

**Rollout.** Ship the new reader behind the existing document shape, deploy `marketTapeTick`, watch one day beside Yahoo, then delete the Yahoo code and add the ban gate in the same pull request.

## 6. News fallback (separate question)

The tape currently reads CNBC, MarketWatch, WSJ World, CoinDesk and Cointelegraph RSS. None of their terms was confirmed to allow automated reads and republishing headlines on a commercial site: CNBC's terms read say "may not scrape, repackage, reproduce, republish, recirculate" (for its paid products; the RSS page was not read), and the Dow Jones RSS terms could not be loaded. Treat all of them as barred until each feed's own terms page is read. The only confirmed-clean official source in this round is the Federal Reserve press release RSS (no reuse restriction found, no explicit grant), which gives central bank news, not market news. Options: read each publisher's RSS terms in a browser, ask a publisher for a licence, link out to headlines without storing text, or show Fed and Treasury releases only. The owner should decide.

## 7. Decisions the owner needs to make

1. **Live prices: is a paid, licensed feed acceptable?** Without one, the strip can only show daily closes for yields and no index prices. If yes, pick a vendor that sells a business display licence (Polygon/Massive Business, Twelve Data with the Redistribution add-on, or similar) and enter its key through the secure form. If no, accept a strip with "No price" for indices.
2. **Crypto:** read the Coinbase market data terms (or approve CoinGecko after its free plan terms are read) so BTC and ETH can stay.
3. **News:** which of the options in section 6.
4. **Stocks fear and greed:** drop it, or find a permitted source.
5. **Treasury endpoint:** OK to read one more page (Treasury Site Policies, FiscalData dataset page) to confirm 10Y and 30Y.

Uncertainty: several fetches were summarised by a small model, so quoted clauses should be checked against the live page before a build. Terms change; this is a Nov 11, 2026 reading.

## Nov 11 confirmation (Treasury endpoint, and the switch)

Owner decision, Nov 11, 2026: the Brief and the header strip move to the permitted set with no spend, and every symbol without a permitted source says "No price". No request was sent to any Yahoo host. The pages below were read with a fetch tool that summarises them, so the quoted clauses are short and should be checked against the live pages.

**Endpoint CONFIRMED to answer (daily 10 and 30 year).** `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=YYYYMM` returned an Atom/OData feed titled "DailyTreasuryYieldCurveRateData", last updated 2026-11-11, one entry per trading day with `NEW_DATE`, `BC_10YEAR` and `BC_30YEAR` (for example 2026-11-10: 4.98 and 5.35). The page that documents the feed is `home.treasury.gov/developer-notice-xml-changes`; it gives the all-years form (`field_tdr_date_value=all`, paged) and a daily file `https://home.treasury.gov/sites/default/files/interest-rates/yield.xml`. It states no rate limit and no terms. The tape reads one month per run (two when the month has fewer than two rows).

**Terms: NOT an explicit grant.** The Site Policies and Notices page (`home.treasury.gov/subfooter/site-policies-and-notices`) was read: it has no clause on automated access, scraping, caching, copyright or reuse. Its only third party text is "Non-federal websites do not necessarily operate under the same laws, regulations, and policies as federal websites." The rate statistics page has no terms text either. So: no ban found, no permission sentence found. The only explicit permission quoted in section 2 is FiscalData's ("free, without restriction") and it covers FiscalData datasets, not this feed. The data is a US government publication, but treat the terms question as open and re-read before relying on it for more than a once an hour GET. FiscalData itself has no daily par yield dataset that was found (the dataset search page named none).

**Cadence.** The yields change once a day, so `marketTapeTick` now runs hourly instead of every 15 minutes (a one line change, a quarter of the runs). alternative.me updates about every 5 minutes and allows 60 requests a minute; one an hour is far inside it.

**What the page shows now.** 10Y and 30Y yield: the close of the latest day, labelled "close of <date>". Crypto fear and greed with "Crypto fear and greed index data from alternative.me" directly under it. Everything else (S&P 500, Nasdaq 100, Dow, Russell 2000, VIX, gold, crude, Bitcoin, Ethereum, SPY, QQQ, DIA): "No price". Charts: "No chart: no permitted source yet". Market News: "No news source yet". The CNN stocks reading and every RSS feed are dropped until their terms are read. The strip's "Long bonds" (TLT, an ETF with no source) became the 30Y yield.

**Adding a source later.** One reader in `READERS` plus its host in `ALLOWED_HOSTS` (and the exact list in `test/noYahooMarketTapeGates.test.js`), then the symbol's `source` in `SYMBOLS`. Bitcoin and Ethereum wait for the owner's reading of the exchange's market data terms.

Not changed: the research recorders under `scripts/` and `.github/workflows/` still name Yahoo hosts (the perps cash price saver and the reference recorder). They are outside the site's functions and were not part of this switch; the owner should decide them separately.

## Note (Nov 12, 2026): the quote recorder's Coinbase and Bitstamp reads

`scripts/record_quotes.py` reads Coinbase and Bitstamp public trades for research. Coinbase's market data terms are unread (403 when fetched); Bitstamp's API page says companies need a signed commercial Data License Agreement; the account is in the owner's own name. This is not a finding that the reads are allowed. The owner accepted the risk on Nov 12, 2026 and the reads continue, for research only. A live probe that reads either venue still needs the owner's own popup naming that source. See CLAUDE.md.
