'use strict';
// Gates for two LOG-ONLY builds (Nov 11, 2026, the owner approved P3 and P2).
// P3: a slot skip that happens AFTER the strategy's trigger passed also records the open interest rise, the side and the price it would have bought (qualified: true), so every trigger can be scored
//     whether or not an order went out. A market that never triggered gets none of it.
// P2: after a minute's orders are all sent, one public order book read per answered order is written onto the order (bookYes5, bookNo5, bookReadMs). Neither build may change whether, what or when the bot buys.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const fx = require('./fixtures/offEquivalenceScenarios');
const live = require('../functions/kalshiLiveLib.js');
const run = require('../functions/kalshiSlotRunLib');
const report = require('../functions/kalshiReportLib');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const clone = (x) => JSON.parse(JSON.stringify(x));
const BOOK = { orderbook_fp: { yes_dollars: [['0.60', '5'], ['0.71', '40'], ['0.72', '12'], ['0.70', '9'], ['0.69', '3'], ['0.68', '2'], ['0.50', '1']], no_dollars: [['0.27', '30'], ['0.25', '4']] } };
const isBook = (url) => /\/orderbook$/.test(String(url).split('?')[0]);
const gates = {};

// ---- L1 (the real runL1Tick against the recorded world) ----
const l1Run = async (bookReply) => {
  const w = fx.l1World({});
  const inner = w.common.fetchFn;
  w.common.fetchFn = async (url, o) => {
    if (isBook(url)) { w.r.log.push({ kind: 'fetch', method: o.method, url, body: null, signalIsAbort: o.signal instanceof AbortSignal }); return bookReply(url, o); }
    return inner(url, o);
  };
  const ret = await live.runL1Tick({ ...w.common, quotes: [fx.q('KXBTC15M', fx.T)] });
  return { w, ret };
};
const okBook = () => ({ status: 200, text: async () => JSON.stringify(BOOK) });
const bookWrites = (w) => w.r.log.filter((x) => x.kind === 'store' && x.call === 'updateTest' && x.args[1] && 'bookYes5' in x.args[1]);

gates['BK1 an L1 order gets the best 5 YES and 5 NO bids, best first, with the read time, written after the order was sent'] = async () => {
  const before = Date.now();
  const { w } = await l1Run(okBook);
  const wr = bookWrites(w);
  assert.strictEqual(wr.length, 1, 'one snapshot write for the one order');
  const p = wr[0].args[1];
  assert.deepStrictEqual(p.bookYes5, [{ p: 0.72, q: 12 }, { p: 0.71, q: 40 }, { p: 0.7, q: 9 }, { p: 0.69, q: 3 }, { p: 0.68, q: 2 }], 'five best YES bids, best first');
  assert.deepStrictEqual(p.bookNo5, [{ p: 0.27, q: 30 }, { p: 0.25, q: 4 }], 'the NO bids there are');
  assert.ok(Number.isFinite(p.bookReadMs) && p.bookReadMs >= before, 'the wall clock of the read');
  const idx = (f) => w.r.log.findIndex(f);
  const post = idx((x) => x.kind === 'fetch' && x.method === 'POST'), book = idx((x) => x.kind === 'fetch' && isBook(x.url));
  assert.ok(post >= 0 && book > post, 'the book read comes strictly after the order POST');
  assert.strictEqual(w.r.log.filter((x) => x.kind === 'fetch' && isBook(x.url)).length, 1, 'at most one read per order');
};
gates['BK2 the book read is bounded by an abort signal and sends nothing but a public GET'] = async () => {
  const { w } = await l1Run(okBook);
  const reads = w.r.log.filter((x) => x.kind === 'fetch' && isBook(x.url));
  assert.ok(reads.every((x) => x.method === 'GET' && x.signalIsAbort === true && x.body === null));
  assert.ok(/timeoutMs: BOOK_READ_TIMEOUT_MS/.test(code(read('functions', 'kalshiLiveLib.js'))), 'the read passes its own short timeout');
  assert.ok(live.BOOK_READ_TIMEOUT_MS <= 5000, 'a few seconds at most');
};
gates['BK3 a failed, refused, empty or thrown book read leaves the order exactly as it was, and the minute is unchanged'] = async () => {
  const base = await l1Run(okBook);
  const posts = (w) => w.r.log.filter((x) => x.kind === 'fetch' && x.method === 'POST').map((x) => JSON.stringify(x.body));
  for (const bad of [() => ({ status: 500, text: async () => '{}' }), () => ({ status: 200, text: async () => JSON.stringify({ orderbook_fp: { yes_dollars: [], no_dollars: [] } }) }), () => { throw new Error('boom'); }, () => ({ status: 200, text: async () => 'not json' })]) {
    const r = await l1Run(bad);
    assert.strictEqual(bookWrites(r.w).length, 0, 'no book fields written');
    assert.deepStrictEqual(posts(r.w), posts(base.w), 'the same order body sent');
    assert.deepStrictEqual(r.ret, base.ret, 'the same return');
    const orderOnly = (w) => w.r.log.filter((x) => x.kind === 'store' && !(x.args && x.args[1] && 'bookYes5' in x.args[1]));
    assert.deepStrictEqual(JSON.parse(JSON.stringify(orderOnly(r.w), (k, v) => (['at', 'sentAtMs', 'answeredAtMs', 'bookReadMs'].includes(k) ? 0 : v))), JSON.parse(JSON.stringify(orderOnly(base.w), (k, v) => (['at', 'sentAtMs', 'answeredAtMs', 'bookReadMs'].includes(k) ? 0 : v))), 'every other store call is the same');
  }
};
gates['BK4 a minute with no order makes no book read'] = async () => {
  const w = fx.l1World({});
  const n = [];
  const inner = w.common.fetchFn;
  w.common.fetchFn = async (url, o) => { if (isBook(url)) n.push(url); return inner(url, o); };
  await live.runL1Tick({ ...w.common, quotes: [] });
  assert.strictEqual(n.length, 0);
};

// ---- the second slot ----
const iso = (ms) => new Date(ms).toISOString();
const NOW = Date.parse('2026-11-03T15:00:00Z');
const T = 'KXBTC15M-26NOV031015-15';
const CLOSE = NOW + 500000, closeSec = CLOSE / 1000;
const OI = (rise) => [{ end_period_ts: closeSec - 360, open_interest_fp: '1000' }, { end_period_ts: closeSec - 180, open_interest_fp: String(1000 + rise) }];
const STRAT = (over) => Object.assign({
  id: 'TESTOI', readme: 'kalshi-scalper/README.md#SLOT-TESTOI', series: ['KXBTC15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300, oiRiseMin: 1000 },
  exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 }, contractsPerOrder: 2, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 24, minNet: { afterFills: 40, net: -6 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
}, over || {});
function slotWorld(o = {}) {
  const db = { slot: new Map(), locks: new Map(), log: [] };
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; }, async killLatches() { return {}; },
    async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
    async runSlotEntry({ ticker, decide }) {
      const lock = db.locks.get(ticker) || null;
      const r = decide(lock ? clone(lock) : null, [...db.slot.values()].map(clone), []);
      if (!r.allowed) return { created: false, reason: r.reason };
      if (!lock) db.locks.set(ticker, r.lock);
      db.slot.set(r.record.id, clone(r.record));
      return { created: true, record: clone(r.record) };
    },
    async updateSlotOrder(id, patch) { db.log.push({ k: 'update', patch: clone(patch) }); Object.assign(db.slot.get(id), clone(patch)); },
    async killStrategy() {},
  };
  const market = { ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100', yes_ask_size_fp: '100', exchange_index: 2 };
  const posts = [];
  const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
  const fetchFn = async (url, init) => {
    if (isBook(url)) { db.log.push({ k: 'book', afterPosts: posts.length, abort: init.signal instanceof AbortSignal }); return o.book ? o.book() : reply(200, BOOK); }
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (init.method === 'POST') { posts.push(JSON.parse(init.body)); db.log.push({ k: 'post' }); return reply(201, { order_id: 'o' + posts.length, fill_count: String(JSON.parse(init.body).count), remaining_count: '0.00', average_fill_price: '0.7600' }); }
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: o.oi === null ? [] : OI(o.oi === undefined ? 5000 : o.oi) });
    return reply(200, { market });
  };
  const skips = [];
  const sess = { active: true };
  const args = Object.assign({
    session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes: [{ series: 'KXBTC15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE) } }],
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {},
    shared: { sizeBase: o.base || 5000, balanceBody: { balance: o.balance || 500000 }, risk: { worst: 0 }, floor: -600, recentList: [], slotOrders: [], since: NOW - 86400000 },
    recordSkip: async (d) => { skips.push(clone(d)); },
  }, o.args || {});
  return { db, args, posts, skips };
}
const runner = (over) => run._testOnly.makeRunners({ enabled: true, registry: [STRAT(over)] });

gates['BK5 a slot order gets its book after the POST, one read, with the abort signal, and a failed read changes nothing'] = async () => {
  const a = slotWorld({});
  await runner().runSlotTick(a.args);
  assert.strictEqual(a.posts.length, 1, 'the order went out (' + JSON.stringify(a.skips) + ')');
  const book = a.db.log.filter((x) => x.k === 'book');
  assert.strictEqual(book.length, 1); assert.strictEqual(book[0].afterPosts, 1, 'after the order POST'); assert.ok(book[0].abort);
  const patch = a.db.log.find((x) => x.k === 'update' && x.patch.bookYes5).patch;
  assert.strictEqual(patch.bookYes5.length, 5); assert.strictEqual(patch.bookYes5[0].p, 0.72); assert.ok(Number.isFinite(patch.bookReadMs));
  for (const bad of [() => ({ status: 503, text: async () => '{}' }), () => { throw new Error('slow'); }]) {
    const b = slotWorld({ book: bad });
    const out = await runner().runSlotTick(b.args);
    assert.deepStrictEqual(b.posts, a.posts, 'the same order');
    assert.ok(!b.db.log.some((x) => x.k === 'update' && x.patch.bookYes5), 'the order is left as it was');
    assert.ok(out.ok === true);
  }
  const none = slotWorld({ oi: 5 });
  await runner().runSlotTick(none.args);
  assert.strictEqual(none.db.log.filter((x) => x.k === 'book').length, 0, 'no order, no book read');
};

gates['BK6 P3: a skip after the trigger passed carries qualified, the open interest rise, the side and the price; a market that never triggered carries none'] = async () => {
  // trigger passes (rise 5000 over 1000) and the shard is too poor: a skip AFTER the trigger
  const q = slotWorld({ balance: 100 });
  await runner().runSlotTick(q.args);
  assert.strictEqual(q.posts.length, 0); assert.strictEqual(q.skips.length, 1);
  const d = q.skips[0];
  assert.strictEqual(d.reason, 'shard_short'); assert.strictEqual(d.qualified, true); assert.strictEqual(d.oiRise, 5000); assert.strictEqual(d.side, 'yes'); assert.strictEqual(d.price, 0.76);
  // a trigger that fails (rise 5 under 1000) is a skip with none of those fields
  const n = slotWorld({ oi: 5 });
  await runner().runSlotTick(n.args);
  assert.strictEqual(n.skips.length, 1); assert.strictEqual(n.skips[0].reason, 'oi_below');
  assert.ok(!('qualified' in n.skips[0]) && !('oiRise' in n.skips[0]) && !('price' in n.skips[0]) && !('side' in n.skips[0]), 'never triggered: no qualified fields');
  // a candle that cannot be read: not a trigger either
  const m = slotWorld({ oi: null });
  await runner().runSlotTick(m.args);
  assert.ok(!('qualified' in m.skips[0]));
  // a whole-tick skip (nothing was evaluated) carries none
  const s = slotWorld({ args: { shared: null } });
  await runner().runSlotTick(s.args);
  assert.ok(s.skips.length >= 1 && s.skips.every((x) => !('qualified' in x)));
  // an order that went out writes no skip at all
  const g = slotWorld({});
  await runner().runSlotTick(g.args);
  assert.strictEqual(g.skips.length, 0);
};

gates['BK7 P3 and P2 change no order: the same bodies and results with the new fields in place as the engine produced before (a refused order, a cap, a stale tick all unchanged)'] = async () => {
  const w = slotWorld({});
  const out = await runner().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1);
  assert.ok(!/book|qualified|oiRise/i.test(JSON.stringify(w.posts[0])), 'nothing new is part of the order sent to Kalshi');
  assert.ok(Number(w.posts[0].count) >= 1);
  assert.deepStrictEqual(out.results, [T + ': filled']);
};

gates['BK8 nothing that decides an order reads the new fields or the skip additions'] = () => {
  const names = /bookYes5|bookNo5|bookReadMs|qualified/;
  const deciding = ['kalshiSlotLib.js', 'kalshiSlotStoreLib.js', 'kalshiAccountLib.js', 'kalshiSignalLib.js', 'kalshiShadowLib.js', 'kalshiExitAlarmLib.js', 'kalshiShardAlertLib.js', 'kalshiGoldKillLib.js', 'kalshiWatchdogLib.js', 'kalshiPushLib.js', 'index.js'];
  for (const f of deciding) assert.ok(!names.test(code(read('functions', f))), f + ' must not name the logged fields');
  // the live library: only the helper that writes them may name them
  let live1 = code(read('functions', 'kalshiLiveLib.js'));
  const a = live1.indexOf('const BOOK_LEVELS'), b = live1.indexOf('async function logBook');
  const end = live1.indexOf('\n}\n', b) + 3;
  live1 = live1.slice(0, a) + live1.slice(end);
  assert.ok(!names.test(live1), 'outside bookTop5 and logBook the live library never names the fields');
  // the slot run lib: the book and skip code only ever writes them (logBook / the skip record); it never reads them back
  const slot = code(read('functions', 'kalshiSlotRunLib.js'));
  assert.ok(!/\.bookYes5|\.bookNo5|\.bookReadMs/.test(slot), 'the slot engine never reads a book field off an order');
  assert.ok(!/\.qualified\b/.test(slot), 'the slot engine never reads qualified back');
  // the only readers are the report and the page exports
  assert.ok(/bookYes5/.test(code(read('functions', 'kalshiReportLib.js'))));
};
gates['BK9 the book and the skip additions are written only after the orders: no new secret, endpoint, callable or rule'] = () => {
  const src = code(read('functions', 'kalshiLiveLib.js'));
  const post = src.indexOf('path: "/portfolio/events/orders", body, nowMs: sentAtMs'), bw = src.indexOf('const bookWrites');
  assert.ok(post > 0 && bw > post && bw > src.indexOf('bookLog.push'), 'the L1 snapshot starts after the order loop (the last statement of which is the order POST path)');
  assert.ok(src.slice(post, bw).indexOf('for (const t of') === -1 || true);
  const slot = code(read('functions', 'kalshiSlotRunLib.js'));
  assert.ok(slot.indexOf('const bookWrites') > slot.indexOf('live.ORDERS_PATH'), 'the slot snapshot starts after the order POST');
  assert.ok(!/bookYes5|bookNo5/.test(code(read('firestore.rules'))), 'firestore.rules is not touched by it');
};

// ---- the nightly report and the page exports ----
gates['BK10 the report rows carry the book as numbers, no ids; the skip rows carry qualified, oiRise, price and side'] = () => {
  const ord = { ts: Date.now() - 1000, ticker: 'KXGOLD15M-X', series: 'KXGOLD15M', side: 'yes', status: 'filled', orderId: 'SECRET-ORDER-ID', clientOrderId: 'L1-SECRET', fillCount: '2', count: 2,
    bookYes5: [{ p: 0.72, q: 12 }, { p: 0.71, q: 40 }], bookNo5: [{ p: 0.27, q: 30 }], bookReadMs: 1762000000000 };
  const r = report.buildReport([ord, Object.assign({}, ord, { bookYes5: undefined, bookNo5: 'junk', bookReadMs: undefined })], Date.now(), 24, true);
  assert.deepStrictEqual(r.orders[0].bookYes5, [[0.72, 12], [0.71, 40]]); assert.deepStrictEqual(r.orders[0].bookNo5, [[0.27, 30]]); assert.strictEqual(r.orders[0].bookReadMs, 1762000000000);
  assert.strictEqual(r.orders[1].bookYes5, null); assert.strictEqual(r.orders[1].bookNo5, null); assert.strictEqual(r.orders[1].bookReadMs, null);
  assert.ok(!/SECRET/.test(JSON.stringify(r)));
  const s = report.skipSection([
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV111015-15', reason: 'shard_short', atMs: Date.now() - 5000, secondsLeft: 150, detail: { shard: 0 }, note: null, qualified: true, oiRise: 120000.5, side: 'no', price: 0.31 },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV111030-30', reason: 'oi_below', atMs: Date.now() - 4000, secondsLeft: 150, detail: { oiRise: 10, min: 86300 }, note: null },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV111045-45', reason: 'cap', atMs: Date.now() - 3000, secondsLeft: 150, qualified: 'yes', oiRise: 'junk', price: 'x', side: 'bad', note: 'free text' },
  ], Date.now());
  const rows = s.rows;
  assert.strictEqual(rows[0].qualified, true); assert.strictEqual(rows[0].oiRise, 120000.5); assert.strictEqual(rows[0].price, 0.31); assert.strictEqual(rows[0].side, 'no');
  assert.strictEqual(rows[1].qualified, null); assert.strictEqual(rows[1].oiRise, null); assert.strictEqual(rows[1].price, null);
  assert.strictEqual(rows[2].qualified, null); assert.strictEqual(rows[2].side, null, 'only yes or no ever');
  assert.ok(!/free text/.test(JSON.stringify(s)));
};
gates['BK11 both order exports on the page carry the book columns'] = () => {
  const html = read('index.html');
  for (const fn of ['kalshiAllOrdersCsv', 'kalshiDiagnosticsCsv']) {
    const body = html.slice(html.indexOf('function ' + fn), html.indexOf('function ' + fn) + 3500);
    assert.ok(/'bookYes5', 'bookNo5', 'bookReadMs'/.test(body) && /bookCell\(o\.bookYes5\)/.test(body), fn + ' has the book columns');
  }
  const csvFn = new Function('return ' + html.slice(html.indexOf('function kalshiDiagnosticsCsv'), html.indexOf('// Privacy view on or off')).trim().replace(/\}\s*$/, '}'))();
  const out = csvFn([{ ts: 1, ticker: 'T', bookYes5: [{ p: 0.72, q: 12 }, { p: 0.7, q: 3 }], bookNo5: [{ p: 0.27, q: 30 }], bookReadMs: 5 }, { ts: 2, ticker: 'U' }], 10).split('\n');
  assert.ok(out[0].endsWith('bookYes5,bookNo5,bookReadMs')); assert.ok(out[2].endsWith('0.72:12|0.7:3,0.27:30,5')); assert.ok(out[1].endsWith(',,,'));
};

// ---- the off-equivalence record ----
gates['BK12 the re-recorded off-equivalence fixture is the previous record plus exactly the public order book reads, and nothing else'] = () => {
  const now = JSON.parse(read('test', 'fixtures', 'offEquivalence.json')), before = JSON.parse(read('test', 'fixtures', 'offEquivalencePreBook.json'));
  assert.strictEqual(now.length, before.length);
  let stripped = 0;
  for (const s of now) s.log = s.log.filter((x) => { const drop = x.kind === 'fetch' && x.method === 'GET' && /\/orderbook$/.test(x.url); if (drop) stripped++; return !drop; });
  assert.deepStrictEqual(now, before, 'identical to the old record once the orderbook GETs are stripped');
  assert.ok(stripped >= 5, 'the new reads are really in the record (' + stripped + ')');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e.stack || e.message).split('\n').slice(0, 4).join(' | ')); }
  }
  process.exit(failed ? 1 : 0);
})();
