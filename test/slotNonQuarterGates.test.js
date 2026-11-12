'use strict';
// SN1 to SN12: the non-15-minute order path (Nov 12, 2026, SPREADCELL; docs/probes/PROBE_SPEC_SPREADCELL.md). Consequence if these fail: a sports market could be bought without the owner naming it,
// a second order could go out for one game, a held order could be sold at 25c or fall out of the loss stop after 24 hours, a refusal could end the whole session, or the switch could be flipped by
// something stored. The switch is OFF: nothing here makes a real call. The switch is forced on ONLY inside this file, through the test-only registry view.
const assert = require('assert');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const root = path.join(__dirname, '..');
const read = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const C = slot.SLOT_PROBE_CANDIDATES.find((x) => x.id === 'SPREADCELL');
const NOW = Date.parse('2026-11-12T15:00:00Z');
const SCHED = NOW + 40 * 3600 * 1000, CLOSE = SCHED + 2 * 24 * 3600 * 1000;           // 40 hours to the game; the market closes two days later
const T = 'KXNBASPREAD-26NOV14LALDEN-LAL5', T2 = 'KXNBASPREAD-26NOV14LALDEN-LAL8', T3 = 'KXNHLSPREAD-26NOV14EDMNYR-EDM2';
const NAMED = [T, T2, T3];
const ON = { enabled: true, registry: [C], everUsed: true };
const W = (i) => slot._testOnly.slotOrderCheckWith(ON, i);
const input = (extra) => Object.assign({ strategyId: 'SPREADCELL', ticker: T, side: 'yes', limit: 0.1, step: 1, depthAtTouch: 1000, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 800, windowCapFraction: 0.055, killLatch: null, secondsLeft: 40 * 3600, shardKnown: true, now: NOW }, extra || {});
const gates = {};
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
function world(o = {}) {
  const db = { slot: new Map(), locks: new Map(), latches: {}, queue: Promise.resolve() };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  const clone = (x) => JSON.parse(JSON.stringify(x));
  for (const t of o.slotOrders || []) db.slot.set(t.id, clone(t));
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; },
    async killLatches() { return clone(db.latches); }, async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
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
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); }, async killStrategy(id, info) { db.latches[id] = clone(info); },
  };
  const m = Object.assign({ ticker: T, status: 'active', close_time: iso(CLOSE), expected_expiration_time: iso(SCHED), yes_bid_dollars: '0.0800', yes_ask_dollars: '0.1000', yes_bid_size_fp: '500.00', yes_ask_size_fp: '500.00', exchange_index: 1 }, o.market || {});
  const calls = [], posts = [], skips = [], asked = [];
  const fetchFn = async (url, init) => {
    calls.push(init.method + ' ' + url.replace(/^.*\/trade-api\/v2/, '').split('?')[0]);
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (url.includes('/orderbook')) return reply(404, {});
    if (url.includes('/markets/')) return reply(200, { market: m });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return (o.post ? reply(o.post, { error: 'x' }) : reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: '0.1000' })); }
    throw new Error('unexpected ' + url);
  };
  const args = { session: { active: true }, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, clock: () => NOW + 1500,
    quotes: o.quotes || [{ series: 'KXNBASPREAD', m }], setSession: async () => {}, logEvent: async () => {}, recordSkip: async (d) => { skips.push(d); },
    shared: { sizeBase: 800, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -96, recentList: [], slotOrders: [], since: NOW - 24 * 3600 * 1000 } };
    return { db, calls, posts, skips, asked, args };
}
const ENG = (extra) => run._testOnly.makeRunners(Object.assign({}, ON, { named: NAMED }, extra || {}));
const mk = (ticker, bid, ask, extra) => ({ series: ticker.split('-')[0], m: Object.assign({ ticker, status: 'active', close_time: iso(CLOSE), expected_expiration_time: iso(SCHED), yes_bid_dollars: bid, yes_ask_dollars: ask, yes_bid_size_fp: '500.00', yes_ask_size_fp: '500.00', exchange_index: 1 }, extra || {}) });
const own = (ticker, extra) => Object.assign({ id: 'S-SPREADCELL-' + ticker + '-1', clientOrderId: 'S-SPREADCELL-' + ticker + '-1', strategy: 'SLOT', slotId: 'SPREADCELL', ticker, side: 'yes', step: 1, count: 1, limit: 0.1, maxCost: 0.17, ts: NOW - 3600000, status: 'filled', fillCount: 1, settled: false, settledPnl: null, exitCount: 0, exitProceeds: 0 }, extra || {});

gates['SN1 OFF by default: the switch is a literal false, the registry and hold list are what they were, no market is named, the production gate refuses, and nothing is read or sent'] = async () => {
  assert.strictEqual(slot.SLOT_PROBE_SWITCH.SPREADCELL, false);
  assert.ok(Object.isFrozen(slot.SLOT_PROBE_SWITCH) && Object.isFrozen(C) && Object.isFrozen(C.entry) && Object.isFrozen(slot.SLOT_HORIZON_NAMED) && Object.isFrozen(slot.SLOT_HORIZON_NAMED.SPREADCELL));
  assert.deepStrictEqual(slot.SLOT_HORIZON_NAMED.SPREADCELL, [], 'no market is named, so none can trade');
  assert.deepStrictEqual(slot.SLOT_STRATEGIES.map((x) => x.id), ['OICORE', 'EVENT830']);
  assert.deepStrictEqual(slot.SLOT_HOLD_ALLOWED, ['OICORE', 'EVENT830']);
  assert.ok(!slot.activeSlotStrategies().some((x) => x.id === 'SPREADCELL'));
  assert.ok(/not in the registry/.test(slot.slotOrderCheck(input()).reasons[0]));
  assert.ok(/SLOT_PROBE_SWITCH = Object\.freeze\(\{ CFRTIBTC: false, SPREADCELL: false \}\);/.test(read('functions/kalshiSlotLib.js')));
  for (const now of [NOW, NOW + 60000 * 5, NOW + 123]) assert.deepStrictEqual(slot.slotHorizonSeriesDue(slot.activeSlotStrategies(), now), [], 'no listing read while off');
  // The production engine given spread quotes makes no call at all.
  const w = world({ quotes: [mk(T, '0.0800', '0.1000')] });
  const out = await run.runSlotTick(w.args);
  assert.strictEqual(w.calls.length, 0, 'no network call: ' + JSON.stringify(w.calls) + JSON.stringify(out)); assert.strictEqual(w.posts.length, 0); assert.strictEqual(w.db.slot.size, 0);
  assert.deepStrictEqual(slot.slotHorizonPick(slot.activeSlotStrategies()[0], [mk(T, '0.08', '0.10')], NOW), [], 'a 15 minute strategy never picks a spread market');
};

gates['SN2 the candidate is yes only, 5c to 14c, 1 contract, held, 24 to 48 hours before the scheduled time; the validator keeps every bound and keeps 15 minute and spread series apart'] = () => {
  assert.deepStrictEqual(slot.validateSlotStrategy(C), { ok: true, errors: [] });
  assert.strictEqual(C.entry.sideRule, 'yes'); assert.strictEqual(C.contractsPerOrder, 1); assert.deepStrictEqual(C.exit, { holdToSettle: true });
  assert.ok(C.entry.priceMin === 0.05 && C.entry.priceMax < 0.15 && C.entry.horizonMinSec === 86400 && C.entry.horizonMaxSec <= 259200);
  assert.deepStrictEqual([...C.series].sort(), ['KXMLBSPREAD', 'KXNBASPREAD', 'KXNCAAFSPREAD', 'KXNCAAMBSPREAD', 'KXNFLSPREAD', 'KXNHLSPREAD']);
  assert.ok(slot.SLOT_PROBE_BUDGET.SPREADCELL > 0 && slot.SLOT_PROBE_BUDGET.SPREADCELL <= 10 && slot.SLOT_PROBE_MAX_CONTRACTS === 1);
  const bad = (patch, entryPatch) => slot.validateSlotStrategy(Object.assign({}, C, patch || {}, entryPatch ? { entry: Object.assign({}, C.entry, entryPatch) } : {})).ok;
  assert.ok(!bad({ series: ['KXBTC15M'] }), 'a 15 minute series on a horizon entry');
  assert.ok(!bad({ series: ['KXNBASPREAD', 'KXBTC15M'] }));
  assert.ok(!bad({ series: ['KXNBAGAME'] }), 'an unlisted series');
  assert.ok(!bad({}, { sideRule: 'no' }) && !bad({}, { sideRule: 'cheap' }) && !bad({}, { priceMax: 0.2 }) && !bad({}, { priceMax: 0.16 }) && !bad({}, { priceMin: 0.01 }));
  assert.ok(!bad({}, { horizonMinSec: 3600 }) && !bad({}, { horizonMaxSec: 400000 }) && !bad({}, { closeTolSec: 99999999 }) && !bad({}, { extra: 1 }));
  assert.ok(!bad({ contractsPerOrder: 2 }) && !bad({ exit: { stopBid: 0.02, targetBid: 0.5, mustExitLeftSec: 60 } }) && !bad({ id: 'OTHERID' }) && !bad({ id: 'OICORE' }));
  assert.ok(!bad({ scaleIn: Object.assign({}, C.scaleIn, { maxSteps: 2 }) }));
  // A 15 minute entry cannot use a spread series, and a horizon-shaped entry cannot be given by a 15 minute id.
  const oi = slot.SLOT_STRATEGIES[0];
  assert.ok(!slot.validateSlotStrategy(Object.assign({}, oi, { series: ['KXNBASPREAD'] })).ok);
};

gates['SN3 tickers: only the six spread series in the strict shape pass the shape test, and only a ticker NAMED in code can trade (nothing is discovered)'] = () => {
  const re = slot.SLOT_HORIZON_TICKER_RE;
  for (const t of ['KXMLBSPREAD-26OCT031300CWSCLE-CLE2', 'KXNBASPREAD-26NOV01BKNIND-BKN10', 'KXNCAAFSPREAD-26NOV04CMUEMU-CMU10', 'KXNCAAMBSPREAD-26NOV02ARIZUCLA-UCLA24', 'KXNFLSPREAD-26NOV01ARIDAL-ARI10', 'KXNHLSPREAD-26NOV01EDMNYR-EDM2']) assert.ok(re.test(t), t);
  for (const t of ['KXBTC15M-26NOV121200-00', 'KXNBAGAME-26NOV01BKNIND-BKN', 'KXNBASPREAD-26NOV01BKNIND', 'kxnbaspread-26nov01bkn-bkn10', 'KXNBASPREAD-26NOV01BKNIND-BKN10-1', 'KXNBASPREAD-26NOV01BKNIND-', 'KXNBASPREAD-26NOV01 BKNIND-BKN10', 'XKXNBASPREAD-26NOV01BKNIND-BKN10']) assert.ok(!re.test(t), t);
  assert.ok(W(input()).allowed === false && /named in code/.test(W(input()).reasons[0]), 'the registry view without a named list refuses');
  assert.ok(slot._testOnly.slotOrderCheckWith(Object.assign({}, ON, { named: [T] }), input()).allowed);
  assert.ok(/named in code/.test(slot._testOnly.slotOrderCheckWith(Object.assign({}, ON, { named: [T] }), input({ ticker: T2 })).reasons[0]), 'a similar ticker that is not named is refused');
  assert.ok(/not a slot market ticker/.test(slot._testOnly.slotOrderCheckWith(Object.assign({}, ON, { named: ['KXBTC15M-26NOV121200-00'] }), input({ ticker: 'KXBTC15M-26NOV121200-00' })).reasons[0]), 'naming a 15 minute ticker does not make it a spread market');
};

const WN = (i) => slot._testOnly.slotOrderCheckWith(Object.assign({}, ON, { named: NAMED }), i);
gates['SN4 the gate: exactly one contract of YES at 5c to 14c, 24 to 48 hours before the scheduled time; wrong side, price, time, shard, a second order for the event, the open cap, the budget or the lock send nothing'] = () => {
  const ok = WN(input({ wanted: 5 }));
  assert.ok(ok.allowed && ok.count === 1, JSON.stringify(ok)); assert.strictEqual(ok.cid, 'S-SPREADCELL-' + T + '-1');
  const no = (extra, re) => { const r = WN(input(extra)); assert.ok(!r.allowed && (!re || re.test(r.reasons[0])), JSON.stringify(extra) + ' -> ' + r.reasons[0]); };
  no({ side: 'no' }); no({ limit: 0.16 }); no({ limit: 0.15 }); no({ limit: 0.04 });
  no({ secondsLeft: 86400 }, /time window/); no({ secondsLeft: 23 * 3600 }, /time window/); no({ secondsLeft: 172801 }, /time window/); no({ secondsLeft: null }); no({ secondsLeft: -5 });
  no({ shardKnown: false }, /shard/); no({ shardKnown: undefined }, /shard/);
  no({ slotOrders: [own(T, { status: 'no fill', fillCount: 0 })] }, /one order per event|already/);
  no({ ticker: T2, slotOrders: [own(T)] }, /one order per event/);
  const five = ['KXNHLSPREAD-26NOV14AAABBB-AAA2', 'KXNHLSPREAD-26NOV14CCCDDD-CCC2', 'KXNHLSPREAD-26NOV14EEEFFF-EEE2', 'KXNHLSPREAD-26NOV14GGGHHH-GGG2', 'KXNHLSPREAD-26NOV14IIIJJJ-III2'];
  assert.ok(WN(input({ slotOrders: five.slice(0, 4).map((t) => own(t, { maxCost: 0.1 })) })).allowed, 'four open is still room');
  no({ slotOrders: five.map((t) => own(t, { maxCost: 0.1 })) }, /open position cap/);
  no({ lock: { side: 'no', by: 'L1' } }); no({ lockTxn: false });
  // The budget: $10 lifetime, open counted as lost, sticky.
  const loss = (n) => Array.from({ length: n }, (_, i) => own('KXNHLSPREAD-26NOV0' + (i % 9 + 1) + 'ZZZ' + String.fromCharCode(65 + i % 26) + 'YY-AB' + i, { id: 'L' + i, ts: NOW - 7200000 - i * 1000, settled: true, result: 'no', settledPnl: -1 }));
  assert.ok(slot.probeState(C, loss(9)).spent === false && slot.probeState(C, loss(10)).spent === true, 'ten dollars of losses spend it');
  assert.ok(slot.probeState(C, loss(9).concat([own(T, { id: 'win', settled: true, result: 'yes', settledPnl: 5, ts: NOW - 1000 })])).spent === false);
  assert.ok(slot.probeState(C, loss(10).concat([own(T, { id: 'win2', settled: true, result: 'yes', settledPnl: 50, ts: NOW })])).spent === true, 'sticky after a later win');
  const o = WN(input({ slotOrders: loss(9) })); assert.ok(!o.allowed || o.cost <= 1.0 + 1e-9, 'the next order must fit in what is left');
};

gates['SN5 end to end: a named market in the window buys ONE contract of YES at the ask, immediate-or-cancel, with a fixed client order id; a second run, or another market of the same event, sends nothing'] = async () => {
  const q = [mk(T, '0.0800', '0.1000')];
  const w = world({ quotes: q, market: {} });
  const out = await ENG().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1, JSON.stringify(out));
  const b = w.posts[0];
  assert.strictEqual(Number(b.count), 1); assert.strictEqual(b.side, 'bid'); assert.strictEqual(b.time_in_force, 'immediate_or_cancel'); assert.ok(Math.abs(Number(b.price) - 0.1) < 1e-9);
  assert.strictEqual(b.client_order_id, 'S-SPREADCELL-' + T + '-1');
  const d = [...w.db.slot.values()][0];
  assert.ok(d.slotId === 'SPREADCELL' && d.count === 1 && d.side === 'yes' && d.maxCost < 0.2 && w.db.locks.get(T).by === 'SLOT:SPREADCELL', JSON.stringify(d));
  await ENG().runSlotTick(Object.assign({}, w.args, { now: NOW + 300000, clock: () => NOW + 301000 }));
  assert.strictEqual(w.posts.length, 1, 'one shot: nothing more for this market');
  // Another market of the same event, on a fresh run in the same books.
  const w2 = world({ quotes: [mk(T2, '0.1200', '0.1400')], slotOrders: [d] }); w2.args.quotes[0].m.ticker = T2;
  await ENG().runSlotTick(w2.args);
  assert.strictEqual(w2.posts.length, 0, 'one order per event');
  // The deterministic id: a second instance computing the same entry gets the same id.
  assert.strictEqual(slot.slotClientOrderId('SPREADCELL', T, 1), 'S-SPREADCELL-' + T + '-1');
};

gates['SN6 of an event\'s markets only the one nearest 50c inside the band is looked at; markets outside the band, the window, the status or not named are never picked'] = () => {
  const s = C, pick = (q) => slot.slotHorizonPick(s, q, NOW, NAMED);
  const a = mk(T, '0.0800', '0.1000'), b = mk(T2, '0.1200', '0.1400');
  assert.deepStrictEqual(pick([a, b]).map((x) => x.ticker), [T2]);
  assert.deepStrictEqual(pick([b, a]).map((x) => x.ticker), [T2]);
  assert.deepStrictEqual(pick([a, mk(T2, '0.3000', '0.3200')]).map((x) => x.ticker), [T], 'a market outside the band is not chosen even if nearer 50c');
  assert.deepStrictEqual(pick([a, mk(T3, '0.0600', '0.0800')]).map((x) => x.ticker).sort(), [T, T3].sort(), 'one per event, two events two picks');
  assert.deepStrictEqual(pick([mk(T, '0.0800', '0.1500')]), [], 'ask of 15c is outside');
  assert.deepStrictEqual(pick([mk(T, '0.0100', '0.0300')]), []);
  assert.deepStrictEqual(pick([mk(T, '0.1100', '0.1000')]), [], 'a crossed book');
  assert.deepStrictEqual(pick([mk(T, '0.0800', '0.1000', { status: 'closed' })]), []);
  assert.deepStrictEqual(slot.slotHorizonPick(s, [a], NOW, []), [], 'an unnamed market is never picked');
  assert.deepStrictEqual(slot.slotHorizonPick(s, [a], NOW), [], 'production list is empty');
  assert.deepStrictEqual(pick([a]).length, 1);
  assert.deepStrictEqual(slot.slotHorizonPick(s, [a], SCHED - 86400 * 1000), [], 'inside 24 hours of the scheduled time');
  assert.deepStrictEqual(slot.slotHorizonPick(s, [a], SCHED - 49 * 3600 * 1000), [], 'further than 48 hours');
};

gates['SN7 the look comes from the SCHEDULED time: expected_expiration_time, else occurrence_datetime; missing, past or far from close_time is no order, and close_time alone is never enough'] = async () => {
  const left = (m, now) => slot.slotHorizonLeft(C, m, now === undefined ? NOW : now);
  const base = { close_time: iso(CLOSE) };
  assert.strictEqual(left(Object.assign({ expected_expiration_time: iso(SCHED) }, base)), 40 * 3600);
  assert.strictEqual(left(Object.assign({ occurrence_datetime: iso(SCHED) }, base)), 40 * 3600, 'the fallback field');
  assert.strictEqual(left(Object.assign({ expected_expiration_time: iso(SCHED), occurrence_datetime: iso(SCHED - 20 * 3600 * 1000) }, base)), 40 * 3600, 'expected_expiration_time wins');
  assert.strictEqual(left(base), null, 'neither field: close_time alone is not enough');
  assert.strictEqual(left(Object.assign({ expected_expiration_time: 'soon' }, base)), null);
  assert.strictEqual(left(Object.assign({ expected_expiration_time: iso(NOW - 1000) }, base)), null, 'in the past');
  assert.strictEqual(left({ expected_expiration_time: iso(SCHED) }), null, 'no close_time');
  assert.strictEqual(left({ expected_expiration_time: iso(SCHED), close_time: iso(SCHED - 2 * 3600 * 1000) }), null, 'closes well before the scheduled time');
  assert.ok(left({ expected_expiration_time: iso(SCHED), close_time: iso(SCHED + C.entry.closeTolSec * 1000) }) !== null, 'at the tolerance');
  assert.strictEqual(left({ expected_expiration_time: iso(SCHED), close_time: iso(SCHED + C.entry.closeTolSec * 1000 + 1000) }), null, 'past the tolerance');
  // The window is measured from the scheduled time, not from a close two days later: the same market is out of the window by a close-based reading and in it by the scheduled one.
  assert.ok((CLOSE - NOW) / 1000 > C.entry.horizonMaxSec && slot.slotHorizonPick(C, [mk(T, '0.08', '0.10')], NOW, NAMED).length === 1);
  // End to end: a market with no scheduled time sends nothing and says why.
  const w = world({ quotes: [mk(T, '0.0800', '0.1000', { expected_expiration_time: undefined })], market: { expected_expiration_time: undefined } });
  await ENG().runSlotTick(w.args); assert.strictEqual(w.posts.length, 0); assert.strictEqual(w.calls.length, 0, 'it is not even a candidate, so nothing is read');
  // It passed the listing but the fresh read says the schedule moved: no order, a skip record.
  const w2 = world({ quotes: [mk(T, '0.0800', '0.1000')], market: { expected_expiration_time: iso(NOW + 3600000) } });
  await ENG().runSlotTick(w2.args); assert.strictEqual(w2.posts.length, 0); assert.ok(w2.skips.some((x) => x.reason === 'schedule_unusable'), JSON.stringify(w2.skips));
};

gates['SN8 the listing read: only for a registered horizon strategy that names a market, only on every 5th minute, and index.js adds it without any unconditional spread read'] = () => {
  const reg = [C], named = Object.freeze({ SPREADCELL: Object.freeze([T, T3]) });
  assert.deepStrictEqual(slot.slotHorizonSeriesDue(reg, 0), [], 'empty named list reads nothing');
  assert.deepStrictEqual(slot.slotHorizonSeriesDue([slot.SLOT_STRATEGIES[0]], 0), []);
  const idx = code(read('functions/index.js'));
  assert.ok(/slotLib\.slotHorizonSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)/.test(idx) && !/SPREAD/.test(idx), 'index.js names no spread series; the read is driven by the registry');
  assert.ok(/SLOT_HORIZON_LIST_EVERY_MIN = 5/.test(read('functions/kalshiSlotLib.js')));
};

gates['SN9 the loss stop and the budget: an open horizon order older than 24 hours still counts as lost; a settled old one does not; a 15 minute order is unchanged'] = () => {
  const old = NOW - 50 * 3600 * 1000, since = NOW - 24 * 3600 * 1000;
  const open = own(T, { ts: old }), settled = own(T2, { ts: old, id: 'x', settled: true, result: 'no', settledPnl: -0.17 });
  const r = slot.slotRiskForBotRisk([open], since);
  assert.ok(r.openCost > 0.1 && r.worst < -0.1, 'old and open still counts: ' + JSON.stringify(r));
  assert.strictEqual(slot.slotRiskForBotRisk([settled], since).worst, 0, 'old and settled is outside the window as before');
  const fifteen = own('KXBTC15M-26NOV121200-00', { slotId: 'OICORE', ts: old, id: 'y' });
  assert.strictEqual(slot.slotRiskForBotRisk([fifteen], since).worst, 0, 'other strategies are unchanged');
  assert.ok(slot.probeState(C, [open]).room < slot.probeState(C, []).room, 'the lifetime budget counts the open order as lost');
  assert.ok(slot.slotRiskContract([open], NOW).lifetime.worst < -0.1);
  // The shared loss stop inside the engine: an old open order leaves the new order less room.
  assert.ok(/SLOT_HORIZON_IDS\.includes\(t\.slotId\) && a\.openCost > 0/.test(read('functions/kalshiSlotLib.js')));
};

gates['SN10 no sell path: a horizon order is never sold by the slot exit pass, registered or not, at any bid'] = async () => {
  const sell = async (registry) => {
    const posts = [], claims = [];
    const order = own(T, { ts: NOW - 600000 });
    const store = { async slotRecentFilled() { return [order]; }, async l1OrdersOnTicker() { return []; }, async slotOrdersOnTicker() { return [order]; },
      async claimSlotExit() { claims.push(1); return true; }, async updateSlotOrder() {}, async killStrategy() {}, async releaseClose() {} };
    const fetchFn = async (url, init) => { const rep = (b) => ({ status: 200, text: async () => JSON.stringify(b) }); if (init.method === 'POST') { posts.push(1); return rep({}); }
      if (url.includes('/portfolio/positions')) return rep({ market_positions: [{ ticker: T, position: 1 }] }); return rep({ market: { ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.0100', yes_ask_dollars: '0.0300', exchange_index: 1 } }); };
    const eng = run._testOnly.makeRunners({ enabled: true, registry, everUsed: true });
    await eng.runSlotExits({ store, fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async () => {}, logEvent: async () => {} });
    return { posts, claims };
  };
  for (const reg of [[C], []]) { const r = await sell(reg); assert.strictEqual(r.posts.length, 0, 'registry ' + reg.length); assert.strictEqual(r.claims.length, 0); }
  const src = read('functions/kalshiSlotRunLib.js');
  assert.ok(/const held = !s && slotLib\.SLOT_HORIZON_IDS\.includes\(t\.slotId\)/.test(src));
  assert.ok(C.exit.holdToSettle === true && Object.keys(C.exit).length === 1, 'the entry has no stop, target or sell time');
};

gates['SN11 a refusal or an unknown shard stops only the probe: Kalshi\'s refusal switches SPREADCELL off without ending the session; a market with no shard sends nothing; a lost answer still ends the session'] = async () => {
  const w = world({ quotes: [mk(T, '0.0800', '0.1000')], post: 400 });
  const ended = []; w.args.setSession = async (p) => { ended.push(p); };
  await ENG().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1); assert.ok(w.db.latches.SPREADCELL, 'the probe is latched off'); assert.strictEqual([...w.db.slot.values()][0].status, 'error');
  assert.strictEqual(ended.length, 0, 'the session is not ended by a refused probe order');
  const n = world({ quotes: [mk(T, '0.0800', '0.1000', { exchange_index: undefined })], market: { exchange_index: undefined } });
  await ENG().runSlotTick(n.args); assert.strictEqual(n.posts.length, 0); assert.ok(n.skips.some((x) => x.reason === 'shard_unknown'), JSON.stringify(n.skips));
  const l = world({ quotes: [mk(T, '0.0800', '0.1000')], post: 503 }); const e2 = []; l.args.setSession = async (p) => { e2.push(p); };
  await ENG().runSlotTick(l.args); assert.ok(e2.some((p) => p.active === false), 'an ambiguous answer ends the session, as for every slot order');
  assert.ok(/shard/i.test(read('docs/probes/PROBE_SPEC_SPREADCELL.md')));
};

gates['SN12 nothing stored, requested or in the environment can switch it on or name a market; the docs say unproven, off, with kill, return and the activation order'] = () => {
  const lib = code(read('functions/kalshiSlotLib.js')), runSrc = code(read('functions/kalshiSlotRunLib.js')), idx = code(read('functions/index.js'));
  assert.ok(!/process\.env|firestore|fetch\(|\.get\(|data\(\)|request\.data|localStorage/.test(lib), 'the library is pure');
  assert.ok(!/SLOT_PROBE_SWITCH|SLOT_HORIZON_NAMED/.test(idx) && !/SLOT_PROBE_SWITCH|SLOT_HORIZON_NAMED|process\.env/.test(runSrc), 'the callers read neither the switch nor the named list');
  assert.ok(/flags === undefined \? undefined : flags\.named/.test(runSrc), 'the named list reaches the picker only through the test view');
  assert.ok(!/args\.named|args\.tickers|session\.named|request\.data/.test(runSrc));
  const spec = read('docs/probes/PROBE_SPEC_SPREADCELL.md');
  assert.ok(/UNPROVEN/.test(spec) && /OFF by default/i.test(spec) && /^## .*Kill/m.test(spec) && /^## .*Return/m.test(spec) && /popup/i.test(spec) && /W-SPREAD-CELL1/.test(spec) && /Activation checklist/i.test(spec) && /scheduled/i.test(spec));
  assert.ok(!/—/.test(spec) && !/—/.test(read('functions/kalshiSlotLib.js').split('Held-to-settlement markets')[1] || ''), 'no em dashes');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 5).join(' | ') : e)); }
  }
  process.exit(failed ? 1 : 0);
})();
