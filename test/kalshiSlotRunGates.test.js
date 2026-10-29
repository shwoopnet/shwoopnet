'use strict';
// Gates for the second slot's ENGINE (functions/kalshiSlotRunLib.js, docs/SECOND_SLOT_WIRING.md step B1). Each states the consequence, not the mechanism.
// The engine is not wired anywhere yet; these tests drive it through fakes (a fake exchange, a fake store whose transactions are serialised like Firestore's).
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');

const root = path.join(__dirname, '..');
const runSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiSlotRunLib.js'), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-11-03T15:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const T = 'KXBTC15M-26NOV031015-15';
const tick = () => new Promise((r) => setImmediate(r));

const GOOD = (over) => Object.assign({
  id: 'TESTA', readme: 'kalshi-scalper/README.md#SLOT-TESTA', series: ['KXBTC15M', 'KXGOLD15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 },
  exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 },
  contractsPerOrder: 4, scaleIn: { maxSteps: 2, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -3 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
}, over || {});
const ON = (over) => ({ enabled: true, registry: [GOOD(over)] });
const R = (flags) => run._testOnly.makeRunners(flags);

// ---- the fake world: one "database" shared by any number of function instances, each with its own store object and call log ----
function makeDb() {
  const db = { slot: new Map(), l1: new Map(), locks: new Map(), closing: new Map(), latches: {}, halted: false, queue: Promise.resolve(), events: [] };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  // What Firestore's transaction does for an L1 order once the slot is wired: read the lock, refuse the other side, else write the lock and the order, all in one commit.
  db.l1CreateLocked = (ticker, side, doc) => db.tx(async () => {
    const lock = db.locks.get(ticker); await tick();
    if (lock && lock.side !== side) return 'direction';
    if (!lock) db.locks.set(ticker, { side, by: 'L1', ts: NOW });
    db.l1.set('L1-' + ticker, Object.assign({ id: 'L1-' + ticker, strategy: 'L1', ticker, side, count: 1, fillCount: '1', maxCost: 0.95, addonCost: 0, status: 'filled', settled: false, ts: NOW - 1000 }, doc || {}));
    return true;
  });
  return db;
}
const clone = (x) => JSON.parse(JSON.stringify(x));
function makeStore(db, name) {
  const calls = [];
  const rec = (n, ...a) => { calls.push(n); db.events.push(name + ':' + n); return a; };
  const s = {
    calls,
    async halted() { rec('halted'); return db.halted; },
    async hasUnresolved() { rec('hasUnresolved'); return [...db.slot.values()].some((t) => ['sending', 'unknown'].includes(t.status)); },
    async l1HasUnresolved() { rec('l1HasUnresolved'); return [...db.l1.values()].some((t) => ['sending', 'unknown'].includes(t.status)); },
    async killLatches() { rec('killLatches'); return clone(db.latches); },
    async allSlotOrders() { rec('allSlotOrders'); return [...db.slot.values()].map(clone); },
    async l1Recent() { rec('l1Recent'); return [...db.l1.values()].map(clone); },
    async runSlotEntry({ ticker, decide }) {
      rec('runSlotEntry');
      return db.tx(async () => {
        const lock = db.locks.get(ticker) || null;
        const slotNow = [...db.slot.values()].map(clone), l1Docs = [...db.l1.values()].filter((t) => t.ticker === ticker).map(clone);
        await tick();     // the other instance gets its chance to interleave: only the serialised transaction keeps them apart
        const r = decide(lock ? clone(lock) : null, slotNow, l1Docs);
        if (!r.allowed) return { created: false, reason: r.reason };
        if (db.slot.has(r.record.id)) return { created: false, reason: 'already attempted' };
        if (!lock) db.locks.set(ticker, r.lock);
        db.slot.set(r.record.id, clone(r.record));
        db.events.push(name + ':commit');
        return { created: true, record: clone(r.record) };
      });
    },
    async updateSlotOrder(id, patch) { rec('updateSlotOrder'); Object.assign(db.slot.get(id), clone(patch)); },
    async killStrategy(id, info) { rec('killStrategy'); db.latches[id] = clone(info); },
    async slotRecentFilled() { rec('slotRecentFilled'); return [...db.slot.values()].filter((t) => t.status === 'filled').map((t) => ({ ...clone(t), id: t.id })); },
    async slotOrdersOnTicker(ticker) { rec('slotOrdersOnTicker'); return [...db.slot.values()].filter((t) => t.ticker === ticker).map(clone); },
    async l1OrdersOnTicker(ticker) { rec('l1OrdersOnTicker'); return [...db.l1.values()].filter((t) => t.ticker === ticker).map(clone); },
    async claimClose(ticker, who, now, ttl) { rec('claimClose'); const c = db.closing.get(ticker); if (c && c.by !== who && now - c.at < ttl) return false; db.closing.set(ticker, { by: who, at: now }); return true; },
    async releaseClose(ticker, who) { rec('releaseClose'); const c = db.closing.get(ticker); if (c && c.by === who) db.closing.delete(ticker); },
    async claimSlotExit(id, tries) { rec('claimSlotExit'); const d = db.slot.get(id); if (d.exitStatus === 'sending' || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false; d.exitStatus = 'sending'; d.exitTries = tries + 1; return true; },
    async finishSlotOrder(id, patch, killEval) {
      rec('finishSlotOrder');
      return db.tx(async () => {
        Object.assign(db.slot.get(id), clone(patch));
        const k = killEval([...db.slot.values()].map(clone));
        if (k) db.latches[k.strategyId] = { killedAt: k.killedAt, reason: k.reason };
      });
    },
  };
  return s;
}
// A fake exchange: markets, signed positions, an order endpoint. Every request is recorded.
function makeExchange(db, o = {}) {
  const calls = [], posts = [];
  const market = Object.assign({ ticker: T, status: 'active', close_time: iso(NOW + 500000), yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7600', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 2 }, o.market || {});
  const positions = o.positions || {};
  const fetchFn = async (url, init) => {
    calls.push({ url, method: init.method, body: init.body ? JSON.parse(init.body) : null });
    db.events.push(init.method + ' ' + url.replace(/^.*\/trade-api\/v2/, '').split('?')[0]);
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) {
      if (o.posStatus) return reply(o.posStatus, {});
      const tk = new URL(url).searchParams.get('ticker');
      return reply(200, { market_positions: positions[tk] === undefined ? [] : [{ ticker: tk, position_fp: String(positions[tk]) }] });
    }
    if (url.includes('/portfolio/orders') && init.method === 'GET') return reply(200, { orders: o.found || [] });
    if (url.includes('/markets/')) return reply(o.marketStatus || 200, { market });
    if (init.method === 'POST') {
      posts.push(JSON.parse(init.body));
      if (o.throwPost) throw new Error('socket hang up');
      if (o.post) return reply(o.post.status, o.post.body);
      return reply(201, { order_id: 'ord-' + posts.length, fill_count: o.fill !== undefined ? o.fill : String(JSON.parse(init.body).count), remaining_count: '0.00', average_fill_price: o.avg || '0.7600' });
    }
    throw new Error('unexpected ' + init.method + ' ' + url);
  };
  return { calls, posts, fetchFn, market, positions };
}
const SHARED = (o) => Object.assign({ sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 24 * 3600 * 1000 }, o || {});
const QUOTES = (over) => [{ series: 'KXBTC15M', m: Object.assign({ ticker: T, status: 'active', close_time: iso(NOW + 500000) }, over || {}) }];
function tickArgs(db, ex, o = {}) {
  const sess = { active: true }, events = [];
  const args = Object.assign({ session: sess, now: NOW, enabled: true, active: true, store: makeStore(db, o.name || 'A'), keyId: 'k', pem, fetchFn: ex.fetchFn, quotes: QUOTES(),
    setSession: async (p) => Object.assign(sess, p), logEvent: async (e) => events.push(e), shared: SHARED() }, o.args || {});
  return { args, sess, events };
}
const slotOrder = (o) => Object.assign({ id: 'S-TESTA-' + T + '-1', strategy: 'SLOT', slotId: 'TESTA', ticker: T, series: 'KXBTC15M', side: 'yes', step: 1, count: 4, fillCount: '4', maxCost: 3.1, price: 0.76, status: 'filled', settled: false, exitCount: 0, exitProceeds: 0, ts: NOW - 120000 }, o);
const l1Order = (o) => Object.assign({ id: 'L1-' + T, strategy: 'L1', ticker: T, side: 'yes', count: 1, fillCount: '1', maxCost: 0.95, addonCost: 0, status: 'filled', settled: false, ts: NOW - 60000 }, o);
function exitWorld(o = {}) {
  const db = makeDb();
  const order = o.order === null ? null : slotOrder(o.order);
  if (order) db.slot.set(order.id, order);
  for (const t of o.extraSlot || []) db.slot.set(t.id, t);
  for (const t of o.l1 || []) db.l1.set(t.id, t);
  for (const [k, v] of Object.entries(o.closing || {})) db.closing.set(k, v);
  const ex = makeExchange(db, Object.assign({ market: { yes_bid_dollars: '0.3500', yes_ask_dollars: '0.3700' }, positions: { [T]: 4 } }, o.ex || {}));
  const store = makeStore(db, 'X');
  const sess = { active: true }, events = [];
  const args = { store, fetchFn: ex.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async (p) => Object.assign(sess, p), logEvent: async (e) => events.push(e) };
  return { db, ex, store, sess, events, args, runner: R(o.flags || ON()) };
}

const gates = {};

// ---- OFF: nothing happens ----------------------------------------------------------------------------------------------------------------
gates['SW4 with the real constants (switch off) the engine makes no call at all: no read, no write, no order'] = async () => {
  const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
  const trap = new Proxy({}, { get: (_, k) => { throw new Error('the engine touched the store: ' + String(k)); } });
  t.args.store = trap;
  const out = await run.runSlotTick(t.args);
  assert.ok(out.skipped, 'a skip');
  assert.strictEqual(ex.calls.length, 0, 'no request');
  const out2 = await run.runSlotExits({ store: trap, fetchFn: ex.fetchFn, keyId: 'k', pem, now: NOW, enabled: true });
  assert.ok(out2.skipped); assert.strictEqual(ex.calls.length, 0);
  assert.strictEqual(await run.slotExitIdle({ store: trap, now: NOW }), true, 'with the slot off the exit loop has nothing to wait for');
  assert.strictEqual(run.runSlotTick.length, 1); assert.strictEqual(run.runSlotExits.length, 1);
  assert.strictEqual(slot.slotActive(), false);
};
gates['SW5 a switch on with no registered strategy, or a registry with one bad entry, sends nothing'] = async () => {
  for (const flags of [{ enabled: true, registry: [] }, { enabled: false, registry: [GOOD()] }, { enabled: true, registry: [GOOD({ contractsPerOrder: 11 })] }, { enabled: true, registry: [GOOD({ exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 30 } })] }]) {
    const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
    const out = await R(flags).runSlotTick(t.args);
    assert.ok(out.skipped, JSON.stringify(flags).slice(0, 80));
    assert.strictEqual(ex.calls.length, 0); assert.strictEqual(db.slot.size, 0); assert.strictEqual(t.args.store.calls.length, 0);
  }
};
gates['the engine will not act when the server switch is off, the exchange is closed, the bot is halted, the session is over or L1 just ended it'] = async () => {
  const variants = [{ enabled: false }, { enabled: 'on' }, { active: false }, { session: { active: false } }, { l1Result: { ended: 'loss stop' } }, { shared: undefined }, { shared: SHARED({ floor: NaN }) }, { quotes: [] },
    { quotes: QUOTES({ close_time: iso(NOW + 100000) }) }, { quotes: QUOTES({ close_time: iso(NOW + 800000) }) }, { quotes: QUOTES({ status: 'closed' }) }];
  for (const v of variants) {
    const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex, { args: v });
    await R(ON()).runSlotTick(t.args);
    assert.strictEqual(ex.posts.length, 0, JSON.stringify(v).slice(0, 60)); assert.strictEqual(db.slot.size, 0); assert.strictEqual(db.locks.size, 0);
  }
  const db = makeDb(); db.halted = true; const ex = makeExchange(db), t = tickArgs(db, ex);
  await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 0, 'halted'); assert.strictEqual(db.locks.size, 0);
  const db2 = makeDb(), ex2 = makeExchange(db2), t2 = tickArgs(db2, ex2, { args: { sessionNow: async () => ({ active: false }) } });
  await R(ON()).runSlotTick(t2.args);
  assert.strictEqual(ex2.posts.length, 0, 'the session was ended by L1 earlier in the minute');
};
gates['an unresolved L1 or slot order, or a store that cannot be read, sends nothing (fails closed)'] = async () => {
  for (const mut of [(db) => db.l1.set('x', l1Order({ id: 'x', status: 'unknown' })), (db) => db.slot.set('y', slotOrder({ id: 'y', status: 'sending', settled: false }))]) {
    const db = makeDb(); mut(db); const ex = makeExchange(db), t = tickArgs(db, ex);
    await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0);
  }
  for (const m of ['allSlotOrders', 'l1Recent', 'halted']) {
    const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
    t.args.store[m] = async () => { throw new Error('firestore down'); };
    await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0, m); assert.strictEqual(db.locks.size, 0);
  }
  const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
  t.args.store.runSlotEntry = async () => { throw new Error('transaction failed'); };
  await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0, 'no document, no send');
};

// ---- Entries ------------------------------------------------------------------------------------------------------------------------------
gates['an allowed entry records the order and the direction lock in one commit BEFORE the buy is sent, and the buy is immediate-or-cancel inside the band'] = async () => {
  const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
  const out = await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 1, JSON.stringify(out));
  const b = ex.posts[0];
  assert.strictEqual(b.time_in_force, 'immediate_or_cancel'); assert.strictEqual(b.side, 'bid', 'a YES buy'); assert.strictEqual(b.client_order_id, 'S-TESTA-' + T + '-1');
  assert.ok(Number(b.price) >= 0.6 && Number(b.price) <= 0.9, 'inside the strategy band'); assert.strictEqual(b.exchange_index, 2);
  assert.ok(Number(b.count) >= 1 && Number(b.count) <= 4);
  assert.ok(db.events.indexOf('A:commit') >= 0 && db.events.indexOf('A:commit') < db.events.findIndex((e) => e.startsWith('POST')), 'the commit comes first');
  assert.strictEqual(db.locks.get(T).side, 'yes'); assert.strictEqual(db.locks.get(T).by, 'SLOT:TESTA');
  const d = db.slot.get('S-TESTA-' + T + '-1');
  assert.strictEqual(d.status, 'filled'); assert.strictEqual(d.strategy, 'SLOT'); assert.strictEqual(d.slotId, 'TESTA'); assert.ok(d.maxCost > 0 && d.fillCount === String(b.count));
};
gates['a NO buy goes to the YES bid as a YES-price ask-side order and costs the NO price'] = async () => {
  const db = makeDb(), ex = makeExchange(db, { market: { yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600' } }), t = tickArgs(db, ex);
  await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 1);
  assert.strictEqual(ex.posts[0].side, 'ask', 'Kalshi books a NO buy as a YES-side ask'); assert.strictEqual(ex.posts[0].price, '0.24');
  assert.strictEqual(db.locks.get(T).side, 'no'); assert.strictEqual(db.slot.get('S-TESTA-' + T + '-1').price, 0.76);
};
gates['no double order from two instances: both compute the same id, one transaction wins, the other sends nothing'] = async () => {
  const db = makeDb(), ex = makeExchange(db);
  const a = tickArgs(db, ex, { name: 'A' }), b = tickArgs(db, ex, { name: 'B' });
  await Promise.all([R(ON()).runSlotTick(a.args), R(ON()).runSlotTick(b.args)]);
  assert.strictEqual(ex.posts.length, 1, 'exactly one buy reached the exchange');
  assert.strictEqual(db.slot.size, 1); assert.strictEqual(db.locks.size, 1);
  assert.strictEqual(db.events.filter((e) => e.endsWith(':commit')).length, 1);
  // Even if the second instance read an empty book and skipped every pre-check, the same client order id would be refused by Kalshi and by the create.
  assert.strictEqual(new Set(ex.posts.map((p) => p.client_order_id)).size, 1);
};
gates['no opposite side: an L1 order, the lock, the account position or an unreadable book each stop a hedge, in both directions'] = async () => {
  const noOnly = { entry: { sideRule: 'no', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 } };
  const noBook = { market: { yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600' } };
  // L1 holds YES on the market; the slot wants NO.
  let db = makeDb(); db.l1.set('L1-' + T, l1Order()); let ex = makeExchange(db, noBook);
  await R(ON(noOnly)).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'L1 holds YES');
  // A stale position read (nothing held) but the lock says YES (another instance got there first, its order not visible in our read).
  db = makeDb(); db.locks.set(T, { side: 'yes', by: 'L1', ts: NOW }); ex = makeExchange(db, noBook);
  await R(ON(noOnly)).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'the lock says YES');
  assert.strictEqual(db.slot.size, 0);
  // The account holds YES (a position read), the slot wants NO.
  db = makeDb(); ex = makeExchange(db, Object.assign({ positions: { [T]: 3 } }, noBook));
  await R(ON(noOnly)).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'the account holds YES');
  // The position cannot be read.
  db = makeDb(); ex = makeExchange(db, Object.assign({ posStatus: 500 }, noBook));
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'unreadable position');
  // The L1 orders cannot be read at all.
  db = makeDb(); ex = makeExchange(db); let t = tickArgs(db, ex); t.args.store.l1Recent = async () => { throw new Error('down'); };
  await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0, 'unreadable L1 orders');
  // A slot NO order exists: a slot YES (favourite flipped) is refused too.
  db = makeDb(); db.slot.set('n', slotOrder({ id: 'n', side: 'no', step: 1 })); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'the slot itself holds NO');
  // Same side as L1 is allowed (the owner's rule), and the slot then adds to the same lock.
  db = makeDb(); db.l1.set('L1-' + T, l1Order()); db.locks.set(T, { side: 'yes', by: 'L1', ts: NOW }); ex = makeExchange(db, { positions: { [T]: 1 } });
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 1, 'the same side as L1 is allowed'); assert.strictEqual(db.locks.get(T).by, 'L1', 'an existing same-side lock is left alone');
};
gates['SW8 the hedge race: L1 yes and slot no reach the lock together, whoever commits first wins, and the two sides are never both written'] = async () => {
  const noOnly = { entry: { sideRule: 'no', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 } };
  const noBook = { market: { yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600' } };
  for (const l1First of [true, false]) {
    const db = makeDb(), ex = makeExchange(db, noBook), t = tickArgs(db, ex);
    const l1 = () => db.l1CreateLocked(T, 'yes');
    const slotRun = () => R(ON(noOnly)).runSlotTick(t.args);
    const [r1] = l1First ? await Promise.all([l1(), slotRun()]) : (await Promise.all([slotRun(), l1()])).reverse();
    const sides = new Set([...db.slot.values(), ...db.l1.values()].map((x) => x.side));
    assert.strictEqual(sides.size, 1, 'one side only: ' + [...sides]);
    assert.strictEqual(db.locks.size, 1); assert.strictEqual(db.locks.get(T).side, [...sides][0]);
    if (r1 === 'direction') assert.strictEqual(db.l1.size, 0, 'a refused L1 order was never written');
    else assert.strictEqual(ex.posts.length, db.slot.size, 'every slot order that exists was sent, and none that was refused');
  }
};
gates['caps are respected: depth share, per-order dollars, window room, and a base too small for the caps all cut the size or stop the order'] = async () => {
  let db = makeDb(), ex = makeExchange(db, { market: { yes_ask_size_fp: '9.00' } });
  await R(ON()).runSlotTick(tickArgs(db, ex).args);
  assert.strictEqual(ex.posts.length, 1); assert.strictEqual(ex.posts[0].count, '2', 'a quarter of the 9 resting at the touch is 2');
  db = makeDb(); ex = makeExchange(db, { market: { yes_ask_size_fp: '2.00' } });
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'a quarter of 2 is not a whole contract');
  db = makeDb(); ex = makeExchange(db);
  await R(ON({ contractsPerOrder: 10, scaleIn: { maxSteps: 1, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true } })).runSlotTick(tickArgs(db, ex).args);
  assert.ok(ex.posts.length === 1 && Number(ex.posts[0].count) <= 6, 'the 1% per-order cap on a $500 base cuts 10 contracts at 76c to ' + (ex.posts[0] && ex.posts[0].count));
  db = makeDb(); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ sizeBase: 20 }) } }).args); assert.strictEqual(ex.posts.length, 0, 'a small base leaves the slot no room');
  db = makeDb(); db.l1.set('a', l1Order({ id: 'a', ticker: 'KXGOLD15M-26NOV031015-15', maxCost: 27 })); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'L1 already used the window cap');
  // Money on the shard is checked too.
  db = makeDb(); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ balanceBody: { balance: 100 } }) } }).args); assert.strictEqual(ex.posts.length, 0, 'only $1 on the shard');
  db = makeDb(); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ balanceBody: 'junk' }) } }).args); assert.strictEqual(ex.posts.length, 0, 'an unreadable balance');
};
gates['the slot counts against the shared loss stop: no room under the floor means no order, and L1 orders made after its read count as lost'] = async () => {
  let db = makeDb(), ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ risk: { worst: -59 } }) } }).args); assert.strictEqual(ex.posts.length, 0, '$1 of room under the stop is not enough for a $3 order');
  db = makeDb(); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ risk: { worst: -40 } }) } }).args); assert.strictEqual(ex.posts.length, 1, 'plenty of room');
  // L1 created an order on another market after botRisk was read: its dollars are counted as lost.
  db = makeDb(); db.l1.set('new', l1Order({ id: 'new', ticker: 'KXGOLD15M-26NOV031015-15', maxCost: 20, side: 'yes' })); ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { shared: SHARED({ risk: { worst: -38 }, floor: -60 }) } }).args);
  assert.strictEqual(ex.posts.length, 0, '38 + 20 > the 60 floor, so the new order has no room');
};
gates['SW12 a lost answer on a buy ends the session, latches the strategy off and is never retried; a refusal and an existing id do the same'] = async () => {
  for (const o of [{ post: { status: 502, body: 'bad gateway' } }, { throwPost: true }, { post: { status: 429, body: 'slow down' } }]) {
    const db = makeDb(), ex = makeExchange(db, o), t = tickArgs(db, ex);
    const out = await R(ON()).runSlotTick(t.args);
    assert.strictEqual(ex.posts.length, 1); assert.strictEqual(out.ended, 'attempted'); assert.strictEqual(t.sess.active, false, 'the whole session ends');
    assert.strictEqual(db.slot.get('S-TESTA-' + T + '-1').status, 'unknown'); assert.ok(db.latches.TESTA && db.latches.TESTA.killedAt === NOW, 'the strategy is latched off');
    // The next minute: nothing is sent, because the order is unresolved and the strategy is latched.
    const t2 = tickArgs(db, ex, { args: { now: NOW + 60000, quotes: QUOTES({ close_time: iso(NOW + 560000) }) } });
    await R(ON()).runSlotTick(t2.args); assert.strictEqual(ex.posts.length, 1, 'never retried');
    db.slot.get('S-TESTA-' + T + '-1').status = 'no fill';     // even if someone marked it resolved by hand, the latch holds
    await R(ON()).runSlotTick(t2.args); assert.strictEqual(ex.posts.length, 1, 'the latch alone blocks it');
  }
  let db = makeDb(), ex = makeExchange(db, { post: { status: 400, body: { error: 'bad' } } }), t = tickArgs(db, ex);
  let out = await R(ON()).runSlotTick(t.args);
  assert.strictEqual(out.ended, 'attempted'); assert.strictEqual(db.slot.get('S-TESTA-' + T + '-1').status, 'error'); assert.ok(db.latches.TESTA);
  db = makeDb(); ex = makeExchange(db, { post: { status: 409, body: 'exists' }, found: [{ client_order_id: 'S-TESTA-' + T + '-1', order_id: 'o9', fill_count_fp: '2' }] }); t = tickArgs(db, ex);
  out = await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 1); assert.strictEqual(out.ended, 'attempted'); assert.strictEqual(db.slot.get('S-TESTA-' + T + '-1').recovered, true); assert.ok(db.latches.TESTA);
};
gates['a step is attempted once: a second tick in the same minute window does not buy again, and scale-in waits for a filled previous step and the gap'] = async () => {
  const db = makeDb(), ex = makeExchange(db, { positions: {} });
  await R(ON()).runSlotTick(tickArgs(db, ex).args);
  assert.strictEqual(ex.posts.length, 1);
  ex.positions[T] = Number(ex.posts[0].count);
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { now: NOW + 10000 } }).args);
  assert.strictEqual(ex.posts.length, 1, 'inside the minimum gap there is no step 2');
  const later = tickArgs(db, ex, { args: { now: NOW + 70000, quotes: QUOTES({ close_time: iso(NOW + 570000) }) } });
  ex.market.close_time = iso(NOW + 570000);
  await R(ON()).runSlotTick(later.args);
  assert.strictEqual(ex.posts.length, 2, 'after the gap step 2 goes'); assert.strictEqual(ex.posts[1].client_order_id, 'S-TESTA-' + T + '-2');
  ex.positions[T] = 8;
  await R(ON()).runSlotTick(tickArgs(db, ex, { args: { now: NOW + 140000, quotes: QUOTES({ close_time: iso(NOW + 640000) }) } }).args);
  assert.strictEqual(ex.posts.length, 2, 'maxSteps is 2');
};
gates['an entry outside the strategy price band or time window sends nothing'] = async () => {
  for (const mk of [{ yes_bid_dollars: '0.9400', yes_ask_dollars: '0.9500' }, { yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5200' }, { yes_bid_dollars: '0.0000', yes_ask_dollars: '1.0000' }, { yes_bid_dollars: '0.7400', yes_ask_dollars: '0.7000' }]) {
    const db = makeDb(), ex = makeExchange(db, { market: mk });
    await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, JSON.stringify(mk)); assert.strictEqual(db.locks.size, 0, 'a refused order leaves no lock');
  }
  const db = makeDb(), ex = makeExchange(db, { market: { close_time: iso(NOW + 100000) } });     // the fresh read says 100 s left though the quote said 500
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'the fresh market read decides the time, not the list');
};
gates['a latched or killed strategy sends nothing: a stored latch, an unreadable latch document and a losing streak'] = async () => {
  let db = makeDb(); db.latches.TESTA = { killedAt: NOW - 1000, reason: 'x' }; let ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0);
  db = makeDb(); ex = makeExchange(db); let t = tickArgs(db, ex); t.args.store.killLatches = async () => { throw new Error('down'); };
  await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0, 'an unreadable latch kills');
  db = makeDb(); for (let i = 0; i < 3; i++) db.slot.set('l' + i, slotOrder({ id: 'l' + i, ticker: 'KXBTC15M-26NOV021015-15', step: 1, status: 'filled', settled: true, result: 'exit', settledPnl: -1, exitCount: 4, ts: NOW - 86400000 + i * 1000, settledAt: NOW - 86400000 + i * 1000 }));
  ex = makeExchange(db);
  await R(ON()).runSlotTick(tickArgs(db, ex).args); assert.strictEqual(ex.posts.length, 0, 'three losses in a row');
};

// ---- Exits --------------------------------------------------------------------------------------------------------------------------------
gates['exits before settlement: the stop, the target and the time exit each sell; a bid between them with time to spare holds'] = async () => {
  for (const [bid, ask, closeIn, sells] of [[0.35, 0.37, 400, true], [0.96, 0.97, 400, true], [0.60, 0.62, 80, true], [0.60, 0.62, 400, false], [0.41, 0.43, 400, false]]) {
    const w = exitWorld({ ex: { market: { yes_bid_dollars: bid.toFixed(4), yes_ask_dollars: ask.toFixed(4), close_time: iso(NOW + closeIn * 1000) } } });
    await w.runner.runSlotExits(w.args);
    assert.strictEqual(w.ex.posts.length, sells ? 1 : 0, 'bid ' + bid + ' with ' + closeIn + ' s left');
  }
  // A market that is closed or has no quote is left to settle.
  for (const mk of [{ status: 'closed' }, { yes_bid_dollars: '0.0000', yes_ask_dollars: '0.0100' }, { close_time: iso(NOW - 1000) }]) {
    const w = exitWorld({ ex: { market: Object.assign({ yes_bid_dollars: '0.2000', yes_ask_dollars: '0.2200' }, mk) } }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0, JSON.stringify(mk));
  }
};
gates['an exit is an immediate-or-cancel close of the right side, sized to the order, recorded as a realised result the shared stop sees'] = async () => {
  const w = exitWorld({ ex: { avg: '0.3500', fill: '4.00' } });
  const out = await w.runner.runSlotExits(w.args);
  assert.strictEqual(w.ex.posts.length, 1, JSON.stringify(out));
  const b = w.ex.posts[0];
  assert.strictEqual(b.time_in_force, 'immediate_or_cancel'); assert.strictEqual(b.side, 'ask', 'a YES long is closed by a YES sell'); assert.strictEqual(b.count, '4'); assert.strictEqual(b.client_order_id, 'SX-TESTA-' + T + '-1-1');
  assert.ok(!b.client_order_id.startsWith('X-') && !b.client_order_id.startsWith('FLAT-'), 'never an L1 or Flatten id');
  const d = w.db.slot.get(slotOrder().id);
  assert.strictEqual(d.settled, true); assert.strictEqual(d.result, 'exit'); assert.strictEqual(d.settledAt, NOW); assert.strictEqual(d.exitStatus, 'sold'); assert.ok(d.settledPnl < 0, 'a stop-out is a loss: ' + d.settledPnl);
  const risk = slot.slotRiskForBotRisk([d], 0); assert.ok(risk.net < 0 && risk.openCost === 0, 'the loss is counted the minute it is sold');
  // A NO position is closed by a YES buy back.
  const n = exitWorld({ order: { side: 'no' }, ex: { market: { yes_bid_dollars: '0.6300', yes_ask_dollars: '0.6500' }, positions: { [T]: -4 } } });
  await n.runner.runSlotExits(n.args);
  assert.strictEqual(n.ex.posts.length, 1); assert.strictEqual(n.ex.posts[0].side, 'bid');
};
gates['SW13 the close lease is taken BEFORE the position is read, and released after, only if held by the slot'] = async () => {
  const w = exitWorld();
  await w.runner.runSlotExits(w.args);
  const e = w.db.events, claim = e.indexOf('X:claimClose'), posRead = e.findIndex((x) => x.startsWith('GET /portfolio/positions')), post = e.findIndex((x) => x.startsWith('POST'));
  assert.ok(claim >= 0 && claim < posRead && posRead < post, 'claim, then position, then sell: ' + e.join(' > '));
  assert.ok(e.indexOf('X:releaseClose') > post, 'released after the sale'); assert.strictEqual(w.db.closing.size, 0, 'nothing is left held');
  // Flatten holds it: nothing is read or sold.
  const f = exitWorld({ closing: { [T]: { by: 'flatten', at: NOW - 1000 } } });
  await f.runner.runSlotExits(f.args);
  assert.strictEqual(f.ex.posts.length, 0); assert.ok(!f.db.events.some((x) => x.startsWith('GET /portfolio/positions')), 'no position read without the lease');
  assert.strictEqual(f.db.closing.get(T).by, 'flatten', 'and the slot did not touch the other closer\'s lease');
  // A claim that cannot be made sells nothing.
  const g = exitWorld(); g.store.claimClose = async () => { throw new Error('down'); }; await g.runner.runSlotExits(g.args); assert.strictEqual(g.ex.posts.length, 0);
  // The lease is released even when the sale was refused.
  const h = exitWorld({ ex: { post: { status: 400, body: 'no' } } }); await h.runner.runSlotExits(h.args); assert.strictEqual(h.db.closing.size, 0);
  // A failed release does not change the result of the sale.
  const i = exitWorld(); i.store.releaseClose = async () => { throw new Error('down'); }; await i.runner.runSlotExits(i.args); assert.strictEqual(i.ex.posts.length, 1);
};
gates['SW10 the slot sells only its own contracts: L1 and other slot steps are left alone, and a short account sells less'] = async () => {
  // The account holds L1 3 + slot 4 = 7: the slot sells 4, not 7.
  let w = exitWorld({ l1: [l1Order({ count: 3, fillCount: '3' })], ex: { positions: { [T]: 7 }, fill: '4.00' } });
  await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts[0].count, '4');
  // The account holds fewer than the sum (a hand sale): the slot sells holding - L1.
  w = exitWorld({ l1: [l1Order({ count: 3, fillCount: '3' })], ex: { positions: { [T]: 5 } } });
  await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts[0].count, '2');
  // The account holds only what L1 holds: the slot sells nothing. That can be a passing state (two reads that are not atomic), so it is NOT written as "skipped" for good: the next pass looks again.
  w = exitWorld({ l1: [l1Order({ count: 3, fillCount: '3' })], ex: { positions: { [T]: 3 } } });
  await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0); assert.notStrictEqual(w.db.slot.get(slotOrder().id).exitStatus, 'skipped');
  // ...and once the others' sale is booked (the position and the books agree again) it sells its own contracts.
  w.ex.positions[T] = 7; w.db.l1.set('L1-' + T, l1Order({ count: 3, fillCount: '3' })); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 1);
  // A clean read that shows NONE of this side is permanent: skipped.
  w = exitWorld({ ex: { positions: { [T]: 0 } } });
  await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0); assert.strictEqual(w.db.slot.get(slotOrder().id).exitStatus, 'skipped');
  // Another slot step on the same side counts as someone else's.
  w = exitWorld({ extraSlot: [slotOrder({ id: 'S-TESTA-' + T + '-2', step: 2, fillCount: '4' })], ex: { positions: { [T]: 6 } } });
  await w.runner.runSlotExits(w.args); assert.ok(w.ex.posts.length >= 1); assert.strictEqual(w.ex.posts[0].count, '2', 'min(own 4, 6 held - 4 of the other step), never the 4 it owns');
  // Opposite side held, or nothing held: a sell here would OPEN the opposite position.
  for (const held of [-4, 0]) { w = exitWorld({ ex: { positions: { [T]: held } } }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0, 'held ' + held); }
  // Unreadable position, unreadable other orders.
  w = exitWorld({ ex: { posStatus: 500 } }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0);
  w = exitWorld(); w.store.l1OrdersOnTicker = async () => { throw new Error('down'); }; await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0);
  w = exitWorld(); w.store.slotOrdersOnTicker = async () => 'junk'; await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0);
  // Orders it must never sell: settled, hand-closed, errored, unfilled, already sold.
  for (const o of [{ settled: true, result: 'hand' }, { status: 'error' }, { status: 'no fill', fillCount: '0' }, { exitStatus: 'sold' }, { settled: true, result: 'yes', settledPnl: 1 }]) {
    w = exitWorld({ order: o }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0, JSON.stringify(o));
  }
  // An L1 order is never touched by this engine.
  w = exitWorld({ order: null, l1: [l1Order()] }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 0);
  // A partly sold order sells only the rest.
  w = exitWorld({ order: { exitCount: 3, exitProceeds: 1, exitStatus: 'partly sold', exitTries: 1 }, ex: { positions: { [T]: 1 }, fill: '1.00' } }); await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts[0].count, '1'); assert.strictEqual(w.ex.posts[0].client_order_id, 'SX-TESTA-' + T + '-1-2');
};
gates['two exit loops at once send one sell (the exit is claimed on the order atomically)'] = async () => {
  const w = exitWorld(); const w2 = { ...w, store: makeStore(w.db, 'Y') };
  await Promise.all([w.runner.runSlotExits(w.args), w.runner.runSlotExits({ ...w.args, store: w2.store })]);
  assert.strictEqual(w.ex.posts.length, 1);
};
gates['SW12b a lost answer on a sell ends the session, latches the strategy and is never retried'] = async () => {
  for (const o of [{ post: { status: 503, body: 'x' } }, { throwPost: true }]) {
    const w = exitWorld({ ex: o });
    const out = await w.runner.runSlotExits(w.args);
    assert.strictEqual(out.ended, true); assert.strictEqual(w.sess.active, false); assert.strictEqual(w.db.slot.get(slotOrder().id).exitStatus, 'unknown'); assert.ok(w.db.latches.TESTA);
    await w.runner.runSlotExits(w.args); assert.strictEqual(w.ex.posts.length, 1, 'never retried');
    assert.strictEqual(w.db.closing.size, 0, 'and the lease is not left behind to stall L1\'s stop');
  }
  const r = exitWorld({ ex: { post: { status: 400, body: 'bad' } } });
  await r.runner.runSlotExits(r.args); assert.strictEqual(r.db.slot.get(slotOrder().id).exitStatus, 'error'); assert.strictEqual(r.sess.active, true, 'a plain refusal does not end the session');
  for (let i = 0; i < 4; i++) await r.runner.runSlotExits(r.args);
  assert.strictEqual(r.ex.posts.length, 3, 'a refused exit is tried at most three times');
  const c = exitWorld({ ex: { post: { status: 409, body: 'exists' } } });
  await c.runner.runSlotExits(c.args); assert.strictEqual(c.db.slot.get(slotOrder().id).exitStatus, 'unknown'); assert.ok(c.db.latches.TESTA);
};
gates['with the server switch off an exit is only logged, once, and the account is not touched'] = async () => {
  const w = exitWorld(); w.args.enabled = false;
  await w.runner.runSlotExits(w.args); await w.runner.runSlotExits(w.args);
  assert.strictEqual(w.ex.posts.length, 0); assert.ok(w.db.slot.get(slotOrder().id).exitShadow); assert.strictEqual(w.events.filter((e) => /log only/.test(e.kind)).length, 1);
  assert.strictEqual(w.ex.calls.filter((c) => c.url.includes('/portfolio/')).length, 0); assert.strictEqual(w.db.closing.size, 0);
  for (const v of [undefined, null, 'on', 1]) { const x = exitWorld(); x.args.enabled = v; await x.runner.runSlotExits(x.args); assert.strictEqual(x.ex.posts.length, 0, String(v)); }
};
gates['a kill rule tripped by an exit latches the strategy in the same write that records the result'] = async () => {
  const w = exitWorld({ flags: ON({ killRules: { maxConsecutiveLosses: 1, minNet: { afterFills: 20, net: -3 } } }), order: { ts: NOW - 300000 } });
  await w.runner.runSlotExits(w.args);
  assert.strictEqual(w.ex.posts.length, 1); assert.ok(w.db.latches.TESTA && /loss/.test(w.db.latches.TESTA.reason), JSON.stringify(w.db.latches));
  assert.ok(!w.db.events.includes('X:killStrategy'), 'it went through the one finishing write, not a second write after it');
  // The latch then blocks the next entry.
  const ex = makeExchange(w.db, { positions: {} });
  const t = tickArgs(w.db, ex); t.args.shared = SHARED(); t.args.now = NOW + 2000000; t.args.quotes = QUOTES({ ticker: 'KXBTC15M-26NOV031100-15', close_time: iso(NOW + 2500000) }); ex.market.ticker = 'KXBTC15M-26NOV031100-15'; ex.market.close_time = iso(NOW + 2500000);
  await R(ON({ killRules: { maxConsecutiveLosses: 1, minNet: { afterFills: 20, net: -3 } } })).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 0, 'killed');
};
gates['an order whose strategy is no longer registered still gets the fallback exits: a fixed stop and out before the close, and no target'] = async () => {
  for (const [bid, ask, closeIn, sells] of [[0.20, 0.22, 400, true], [0.60, 0.62, 400, false], [0.99, 0.99, 400, false], [0.60, 0.62, 50, true], [0.60, 0.62, 80, false]]) {
    const w = exitWorld({ order: { slotId: 'GONE' }, ex: { market: { yes_bid_dollars: bid.toFixed(4), yes_ask_dollars: ask.toFixed(4), close_time: iso(NOW + closeIn * 1000) } } });
    await w.runner.runSlotExits(w.args);
    assert.strictEqual(w.ex.posts.length, sells ? 1 : 0, 'bid ' + bid + ' with ' + closeIn + ' s left');
  }
};
gates['SW-ORPHAN turning the slot off, or deleting the strategy, with a live slot position still exits it, settles it and keeps it in the shared stop'] = async () => {
  // Entries are OFF (enabled false) but a slot order has been used: the registry is still there, and so is an order that is down through its stop.
  const off = { enabled: false, registry: [GOOD()], everUsed: true };
  let w = exitWorld({ flags: off });
  await w.runner.runSlotExits(w.args);
  assert.strictEqual(w.ex.posts.length, 1, 'the stop still fires with entries switched off');
  // The strategy was deleted entirely (empty registry): the fallback exit takes over.
  w = exitWorld({ flags: { enabled: false, registry: [], everUsed: true }, order: { slotId: 'GONE' }, ex: { market: { yes_bid_dollars: '0.2000', yes_ask_dollars: '0.2200' } } });
  await w.runner.runSlotExits(w.args);
  assert.strictEqual(w.ex.posts.length, 1, 'the fallback stop still fires with no strategy');
  // The settle sweep still settles it.
  w = exitWorld({ flags: { enabled: false, registry: [], everUsed: true }, order: { slotId: 'GONE', side: 'yes' }, ex: { market: { result: 'no' } } });
  const sw = await w.runner.runSlotSettle({ store: w.store, fetchFn: w.ex.fetchFn, keyId: 'k', pem, now: NOW });
  assert.strictEqual(sw.settled, 1, JSON.stringify(sw));
  assert.strictEqual(await R({ enabled: false, registry: [], everUsed: true }).slotExitIdle({ store: exitWorld().store, now: NOW }), false, 'and the exit loop is not idle while the order is open');
  // Never used and off: nothing is read at all (the shipped state).
  const trap = new Proxy({}, { get: () => { throw new Error('touched'); } });
  assert.deepStrictEqual((await R({ enabled: false, registry: [] }).runSlotExits({ store: trap, now: NOW })).skipped, 'no slot strategy');
  // Entries stay closed while only watching.
  const db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
  await R(off).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 0, 'watching is not entering'); assert.strictEqual(db.slot.size, 0);
};
gates['SW-HEDGE a hedge made by an old revision (an L1 order that never read the lock) is sold out of by the slot on its next exit pass, and the strategy is latched off'] = async () => {
  const db = makeDb();
  // The slot (NO) enters first through the lock...
  const ex = makeExchange(db, { positions: {}, market: { yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600' } });   // the favourite is NO at 0.76
  const t = tickArgs(db, ex);
  await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 1, 'the slot NO entry went out'); const slotId = [...db.slot.keys()][0]; assert.strictEqual(db.slot.get(slotId).side, 'no');
  // ...then an old instance creates its L1 YES order with a bare create (what origin/main's createTest does: no lock read, no slot read).
  db.l1.set('L1-' + T, l1Order({ side: 'yes', ts: NOW - 500 }));
  const w = { db, ex, store: makeStore(db, 'X'), sess: { active: true }, events: [] };
  ex.positions[T] = -4;          // the account really is net short here: the slot's NO (the L1 YES is in flight)
  ex.market.yes_bid_dollars = '0.6500'; ex.market.yes_ask_dollars = '0.6700';     // NO is NOT near its stop: only the hedge can make it sell
  const runner = R(ON());
  await runner.runSlotExits({ store: w.store, fetchFn: ex.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async (p) => Object.assign(w.sess, p), logEvent: async (e) => w.events.push(e) });
  assert.strictEqual(ex.posts.length, 2, 'the slot sold its contracts: ' + JSON.stringify(ex.posts.slice(1)));
  assert.strictEqual(db.slot.get(slotId).exitWhy, 'hedge'); assert.ok(db.latches.TESTA, 'the strategy is latched off');
  // The same trade without the opposite L1 order holds.
  const db2 = makeDb(), ex2 = makeExchange(db2, { positions: {}, market: { yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600' } });
  await R(ON()).runSlotTick(tickArgs(db2, ex2).args);
  ex2.positions[T] = -4; ex2.market.yes_bid_dollars = '0.3300'; ex2.market.yes_ask_dollars = '0.3500';
  await R(ON()).runSlotExits({ store: makeStore(db2, 'X'), fetchFn: ex2.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async () => {} });
  assert.strictEqual(ex2.posts.length, 1, 'no hedge, no sale');
  // The same side as L1 is not a hedge.
  const db3 = makeDb(), ex3 = makeExchange(db3, { positions: {} });
  await R(ON()).runSlotTick(tickArgs(db3, ex3).args);
  db3.l1.set('L1-' + T, l1Order({ side: 'yes' })); ex3.positions[T] = 5; ex3.market.yes_bid_dollars = '0.6500'; ex3.market.yes_ask_dollars = '0.6700';
  await R(ON()).runSlotExits({ store: makeStore(db3, 'X'), fetchFn: ex3.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async () => {} });
  assert.strictEqual(ex3.posts.length, 1, 'same side: nothing sold');
};
gates['SW-CLOCK an entry is judged on the clock at commit time: a minute that ran long sends nothing, and a window that closed while it ran is refused'] = async () => {
  // 20 s into a window that is 305 s from its floor... the strategy needs room: leftMinSec 300 vs exit floor 90.
  let db = makeDb(), ex = makeExchange(db), t = tickArgs(db, ex);
  t.args.clock = () => NOW + 25000;        // 25 s after the minute began
  await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 0, 'too stale'); assert.strictEqual(db.locks.size, 0); assert.strictEqual(db.slot.size, 0);
  // The market has 305 s left at the start of the minute and 295 s at the commit: outside leftMinSec 300.
  db = makeDb(); ex = makeExchange(db, { market: { close_time: iso(NOW + 305000) } }); t = tickArgs(db, ex, { args: { quotes: QUOTES({ close_time: iso(NOW + 305000) }) } });
  t.args.clock = () => NOW + 10000;
  await R(ON()).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 0, 'the entry window closed while the minute ran'); assert.strictEqual(db.slot.size, 0);
  // The control: the same market with a prompt clock trades.
  db = makeDb(); ex = makeExchange(db, { market: { close_time: iso(NOW + 305000) } }); t = tickArgs(db, ex, { args: { quotes: QUOTES({ close_time: iso(NOW + 305000) }) } });
  t.args.clock = () => NOW + 1000;
  await R(ON()).runSlotTick(t.args); assert.strictEqual(ex.posts.length, 1);
  // A strategy whose entry window ends too close to its exit floor never enters.
  db = makeDb(); ex = makeExchange(db); t = tickArgs(db, ex);
  const out = await R(ON({ exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 290 } })).runSlotTick(t.args);
  assert.strictEqual(ex.posts.length, 0); assert.ok(/too close to its exit floor/.test(JSON.stringify(out)), JSON.stringify(out));
};
gates['SW-LOST-ANSWER a database failure while writing the status of a lost-answer order still latches the strategy off and ends the session (entry and exit)'] = async () => {
  // Entry: the answer is lost, then the status write throws.
  let db = makeDb(), ex = makeExchange(db, { post: { status: 503, body: 'x' } }), t = tickArgs(db, ex);
  t.args.store.updateSlotOrder = async () => { throw new Error('firestore blip'); };
  let out = await R(ON()).runSlotTick(t.args);
  assert.strictEqual(out.ended, 'attempted'); assert.strictEqual(t.sess.active, false); assert.ok(db.latches.TESTA, 'latched');
  // Exit: the sell answer is lost, then the status write throws.
  const w = exitWorld({ ex: { post: { status: 503, body: 'x' } } });
  w.store.updateSlotOrder = async (id, p) => { if (p.exitStatus === 'unknown') throw new Error('firestore blip'); Object.assign(w.db.slot.get(id), p); };
  out = await w.runner.runSlotExits(w.args);
  assert.strictEqual(out.ended, true); assert.strictEqual(w.sess.active, false); assert.ok(w.db.latches.TESTA);
};
gates['the exit loop is idle only when no slot order is open, and an unreadable store is not idle'] = async () => {
  const w = exitWorld({ order: null }); assert.strictEqual(await w.runner.slotExitIdle({ store: w.store, now: NOW }), true);
  const x = exitWorld(); assert.strictEqual(await x.runner.slotExitIdle({ store: x.store, now: NOW }), false);
  x.store.slotRecentFilled = async () => { throw new Error('down'); }; assert.strictEqual(await x.runner.slotExitIdle({ store: x.store, now: NOW }), false);
  assert.strictEqual(await R({ enabled: false, registry: [GOOD()] }).slotExitIdle({ store: x.store, now: NOW }), true, 'off is idle');
};
gates['unsoldOf reads in-flight and unreadable orders as holding everything (the conservative way for the other engine)'] = () => {
  assert.strictEqual(run.unsoldOf(l1Order({ count: 3, fillCount: '3' })), 3);
  assert.strictEqual(run.unsoldOf(l1Order({ count: 3, fillCount: '3', exitCount: 2 })), 1);
  assert.strictEqual(run.unsoldOf(l1Order({ status: 'sending', fillCount: '0', count: 2 })), 2);
  assert.strictEqual(run.unsoldOf(l1Order({ status: 'unknown', fillCount: '0', count: 2 })), 2);
  assert.strictEqual(run.unsoldOf(l1Order({ settled: true })), 0); assert.strictEqual(run.unsoldOf(l1Order({ status: 'no fill', fillCount: '0' })), 0); assert.strictEqual(run.unsoldOf(null), 0);
};

// ---- The file itself ---------------------------------------------------------------------------------------------------------------------
gates['the engine file has no environment, randomness, timers or Firestore, requires only the three libraries, and exposes no switch'] = () => {
  const c = code(runSrc);
  assert.ok(!/process\.env|Math\.random|setTimeout|setInterval|getFirestore|firebase|\.collection\(|eval\(|child_process|\bfs\b/.test(c));
  assert.deepStrictEqual([...c.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ['"./kalshiSignalLib"', '"./kalshiSlotLib"', '"./kalshiLiveLib"']);
  assert.ok(!/portfolio\/events\/orders/.test(c), 'the order path lives with the other order code');
  assert.strictEqual((c.match(/method: "POST"/g) || []).length, 2, 'two places send an order: the entry and the exit');
  assert.ok(!/time_in_force/.test(c), 'the order bodies come only from liveOrderBody and exitBody, which are immediate-or-cancel');
  assert.ok(!/_testForce|SLOT_ENABLED\s*=|enabled:\s*true/.test(c));
  assert.ok(/store\.halted\(\)[\s\S]*store\.runSlotEntry/.test(c), 'the halt is read again right before the order is recorded');
  assert.ok(c.indexOf('store.runSlotEntry(') < c.indexOf('method: "POST"'), 'the order document is created before the buy is sent');
  const exits = c.slice(c.indexOf('async function runSlotExits'));
  assert.ok(exits.indexOf('live.claimClose(') > 0 && exits.indexOf('live.claimClose(') < exits.indexOf('/portfolio/positions'), 'the lease comes before the position read');
  assert.ok(exits.indexOf('/portfolio/positions') < exits.indexOf('method: "POST"'), 'the position is read before anything is sold');
  assert.ok(!/side: "(bid|ask)"/.test(c), 'no hand-built order side');
  assert.strictEqual(Object.keys(run).sort().join(), ['EXIT_LOOKBACK_MS', '_testOnly', 'runSlotExits', 'runSlotSettle', 'runSlotTick', 'slotExitIdle', 'unsoldOf'].sort().join());
  assert.strictEqual(typeof run.runSlotTick, 'function');
};
gates['the engine is wired only into functions/index.js (behind SLOT_ON, step B3): nothing else imports it'] = () => {
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (['node_modules', '.git', 'data'].includes(e.name) || e.isSymbolicLink() ? [] : e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));
  for (const f of walk(root).filter((x) => /\.(js|json|yml|yaml|sh|html)$/.test(x) && !/[\\/]test[\\/]|kalshiSlotRunLib\.js$|functions[\\/]index\.js$/.test(x))) assert.ok(!/kalshiSlotRunLib/.test(fs.readFileSync(f, 'utf8')), path.relative(root, f) + ' must not import the engine');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 8).join(' | ') : e)); }
  }
  process.exit(failed ? 1 : 0);
})();
