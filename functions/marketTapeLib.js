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
  { sym: "SPY", name: "S&P 500 (SPY)", kind: "etf", tape: false },
  { sym: "QQQ", name: "Nasdaq 100 (QQQ)", kind: "etf", tape: false },
  { sym: "DIA", name: "Dow (DIA)", kind: "etf", tape: false },
];

const NEWS_FEEDS = [
  { source: "CNBC", url: "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114" },
  { source: "MarketWatch", url: "https://feeds.content.dowjones.io/public/rss/mw_topstories" },
];
const NEWS_KEEP = 6;
const FETCH_TIMEOUT_MS = 8000;
const UA = "Mozilla/5.0 (compatible; shwoopnet-market-tape)";

const num = (v) => { const x = Number(v); return v !== null && v !== undefined && v !== "" && Number.isFinite(x) ? x : null; };

function chartUrl(sym) {
  return "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sym) + "?range=1d&interval=5m&includePrePost=true";
}

// One Yahoo chart answer to one quote. null when the answer has no usable price or previous close: a half quote is never stored. `state` is where the trading day stands for
// that instrument (the chart meta carries the pre, regular and post periods); instruments without periods (crypto, some futures) report "open".
function parseChart(json, nowMs) {
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
  return { price, prevClose: prev, asOf: at !== null ? at * 1000 : nowMs, state };
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

function mergeNews(lists) {
  const seen = new Set();
  return [].concat(...lists).filter((a) => {
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
      const q = parseChart(JSON.parse(await getText(fetchFn, chartUrl(s.sym))), nowMs);
      if (!q) throw new Error("no usable price");
      quotes[s.sym] = q;
    } catch (e) { errors.push(s.sym + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  const lists = [];
  await Promise.all(NEWS_FEEDS.map(async (f) => {
    try { lists.push(parseRss(await getText(fetchFn, f.url), f.source)); }
    catch (e) { errors.push(f.source + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  const news = lists.length ? mergeNews(lists) : null;
  return { quotes, news: news && news.length ? news : null, errors };
}

module.exports = { SYMBOLS, NEWS_FEEDS, parseChart, parseRss, mergeNews, decodeEntities, readTape, chartUrl };
