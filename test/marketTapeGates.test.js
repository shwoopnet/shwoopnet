// The market tape: prices for the ticker strip and the Brief's index cards, and a few headlines, from shared/marketTape (functions/marketTapeLib.js, written every 5 minutes by a keyless
// scheduled function). Each test states a consequence: a failed feed never blanks the page, third-party text never reaches the page as markup, and an old price never replaces a new one.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/marketTapeLib.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const rules = fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8');
const NOW = Date.parse('2026-10-12T19:00:00Z');
const gates = {};

const chart = (over = {}, metaOver = {}) => ({ chart: { result: [Object.assign({ meta: Object.assign({
  symbol: 'SPY', regularMarketPrice: 777.15, chartPreviousClose: 778.57, regularMarketTime: NOW / 1000 - 30,
  currentTradingPeriod: { pre: { start: NOW / 1000 - 5 * 3600, end: NOW / 1000 - 1800 }, regular: { start: NOW / 1000 - 1800, end: NOW / 1000 + 3 * 3600 }, post: { start: NOW / 1000 + 3 * 3600, end: NOW / 1000 + 7 * 3600 } },
}, metaOver) }, over)] } });

// A chart answer becomes one quote with the price, the previous close and when it printed; a half quote is never stored.
gates.T1 = () => {
  const q = lib.parseChart(chart(), NOW);
  assert.deepStrictEqual([q.price, q.prevClose, q.state], [777.15, 778.57, 'open']);
  assert.strictEqual(q.asOf, NOW - 30000, 'the time it printed, in milliseconds, not the time we looked');
  assert.strictEqual(lib.parseChart(chart({}, { regularMarketPrice: null }), NOW), null, 'no price: no quote');
  assert.strictEqual(lib.parseChart(chart({}, { chartPreviousClose: 0, previousClose: null }), NOW), null, 'no previous close: no quote, so no percentage can be invented');
  assert.strictEqual(lib.parseChart({ chart: { result: null } }, NOW), null);
  assert.strictEqual(lib.parseChart(null, NOW), null);
  const prevOnly = lib.parseChart(chart({}, { chartPreviousClose: undefined, previousClose: 700 }), NOW);
  assert.strictEqual(prevOnly.prevClose, 700, 'falls back to previousClose');
  const post = lib.parseChart(chart({}, {}), NOW + 4 * 3600 * 1000);
  assert.strictEqual(post.state, 'post', 'after the close it says after hours');
  assert.strictEqual(lib.parseChart(chart({}, { currentTradingPeriod: undefined }), NOW).state, 'open', 'crypto has no periods and is always open');
};

// Headlines: entities decoded, only the fields the page shows, a link that is not http(s) dropped, newest first, no duplicates.
gates.T2 = () => {
  const xml = '<rss><channel><title>Feed</title>' +
    '<item><title>Fed holds &apos;steady&apos; as markets &lt;rally&gt;</title><link>https://www.cnbc.com/a</link><pubDate>Mon, 12 Oct 2026 18:00:00 GMT</pubDate></item>' +
    '<item><title><![CDATA[Stocks & bonds]]></title><link>javascript:alert(1)</link><pubDate>Mon, 12 Oct 2026 19:00:00 GMT</pubDate></item>' +
    '<item><link>https://x.test/no-title</link></item></channel></rss>';
  const items = lib.parseRss(xml, 'CNBC');
  assert.strictEqual(items.length, 2, 'an item with no headline is dropped');
  assert.strictEqual(items[0].headline, "Fed holds 'steady' as markets <rally>", 'entities decoded to text (the page escapes it on display)');
  assert.strictEqual(items[1].url, '', 'a javascript: link never reaches the page');
  assert.deepStrictEqual(Object.keys(items[0]).sort(), ['datetime', 'headline', 'source', 'url'], 'only the four fields the page shows');
  assert.ok(items.every((a) => typeof a.headline === 'string' && typeof a.datetime === 'number'));
  const merged = lib.mergeNews([items, [{ headline: 'FED HOLDS \'STEADY\' AS MARKETS <RALLY>', source: 'MW', url: '', datetime: 5 }, { headline: 'Newest', source: 'MW', url: '', datetime: 2e9 }]]);
  assert.strictEqual(merged[0].headline, 'Newest', 'newest first');
  assert.strictEqual(merged.filter((a) => /fed holds/i.test(a.headline)).length, 1, 'the same headline from two feeds appears once');
};

// A failed symbol or feed never blanks the rest, and what failed is named. With every source down it returns nothing to write.
gates.T3 = async () => {
  const ok = (body) => ({ ok: true, status: 200, text: async () => body });
  const fetchFn = async (url) => {
    if (/%5EGSPC/.test(url)) return { ok: false, status: 429, text: async () => '' };
    if (/query1\.finance\.yahoo\.com/.test(url)) return ok(JSON.stringify(chart()));
    if (/cnbc/.test(url)) throw new Error('timeout');
    return ok('<rss><channel><item><title>Only MarketWatch</title><link>https://mw.test/a</link><pubDate>Mon, 12 Oct 2026 18:00:00 GMT</pubDate></item></channel></rss>');
  };
  const r = await lib.readTape({ fetchFn, now: NOW });
  assert.ok(!('^GSPC' in r.quotes) && 'SPY' in r.quotes && Object.keys(r.quotes).length === lib.SYMBOLS.length - 1, 'one symbol failed, the others answered');
  assert.ok(r.errors.some((e) => /^\^GSPC: HTTP 429/.test(e)) && r.errors.some((e) => /^CNBC: timeout/.test(e)), 'what failed is named');
  assert.strictEqual(r.news.length, 1, 'one feed down, the other still gives headlines');
  const dead = await lib.readTape({ fetchFn: async () => { throw new Error('offline'); }, now: NOW });
  assert.deepStrictEqual([Object.keys(dead.quotes).length, dead.news], [0, null], 'nothing readable: nothing to write');
};

// The scheduled function holds no secret, places nothing, merges quotes one symbol at a time, and only writes what it read.
gates.T4 = () => {
  const fn = idx.slice(idx.indexOf('exports.marketTapeTick = onSchedule'), idx.indexOf('exports.kalshiLiveExit = onSchedule'));
  assert.ok(/schedule: "every 5 minutes"/.test(fn), 'every 5 minutes');
  assert.ok(!/secrets:|KALSHI|signRequest|\/portfolio|createOrder|process\.env/.test(fn), 'no secret, no key, no order code');
  assert.ok(/\.set\(patch, \{ merge: true \}\)/.test(fn) && /if \(Object\.keys\(r\.quotes\)\.length\) patch\.quotes = r\.quotes;/.test(fn) && /if \(r\.news\) patch\.news = r\.news;/.test(fn), 'merged, and quotes and news only when something was read');
  assert.ok(/collection\("shared"\)\.doc\("marketTape"\)/.test(fn), 'the one shared document');
  assert.ok(/match \/shared\/\{doc\}[\s\S]{0,80}allow read: if signedIn\(\);[\s\S]{0,40}allow write: if false;/.test(rules), 'signed-in accounts read it and no client can write it');
  const code = fs.readFileSync(path.join(__dirname, '..', 'functions', 'marketTapeLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/KALSHI|signRequest|apiKey|api_key|Authorization/i.test(code), 'the library has no key and no signing');
};

// The strip on the page lists the same instruments as the server writes, and shows the right thing for each kind.
const fnSource = (name) => { const m = new RegExp('(function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'missing ' + name); return m[1]; };
const lift = () => {
  const items = /var TAPE_ITEMS = (\[[\s\S]*?\]);/.exec(html);
  assert.ok(items, 'TAPE_ITEMS');
  const src = ['tapeStateWord', 'tapeAsOfText', 'tapeItemHtml', 'tapeNews'].map(fnSource).join('\n');
  return new Function('kalTime', 'kalDate', 'pct', 'marketTapeData',
    'var TAPE_STALE_MS = 20 * 60 * 1000; var TAPE_ITEMS = ' + items[1] + ';\n' + src + '\nreturn { TAPE_ITEMS, tapeAsOfText, tapeItemHtml, tapeStateWord, tapeNews };')(
    (ms) => 'T' + ms, (ms) => 'D' + ms, (a, b) => (a - b) / b * 100, { news: [{ headline: 'x' }] });
};
gates.T5 = () => {
  const f = lift();
  const shown = lib.SYMBOLS.filter((s) => s.tape).map((s) => [s.sym, s.name, s.kind]);
  assert.deepStrictEqual(f.TAPE_ITEMS.map((i) => [i.sym, i.name, i.kind]), shown, 'the page strip and the server list name the same instruments, in the same order');
  assert.ok(['SPY', 'QQQ', 'DIA'].every((s) => lib.SYMBOLS.some((x) => x.sym === s && !x.tape)), 'the three index proxies the Brief cards use are fetched too');
  const idxItem = f.tapeItemHtml({ sym: '^GSPC', name: 'S&P 500', kind: 'index' }, { price: 7798.05, prevClose: 7811.54 });
  assert.ok(/S&P 500/.test(idxItem) && /7,798\.05/.test(idxItem) && /tape-chg down/.test(idxItem) && /0\.17%/.test(idxItem), 'level and percent change, red when down');
  const y = f.tapeItemHtml({ sym: '^TNX', name: '10Y yield', kind: 'yield' }, { price: 5.26, prevClose: 5.244 });
  assert.ok(/5\.26%/.test(y) && /tape-chg up/.test(y) && /1\.6 bp/.test(y), 'a yield shows the level and the move in basis points');
  const btc = f.tapeItemHtml({ sym: 'BTC-USD', name: 'Bitcoin', kind: 'crypto' }, { price: 82311.9, prevClose: 83673.01 });
  assert.ok(/82,312/.test(btc) && !/82,311\.9/.test(btc), 'Bitcoin without cents');
  const none = f.tapeItemHtml({ sym: 'TLT', name: 'Long bonds', kind: 'etf' }, undefined);
  assert.ok(/&mdash;/.test(none) && !/tape-chg/.test(none), 'no quote shows a dash, never a made-up number');
  assert.ok(/tape-chg/.test(f.tapeItemHtml({ sym: 'TLT', name: 'Long bonds', kind: 'etf' }, { price: 0, prevClose: 5 })) === false, 'a zero price is no quote');
};
gates.T6 = () => {
  const f = lift();
  const fresh = f.tapeAsOfText({ updatedAt: NOW - 120000, quotes: { '^GSPC': { state: 'open' } } }, NOW);
  assert.deepStrictEqual([fresh.stale, /^Market open\. Updated T\d+ CT$/.test(fresh.text)], [false, true], 'fresh data says the market state and when it updated');
  const old = f.tapeAsOfText({ updatedAt: NOW - 3 * 3600 * 1000, quotes: { '^GSPC': { state: 'closed' } } }, NOW);
  assert.ok(old.stale && /last updated/.test(old.text) && /may be down/.test(old.text), 'a feed that stopped says so instead of looking current');
  assert.deepStrictEqual(f.tapeAsOfText(null, NOW), { text: '', stale: false });
  assert.strictEqual(f.tapeStateWord('pre'), 'Pre-market');
  assert.strictEqual(f.tapeStateWord('post'), 'After hours');
};

// The page keeps the tape strictly newer than the old snapshot for the index cards, falls back to the old headlines when the tape has none, and unsubscribes on sign-out.
gates.T7 = () => {
  assert.ok(/existing\.tapeAsOf >= \(Number\(q\.priceAsOf\) \|\| 0\)\) return;/.test(html), 'an older snapshot price never replaces a newer tape price');
  assert.ok(/renderMarketNews\(tapeNews\(\) \|\| data\.news\)/.test(html), 'headlines: the tape first, the old snapshot as the fallback');
  assert.ok(/tapeUnsubscribe = api\.watchMarketTape\(handleMarketTapeUpdate\)/.test(html) && /if\(tapeUnsubscribe\)\{ tapeUnsubscribe\(\); tapeUnsubscribe = null; \}/.test(html), 'subscribed on sign-in, released on sign-out');
  assert.ok(/id="marketTape"[^>]*hidden/.test(html) && /id="briefAsOf"/.test(html), 'the strip starts hidden until data arrives; the Brief has its as-of line');
  assert.ok(/doc\(db, 'shared', 'marketTape'\)/.test(html), 'reads the one shared document');
  assert.ok(!/finance\.yahoo|query1\.|cnbc\.com|dowjones/.test(html), 'the page itself calls no market-data host');
};

// The Brief's catalysts and small charts (Oct 23, 2026, the owner chose concept B). Each test states a consequence: only high and medium events of the major economies reach the page, past events and junk rows are dropped,
// a quote carries a thinned day series of plain numbers, and a failed calendar never blanks the stored list.
gates.T20 = () => {
  const now = Date.parse('2026-10-23T10:00:00Z');
  const rows = [
    { title: 'CPI y/y', country: 'USD', date: '2026-10-23T12:30:00Z', impact: 'High' },
    { title: 'Low thing', country: 'USD', date: '2026-10-23T13:00:00Z', impact: 'Low' },
    { title: 'Other economy', country: 'AUD', date: '2026-10-23T13:00:00Z', impact: 'High' },
    { title: 'Already past', country: 'USD', date: '2026-10-20T12:30:00Z', impact: 'High' },
    { title: 'Bad time', country: 'USD', date: 'soon', impact: 'High' },
    { title: 'Fed speaks', country: 'USD', date: '2026-10-23T14:00:00Z', impact: 'Medium' },
    null, 'x', { title: 5, country: 'USD' },
  ];
  const ev = lib.parseEvents(rows, now);
  assert.deepStrictEqual(ev.map((e) => e.title), ['CPI y/y', 'Fed speaks'], 'only upcoming high and medium events of listed economies, soonest first');
  assert.deepStrictEqual(Object.keys(ev[0]).sort(), ['at', 'country', 'impact', 'title'], 'only the four fields the page shows');
  assert.deepStrictEqual(lib.parseEvents({ not: 'a list' }, now), [], 'a wrong shape is an empty list, not a crash');
  const many = Array.from({ length: 80 }, (_, i) => ({ title: 't' + i, country: 'USD', date: new Date(now + i * 60000).toISOString(), impact: 'High' }));
  assert.ok(lib.parseEvents(many, now).length <= 40, 'the list is capped');
};
gates.T21 = () => {
  const closes = Array.from({ length: 300 }, (_, i) => 100 + i);
  closes[5] = null;
  const ser = lib.chartSeries({ indicators: { quote: [{ close: closes }] } });
  assert.ok(ser.length >= 2 && ser.length <= 100 && ser.every((v) => typeof v === 'number'), 'a thinned list of numbers');
  assert.strictEqual(ser[ser.length - 1], 399, 'it always ends on the latest close');
  assert.deepStrictEqual(lib.chartSeries({}), [], 'no data, no chart');
  assert.deepStrictEqual(lib.chartSeries({ indicators: { quote: [{ close: [5] }] } }), [], 'one point is not a chart');
  const q = lib.parseChart(chart({ indicators: { quote: [{ close: [1, 2, 3] }] } }), NOW);
  assert.deepStrictEqual(q.series, [1, 2, 3], 'the series rides on the quote');
};
gates.T22 = () => {
  const syms = lib.SYMBOLS.map((s) => s.sym);
  for (const need of ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'GC=F', 'CL=F']) assert.ok(syms.includes(need), need + ' is read for the Brief charts');
  assert.ok(lib.NEWS_FEEDS.some((f) => /coindesk/.test(f.url)) && lib.NEWS_FEEDS.some((f) => /bbci/.test(f.url)), 'crypto and world economy headlines are read');
  const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/if \(r\.events\) patch\.events = r\.events;/.test(idx), 'a failed calendar leaves the stored events alone (the patch is merged)');
  assert.ok(!/faireconomy|coindesk|bbci/.test(html), 'the page itself calls none of these hosts');
  assert.ok(/id="briefEvents"/.test(html) && /id="briefCharts"/.test(html) && /id="briefNextTime"/.test(html), 'the Brief has its catalysts, countdown and charts');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
