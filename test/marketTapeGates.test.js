// The market tape (functions/marketTapeLib.js, written hourly by a keyless scheduled function) since Nov 11, 2026: only sources whose terms allow machine reads (Treasury yields, alternative.me
// crypto fear and greed). Each test states a consequence: a symbol with no permitted source says "No price" and never a number, a failed source keeps the old close with its own date and never
// aborts the others, an old Yahoo quote still in the document is never shown, and the required attribution is next to the data it credits.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/marketTapeLib.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const rules = fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8');
const NOW = Date.parse('2026-10-12T19:00:00Z');
const gates = {};

const NOW_TREASURY = Date.parse('2026-11-11T18:00:00Z');
const entry = (date, y10, y30) => '<entry><content><m:properties><d:NEW_DATE m:type="Edm.DateTime">' + date + 'T00:00:00</d:NEW_DATE>' + (y10 === null ? '' : '<d:BC_10YEAR m:type="Edm.Double">' + y10 + '</d:BC_10YEAR>') + (y30 === null ? '' : '<d:BC_30YEAR m:type="Edm.Double">' + y30 + '</d:BC_30YEAR>') + '</m:properties></content></entry>';
const feed = (rows) => '<feed>' + rows.map((r) => entry(r[0], r[1], r[2])).join('') + '</feed>';
const ok = (body) => ({ ok: true, status: 200, text: async () => body });

// Treasury XML becomes dated rows of plain numbers; a row with no date or no 10 year yield is dropped and nothing else in the feed is kept.
gates.T1 = () => {
  const rows = lib.parseTreasuryXml(feed([['2026-11-10', 4.98, 5.35], ['2026-11-09', 4.88, 5.26], ['2026-11-08', null, 5.0], ['2026-11-07', 4.9, null]]) + '<d:NEW_DATE>junk</d:NEW_DATE>');
  assert.deepStrictEqual(rows.map((r) => r.date), ['2026-11-07', '2026-11-09', '2026-11-10'], 'oldest first, the row with no 10 year yield dropped');
  assert.strictEqual(rows[0].y30, null, 'a missing 30 year is null, never zero');
  assert.deepStrictEqual(lib.parseTreasuryXml(null), [], 'a non-string body is no answer');
  assert.deepStrictEqual(lib.parseTreasuryXml(feed([['2026-11-10', 99, 5]])), [], 'an impossible yield is dropped');
  const q = lib.treasuryQuotes(lib.parseTreasuryXml(feed([['2026-11-09', 4.88, 5.26], ['2026-11-10', 4.98, 5.35]])), NOW_TREASURY);
  assert.deepStrictEqual([q.UST10Y.price, q.UST10Y.prevClose, q.UST10Y.closeDate, q.UST10Y.daily, q.UST10Y.source], [4.98, 4.88, '2026-11-10', true, 'treasury'], 'the latest close, the one before it, labelled daily with its date');
  assert.strictEqual(q.UST30Y.price, 5.35);
  assert.deepStrictEqual(lib.treasuryQuotes(lib.parseTreasuryXml(feed([['2026-11-10', 4.98, 5.35]])), NOW_TREASURY), {}, 'one row has no previous close, so no move can be shown: no quote');
};

// The crypto reading: only a score inside 0 to 100 counts, a rating is letters only, a body that is not an object is no answer.
gates.T24 = () => {
  const c = lib.parseFearGreedCrypto({ data: [{ value: '50', value_classification: 'Neutral' }, { value: '68', value_classification: 'Greed' }] });
  assert.deepStrictEqual([c.score, c.rating, c.prev], [50, 'neutral', 68]);
  for (const bad of [null, 5, 'x', {}, { data: [] }, { data: [{ value: '140' }] }, { data: [{ value: '-3' }] }]) assert.strictEqual(lib.parseFearGreedCrypto(bad), null, 'no usable score, no reading');
  assert.strictEqual(lib.parseFearGreedCrypto({ data: [{ value: '40', value_classification: '<img src=x>' }] }).rating, 'img srcx', 'a rating is letters and spaces only');
};

// The symbol table: every symbol with no permitted source is written as noPrice, every sourced one names a reader that exists, and only the Treasury yields have a source today.
gates.T22 = () => {
  const withSource = lib.SYMBOLS.filter((s) => s.source).map((s) => s.sym).sort();
  assert.deepStrictEqual(withSource, ['UST10Y', 'UST30Y'], 'only the Treasury yields have a permitted source (Bitcoin and Ethereum wait for the owner to read the exchange terms)');
  assert.ok(lib.SYMBOLS.filter((s) => s.source).every((s) => typeof lib.READERS[s.source] === 'function'), 'a named source has a reader');
  for (const need of ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'GC=F', 'CL=F', '^VIX']) assert.ok(lib.SYMBOLS.some((s) => s.sym === need && s.source === null), need + ' is listed with no source, so it says No price');
  assert.ok(/id="marketNewsList"/.test(html) && /id="briefCharts"/.test(html) && /id="briefMood"/.test(html), 'the Brief has its news, charts and mood');
};

// A failed source never blanks the rest, and what failed is named. With everything down there is nothing to write but the noPrice markers.
gates.T3 = async () => {
  const fetchFn = async (url) => {
    if (/alternative\.me/.test(url)) throw new Error('timeout');
    return ok(feed([['2026-11-09', 4.88, 5.26], ['2026-11-10', 4.98, 5.35]]));
  };
  const r = await lib.readTape({ fetchFn, now: NOW_TREASURY });
  assert.deepStrictEqual(Object.keys(r.quotes).sort(), ['UST10Y', 'UST30Y']);
  assert.strictEqual(r.mood, null);
  assert.ok(r.errors.some((e) => /^fear and greed crypto: timeout/.test(e)), 'what failed is named');
  const f2 = async (url) => /alternative\.me/.test(url) ? ok(JSON.stringify({ data: [{ value: '44', value_classification: 'Fear' }, { value: '40' }] })) : { ok: false, status: 429, text: async () => '' };
  const r2 = await lib.readTape({ fetchFn: f2, now: NOW_TREASURY });
  assert.deepStrictEqual([Object.keys(r2.quotes).length, r2.mood.crypto.score, r2.mood.crypto.source], [0, 44, 'alternative.me'], 'Treasury down, the crypto reading still lands');
  assert.ok(r2.errors.some((e) => /^treasury: HTTP 429/.test(e)));
  const dead = await lib.readTape({ fetchFn: async () => { throw new Error('offline'); }, now: NOW_TREASURY });
  assert.deepStrictEqual([Object.keys(dead.quotes).length, dead.mood], [0, null]);
  assert.ok(dead.noPrice.includes('BTC-USD') && !dead.noPrice.includes('UST10Y'), 'the unsourced symbols are named');
};
// A body that is not what was expected is no answer, never a quote: a login page, an empty feed, JSON where XML was due.
gates.T3b = async () => {
  for (const body of ['<html>blocked</html>', '', '{"a":1}', feed([])]) {
    const r = await lib.readTape({ fetchFn: async (url) => /alternative\.me/.test(url) ? ok('5') : ok(body), now: NOW_TREASURY });
    assert.deepStrictEqual([Object.keys(r.quotes).length, r.mood], [0, null], 'bad body: ' + body.slice(0, 20));
  }
  let calls = [];
  await lib.readTape({ fetchFn: async (url, opts) => { calls.push([url, opts]); return ok(''); }, now: NOW_TREASURY });
  assert.ok(calls.every(([u, o]) => /^https:\/\//.test(u) && o.redirect === 'manual' && o.headers['user-agent'] === 'shwoopnet-market-tape'), 'https only, no redirect followed, a generic client name');
  await assert.rejects(() => lib.getText(async () => ok(''), 'https://evil.example/x'), /host not allowed/, 'a host off the allowlist is never contacted');
  await assert.rejects(() => lib.getText(async () => ok(''), 'http://home.treasury.gov/x'), /host not allowed/, 'plain http is refused');
};

// The stored document: a failure keeps the older close with its own date, a noPrice symbol never carries a number, and nothing a removed source wrote survives.
gates.T3c = () => {
  const oldYahoo = { price: 5000, prevClose: 4990, asOf: 1, series: [1, 2], state: 'open' };
  const keep = { price: 4.9, prevClose: 4.8, asOf: 5, source: 'treasury', daily: true, closeDate: '2026-11-05' };
  const prev = { quotes: { '^GSPC': oldYahoo, UST10Y: keep, UST30Y: oldYahoo, 'BTC-USD': Object.assign({ source: 'treasury' }, oldYahoo) }, news: [{ headline: 'x' }], mood: { stocks: { score: 20 }, crypto: { score: 30, source: 'alternative.me' } } };
  const doc = lib.buildTapeDoc(prev, { quotes: {}, errors: ['treasury: HTTP 500'], mood: null }, NOW);
  assert.deepStrictEqual(doc.quotes.UST10Y, keep, 'the source failed: the older close stays with its own asOf and date');
  assert.ok(!('UST30Y' in doc.quotes), 'an old Yahoo quote (no source) is dropped, not kept for a permitted symbol');
  assert.deepStrictEqual(doc.quotes['^GSPC'], { noPrice: true, source: null, asOf: NOW }, 'no source: noPrice, and no old number survives');
  assert.deepStrictEqual(doc.quotes['BTC-USD'], { noPrice: true, source: null, asOf: NOW }, 'even a forged source cannot give an unsourced symbol a price');
  assert.ok(!('news' in doc) && !doc.mood.stocks && doc.mood.crypto.score === 30, 'headlines and the stocks reading are gone; the crypto reading is kept when its read failed');
  const fresh = lib.buildTapeDoc(prev, { quotes: { UST10Y: Object.assign({}, keep, { price: 5 }) }, errors: [], mood: { crypto: { score: 60, source: 'alternative.me' } } }, NOW);
  assert.deepStrictEqual([fresh.quotes.UST10Y.price, fresh.mood.crypto.score], [5, 60], 'a fresh read replaces the old one');
  assert.strictEqual(lib.buildTapeDoc(null, { quotes: {}, errors: [], mood: null }, NOW).mood, undefined, 'no reading at all: no mood');
};

// The scheduled function holds no secret, places nothing, runs hourly, and writes the whole document.
gates.T4 = () => {
  const fn = idx.slice(idx.indexOf('exports.marketTapeTick = onSchedule'), idx.indexOf('exports.kalshiLiveExit = onSchedule'));
  assert.ok(/schedule: "every 60 minutes"/.test(fn), 'hourly: the sources change once a day (it was every 15 minutes until Nov 11, 2026)');
  assert.ok(!/secrets:|KALSHI|signRequest|\/portfolio|createOrder|process\.env/.test(fn), 'no secret, no key, no order code');
  assert.ok(/ref\.set\(marketTape\.buildTapeDoc\(prev, r, Date\.now\(\)\)\)/.test(fn) && !/merge: true/.test(fn), 'the document is replaced whole, so nothing a removed source wrote can linger');
  assert.ok(/collection\("shared"\)\.doc\("marketTape"\)/.test(fn), 'the one shared document');
  assert.ok(/match \/shared\/\{doc\}[\s\S]{0,80}allow read: if signedIn\(\);[\s\S]{0,40}allow write: if false;/.test(rules), 'signed-in accounts read it and no client can write it');
  const code = fs.readFileSync(path.join(__dirname, '..', 'functions', 'marketTapeLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/KALSHI|signRequest|apiKey|api_key|Authorization|process\.env/i.test(code), 'the library has no key and no signing');
};

// The page strip lifts the same instruments the server lists, shows "No price" for an unsourced one, a close date for a daily one, and never an old Yahoo quote.
const fnSource = (name) => { const m = new RegExp('(function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'missing ' + name); return m[1]; };
const lift = () => {
  const items = /var TAPE_ITEMS = (\[[\s\S]*?\]);/.exec(html);
  assert.ok(items, 'TAPE_ITEMS');
  const src = ['tapeUsableQuotes', 'tapeCloseText', 'tapeAsOfText', 'tapeItemHtml', 'tapeNews'].map(fnSource).join('\n');
  return new Function('kalTime', 'kalDate', 'pct', 'marketTapeData',
    'var TAPE_STALE_MS = 3 * 3600 * 1000; var TAPE_ITEMS = ' + items[1] + ';\n' + src + '\nreturn { TAPE_ITEMS, tapeUsableQuotes, tapeCloseText, tapeAsOfText, tapeItemHtml, tapeNews };')(
    (ms) => 'T' + ms, (ms) => 'D' + ms, (a, b) => (a - b) / b * 100, { news: [{ headline: 'x' }] });
};
gates.T5 = () => {
  const f = lift();
  const shown = lib.SYMBOLS.filter((s) => s.tape).map((s) => [s.sym, s.name, s.kind]);
  assert.deepStrictEqual(f.TAPE_ITEMS.map((i) => [i.sym, i.name, i.kind]), shown, 'the page strip and the server list name the same instruments, in the same order');
  const none = f.tapeItemHtml({ sym: 'BTC-USD', name: 'Bitcoin', kind: 'crypto' }, undefined);
  assert.ok(/No price/.test(none) && !/tape-chg|\d/.test(none.replace(/<[^>]*>/g, '')), 'no quote says No price, never a number');
  assert.ok(/No price/.test(f.tapeItemHtml({ sym: 'TLT', name: 'x', kind: 'etf' }, { price: 0, prevClose: 5 })), 'a zero price is no quote');
  const y = f.tapeItemHtml({ sym: 'UST10Y', name: '10Y yield', kind: 'yield' }, { price: 4.98, prevClose: 4.88, source: 'treasury', daily: true, closeDate: '2026-11-10' });
  assert.ok(/4\.98%/.test(y) && /tape-chg up/.test(y) && /10\.0 bp/.test(y) && /close of Nov 10/.test(y), 'a yield shows the level, the move in basis points and the date of its close');
  const used = f.tapeUsableQuotes({ a: { price: 5, prevClose: 4 }, b: { noPrice: true, price: 5, prevClose: 4, source: 'x' }, c: { price: 5, prevClose: 4, source: 'treasury' }, d: null });
  assert.deepStrictEqual(Object.keys(used), ['c'], 'a quote with no source (an old Yahoo one) or marked noPrice is never shown');
  assert.strictEqual(f.tapeCloseText('not a date'), '', 'a bad date says nothing');
};
gates.T6 = () => {
  const f = lift();
  const fresh = f.tapeAsOfText({ updatedAt: NOW - 120000, quotes: { UST10Y: { daily: true, closeDate: '2026-11-10' } } }, NOW);
  assert.deepStrictEqual([fresh.stale, /^Yields: close of Nov 10\. Checked T\d+ CT$/.test(fresh.text)], [false, true], 'daily data says it is a close and its date, not that it is live');
  const old = f.tapeAsOfText({ updatedAt: NOW - 4 * 3600 * 1000, quotes: {} }, NOW);
  assert.ok(old.stale && /Last checked/.test(old.text) && /may be down/.test(old.text), 'a feed that stopped says so instead of looking current');
  assert.deepStrictEqual(f.tapeAsOfText(null, NOW), { text: '', stale: false });
};

// The page keeps no stale headlines: news shows only when the document names a permitted source, and the old snapshot's headlines are never a fallback.
gates.T7 = () => {
  const f = lift();
  assert.strictEqual(f.tapeNews(), null, 'headlines without a newsSource marker are never shown (an old document may still hold some)');
  assert.ok(/renderMarketNews\(tapeNews\(\)\);/.test(html) && !/tapeNews\(\) \|\| data\.news/.test(html), 'no fallback to the old snapshot headlines');
  assert.ok(/tapeUnsubscribe = api\.watchMarketTape\(handleMarketTapeUpdate\)/.test(html) && /if\(tapeUnsubscribe\)\{ tapeUnsubscribe\(\); tapeUnsubscribe = null; \}/.test(html), 'subscribed on sign-in, released on sign-out');
  assert.ok(/id="marketTape"[^>]*hidden/.test(html) && /id="briefAsOf"/.test(html), 'the strip starts hidden until data arrives; the Brief has its as-of line');
  assert.ok(/doc\(db, 'shared', 'marketTape'\)/.test(html), 'reads the one shared document');
  assert.ok(!/finance\.yahoo|query1\.|cnbc\.com|dowjones|treasury\.gov|alternative\.me\/(fng|crypto)/.test(html), 'the page itself calls no market-data host');
  assert.ok(/No news source yet/.test(html), 'an empty Market News says so plainly');
};

// Attribution (alternative.me allows commercial use only with it "right next to the display of the data"): the credit sits in the same card, directly under the crypto gauge it credits.
gates.T8 = () => {
  assert.ok(/briefGaugeHtml\('Crypto', mood\.crypto\) \+ '<div class="mood-src">Crypto fear and greed index data from alternative\.me<\/div>'/.test(html), 'the attribution follows the crypto reading with nothing between');
  assert.ok(!/briefGaugeHtml\('Stocks'/.test(html) && !/CNN/.test(html.replace(/<style>[\s\S]*?<\/style>/, '')), 'the CNN stocks reading is gone');
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

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
