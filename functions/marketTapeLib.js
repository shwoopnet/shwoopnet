"use strict";
// The market tape: prices for the ticker strip and the Brief's index cards, and a few headlines, written to the one document shared/marketTape.
//
// KEYLESS. It holds no secret and no account credential, and it places no order. Prices come from Yahoo's public chart endpoint (unofficial, so it can change or refuse a
// request: every symbol and every feed fails on its own and a failure never blanks what is already stored), headlines from the public RSS feeds of CNBC and MarketWatch.
// It replaces the Brief's dependence on shwoop-server, which only refreshed prices between 08:00 and 17:00 Eastern and needed paid keys for news.
//
// Everything written is plain strings and numbers: the headline text is third-party text that every signed-in account reads, so only the four fields the page shows are kept, as
// strings, and a link that is not plain http(s) is dropped.

// `tape: true` shows in the strip. The three ETFs feed the Brief's index cards (SPY, QQQ and DIA are the tradable stand-ins it already labels as proxies).
const SYMBOLS = [
  { sym: "^GSPC", name: "S&P 500", kind: "index", tape: true },
  { sym: "^NDX", name: "Nasdaq 100", kind: "index", tape: true },
  { sym: "^DJI", name: "Dow", kind: "index", tape: true },
  { sym: "^RUT", name: "Russell 2000", kind: "index", tape: true },
  { sym: "^TNX", name: "10Y yield", kind: "yield", tape: true },
  { sym: "TLT", name: "Long bonds", kind: "etf", tape: true },
  { sym: "^VIX", name: "VIX", kind: "index", tape: true },
  { sym: "GC=F", name: "Gold", kind: "future", tape: true },
  { sym: "BTC-USD", name: "Bitcoin", kind: "crypto", tape: true },
  { sym: "ETH-USD", name: "Ethereum", kind: "crypto", tape: false },
  { sym: "CL=F", name: "Crude oil", kind: "future", tape: false },
  { sym: "SPY", name: "S&P 500 (SPY)", kind: "etf", tape: false },
  { sym: "QQQ", name: "Nasdaq 100 (QQQ)", kind: "etf", tape: false },
  { sym: "DIA", name: "Dow (DIA)", kind: "etf", tape: false },
];

// Top stories, the economy, world news and two crypto desks (the owner, Oct 23, 2026: crypto and world economy news). BBC, the Guardian and NPR refused a plain request in a live check, so they are not here.
const NEWS_FEEDS = [
  { source: "CNBC", url: "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114" },
  { source: "CNBC Economy", url: "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258" },
  { source: "WSJ World", url: "https://feeds.content.dowjones.io/public/rss/RSSWorldNews" },
  { source: "MarketWatch", url: "https://feeds.content.dowjones.io/public/rss/mw_topstories" },
  { source: "CoinDesk", url: "https://www.coindesk.com/arc/outboundfeeds/rss/" },
  { source: "Cointelegraph", url: "https://cointelegraph.com/rss" },
];
const NEWS_KEEP = 12;
// No single desk may fill the list: each feed contributes its newest few, then the lists are merged newest first.
const NEWS_PER_FEED = 3;
// The two fear and greed indexes for the Brief's risk mood: CNN's for stocks and alternative.me's for crypto, both public and keyless (unofficial, so each fails on its own and a failure leaves the stored value).
const FG_STOCKS_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata";
const FG_CRYPTO_URL = "https://api.alternative.me/fng/?limit=2";
const FETCH_TIMEOUT_MS = 8000;
const UA = "Mozilla/5.0 (compatible; shwoopnet-market-tape)";

const num = (v) => { const x = Number(v); return v !== null && v !== undefined && v !== "" && Number.isFinite(x) ? x : null; };

// range 1d at 5 minutes is the quote (price, previous close, session state); range 7d at 1 hour is the Brief chart (Oct 26, 2026, the owner: weekly charts, updated less often, to cut cost).
function chartUrl(sym, range) {
  const r = range || "1d";
  return "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sym) + "?range=" + r + "&interval=" + (r === "7d" ? "1h" : "5m") + "&includePrePost=true";
}

// One Yahoo chart answer to one quote. null when the answer has no usable price or previous close: a half quote is never stored. `state` is where the trading day stands for
// that instrument (the chart meta carries the pre, regular and post periods); instruments without periods (crypto, some futures) report "open".
function parseChart(json, nowMs, fallbackJson, weeklyJson) {
  const weeklyResult = weeklyJson && weeklyJson.chart && Array.isArray(weeklyJson.chart.result) ? weeklyJson.chart.result[0] : null;
  const fallbackResult = fallbackJson && fallbackJson.chart && Array.isArray(fallbackJson.chart.result) ? fallbackJson.chart.result[0] : null;
  const r = json && json.chart && Array.isArray(json.chart.result) ? json.chart.result[0] : null;
  const m = r && r.meta;
  if (!m) return null;
  const price = num(m.regularMarketPrice);
  const prev = num(m.chartPreviousClose) !== null ? num(m.chartPreviousClose) : num(m.previousClose);
  const at = num(m.regularMarketTime);
  if (price === null || prev === null || prev <= 0 || price <= 0) return null;
  let state = "open";
  const p = m.currentTradingPeriod;
  if (p && p.regular && num(p.regular.start) !== null && num(p.regular.end) !== null) {
    const t = Math.floor(nowMs / 1000);
    if (t >= p.regular.start && t < p.regular.end) state = "open";
    else if (p.pre && t >= p.pre.start && t < p.regular.start) state = "pre";
    else if (p.post && t >= p.regular.end && t < p.post.end) state = "post";
    else state = "closed";
  }
  // The chart is the week when the weekly answer has one; the quote above stays today's, so the header strip keeps its daily move. Otherwise it is today's line, as before.
  let pts = chartPoints(r), range;
  const week = weeklyResult ? chartPoints(weeklyResult) : null;
  if (week && week.series.length >= 2) { pts = week; range = "7d"; }
  else if (!pts.series.length && fallbackResult) pts = chartPoints(lastSession(fallbackResult));
  // seriesT (Oct 24, 2026, the owner: charts with a real time axis): the unix second of each point in `series`, same thinning, so the page can label the x axis. [] whenever the answer carried no timestamps.
  const out = { price, prevClose: prev, asOf: at !== null ? at * 1000 : nowMs, state, series: pts.series, seriesT: pts.times };
  if (range) out.range = range;
  return out;
}

// The day's closes for the Brief's small charts: numbers only, gaps dropped, thinned to at most SERIES_MAX points. [] when the answer has none, so a chart simply does not draw.
const SERIES_MAX = 96;
function chartPoints(r) {
  const q = r && r.indicators && Array.isArray(r.indicators.quote) ? r.indicators.quote[0] : null;
  const stamps = r && Array.isArray(r.timestamp) ? r.timestamp : [];
  const raw = q && Array.isArray(q.close) ? q.close : [];
  const pairs = [];
  raw.forEach((c, i) => { const v = num(c); if (v !== null && v > 0) pairs.push([v, num(stamps[i])]); });
  if (pairs.length < 2) return { series: [], times: [] };
  const step = Math.max(1, Math.ceil(pairs.length / SERIES_MAX));
  const kept = pairs.filter((_, i) => i % step === 0 || i === pairs.length - 1);
  const series = kept.map((x) => Number(x[0].toPrecision(7)));
  // Times only when EVERY kept point has one: a partly labelled axis would be worse than none.
  const times = kept.every((x) => x[1] !== null) ? kept.map((x) => x[1]) : [];
  return { series, times };
}
function chartSeries(r) { return chartPoints(r).series; }

// Oct 25, 2026 (the owner: "commodities has no charts"): while a futures market is closed (gold and crude on a weekend) Yahoo answers range=1d with a price and NO bars, so the Brief drew a price without a line. A 5 day answer still holds the last session; this keeps only its newest run of bars (a gap of more than 3 hours starts a new session) so the chart shows the last day traded, not a week.
const SESSION_GAP_S = 3 * 3600;
function lastSession(r) {
  const q = r && r.indicators && Array.isArray(r.indicators.quote) ? r.indicators.quote[0] : null;
  const stamps = r && Array.isArray(r.timestamp) ? r.timestamp : [];
  const raw = q && Array.isArray(q.close) ? q.close : [];
  const rows = [];
  raw.forEach((c, i) => { const t = num(stamps[i]); if (num(c) !== null && t !== null) rows.push([t, c]); });
  if (rows.length < 2) return r;
  let from = 0;
  for (let i = 1; i < rows.length; i++) if (rows[i][0] - rows[i - 1][0] > SESSION_GAP_S) from = i;
  const kept = rows.slice(from);
  return { indicators: { quote: [{ close: kept.map((x) => x[1]) }] }, timestamp: kept.map((x) => x[0]) };
}

// A fear and greed reading to {score 0 to 100, rating, prev}. Only a finite score inside 0 to 100 counts; the rating is cut to a short plain string. null when the answer has no usable score.
const fgNum = (v) => { const x = num(v); return x !== null && x >= 0 && x <= 100 ? Math.round(x * 10) / 10 : null; };
const fgText = (v) => String(v || "").replace(/[^A-Za-z ]/g, "").trim().toLowerCase().slice(0, 24);
function parseFearGreedStocks(json) {
  const f = json && json.fear_and_greed;
  const score = fgNum(f && f.score);
  if (score === null) return null;
  return { score, rating: fgText(f.rating), prev: fgNum(f.previous_close) };
}
function parseFearGreedCrypto(json) {
  const d = json && Array.isArray(json.data) ? json.data : [];
  const score = fgNum(d[0] && d[0].value);
  if (score === null) return null;
  return { score, rating: fgText(d[0].value_classification), prev: fgNum(d[1] && d[1].value) };
}

function decodeEntities(s) {
  return String(s)
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => { try { return String.fromCodePoint(parseInt(h, 16)); } catch (e) { return ""; } })
    .replace(/&#(\d+);/g, (_, d) => { try { return String.fromCodePoint(parseInt(d, 10)); } catch (e) { return ""; } })
    .replace(/&apos;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}

function tagText(block, tag) {
  const m = new RegExp("<" + tag + "[^>]*>([\\s\\S]*?)</" + tag + ">", "i").exec(block);
  if (!m) return "";
  return decodeEntities(m[1].replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")).trim();
}

// RSS items to {headline, source, url, datetime (seconds)}. A link that is not plain http(s) becomes "", and an item with no headline is dropped.
function parseRss(xml, source) {
  const out = [];
  const re = /<item[ >][\s\S]*?<\/item>/gi;
  let m;
  while ((m = re.exec(String(xml || "")))) {
    const block = m[0];
    const headline = tagText(block, "title");
    if (!headline) continue;
    const link = tagText(block, "link");
    const when = Date.parse(tagText(block, "pubDate"));
    out.push({
      headline: String(headline).slice(0, 300),
      source: String(source),
      url: /^https?:\/\//i.test(link) ? String(link).slice(0, 500) : "",
      datetime: Number.isFinite(when) ? Math.floor(when / 1000) : 0,
    });
  }
  return out;
}

// Market News relevance (the owner, Oct 29, 2026: "only pull equities, crypto or commodity related articles", after a MarketWatch advice column about an ex-husband and a college fund showed up). A headline is kept only when it is
// about stocks, crypto or commodities (or the rates, inflation, dollar and tariff news that moves them), and personal advice columns and lifestyle pieces are dropped even when a market word appears in them. The two crypto desks
// are about crypto by definition, so they pass on the source alone (the advice and lifestyle drop still applies). Applied to every feed BEFORE the per feed cap, so each desk's newest few are its newest RELEVANT few.
const CRYPTO_DESKS = ["CoinDesk", "Cointelegraph"];
const NEWS_ALLOW = new RegExp("\\b(" + [
  // equities
  "stocks?", "equit(?:y|ies)", "shares", "share price", "wall street", "S&P(?: 500)?", "nasdaq", "dow(?: jones)?", "russell", "nyse", "earnings", "profit warning", "guidance", "ipo", "etfs?", "index funds?", "rally", "rallies", "sell-?off", "bull market", "bear market", "correction",
  "investors?", "traders?", "buyback", "dividends?", "merger", "takeover", "price target", "upgrades?", "downgrades?", "analysts?", "hedge funds?", "short sellers?", "valuation", "market cap", "markets?", "futures", "options trading", "volatility", "vix", "bubble",
  // commodities
  "oil", "crude", "brent", "wti", "opec", "natural gas", "gasoline", "gold", "silver", "copper", "platinum", "palladium", "commodit(?:y|ies)", "wheat", "corn", "soybeans?", "coffee", "cocoa", "sugar", "cotton", "lumber", "uranium", "lithium", "bullion",
  // crypto
  "bitcoin", "btc", "ethereum", "ether", "crypto(?:currency|currencies)?", "stablecoins?", "solana", "xrp", "ripple", "dogecoin", "altcoins?", "blockchain", "tokens?", "defi", "coinbase", "binance", "digital assets?", "memecoins?",
  // what moves them
  "fed", "federal reserve", "powell", "interest rates?", "rate cuts?", "rate hikes?", "inflation", "cpi", "ppi", "payrolls", "jobs report", "gdp", "treasur(?:y|ies)", "yields?", "bonds?", "dollar", "tariffs?", "recession", "central bank", "ecb", "boj"
].join("|") + ")\\b", "i");
// Personal finance advice columns ("My ex-husband promised..."), reader questions, and lifestyle pieces: never market news, whatever words they contain.
const NEWS_DENY = new RegExp([
  "^(?:my|i|i['\u2019]m|i['\u2019]ve|dear)\\b",
  "\\bmy (?:ex|ex-\\w+|husband|wife|spouse|partner|boyfriend|girlfriend|mom|mother|dad|father|parents?|in-laws?|mother-in-law|father-in-law|sister|brother|son|daughter|kids?|children|neighbou?r|boss|landlord|roommate|fianc\u00e9e?)\\b",
  "\\b(?:moneyist|quentin fottrell)\\b",
  "\\b(?:should|can|could|do|am|will) I\\b",
  "\\b(?:is|are) (?:he|she|they) (?:legally|obligated)\\b",
  "\\b(?:horoscope|recipes?|kardashian|royal family|reality tv)\\b",
].join("|"), "i");
// `item` is a parsed feed item ({ headline, source }); a bare headline string is judged with no source.
function isMarketNews(item) {
  const headline = String(item && typeof item === "object" ? item.headline : item || "");
  const source = String(item && typeof item === "object" ? item.source || "" : "");
  if (!headline || NEWS_DENY.test(headline)) return false;
  return CRYPTO_DESKS.includes(source) || NEWS_ALLOW.test(headline);
}

function mergeNews(lists) {
  const seen = new Set();
  const capped = lists.map((l) => l.slice().sort((a, b) => b.datetime - a.datetime).slice(0, NEWS_PER_FEED));
  return [].concat(...capped).filter((a) => {
    const k = a.headline.toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  }).sort((a, b) => b.datetime - a.datetime).slice(0, NEWS_KEEP);
}

async function getText(fetchFn, url) {
  const ctl = typeof AbortController === "function" ? new AbortController() : null;
  const timer = ctl ? setTimeout(() => ctl.abort(), FETCH_TIMEOUT_MS) : null;
  try {
    const res = await fetchFn(url, { headers: { "user-agent": UA, accept: "*/*" }, signal: ctl ? ctl.signal : undefined });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.text();
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// Every symbol and every feed is independent. Returns only what was read: `quotes` holds the symbols that answered, `news` is null when no feed answered, and `errors` names
// what failed. The caller merges quotes into the stored document, so a symbol that fails keeps its older quote with its own asOf.
async function readTape({ fetchFn, now }) {
  const nowMs = typeof now === "number" ? now : Date.now();
  const quotes = {}, errors = [];
  await Promise.all(SYMBOLS.map(async (s) => {
    try {
      const json = JSON.parse(await getText(fetchFn, chartUrl(s.sym)));
      // The week for the Brief chart. A failure here leaves today's quote and today's line as they were.
      let week = null;
      try { week = JSON.parse(await getText(fetchFn, chartUrl(s.sym, "7d"))); } catch (e) { /* today's line */ }
      const q = parseChart(json, nowMs, week, week);
      if (!q) throw new Error("no usable price");
      quotes[s.sym] = q;
    } catch (e) { errors.push(s.sym + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  const lists = [];
  await Promise.all(NEWS_FEEDS.map(async (f) => {
    try { lists.push(parseRss(await getText(fetchFn, f.url), f.source).filter(isMarketNews)); }
    catch (e) { errors.push(f.source + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  const news = lists.length ? mergeNews(lists) : null;
  const mood = {};
  await Promise.all([["stocks", FG_STOCKS_URL, parseFearGreedStocks], ["crypto", FG_CRYPTO_URL, parseFearGreedCrypto]].map(async (x) => {
    try { const v = x[2](JSON.parse(await getText(fetchFn, x[1]))); if (v) mood[x[0]] = Object.assign(v, { asOf: nowMs }); else throw new Error("no usable score"); }
    catch (e) { errors.push("fear and greed " + x[0] + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  return { quotes, news: news && news.length ? news : null, mood: Object.keys(mood).length ? mood : null, errors };
}

module.exports = { SYMBOLS, NEWS_FEEDS, parseFearGreedStocks, parseFearGreedCrypto, chartSeries, chartPoints, lastSession, parseChart, parseRss, mergeNews, isMarketNews, NEWS_ALLOW, NEWS_DENY, CRYPTO_DESKS, decodeEntities, readTape, chartUrl };
