'use strict';
// SX1 to SX9: SPXOI1, the S&P 500 trial seat of the second slot (Nov 13, 2026; kalshi-scalper/README.md#SLOT-SPXOI1). Each gate states the consequence.
// The threshold T is NOT KNOWN YET (it is the 90th percentile of the open interest rise over Nov 5 to Nov 13, from candles not fetched yet). Every test that needs a T uses an INVENTED value, in the test only.
// While SPXOI1_T is null the seat is not registered, so nothing can be sent for it and no other seat changes.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const cfg = require('../functions/kalshiSpxoiConfig');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-11-16T16:57:30Z');          // a Monday, 150 s before a 17:00Z close
const CLOSE = NOW + 150000, CLOSE_SEC = Math.round(CLOSE / 1000);
const T_INV = 5000;                                       // INVENTED, test only
const TK = 'KXINX15M-26NOV161200-00';
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const gates = {};
const spx = slot.spxoiEntry(T_INV);

gates['SX1 with the threshold null the seat is not registered: nothing can be sent for it, the other seats are untouched, and the config holds no guess'] = async () => {
  assert.strictEqual(cfg.SPXOI1_T, null, 'T is null until it is frozen from the Nov 5 to 13 candles and Auditor B has checked it');
  assert.ok(Object.isFrozen(cfg));
  assert.deepStrictEqual(slot.SLOT_STRATEGIES.map((s) => s.id), ['OICORE', 'EVENT830', 'CFRTIK'], 'the registry is exactly what it was');
  assert.strictEqual(slot.SPXOI1_ENTRY, null);
  for (const bad of [null, undefined, NaN, 0, -5, Infinity, '5000']) assert.strictEqual(slot.spxoiEntry(bad), null, 'no seat for ' + String(bad));
  assert.ok(slot.activeSlotStrategies().length === 3 && slot.slotActive());
  const r = slot.slotOrderCheck({ strategyId: 'SPXOI1', ticker: TK, side: 'yes', limit: 0.3, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true, lockTxn: true, lock: null, position: 0,
    sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 150, now: NOW, oiRise: 99999 });
  assert.strictEqual(r.allowed, false, 'no active strategy with that id');
  // The real registry, quotes for the S&P market inside the entry window: no call of any kind.
  const calls = [];
  const out = await run._testOnly.makeRunners().runSlotTick({ session: { active: true }, now: NOW, enabled: true, active: true, store: { halted: async () => { calls.push('store'); return false; } }, keyId: 'k', pem,
    fetchFn: async (u) => { calls.push(u); throw new Error('no call expected'); }, quotes: [{ series: 'KXINX15M', m: { ticker: TK, status: 'active', close_time: iso(CLOSE) } }], setSession: async () => {}, shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60 } });
  assert.deepStrictEqual(calls, [], 'not one read, write or order: ' + JSON.stringify(out));
  assert.ok(/no market in a slot entry window/.test(out.skipped), JSON.stringify(out));
  assert.deepStrictEqual(slot.slotSessionSeriesDue(slot.activeSlotStrategies(), NOW), [], 'and the minute function reads no S&P market for the slot');
};

gates['SX2 the entry is exactly the approved spec, frozen, valid, may hold to settlement, and a value that fails validation leaves only itself out'] = () => {
  assert.deepStrictEqual(JSON.parse(JSON.stringify(spx)), {
    id: 'SPXOI1', readme: 'kalshi-scalper/README.md#SLOT-SPXOI1', series: ['KXINX15M'],
    entry: { sideRule: 'cheap', priceMin: 0.08, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: T_INV },
    exit: { holdToSettle: true }, contractsPerOrder: 3, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 5, net: -18 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-11-13' });
  assert.ok(Object.isFrozen(spx) && Object.isFrozen(spx.entry) && Object.isFrozen(spx.exit) && Object.isFrozen(spx.killRules) && Object.isFrozen(spx.killRules.minNet) && Object.isFrozen(spx.series));
  assert.ok(slot.validateSlotStrategy(spx).ok, JSON.stringify(slot.validateSlotStrategy(spx).errors));
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes('SPXOI1'));
  assert.ok(!slot.validateSlotStrategy(Object.assign({}, JSON.parse(JSON.stringify(spx)), { id: 'SPXOI2' })).ok, 'another id may not hold to settlement on it');
  // A threshold under the validator's 1,000 line fails validation: the registry builder then leaves the seat out by itself (the other seats still trade) and this gate would fail if T were set that way.
  assert.ok(!slot.validateSlotStrategy(slot.spxoiEntry(500)).ok);
  // If T is ever set, the seat MUST be registered (a silent drop of a set value is a failure).
  if (cfg.SPXOI1_T !== null) assert.ok(slot.SLOT_STRATEGIES.some((s) => s.id === 'SPXOI1'), 'a set threshold that does not validate (under 1000?) left the seat out');
  assert.strictEqual(slot.SLOT_LAST_REVIEWED_ON, '2026-11-13');
};

const input = (o) => Object.assign({ strategyId: 'SPXOI1', ticker: TK, side: 'yes', limit: 0.3, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true, lockTxn: true, lock: null,
  position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 150, now: NOW, oiRise: T_INV }, o || {});
const chk = (o) => slot._testOnly.slotOrderCheckWith({ enabled: true, registry: [spx], everUsed: true }, input(o));

gates['SX3 the gate: ask 8c to 50c only (never 88c or above), the rise at or above T, 3 contracts only, per order at most $3, its own daily loss cap $9, KXINX15M and nothing else'] = () => {
  const ok = chk();
  assert.strictEqual(ok.allowed, true, JSON.stringify(ok.reasons));
  assert.strictEqual(ok.count, 3);
  for (const wanted of [1, 5, 10, 30]) assert.ok(chk({ wanted }).count <= 3, 'asked ' + wanted);
  assert.ok(chk({ limit: 0.5 }).cost <= 3 && chk({ limit: 0.5 }).allowed, 'the dearest allowed order costs well under $3');
  for (const limit of [0.5, 0.08]) assert.strictEqual(chk({ limit }).allowed, true, 'edge ' + limit);
  for (const limit of [0.07, 0.51, 0.6, 0.88, 0.9, 0.97]) assert.strictEqual(chk({ limit }).allowed, false, 'refused at ' + limit);
  assert.strictEqual(chk({ oiRise: T_INV }).allowed, true, 'exactly T trades');
  for (const oiRise of [T_INV - 1, undefined, null, NaN]) assert.strictEqual(chk({ oiRise }).allowed, false, 'refused with rise ' + oiRise);
  for (const secondsLeft of [181, 119, 600]) assert.strictEqual(chk({ secondsLeft }).allowed, false, 'only 3 to 2 minutes before the close');
  assert.strictEqual(chk({ ticker: 'KXBTC15M-26NOV161200-00' }).allowed, false, 'only the S&P market');
  assert.strictEqual(chk({ ticker: 'KXSILVER15M-26NOV161200-00' }).allowed, false);
  // its own daily loss cap is $9: with $8.50 already lost today no order of about $1.5 more fits
  const lost = (n) => ({ id: 'S-SPXOI1-' + TK + '-' + n, strategy: 'SLOT', slotId: 'SPXOI1', ticker: 'KXINX15M-26NOV160900-0' + n, series: 'KXINX15M', side: 'yes', step: 1, count: 3, fillCount: '3', maxCost: 1.5, price: 0.5, status: 'filled', settled: true, result: 'no', settledPnl: -1.5, ts: NOW - 3600000 });
  assert.strictEqual(chk({ slotOrders: [lost(1), lost(2), lost(3), lost(4)] }).allowed, true, '$6 lost, $3 of room, the order fits');
  const r = chk({ slotOrders: [lost(1), lost(2), lost(3), lost(4), lost(5)], limit: 0.5 });
  assert.ok(!r.allowed || r.cost <= 1.5 + 1e-9, '$7.50 lost leaves $1.50 of the $9 cap, so a 50c order is cut to fit: ' + JSON.stringify(r));
  assert.ok(r.count < 3, 'cut below 3 contracts');
  const r6 = chk({ slotOrders: [lost(1), lost(2), lost(3), lost(4), lost(5), lost(6)] });
  assert.strictEqual(r6.allowed, false, '$9 lost is the daily cap: no order: ' + JSON.stringify(r6));
  assert.strictEqual(slot.SLOT_SEAT_CAPS.SPXOI1.perOrder, 3); assert.strictEqual(slot.SLOT_SEAT_CAPS.SPXOI1.daily, 9);
  assert.strictEqual(chk({ sizingBase: 10000 }).allowed, true, 'a huge base cannot lift the seat above its own caps');
  assert.ok(chk({ sizingBase: 10000, limit: 0.5 }).cost <= 3);
  // The seat caps only lower: another seat is unchanged.
  assert.strictEqual(Object.prototype.hasOwnProperty.call(slot.SLOT_SEAT_CAPS, 'OICORE'), false);
};

gates['SX4 KXINX15M is this seat\'s alone, even before it is registered: any other strategy listing it is refused'] = () => {
  assert.ok(slot.SLOT_SERIES_ALLOWED.includes('KXINX15M'));
  assert.strictEqual(slot.SLOT_SERIES_RESERVED.KXINX15M, 'SPXOI1');
  const other = Object.assign(JSON.parse(JSON.stringify(slot.SLOT_STRATEGIES[0])), { id: 'OICORE', series: ['KXINX15M'] });
  const errs = slot.validateSlotStrategy(other).errors;
  assert.ok(errs.some((e) => /KXINX15M is reserved for SPXOI1/.test(e)), JSON.stringify(errs));
  assert.strictEqual(chk({ ticker: 'KXINX15M-26NOV051300-00', secondsLeft: 150 }).allowed, true, 'the ticker shape of the real S&P windows passes the slot ticker check');
  assert.strictEqual(chk({ ticker: 'KXINX15M-26NOV05130-00' }).allowed, false);
  const live = require('../functions/kalshiLiveLib');
  assert.ok(!live.L1_SERIES.includes('KXINX15M'), 'not an L1 market, so no L1 order can sit against it');
  assert.strictEqual(live.maxContractsFor('KXINX15M'), 0, 'and L1 may send nothing there');
};

// ---- end to end through the engine (a fake exchange and store, as the other slot gates) ----
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
  const market = Object.assign({ ticker: TK, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.4000', yes_ask_dollars: '0.4200', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 0 }, o.market || {});
  const posts = [], gets = [];
  const oiCandles = o.candles === undefined ? [{ end_period_ts: CLOSE_SEC - 360, open_interest_fp: '1000' }, { end_period_ts: CLOSE_SEC - 180, open_interest_fp: String(1000 + (o.rise === undefined ? T_INV + 100 : o.rise)) }] : o.candles;
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
  const args = { session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes: [{ series: 'KXINX15M', m: { ticker: TK, status: 'active', close_time: iso(CLOSE) } }],
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {}, clock: () => NOW, recordSkip: async (d) => { skips.push(d); },
    shared: { sizeBase: 500, balanceBody: o.balanceBody || { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 86400000 } };
  const runner = run._testOnly.makeRunners({ enabled: true, registry: [spx], everUsed: true });
  return { db, posts, gets, skips, go: () => runner.runSlotTick(args) };
}

gates['SX5 end to end: it buys the cheaper side at the ask seen, 3 contracts, immediate-or-cancel, held; a tie goes YES; the NO side is bought when NO is cheaper'] = async () => {
  let w = world(); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips));
  assert.strictEqual(w.posts[0].side, 'bid'); assert.strictEqual(Number(w.posts[0].count), 3); assert.strictEqual(w.posts[0].time_in_force, 'immediate_or_cancel');
  assert.ok(Math.abs(Number(w.posts[0].price) - 0.42) < 1e-9, 'the ask seen, no slip: ' + w.posts[0].price);
  const d = [...w.db.slot.values()][0];
  assert.strictEqual(d.slotId, 'SPXOI1'); assert.strictEqual(d.oiRise, T_INV + 100); assert.strictEqual(w.db.locks.get(TK).by, 'SLOT:SPXOI1');
  assert.strictEqual(w.posts.filter((p) => p.action === 'sell').length, 0, 'held to settlement: no sale');
  // a tie (YES ask 0.51 and NO ask 0.51) goes YES, and 51c is above the band, so no order; with the band edge tie at 0.50 it buys YES
  w = world({ market: { yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5000' } }); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips)); assert.strictEqual(w.posts[0].side, 'bid', 'a tie goes YES'); assert.ok(Math.abs(Number(w.posts[0].price) - 0.5) < 1e-9);
  assert.strictEqual(slot.slotCheapSide('SPXOI1', 0.5, 0.5), 'yes'); assert.strictEqual(slot.slotCheapSide('OICORE', 0.5, 0.5), 'no', 'every other seat keeps its older tie reading');
  assert.strictEqual(slot.slotCheapSide('SPXOI1', 0.4, 0.61), 'yes'); assert.strictEqual(slot.slotCheapSide('SPXOI1', 0.61, 0.4), 'no');
  // NO cheaper: YES ask 0.62, bid 0.60 -> NO price 0.40: a NO buy is sent as an ask at the YES price 0.60
  w = world({ market: { yes_bid_dollars: '0.6000', yes_ask_dollars: '0.6200' } }); await w.go();
  assert.strictEqual(w.posts.length, 1, JSON.stringify(w.skips)); assert.strictEqual(w.posts[0].side, 'ask'); assert.ok(Math.abs(Number(w.posts[0].price) - 0.6) < 1e-9, 'the YES price the NO order goes to: ' + w.posts[0].price);
  assert.strictEqual([...w.db.slot.values()][0].side, 'no');
};

gates['SX6 never at 88c or above, never below 8c: an out-of-band ask sends nothing and says so'] = async () => {
  for (const [bid, ask] of [['0.4600', '0.5500'], ['0.0300', '0.0500'], ['0.9400', '0.9500']]) {
    const w = world({ market: { yes_bid_dollars: bid, yes_ask_dollars: ask } }); await w.go();
    assert.strictEqual(w.posts.length, 0, bid + '/' + ask + ' ' + JSON.stringify(w.skips));
    assert.ok(w.skips.some((s) => s.reason === 'price_out_of_band'), JSON.stringify(w.skips));
  }
  // a 95c YES / 5c NO market: the cheaper side is NO at 5c, under the 8c floor, so no order
  const w = world({ market: { yes_bid_dollars: '0.9400', yes_ask_dollars: '0.9500' } }); await w.go();
  assert.strictEqual(w.posts.length, 0);
};

gates['SX7 the open interest rule fails closed: a missing candle or a rise under T sends nothing; exactly T trades'] = async () => {
  let w = world({ candles: [] }); await w.go();
  assert.strictEqual(w.posts.length, 0); assert.ok(w.skips.some((s) => s.reason === 'no_oi_candle'), JSON.stringify(w.skips));
  w = world({ candles: [{ end_period_ts: CLOSE_SEC - 180, open_interest_fp: '9000' }] }); await w.go();
  assert.strictEqual(w.posts.length, 0, 'only one of the two candles'); assert.ok(w.skips.some((s) => s.reason === 'no_oi_candle'));
  w = world({ rise: T_INV - 1 }); await w.go();
  assert.strictEqual(w.posts.length, 0); assert.ok(w.skips.some((s) => s.reason === 'oi_below' && s.detail.oiRise === T_INV - 1 && s.detail.min === T_INV), JSON.stringify(w.skips));
  w = world({ rise: T_INV }); await w.go();
  assert.strictEqual(w.posts.length, 1, 'exactly T trades: ' + JSON.stringify(w.skips));
};

gates['SX8 shard 0 with too little money: a shard_short skip is logged and nothing is sent'] = async () => {
  const w = world({ balanceBody: { balance_breakdown: [{ exchange_index: 0, balance: 0.5 }, { exchange_index: 2, balance: 500 }] } }); await w.go();
  assert.strictEqual(w.posts.length, 0);
  const s = w.skips.find((x) => x.reason === 'shard_short');
  assert.ok(s && s.detail.shard === 0 && s.detail.avail < s.detail.need, JSON.stringify(w.skips));
  // with money on shard 0 it goes
  const ok = world({ balanceBody: { balance_breakdown: [{ exchange_index: 0, balance: 50 }, { exchange_index: 2, balance: 0 }] } }); await ok.go();
  assert.strictEqual(ok.posts.length, 1, JSON.stringify(ok.skips));
};

gates['SX9 the wiring: quotes reach the slot tick only around the weekday entry span, and a set threshold cannot ship without the page, the registry row and the relay'] = () => {
  const mon = (hh, mm, ss) => Date.parse('2026-11-16T' + hh + ':' + mm + ':' + ss + 'Z');
  const due = (t) => slot.slotSessionSeriesDue([spx, ...slot.SLOT_STRATEGIES], t);
  assert.deepStrictEqual(due(mon('16', '57', '30')), ['KXINX15M'], '150 s before a close, in the session');
  assert.deepStrictEqual(due(mon('16', '57', '00')), ['KXINX15M'], 'from 30 s before the window opens');
  for (const t of [mon('16', '50', '00'), mon('16', '59', '30'), mon('16', '30', '10'), mon('14', '57', '30'), mon('21', '12', '30'), mon('22', '57', '30'), Date.parse('2026-11-14T16:57:30Z'), Date.parse('2026-11-15T16:57:30Z')]) assert.deepStrictEqual(due(t), [], iso(t) + ' reads nothing');
  assert.deepStrictEqual(slot.slotSessionSeriesDue(slot.SLOT_STRATEGIES, mon('16', '57', '30')), [], 'seats without session hours add no read (OICORE, EVENT830, CFRTIK are unchanged)');
  assert.deepStrictEqual(slot.slotSessionSeriesDue([spx], NaN), []);
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(/slotLib\.slotCalendarSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)\.concat\(slotLib\.slotSessionSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)\)/.test(idx), 'the minute function asks the library with its own clock');
  // If T is ever set, the same pull request must also carry these (this fails until it does).
  if (cfg.SPXOI1_T !== null) {
    const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
    assert.ok(/KAL_SLOT_REGISTERED = \[[^\]]*'SPXOI1'/.test(html), 'KAL_SLOT_REGISTERED names SPXOI1');
    assert.ok(/SPXOI1: \{ name:/.test(html), 'KAL_STRATEGY_INFO names it');
    assert.ok(/KXINX15M/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiLib.js'), 'utf8')), 'the market relay lists KXINX15M so an open position draws a chart');
    const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
    assert.ok(reg.strategies.some((x) => x.code && x.code.slot === 'SPXOI1'), 'the registry row names it in code.slot');
  } else {
    const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
    const row = reg.strategies.find((x) => x.id === 'SPXOI1');
    assert.ok(row && row.stage === 'Probe' && row.label === 'UNPROVEN' && /Trial: below the research bar, no evidence/.test(JSON.stringify(row)) && /waiting for its threshold/i.test(JSON.stringify(row)), 'the registry says: trial, waiting for its threshold');
    assert.ok(!(row.code && (row.code.slot || row.code.live)), 'and does not claim a coded seat while T is null');
  }
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-SPXOI1/m.test(readme), 'the pre-registration anchor exists');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + name.slice(0, 110)); } catch (e) { failed++; console.log('FAIL ' + name.slice(0, 110) + ': ' + e.message); } }
  process.exit(failed ? 1 : 0);
})();
