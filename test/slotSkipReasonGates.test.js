'use strict';
// Gates for the second slot's skip log (Nov 5, 2026, the owner: "Save skip reasons"). Each states the consequence, not the mechanism.
// Why: 8 of 44 OICORE triggers since Oct 30 and three EVENT830 markets on Nov 5 got no live order and left no record. The skip log keeps one small document per strategy and market window,
// and it is LOG ONLY: it may never change, delay or fail an order, and nothing that decides an order may read it.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const run = require('../functions/kalshiSlotRunLib');
const storeLib = require('../functions/kalshiSlotStoreLib');
const report = require('../functions/kalshiReportLib');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-11-03T15:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const T = 'KXBTC15M-26NOV031015-15', T2 = 'KXGOLD15M-26NOV031015-15';
const clone = (x) => JSON.parse(JSON.stringify(x));

// A test strategy (the same shape the engine gates use), entry span 300 to 700 s before the close.
const GOOD = (over) => Object.assign({
  id: 'TESTA', readme: 'kalshi-scalper/README.md#SLOT-TESTA', series: ['KXBTC15M', 'KXGOLD15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 },
  exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 },
  contractsPerOrder: 4, scaleIn: { maxSteps: 2, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -3 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
}, over || {});
const runner = (over) => run._testOnly.makeRunners({ enabled: true, registry: [GOOD(over)] });

function world(o = {}) {
  const db = { slot: new Map(), l1: new Map(), locks: new Map(), events: [], halted: false };
  for (const t of o.l1 || []) db.l1.set(t.id, t);
  const store = {
    async halted() { return db.halted; },
    async hasUnresolved() { return [...db.slot.values()].some((t) => ['sending', 'unknown'].includes(t.status)); },
    async l1HasUnresolved() { return [...db.l1.values()].some((t) => ['sending', 'unknown'].includes(t.status)); },
    async killLatches() { return {}; },
    async allSlotOrders() { return [...db.slot.values()].map(clone); },
    async l1Recent() { return [...db.l1.values()].map(clone); },
    async runSlotEntry({ ticker, decide }) {
      const lock = db.locks.get(ticker) || null;
      const r = decide(lock ? clone(lock) : null, [...db.slot.values()].map(clone), [...db.l1.values()].filter((t) => t.ticker === ticker).map(clone));
      if (!r.allowed) return { created: false, reason: r.reason };
      if (!lock) db.locks.set(ticker, r.lock);
      db.slot.set(r.record.id, clone(r.record));
      return { created: true, record: clone(r.record) };
    },
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); },
    async killStrategy() {},
  };
  const markets = Object.assign({
    [T]: { ticker: T, status: 'active', close_time: iso(NOW + 500000), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 2 },
    [T2]: { ticker: T2, status: 'active', close_time: iso(NOW + 500000), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 2 },
  }, o.markets || {});
  const posts = [];
  const fetchFn = async (url, init) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (init.method === 'POST') {
      posts.push(JSON.parse(init.body)); db.events.push('POST');
      return reply(201, { order_id: 'ord-' + posts.length, fill_count: String(JSON.parse(init.body).count), remaining_count: '0.00', average_fill_price: '0.7600' });
    }
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: [] });
    const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
    return markets[tk] ? reply(200, { market: markets[tk] }) : reply(404, {});
  };
  const skips = [];
  const sess = { active: true };
  const quotes = (o.tickers || [T]).map((tk) => ({ series: tk.split('-')[0], m: { ticker: tk, status: 'active', close_time: markets[tk].close_time } }));
  const args = Object.assign({
    session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes,
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {},
    shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 24 * 3600 * 1000 },
    recordSkip: async (d) => { db.events.push('skip'); skips.push(clone(d)); },
  }, o.args || {});
  return { db, store, args, posts, skips };
}
const strip = (r) => JSON.parse(JSON.stringify(r));
const gates = {};

gates['K1 a market inside the entry span that is skipped writes exactly one skip document, with the right reason, strategy, ticker and seconds left'] = async () => {
  const cases = [
    { name: 'price out of the band', o: { markets: { [T]: { ticker: T, status: 'active', close_time: iso(NOW + 500000), yes_bid_dollars: '0.9500', yes_ask_dollars: '0.9700', yes_bid_size_fp: '100', yes_ask_size_fp: '100', exchange_index: 2 } } }, reason: 'price_out_of_band' },
    { name: 'shard short', o: { args: { shared: { sizeBase: 500, balanceBody: { balance: 100 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 86400000 } } }, reason: 'shard_short', detail: { shard: 2, avail: 1 } },
    { name: 'stale tick', o: { args: { clock: () => NOW + 30000 } }, reason: 'stale_tick' },
    { name: 'market unreadable', o: { markets: { [T]: undefined }, tickers: [] }, reason: 'market_unreadable', custom: true },
    { name: 'unresolved earlier order', o: { l1: [{ id: 'L1-x', ticker: T2, side: 'yes', status: 'sending', ts: NOW - 1000 }] }, reason: 'unresolved_order' },
    { name: 'direction lock (an L1 order on the other side)', o: { l1: [{ id: 'L1-' + T, strategy: 'L1', ticker: T, side: 'no', count: 1, fillCount: '1', maxCost: 0.3, status: 'filled', settled: false, ts: NOW - 60000 }] }, reason: 'direction_lock' },
  ];
  for (const c of cases) {
    let w;
    if (c.custom) {
      // the quote says the market is in the span, the fresh read of it fails
      w = world({});
      w.args.fetchFn = async (url) => ({ status: url.includes('/markets/') ? 503 : 200, text: async () => '{}' });
    } else w = world(c.o);
    const out = await runner().runSlotTick(w.args);
    assert.strictEqual(w.posts.length, 0, c.name + ': no order');
    assert.strictEqual(w.skips.length, 1, c.name + ': exactly one skip document (' + JSON.stringify(out).slice(0, 160) + ')');
    const d = w.skips[0];
    assert.strictEqual(d.reason, c.reason, c.name + ': reason ' + d.reason + ' (' + d.note + ')');
    assert.strictEqual(d.strategy, 'TESTA'); assert.strictEqual(d.ticker, T);
    assert.ok(Number.isFinite(d.atMs) && Number.isFinite(d.secondsLeft) && d.secondsLeft > 0 && d.secondsLeft <= 500, c.name + ': time and seconds left');
    for (const [k, v] of Object.entries(c.detail || {})) assert.strictEqual(d.detail[k], v, c.name + ': detail ' + k);
  }
  // the reason code table: the gate's sentences map to fixed codes, never free text in `reason`
  const rc = run._testOnly.checkReasonCode;
  assert.strictEqual(rc('killed: 3 losses in a row'), 'killed');
  assert.strictEqual(rc("the slot's own daily loss cap is reached"), 'cap');
  assert.strictEqual(rc('no whole contract fits the caps (per order, per market)'), 'cap');
  assert.strictEqual(rc('the account holds YES here, so a NO buy would hedge it'), 'direction_lock');
  assert.strictEqual(rc('the open interest rise is missing or below 86300 contracts'), 'oi_below');
};

gates['K1b the open interest and band reasons OICORE needs: a missing candle is no_oi_candle, and a skip a later minute repeats overwrites the same document key'] = async () => {
  const w = world({});
  const r = run._testOnly.makeRunners({ enabled: true, registry: [GOOD({ entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300, oiRiseMin: 86300 } })] });
  await r.runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 0);
  assert.strictEqual(w.skips.length, 1); assert.strictEqual(w.skips[0].reason, 'no_oi_candle');
  // the Firestore writer keys by strategy and ticker (one document per window) and overwrites (no merge), so the latest reason is the one kept, never a mix of two minutes' fields
  const sets = [];
  const fakeDb = { collection: (c) => ({ doc: (id) => ({ set: async (...a) => { sets.push({ c, id, a }); } }) }) };
  await storeLib.slotSkipWriter(fakeDb)(w.skips[0]);
  assert.strictEqual(sets.length, 1);
  assert.strictEqual(sets[0].c, 'kalshiSlotSkips'); assert.strictEqual(sets[0].id, 'TESTA_' + T);
  assert.strictEqual(sets[0].a.length, 1, 'a plain set: the latest reason replaces the document');
};

gates['K2 outside the entry span nothing is written, and a market that gets its order writes nothing'] = async () => {
  for (const left of [1000000, 100000, -5000]) {
    const w = world({ markets: { [T]: { ticker: T, status: 'active', close_time: iso(NOW + left), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100', yes_ask_size_fp: '100', exchange_index: 2 } } });
    await runner().runSlotTick(w.args);
    assert.strictEqual(w.skips.length, 0, 'no skip document ' + left / 1000 + ' s before the close');
  }
  // switched off or no session: returns before the span check, nothing written
  for (const over of [{ enabled: false }, { active: false }, { session: { active: false } }]) {
    const w = world({ args: over });
    await runner().runSlotTick(w.args);
    assert.strictEqual(w.skips.length, 0, 'nothing written: ' + JSON.stringify(over));
  }
  const w = world({});
  const out = await runner().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1, 'the order went out'); assert.deepStrictEqual(out.results, [T + ': filled']);
  assert.strictEqual(w.skips.length, 0, 'an order is not a skip');
};

gates['K3 a throwing, rejecting or missing skip writer changes nothing about the tick: same result, same orders, and the skip is handed over only after the minute\'s orders are sent'] = async () => {
  // two markets: the first is skipped (out of the band), the second is ordered
  const mk = () => world({ tickers: [T, T2], markets: { [T]: { ticker: T, status: 'active', close_time: iso(NOW + 500000), yes_bid_dollars: '0.9500', yes_ask_dollars: '0.9700', yes_bid_size_fp: '100', yes_ask_size_fp: '100', exchange_index: 2 } } });
  const base = mk(); delete base.args.recordSkip;
  const want = strip(await runner().runSlotTick(base.args));
  assert.strictEqual(base.posts.length, 1);
  const writers = [() => { throw new Error('sync boom'); }, async () => { throw new Error('async boom'); }, () => Promise.reject(new Error('rejected')), 'not a function'];
  for (const wr of writers) {
    const w = mk(); w.args.recordSkip = wr;
    const got = strip(await runner().runSlotTick(w.args));
    assert.deepStrictEqual(got, want, 'the same result');
    assert.deepStrictEqual(w.posts, base.posts, 'the same order');
  }
  const w = mk();
  await runner().runSlotTick(w.args);
  assert.deepStrictEqual(w.db.events, ['POST', 'skip'], 'the skip write comes after the order was sent');
  // the preconditions path also still returns its own skip result when the writer throws
  const u = world({ l1: [{ id: 'L1-x', ticker: T2, side: 'yes', status: 'sending', ts: NOW - 1000 }] });
  u.args.recordSkip = () => { throw new Error('boom'); };
  assert.deepStrictEqual(await runner().runSlotTick(u.args), { skipped: 'an L1 order is unresolved' });
};

gates['K4 nothing that decides an order reads the skip collection: the engine never names it, the store only writes it, and only the report reads it'] = () => {
  const runCode = code(read('functions', 'kalshiSlotRunLib.js'));
  assert.ok(!/kalshiSlotSkips|SKIPS/.test(runCode), 'the engine does not know the collection');
  assert.strictEqual((runCode.match(/recordSkip/g) || []).length, 2, 'the engine only calls the hook (one type check, one call), in the flush');
  const flushAt = runCode.indexOf('const flushSkips'), loopAt = runCode.indexOf('for (const job of jobs)');
  assert.ok(flushAt > 0 && flushAt < loopAt, 'the flush is defined before the order loop and only called at the returns');
  const storeCode = code(read('functions', 'kalshiSlotStoreLib.js'));
  const uses = storeCode.split('SKIPS').length - 1;
  assert.strictEqual(uses, 3, 'SKIPS: the name, the writer, the exported name');
  const writer = storeCode.slice(storeCode.indexOf('function slotSkipWriter'), storeCode.indexOf('module.exports'));
  assert.ok(/\.set\(d\)/.test(writer) && !/\.get\(|runTransaction|where\(/.test(writer), 'the writer only writes');
  const idx = code(read('functions', 'index.js'));
  assert.ok(!/kalshiSlotSkips/.test(idx), 'index.js names the collection only through the store library');
  const skipUses = [...idx.matchAll(/COLLECTIONS\.SKIPS|slotSkipWriter/g)].map((m) => m.index);
  assert.strictEqual(skipUses.length, 2, 'one writer (the minute function) and one read (the nightly report)');
  assert.ok(idx.indexOf('exports.kalshiNightlyReport') < skipUses.find((i) => /COLLECTIONS\.SKIPS/.test(idx.slice(i, i + 20))), 'the only read is in the report');
  for (const f of ['kalshiLiveLib.js', 'kalshiSlotLib.js', 'kalshiSignalLib.js', 'kalshiPushLib.js']) assert.ok(!/kalshiSlotSkips/.test(read('functions', f)), f + ' never reads it');
};

gates['K5 the rules give the admin read and no client write, and the page does not read it'] = () => {
  const rules = read('firestore.rules');
  const m = rules.match(/match \/kalshiSlotSkips\/\{id\} \{([\s\S]*?)\}/);
  assert.ok(m, 'a rule exists');
  assert.ok(/allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]) && (m[1].match(/allow/g) || []).length === 2, 'admin read, no write');
  assert.ok(!/kalshiSlotSkips/.test(read('index.html')), 'the page does not read the skip log');
};

gates['K6 the nightly report carries the last 7 days of skips as counts per reason and rows, never a document id, and a failed read leaves the report intact'] = async () => {
  const day = 86400000, NOWR = NOW;
  const docs = [
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV010845-45', reason: 'stale_tick', detail: { lateSec: 23 }, note: 'x', atMs: NOWR - day, secondsLeft: 150, id: 'should-not-pass' },
    { strategy: 'EVENT830', ticker: 'KXEURUSD15M-26NOV050830-30', reason: 'shard_short', detail: { shard: 0, avail: 0.12, need: 1, evil: 'str' }, atMs: NOWR - 2 * day, secondsLeft: 170 },
    { strategy: 'EVENT830', ticker: 'KXGBPUSD15M-26NOV050830-30', reason: 'shard_short', detail: { shard: 0, avail: 0.12, need: 1 }, atMs: NOWR - 2 * day, secondsLeft: 170 },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26OCT200845-45', reason: 'oi_below', atMs: NOWR - 9 * day, secondsLeft: 150 },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV020845-45', reason: '<b>x</b>', atMs: NOWR - day, secondsLeft: 150 },
  ];
  const s = report.skipSection(docs, NOWR);
  assert.strictEqual(s.days, 7); assert.strictEqual(s.count, 4, 'older than 7 days is left out');
  assert.deepStrictEqual(s.byReason, { shard_short: 2, stale_tick: 1, unknown: 1 });
  assert.ok(!JSON.stringify(s).includes('should-not-pass') && !JSON.stringify(s).includes('<b>'), 'no id, no odd text');
  assert.deepStrictEqual(s.rows.find((r) => r.ticker.startsWith('KXEURUSD')).detail, { shard: 0, avail: 0.12, need: 1 }, 'numbers only');
  assert.deepStrictEqual(Object.keys(s.rows[0]).sort(), ['at', 'atMs', 'detail', 'reason', 'secondsLeft', 'side', 'strategy', 'ticker']);
  const token = 'x'.repeat(32);
  const call = async (deps) => {
    const res = { code: 0, body: null, set() {}, status(c) { this.code = c; return this; }, json(b) { this.body = b; } };
    await report.makeReportHandler(Object.assign({ getToken: () => token, now: () => NOWR, readOrders: async () => [] }, deps))({ method: 'GET', headers: { authorization: 'Bearer ' + token }, query: {} }, res);
    return res;
  };
  const ok = await call({ readSkips: async () => docs });
  assert.strictEqual(ok.code, 200); assert.strictEqual(ok.body.skips.count, 4);
  const bad = await call({ readSkips: async () => { throw new Error('down'); } });
  assert.strictEqual(bad.code, 200); assert.ok(!('skips' in bad.body) && bad.body.total, 'the report stands without the section');
  const none = await call({});
  assert.ok(!('skips' in none.body), 'no reader, no section');
};

gates['K7 deploy-latest offers the minute function for this change and says how the rules are deployed'] = () => {
  const sh = read('functions', 'deploy-latest.sh');
  assert.ok(/kalshiS\[l\]ot\[A-Za-z\]\*Lib/.test(sh), 'a slot library change selects deploy-sizing.sh');
  assert.ok(/\^firestore\\\.rules\$/.test(sh) && /firestore:rules/.test(sh), 'a rules change is named with its deploy command');
};

// A price skip says which side it would have bought (Nov 8, 2026, the refinement chat's S-OICHEAPSKIP1 read). Consequence: the report row carries side "yes" or "no" and the price, so a skipped signal can be scored without guessing the side; anything else in the note is dropped.
gates['K8 the report row of a price skip carries the side (yes or no only) and its price'] = () => {
  const NOWR = NOW;
  const ok = report.skipSection([
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV081000-00', reason: 'cheap_skipped', atMs: NOWR - 1000, secondsLeft: 150, detail: { price: 0.06, min: 0.08 }, note: 'no' },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV081015-15', reason: 'cheap_skipped', atMs: NOWR - 900, secondsLeft: 150, detail: { price: 0.05, min: 0.08 }, note: 'a free text note with a secret' },
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV081030-30', reason: 'oi_below', atMs: NOWR - 800, secondsLeft: 150, detail: null, note: 'yes' }], NOWR);
  assert.strictEqual(ok.rows[0].side, 'no'); assert.deepStrictEqual(ok.rows[0].detail, { price: 0.06, min: 0.08 });
  assert.strictEqual(ok.rows[1].side, null, 'free text is dropped, never echoed');
  assert.strictEqual(ok.rows[2].side, 'yes');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 6).join(' | ') : e)); }
  }
  process.exit(failed ? 1 : 0);
})();
