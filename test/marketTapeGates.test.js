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
    return ok('<rss><channel><item><title>Stocks edge higher</title><link>https://mw.test/a</link><pubDate>Mon, 12 Oct 2026 18:00:00 GMT</pubDate></item></channel></rss>');
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
  assert.ok(/schedule: "every 15 minutes"/.test(fn), 'every 15 minutes (it was every 5 until Oct 26, 2026, to cut cost)');
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
    'var TAPE_STALE_MS = 45 * 60 * 1000; var TAPE_ITEMS = ' + items[1] + ';\n' + src + '\nreturn { TAPE_ITEMS, tapeAsOfText, tapeItemHtml, tapeStateWord, tapeNews };')(
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

// The Brief's small charts (Oct 23, 2026, the owner chose concept B; the catalysts calendar was dropped the same day for the news feed): a quote carries a thinned day series of plain numbers.
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
// The chart times (Oct 24, 2026, the owner: charts with a real x axis): each kept point carries its unix second, thinned the same way, and only when every kept point has one.
gates.T21b = () => {
  const r = { indicators: { quote: [{ close: [1, null, 3, 4] }] }, timestamp: [100, 200, 300, 400] };
  assert.deepStrictEqual(lib.chartPoints(r), { series: [1, 3, 4], times: [100, 300, 400] }, 'a gap drops its time with its price, so they stay paired');
  assert.deepStrictEqual(lib.chartPoints({ indicators: { quote: [{ close: [1, 2] }] } }).times, [], 'no timestamps: no times, never invented ones');
  assert.deepStrictEqual(lib.chartPoints({ indicators: { quote: [{ close: [1, 2, 3] }] }, timestamp: [100, null, 300] }).times, [], 'a partly stamped list is dropped whole');
  const closes = Array.from({ length: 300 }, (_, i) => 100 + i), ts = closes.map((_, i) => 1000 + i * 300);
  const big = lib.chartPoints({ indicators: { quote: [{ close: closes }] }, timestamp: ts });
  assert.ok(big.series.length === big.times.length && big.times[big.times.length - 1] === ts[ts.length - 1], 'thinned together, ending on the latest');
  const q = lib.parseChart(chart({ indicators: { quote: [{ close: [1, 2, 3] }] }, timestamp: [10, 20, 30] }), NOW);
  assert.deepStrictEqual(q.seriesT, [10, 20, 30], 'the times ride on the quote');
};
// Closed futures (Oct 25, 2026, the owner: "commodities has no charts"): a 1d answer with a price and no bars falls back to the last session of a 5d answer, never a week of it.
gates.T21c = () => {
  const day = 86400, base = 1700000000;
  const old = [1, 2, 3].map((v, i) => [base + i * 300, 50 + v]);
  const last = [1, 2, 3, 4].map((v, i) => [base + day + i * 300, 100 + v]);
  const five = { chart: { result: [{ indicators: { quote: [{ close: old.concat(last).map((x) => x[1]) }] }, timestamp: old.concat(last).map((x) => x[0]) }] } };
  const s = lib.lastSession(five.chart.result[0]);
  assert.deepStrictEqual(s.indicators.quote[0].close, [101, 102, 103, 104], 'only the newest session, not the week');
  const q = lib.parseChart(chart({}), NOW, five);
  assert.deepStrictEqual(q.series, [101, 102, 103, 104], 'a quote with no bars today takes the last session');
  assert.strictEqual(q.seriesT.length, 4, 'with its times');
  const own = lib.parseChart(chart({ indicators: { quote: [{ close: [7, 8] }] } }), NOW, five);
  assert.deepStrictEqual(own.series, [7, 8], "today's own bars win over the fallback");
};
// The Brief chart is the week (Oct 26, 2026, the owner: weekly charts, updated less often): the quote stays today's, the line comes from the 7 day read, marked range 7d. No weekly answer: today's line, no marker.
gates.T21d = () => {
  assert.ok(/range=7d&interval=1h/.test(lib.chartUrl('BTC-USD', '7d')) && /range=1d&interval=5m/.test(lib.chartUrl('BTC-USD')), 'one read for the quote, one for the week');
  const week = { chart: { result: [{ indicators: { quote: [{ close: [100, 101, 102, 103] }] }, timestamp: [1000, 4600, 8200, 11800] }] } };
  const today = chart({ indicators: { quote: [{ close: [9, 10] }] }, timestamp: [1, 2] });
  const q = lib.parseChart(today, NOW, week, week);
  assert.deepStrictEqual([q.series, q.seriesT, q.range, q.prevClose], [[100, 101, 102, 103], [1000, 4600, 8200, 11800], '7d', q.prevClose], 'the line is the week, marked');
  const d = lib.parseChart(today, NOW, null, null);
  assert.ok(d.range === undefined && d.series.length === 2, 'no weekly answer keeps today\'s line and no marker');
};
gates.T22 = () => {
  const syms = lib.SYMBOLS.map((s) => s.sym);
  for (const need of ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'GC=F', 'CL=F']) assert.ok(syms.includes(need), need + ' is read for the Brief charts');
  assert.ok(lib.NEWS_FEEDS.some((f) => /coindesk|cointelegraph/.test(f.url)) && lib.NEWS_FEEDS.some((f) => /20910258|RSSWorldNews/.test(f.url)), 'crypto, economy and world headlines are read');
  const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(!/faireconomy|coindesk|cointelegraph|dowjones/.test(html), 'the page itself calls none of these hosts');
  assert.ok(/id="marketNewsList"/.test(html) && /id="briefCharts"/.test(html) && /id="briefMood"/.test(html) && !/briefEvents/.test(html), 'the Brief has its news, charts and risk mood, and no calendar');
};

// No single desk fills the list (Oct 23, 2026): each feed contributes its newest few, so a busy crypto desk cannot push the economy and world headlines off the Brief.
gates.T23 = () => {
  const mk = (src, n) => Array.from({ length: n }, (_, i) => ({ headline: src + ' ' + i, source: src, url: '', datetime: 1000 - i }));
  const merged = lib.mergeNews([mk('Busy', 20), mk('Quiet', 2)].map((l, k) => k === 0 ? l.map((x) => Object.assign({}, x, { datetime: x.datetime + 500 })) : l));
  assert.strictEqual(merged.filter((x) => x.source === 'Busy').length, 3, 'a busy feed contributes only its newest 3');
  assert.strictEqual(merged.filter((x) => x.source === 'Quiet').length, 2, 'a quiet feed is still there');
  assert.ok(merged.length <= 12, 'and the list is capped');
};

// The risk mood (Oct 23, 2026): two fear and greed indexes, each kept only with a score inside 0 to 100, plain-string ratings, and a failure of one never blanks the other or what is stored.
gates.T24 = () => {
  const s = lib.parseFearGreedStocks({ fear_and_greed: { score: 20.94, rating: 'extreme fear', previous_close: 19.81 } });
  assert.deepStrictEqual([s.score, s.rating, s.prev], [20.9, 'extreme fear', 19.8], 'stocks: score, rating and yesterday');
  const c = lib.parseFearGreedCrypto({ data: [{ value: '50', value_classification: 'Neutral' }, { value: '68', value_classification: 'Greed' }] });
  assert.deepStrictEqual([c.score, c.rating, c.prev], [50, 'neutral', 68], 'crypto: score, rating and yesterday');
  for (const bad of [null, {}, { fear_and_greed: { score: 140 } }, { fear_and_greed: { score: 'x' } }]) assert.strictEqual(lib.parseFearGreedStocks(bad), null, 'no usable score, no reading');
  assert.strictEqual(lib.parseFearGreedCrypto({ data: [{ value: '-3' }] }), null, 'a score outside 0 to 100 is not stored');
  assert.strictEqual(lib.parseFearGreedStocks({ fear_and_greed: { score: 40, rating: '<img src=x>' } }).rating, 'img srcx', 'a rating is letters and spaces only');
  const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/if \(r\.mood\) patch\.mood = r\.mood;/.test(idx), 'a failed read leaves the stored mood alone');
};
gates.T25 = () => {
  const f = new Function(fnSource('briefMoodWord') + '\nreturn briefMoodWord;')();
  assert.deepStrictEqual([f(12), f(16), f(24), f(35), f(0), f(null)], ['Calm', 'Normal', 'Elevated', 'High', null, null], 'the one word comes from the VIX alone and is missing when the VIX is');
  const g = new Function('escapeHtml', fnSource('briefSentiment') + '\n' + fnSource('briefGaugeHtml') + '\nreturn briefGaugeHtml;')((x) => String(x));
  assert.ok(/&mdash;/.test(g('Stocks', undefined)) && !/mood-track/.test(g('Stocks', undefined)), 'no reading: a dash, no gauge');
  assert.ok(/left:50\.0%/.test(g('Crypto', { score: 50, rating: 'neutral', prev: 68 })) && /Yesterday 68/.test(g('Crypto', { score: 50, rating: 'neutral', prev: 68 })), 'a reading places its marker and shows yesterday');
  assert.ok(/left:100\.0%/.test(g('x', { score: 250 })), 'a wild score cannot push the marker off the track');
  assert.ok(!/mood-(up|down)/.test(g('x', { score: 21 })) && !/mood-(up|down)/.test(g('x', { score: 75 })), 'the mood is white and grey, never red or green: a feeling is not a verdict (the owner: as little panic-y as possible)');
  const sf = new Function(fnSource('briefSentiment') + '\nreturn briefSentiment;')();
  assert.deepStrictEqual([sf(10), sf(30), sf(50), sf(65), sf(90)].map((x) => x.word), ['Very cautious', 'Cautious', 'Neutral', 'Optimistic', 'Very optimistic'], 'calm words for the fear and greed score');
  assert.ok(!/Fear|Greed|Nervous|Stressed|panic/i.test(g('Stocks', { score: 12, rating: 'extreme fear', prev: 30 })), 'no fear word is shown, even on an extreme reading');
  assert.strictEqual(sf(NaN), null, 'no score, no word');
  assert.ok(/\.mood-kv > span:first-child/.test(html), 'the row label rule cannot reach the change inside the value, which stays green or red');
};

// NF1 and NF2: Market News keeps only equities, crypto and commodity stories (the owner, Oct 29, 2026, after an advice column about an ex-husband and a college fund appeared). Consequence: a personal advice or lifestyle piece must never reach
// the Brief even when it names a stock, and the per feed cap must pick each desk's newest RELEVANT stories, not the newest stories (three irrelevant ones would otherwise empty a desk).
gates.NF1 = () => {
  const keep = [['Stocks fall as Fed signals fewer rate cuts', 'CNBC'], ['Gold hits record high on tariff fears', 'MarketWatch'], ['Nvidia earnings beat forecasts, shares jump', 'CNBC'], ['Oil prices slide as OPEC+ weighs output', 'WSJ World'],
    ['Solana ETF filing delayed', 'CoinDesk'], ['Dogecoin whales accumulate', 'Cointelegraph'], ['Bond yields fall as the dollar slips', 'CNBC Economy'], ['S&P 500 closes at a record', 'MarketWatch'], ['Alphabet tanks nearly 13% for worst day ever, losing $500 billion in value', 'CNBC'], ['Amazon posts negative free cash flow of $42.4 billion, holds 2026 capex unchanged', 'CNBC'], ['Jobless claims near the lowest since the 1960s', 'CNBC Economy'], ['A Starbucks turnaround is brewing', 'MarketWatch']];
  const drop = [['My abusive ex-husband promised $20,000 for our kids\u2019 education. Now he refuses to pay. Is he legally obligated?', 'MarketWatch'], ['Trump signs defense bill after weeks of delay', 'WSJ World'], ['10 best fall road trips in America', 'CNBC'],
    ['Moneyist: I am 62 and my wife wants to retire. Should I sell stocks?', 'MarketWatch'], ['Earthquake hits coastal city', 'WSJ World'], ['My husband wants to buy gold with our savings. Is that smart?', 'MarketWatch'], ['', 'CNBC'], ['Why Does Spain Keep Having Deadly Rail Accidents?', 'WSJ World'], ['The midterms are crucial to the future of Social Security', 'MarketWatch'], ['My wife cried when I found out she had only $80,000 in her 401(k). Am I wrong?', 'MarketWatch']];
  keep.forEach(([h, s]) => assert.strictEqual(lib.isMarketNews({ headline: h, source: s }), true, 'kept: ' + h));
  drop.forEach(([h, s]) => assert.strictEqual(lib.isMarketNews({ headline: h, source: s }), false, 'dropped: ' + h));
  assert.strictEqual(lib.isMarketNews({ headline: 'My ex-husband and his bitcoin', source: 'CoinDesk' }), false, 'a crypto desk is not exempt from the advice and lifestyle drop');
  assert.strictEqual(lib.isMarketNews({ headline: 'Anything at all about a new token', source: 'CoinDesk' }), true, 'a crypto desk passes on its source');
  assert.strictEqual(lib.isMarketNews('Stocks edge higher'), true, 'a bare headline string works too');
};
gates.NF2 = async () => {
  const ok = (body) => ({ ok: true, status: 200, text: async () => body });
  const item = (title, when) => '<item><title>' + title + '</title><link>https://x.test/' + encodeURIComponent(title) + '</link><pubDate>' + when + '</pubDate></item>';
  const fetchFn = async (url) => {
    if (/query1\.finance\.yahoo\.com/.test(url)) return ok(JSON.stringify(chart()));
    if (/mw_topstories/.test(url)) {
      return ok('<rss><channel>' + item('My husband refuses to pay for college. Is he obligated?', 'Mon, 12 Oct 2026 18:50:00 GMT') + item('Moneyist: my mother-in-law wants a loan', 'Mon, 12 Oct 2026 18:40:00 GMT') +
        item('Dear Moneyist, should I buy stocks?', 'Mon, 12 Oct 2026 18:30:00 GMT') + item('Stocks slide as yields climb', 'Mon, 12 Oct 2026 17:00:00 GMT') + item('Gold steadies near a record', 'Mon, 12 Oct 2026 16:00:00 GMT') + '</channel></rss>');
    }
    return ok('<rss><channel></channel></rss>');
  };
  const r = await lib.readTape({ fetchFn, now: NOW });
  assert.deepStrictEqual(r.news.map((n) => n.headline), ['Stocks slide as yields climb', 'Gold steadies near a record'], 'the three newest MarketWatch stories were advice columns; the cap picked the newest relevant ones instead');
  const none = await lib.readTape({ fetchFn: async (url) => /query1\.finance\.yahoo\.com/.test(url) ? ok(JSON.stringify(chart())) : /coindesk|cointelegraph/.test(url) ? ok('<rss><channel></channel></rss>') : ok('<rss><channel>' + item('A celebrity wedding, and what to wear', 'Mon, 12 Oct 2026 18:00:00 GMT') + '</channel></rss>'), now: NOW });
  assert.strictEqual(none.news, null, 'nothing relevant: no news to write, so the page keeps its last headlines or says there are none');
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'marketTapeLib.js'), 'utf8');
  assert.ok(/parseRss\(await getText\(fetchFn, f\.url\), f\.source\)\.filter\(isMarketNews\)/.test(src), 'the filter runs on each feed before the per feed cap');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
