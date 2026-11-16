'use strict';
// LS1 to LS8: OIREL1 and XRPFAV10, the two live TRIAL seats of the second slot (Nov 15, 2026; the owner's answer "Live now, trial size", relayed by the EA). Each gate states the consequence.
// Both are below the research bar and hold to settlement; each is 3 contracts, at most $3 an order, $9 lost a day, net kill -$18 after 5 fills, 30 losses in a row.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const live = require('../functions/kalshiLiveLib');
const root = path.join(__dirname, '..');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const REL = 0.26764675317954373;
const NOW = Date.parse('2026-11-16T16:57:30Z');          // 150 s before a 17:00Z close
const CLOSE = NOW + 150000, CLOSE_SEC = Math.round(CLOSE / 1000);
const TK = 'KXBTC15M-26NOV161200-00', XTK = 'KXXRP15M-26NOV161200-00';
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const gates = {};
const OIREL = slot.SLOT_STRATEGIES.find((s) => s.id === 'OIREL1'), XRPF = slot.SLOT_STRATEGIES.find((s) => s.id === 'XRPFAV10');

gates['LS1 both seats are registered exactly as the owner ordered: frozen, valid, 3 contracts, held to settlement, net kill -$18 after 5 fills, 30 losses in a row, $3 an order and $9 a day'] = () => {
  for (const s of [OIREL, XRPF]) {
    assert.ok(s && Object.isFrozen(s) && Object.isFrozen(s.entry) && Object.isFrozen(s.killRules), s && s.id);
    assert.deepStrictEqual(slot.validateSlotStrategy(s).errors, []);
    assert.deepStrictEqual([s.contractsPerOrder, s.exit, s.killRules.maxConsecutiveLosses, s.killRules.minNet, s.reviewedAt], [3, { holdToSettle: true }, 30, { afterFills: 5, net: -18 }, '2026-11-15']);
    assert.ok(slot.SLOT_HOLD_ALLOWED.includes(s.id));
    assert.deepStrictEqual(JSON.parse(JSON.stringify(slot.SLOT_SEAT_CAPS[s.id])), { perOrder: 3, daily: 9 });
    assert.ok(fs.existsSync(path.join(root, s.readme.split('#')[0])), 'its pre-registration is in the repo');
  }
  assert.deepStrictEqual([OIREL.series, OIREL.entry], [['KXBTC15M'], { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRelMin: REL }]);
  assert.deepStrictEqual([XRPF.series, XRPF.entry], [['KXXRP15M'], { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.92, leftMaxSec: 640, leftMinSec: 570 }]);
};

gates['LS2 XRP is a slot market for XRPFAV10 ONLY; gold\'s own rule (L1) still may not trade XRP, and no other seat may list it'] = () => {
  assert.deepStrictEqual(slot.SLOT_STRATEGIES.filter((s) => s.series.includes('KXXRP15M')).map((s) => s.id), ['XRPFAV10']);
  assert.ok(live.PAUSED_SERIES.includes('KXXRP15M'), 'XRP stays paused for L1 in code');
  assert.strictEqual(live.maxContractsAt ? live.maxContractsAt('KXXRP15M', NOW) : live.maxContractsFor('KXXRP15M'), live.maxContractsFor('KXXRP15M'));
  const other = Object.assign(JSON.parse(JSON.stringify(OIREL)), { id: 'OICORE', series: ['KXXRP15M'] });
  assert.strictEqual(slot.validateSlotStrategy(Object.assign(other, { entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: 86300 } })).ok, true, '(the validator allows the series; the engine registry is what decides who trades it, and it lists XRPFAV10 alone)');
};

const input = (id, o) => Object.assign({ strategyId: id, ticker: id === 'XRPFAV10' ? XTK : TK, side: 'yes', limit: id === 'XRPFAV10' ? 0.9 : 0.3, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true, lockTxn: true, lock: null,
  position: 0, sizingBase: 800, windowCapFraction: 0.055, secondsLeft: id === 'XRPFAV10' ? 600 : 150, now: NOW, oiRel: REL + 0.01 }, o || {});
const chk = (id, o) => slot._testOnly.slotOrderCheckWith({ enabled: true, registry: [slot.SLOT_STRATEGIES.find((s) => s.id === id)], everUsed: true }, input(id, o));

gates['LS3 OIREL1 gate: the relative rise must be STRICTLY above the registered line; missing, equal or under sends nothing; 3 contracts and at most $3'] = () => {
  const ok = chk('OIREL1');
  assert.strictEqual(ok.allowed, true, JSON.stringify(ok.reasons)); assert.strictEqual(ok.count, 3);
  for (const oiRel of [REL, REL - 0.001, 0, undefined, null, NaN]) assert.strictEqual(chk('OIREL1', { oiRel }).allowed, false, 'refused with ' + oiRel);
  for (const limit of [0.51, 0.04]) assert.strictEqual(chk('OIREL1', { limit }).allowed, false, 'band ' + limit);
  for (const limit of [0.05, 0.5]) assert.strictEqual(chk('OIREL1', { limit }).allowed, true, 'edge ' + limit);
  for (const wanted of [1, 10, 30]) assert.ok(chk('OIREL1', { wanted }).count <= 3);
  assert.ok(chk('OIREL1', { limit: 0.5 }).cost <= 3);
  for (const secondsLeft of [181, 119]) assert.strictEqual(chk('OIREL1', { secondsLeft }).allowed, false, 'only 3 to 2 minutes before the close');
  assert.strictEqual(chk('OIREL1', { ticker: XTK }).allowed, false, 'Bitcoin only');
};

gates['LS4 XRPFAV10 gate: the favourite at 88c to 92c only, 570 to 640 s, 3 contracts, never more than $3 an order even at 92c'] = () => {
  const ok = chk('XRPFAV10');
  assert.strictEqual(ok.allowed, true, JSON.stringify(ok.reasons)); assert.strictEqual(ok.count, 3);
  assert.ok(chk('XRPFAV10', { limit: 0.92 }).allowed && chk('XRPFAV10', { limit: 0.92 }).cost <= 3, 'the dearest order is 3 contracts at 92c plus fee, under the $3 cap: ' + JSON.stringify(chk('XRPFAV10', { limit: 0.92 })));
  for (const limit of [0.87, 0.93, 0.97, 0.5]) assert.strictEqual(chk('XRPFAV10', { limit }).allowed, false, 'refused at ' + limit);
  for (const secondsLeft of [641, 569, 150]) assert.strictEqual(chk('XRPFAV10', { secondsLeft }).allowed, false, 'only about 10 minutes before the close: ' + secondsLeft);
  assert.strictEqual(chk('XRPFAV10', { ticker: TK }).allowed, false, 'XRP only');
  assert.strictEqual(chk('XRPFAV10', { sizingBase: 100000 }).count, 3, 'a huge base cannot lift the seat above its own caps');
};

gates['LS5 overlap with OICORE on one Bitcoin window: the slot\'s per market cap and the direction lock stop OIREL1 from stacking past the limit or hedging OICORE'] = () => {
  const held = (id, side, count) => ({ id: 'S-' + id + '-' + side, strategy: 'SLOT', slotId: id, ticker: TK, series: 'KXBTC15M', side, step: 1, count, fillCount: String(count), maxCost: count * 0.2, price: 0.2, status: 'filled', settled: false, ts: NOW - 20000, accountId: live.DEFAULT_ACCOUNT_ID });
  const reg = [slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE'), OIREL];
  const c = (orders, o) => slot._testOnly.slotOrderCheckWith({ enabled: true, registry: reg, everUsed: true }, input('OIREL1', Object.assign({ slotOrders: orders }, o || {})));
  assert.strictEqual(c([]).allowed, true, 'alone on the window it trades');
  assert.strictEqual(c([held('OICORE', 'yes', 3)]).allowed, true, 'a small OICORE position of the SAME side leaves room under the cap of ten contracts');
  const big = c([held('OICORE', 'yes', 20)]);
  assert.strictEqual(big.allowed, false, 'OICORE at its ladder size already holds more than the per-market cap: OIREL1 adds nothing: ' + JSON.stringify(big.reasons));
  const hedge = c([held('OICORE', 'no', 3)], { lock: { side: 'no', by: 'SLOT:OICORE' } });
  assert.strictEqual(hedge.allowed, false, 'the opposite side of an OICORE position is a hedge and is refused: ' + JSON.stringify(hedge.reasons));
};

function world(o = {}) {
  const db = { slot: new Map(), l1: new Map(), locks: new Map(), latches: {}, halted: false, queue: Promise.resolve() };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const store = {
    async halted() { return db.halted; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; }, async killLatches() { return clone(db.latches); },
    async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
    async runSlotEntry({ ticker, decide }) {
      return db.tx(async () => {
        const lock = db.locks.get(ticker) || null; await tick();
        const r = decide(lock ? clone(lock) : null, [...db.slot.values()].map(clone), []);
        if (!r.allowed) return { created: false, reason: r.reason };
        if (!lock) db.locks.set(ticker, r.lock);
        db.slot.set(r.record.id, clone(r.record));
        return { created: true, record: clone(r.record) };
      });
    },
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); }, async killStrategy() {},
  };
  const market = Object.assign({ ticker: o.tk, status: 'active', close_time: iso(o.closeMs || CLOSE), yes_bid_dollars: '0.4000', yes_ask_dollars: '0.4200', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 0 }, o.market || {});
  const posts = [], gets = [];
  const oiCandles = o.candles === undefined ? [{ end_period_ts: CLOSE_SEC - 360, open_interest_fp: '100000' }, { end_period_ts: CLOSE_SEC - 180, open_interest_fp: String(100000 + (o.rise === undefined ? 30000 : o.rise)) }] : o.candles;
  const fetchFn = async (url, init) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    gets.push(init.method + ' ' + url.replace(/^.*\/trade-api\/v2/, '').split('?')[0]);
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: oiCandles });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (url.includes('/portfolio/orders') && init.method === 'GET') return reply(200, { orders: [] });
    if (url.includes('/markets/')) return reply(200, { market });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: b.price }); }
    throw new Error('unexpected ' + init.method + ' ' + url);
  };
  const skips = [];
  const sess = { active: true };
  const args = { session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes: [{ series: o.seat.series[0], m: { ticker: o.tk, status: 'active', close_time: iso(o.closeMs || CLOSE) } }],
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {}, clock: () => NOW, recordSkip: async (d) => { skips.push(d); },
    shared: { sizeBase: 500, balanceBody: o.balanceBody || { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 86400000 } };
  const runner = run._testOnly.makeRunners({ enabled: true, registry: [o.seat], everUsed: true });
  return { db, posts, gets, skips, go: () => runner.runSlotTick(args) };
}


gates['LS6 OIREL1 end to end through the engine: a relative rise above the line buys the cheaper side at the ask seen, 3 contracts, immediate-or-cancel, held; at or under the line or with a missing candle nothing is sent and the skip says why'] = async () => {
  let w = world({ seat: OIREL, tk: TK }); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips));
  assert.strictEqual(Number(w.posts[0].count), 3); assert.strictEqual(w.posts[0].time_in_force, 'immediate_or_cancel');
  const d = [...w.db.slot.values()][0];
  assert.strictEqual(d.slotId, 'OIREL1'); assert.ok(Math.abs(d.oiRel - 0.3) < 1e-6, 'the relative rise is stored on the order: ' + d.oiRel); assert.strictEqual(d.oiRise, 30000);
  assert.strictEqual(w.posts.filter((p) => p.action === 'sell').length, 0, 'held to settlement: no sale');
  // 26,764 of 100,000 is under the line (0.26764 < 0.267646...), 26,765 is over it
  w = world({ seat: OIREL, tk: TK, rise: 26764 }); await w.go();
  assert.strictEqual(w.posts.length, 0); assert.ok(w.skips.some((s) => s.reason === 'oi_below' && s.detail && s.detail.oiRel !== undefined), JSON.stringify(w.skips));
  w = world({ seat: OIREL, tk: TK, rise: 26765 }); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips));
  // a missing 180 s candle, or a zero level, is no data and no order
  w = world({ seat: OIREL, tk: TK, candles: [{ end_period_ts: CLOSE_SEC - 360, open_interest_fp: '100000' }] }); await w.go();
  assert.strictEqual(w.posts.length, 0); assert.ok(w.skips.some((s) => s.reason === 'no_oi_candle'));
  w = world({ seat: OIREL, tk: TK, candles: [{ end_period_ts: CLOSE_SEC - 360, open_interest_fp: '0' }, { end_period_ts: CLOSE_SEC - 180, open_interest_fp: '5000' }] }); await w.go();
  assert.strictEqual(w.posts.length, 0); assert.ok(w.skips.some((s) => s.reason === 'no_oi_candle'), 'a zero level has no ratio');
};

gates['LS7 XRPFAV10 end to end through the engine: the favourite at 88c to 92c is bought at the ask seen, 3 contracts, held; a favourite under 88c or over 92c sends nothing'] = async () => {
  const mk = (bid, ask) => ({ seat: XRPF, tk: XTK, closeMs: NOW + 600000, market: { yes_bid_dollars: bid, yes_ask_dollars: ask } });   // 600 s before the close: inside 570 to 640
  let w = world(mk('0.9000', '0.9100')); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips));
  assert.strictEqual(w.posts[0].side, 'bid'); assert.strictEqual(Number(w.posts[0].count), 3); assert.ok(Math.abs(Number(w.posts[0].price) - 0.91) < 1e-9);
  assert.strictEqual([...w.db.slot.values()][0].slotId, 'XRPFAV10');
  for (const [bid, ask] of [['0.8300', '0.8500'], ['0.9300', '0.9400'], ['0.5000', '0.5200']]) {
    w = world(mk(bid, ask)); await w.go();
    assert.strictEqual(w.posts.length, 0, bid + '/' + ask + ' ' + JSON.stringify(w.skips));
  }
};

gates['LS8 the shadow rules are gone for both (they went live instead), and the nightly report and exit watch need no change: both ids hold to settlement under the same exit code as OICORE'] = () => {
  const sh = require('../functions/kalshiShadowLib');
  assert.deepStrictEqual(sh.SHADOW_RULES.map((r) => r.id), ['GOLDOFF']);
  const runSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/const rules = s \? s\.exit : FALLBACK_EXIT;/.test(runSrc), 'a registered seat gets its own hold-to-settle rule, not the 25c fallback');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
