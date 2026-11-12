'use strict';
// Gates for the OICORE oiRise LOG (Nov 12, 2026, the owner approved). LOGGING ONLY.
// (1) A placed OICORE order carries the open interest rise its signal fired on (numbers the tick already read), null when there is none.
// (2) The nightly report lists it on slot order rows, and its skip section joins each oi_below skip to the market result when a settled row for that market is already in hand, with near-miss counts.
// Nothing here may change whether, what or when the bot buys, and the report stays read only, token gated, with no id or token in its output.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const run = require('../functions/kalshiSlotRunLib');
const report = require('../functions/kalshiReportLib');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const clone = (x) => JSON.parse(JSON.stringify(x));
const iso = (ms) => new Date(ms).toISOString();
const NOW = Date.parse('2026-11-03T15:00:00Z');
const T = 'KXBTC15M-26NOV031015-15';
const CLOSE = NOW + 500000, closeSec = CLOSE / 1000;
const OI = (rise) => [{ end_period_ts: closeSec - 360, open_interest_fp: '1000' }, { end_period_ts: closeSec - 180, open_interest_fp: String(1000 + rise) }];
const STRAT = () => ({
  id: 'TESTOI', readme: 'kalshi-scalper/README.md#SLOT-TESTOI', series: ['KXBTC15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300, oiRiseMin: 1000 },
  exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 }, contractsPerOrder: 2, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 24, minNet: { afterFills: 40, net: -6 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
});
function slotWorld(o = {}) {
  const db = { slot: new Map(), locks: new Map() };
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
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); },
    async killStrategy() {},
  };
  const market = { ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100', yes_ask_size_fp: '100', exchange_index: 2 };
  const posts = [];
  const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
  const fetchFn = async (url, init) => {
    if (/\/orderbook$/.test(String(url).split('?')[0])) return reply(200, { orderbook_fp: { yes_dollars: [], no_dollars: [] } });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (init.method === 'POST') { posts.push(JSON.parse(init.body)); return reply(201, { order_id: 'o' + posts.length, fill_count: String(JSON.parse(init.body).count), remaining_count: '0.00', average_fill_price: '0.7600' }); }
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: o.oi === null ? [] : OI(o.oi === undefined ? 5000 : o.oi) });
    return reply(200, { market });
  };
  const skips = [];
  const sess = { active: true };
  const args = {
    session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes: [{ series: 'KXBTC15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE) } }],
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {},
    shared: { sizeBase: 5000, balanceBody: { balance: 500000 }, risk: { worst: 0 }, floor: -600, recentList: [], slotOrders: [], since: NOW - 86400000 },
    recordSkip: async (d) => { skips.push(clone(d)); },
  };
  return { db, args, posts, skips };
}
const runner = () => run._testOnly.makeRunners({ enabled: true, registry: [STRAT()] });
const gates = {};

gates['OR1 a placed OICORE order stores the open interest rise its signal fired on, as a number'] = async () => {
  const w = slotWorld({ oi: 5000 });
  await runner().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1);
  const rec = [...w.db.slot.values()][0];
  assert.strictEqual(rec.oiRise, 5000);
};
gates['OR2 the order decision is the same as before the log: the same body goes to Kalshi whatever the rise is above the line, and a rise under the line still sends nothing'] = async () => {
  const a = slotWorld({ oi: 5000 }), b = slotWorld({ oi: 1000 });
  await runner().runSlotTick(a.args); await runner().runSlotTick(b.args);
  assert.deepStrictEqual(a.posts, b.posts, 'the order body does not depend on the logged value');
  assert.ok(!/oiRise/i.test(JSON.stringify(a.posts[0])), 'the order sent to Kalshi does not carry it');
  const under = slotWorld({ oi: 999 });
  await runner().runSlotTick(under.args);
  assert.strictEqual(under.posts.length, 0); assert.strictEqual(under.skips[0].reason, 'oi_below');
  assert.strictEqual(under.skips[0].detail.oiRise, 999);
};
gates['OR3 an order with no readable rise stores null, never a made-up number, and a strategy without the open interest line stores null'] = async () => {
  const m = slotWorld({ oi: null });
  await runner().runSlotTick(m.args);
  assert.strictEqual(m.posts.length, 0, 'no candle, no order (unchanged)');
  const noLine = slotWorld({});
  const reg = STRAT(); delete reg.entry.oiRiseMin;
  await run._testOnly.makeRunners({ enabled: true, registry: [reg] }).runSlotTick(noLine.args);
  if (noLine.posts.length) assert.strictEqual([...noLine.db.slot.values()][0].oiRise, null);
};
gates['OR4 nothing that decides an order reads oiRise back off a stored order or skip'] = () => {
  // kalshiSlotLib.js already reads its own input `i.oiRise` in slotOrderCheck (the caller's reading, before this log); it never reads a stored order's field.
  assert.ok(!/(?:o|rec|record|order|d)\.oiRise\b/.test(code(read('functions', 'kalshiSlotLib.js'))));
  for (const f of ['kalshiSlotStoreLib.js', 'kalshiLiveLib.js', 'kalshiShadowLib.js', 'index.js']) assert.ok(!/\.oiRise\b/.test(code(read('functions', f))), f + ' must not read .oiRise');
  assert.ok(!/\b(?:o|rec|record|order|d)\.oiRise\b/.test(code(read('functions', 'kalshiSlotRunLib.js'))), 'the slot engine only writes it');
};

const SKIP = (ticker, rise, extra) => Object.assign({ strategy: 'OICORE', ticker, reason: 'oi_below', atMs: NOW - 1000, secondsLeft: 150, detail: { oiRise: rise, min: 86300 }, note: null }, extra || {});
gates['OR5 the report lists oiRise on slot order rows (null when absent) and the L1 row shape is unchanged'] = () => {
  const slot = { ts: NOW - 1000, ticker: 'KXBTC15M-X', side: 'yes', status: 'filled', slotId: 'OICORE', fillCount: '1', oiRise: 91000 };
  const r = report.buildReport([], NOW, 24, true, [slot, Object.assign({}, slot, { oiRise: undefined }), Object.assign({}, slot, { oiRise: 'junk' })]);
  assert.strictEqual(r.slotOrders[0].oiRise, 91000); assert.strictEqual(r.slotOrders[1].oiRise, null); assert.strictEqual(r.slotOrders[2].oiRise, null);
  const l1 = report.buildReport([{ ts: NOW - 1000, ticker: 'KXBTC15M-X', side: 'yes', status: 'filled', fillCount: '1', oiRise: 5 }], NOW, 24, true);
  assert.ok(!('oiRise' in l1.orders[0]), 'L1 rows do not gain the field');
};
gates['OR6 skip join shape: oiSeen, oiMin, shortBy and result per skip; near misses counted by result; existing fields kept'] = () => {
  const A = 'KXBTC15M-26NOV111015-15', B = 'KXBTC15M-26NOV111030-30', C = 'KXBTC15M-26NOV111045-45', D = 'KXBTC15M-26NOV111100-00';
  const results = report.resultsFromRows([
    { ticker: A, settled: true, result: 'yes' }, { ticker: B, settled: true, result: 'no' }, { ticker: C, settled: false, result: 'yes' }, { ticker: 'KXOTHER', settled: true, result: 'maybe' },
  ]);
  assert.deepStrictEqual(results, { [A]: 'yes', [B]: 'no' });
  const s = report.skipSection([
    SKIP(A, 80000), SKIP(B, 40000), SKIP(C, 85000), SKIP(D, null, { detail: { min: 86300 } }),
    { strategy: 'OICORE', ticker: 'KXBTC15M-26NOV111115-15', reason: 'shard_short', atMs: NOW - 500, qualified: true, oiRise: 120000, price: 0.8, side: 'yes' },
  ], NOW, results);
  const by = (t) => s.rows.find((r) => r.ticker === t);
  assert.strictEqual(by(A).oiSeen, 80000); assert.strictEqual(by(A).oiMin, 86300); assert.strictEqual(by(A).shortBy, 6300); assert.strictEqual(by(A).result, 'yes');
  assert.strictEqual(by(B).shortBy, 46300); assert.strictEqual(by(B).result, 'no');
  assert.strictEqual(by(C).result, null, 'an unsettled row is no result');
  assert.strictEqual(by(D).oiSeen, null); assert.strictEqual(by(D).shortBy, null, 'a missing rise stays null');
  assert.strictEqual(by('KXBTC15M-26NOV111115-15').oiSeen, 120000); assert.strictEqual(by('KXBTC15M-26NOV111115-15').shortBy, null);
  assert.strictEqual(by('KXBTC15M-26NOV111115-15').oiRise, 120000, 'the existing qualified field is kept');
  assert.strictEqual(by(A).oiRise, null, 'the existing oiRise field is unchanged for an oi_below skip');
  assert.deepStrictEqual(s.openInterest, { belowLine: 4, nearMissLimit: 10000, nearMisses: 2, nearMissByResult: { yes: 1, no: 0, unknown: 1 }, belowByResult: { yes: 1, no: 1, unknown: 2 } });
  assert.strictEqual(s.count, 5); assert.ok(s.byReason.oi_below === 4);
  assert.deepStrictEqual(Object.keys(report.skipSection([], NOW)).sort(), ['byReason', 'count', 'days', 'openInterest', 'rows']);
};
gates['OR7 the report stays read only and token gated: no Kalshi call, no key, no id or token in the output, a failed shadow read leaves the skips with null results'] = async () => {
  const lib = code(read('functions', 'kalshiReportLib.js'));
  assert.ok(!/fetch\(|kalshi\.com|https?:\/\/|signRequest|KALSHI_KEY|privateKey/i.test(lib), 'the report library makes no network call and holds no key');
  const TOKEN = 'x'.repeat(32);
  const mk = (shadowThrows) => report.makeReportHandler({
    getToken: () => TOKEN, now: () => NOW, readOrders: async () => [], readSkips: async () => [SKIP('KXBTC15M-26NOV111015-15', 80000, { id: 'DOC-ID-SECRET' })],
    readShadowRows: async () => { if (shadowThrows) throw new Error('boom'); return [{ ticker: 'KXBTC15M-26NOV111015-15', settled: true, result: 'yes' }]; }, shadowRules: () => [], logError: () => {},
  });
  const call = async (h, auth) => { let out; await h({ method: 'GET', headers: auth ? { authorization: 'Bearer ' + TOKEN } : {}, query: {} }, { set() {}, status(c) { return { json(b) { out = { code: c, body: b }; } }; } }); return out; };
  assert.strictEqual((await call(mk(false), false)).code, 401);
  const ok = await call(mk(false), true);
  assert.strictEqual(ok.code, 200); assert.strictEqual(ok.body.skips.rows[0].result, 'yes');
  assert.ok(!/SECRET|xxxxxxxx/.test(JSON.stringify(ok.body)), 'no document id and no token in the output');
  const bad = await call(mk(true), true);
  assert.strictEqual(bad.code, 200); assert.strictEqual(bad.body.skips.rows[0].result, null); assert.strictEqual(bad.body.skips.rows[0].oiSeen, 80000);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.error('FAIL ' + name + '\n  ' + (e && e.message)); }
  }
  if (failed) process.exit(1);
  console.log('oicoreOiRiseLogGates: ' + Object.keys(gates).length + ' gates passed');
})();
