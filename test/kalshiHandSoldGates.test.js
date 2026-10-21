'use strict';
// A position the owner closes BY HAND (a manual sell, or Flatten) is not a trade the bot held to the end. Before this, settlement booked the market's result as the bot's win or loss, so a hand sale
// moved the stats, the loss stop and the profit pool by a figure the owner never got. Each gate states the consequence. Approach A (the owner's pick, 2026-10-20): a hand-closed order is left out of
// the bot's record, its loss stop and its pool, and the page says "sold by hand".
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-10-20T20:00:00Z');
const TS = NOW - 600000;                    // the bot bought ten minutes ago
const iso = (ms) => new Date(ms).toISOString();

function world({ result = 'no', fills = [], fillsStatus = 200, orders = {} } = {}) {
  const docs = new Map(Object.entries(orders));
  const calls = [];
  const store = {
    async openFilled() { return [...docs.entries()].filter(([, d]) => d.status === 'filled').map(([id, d]) => ({ id, ...d })); },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades() { return [...docs.entries()].map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url) => {
    calls.push(url);
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/fills')) return reply(fillsStatus, { fills });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'settled', result } });
    throw new Error('unexpected ' + url);
  };
  return { docs, calls, store, fetchFn, settle: () => live.settleOpenOrders({ store, fetchFn, nowMs: NOW, keyId: 'k', pem }), risk: () => live.botRisk({ store, since: 0, fetchFn, nowMs: NOW, keyId: 'k', pem, orders: [...docs.entries()].map(([id, d]) => ({ id, ...d })) }) };
}
const order = (over) => Object.assign({ strategy: 'L1', orderId: 'entry-1', ticker: 'KXBTC15M-T1', series: 'KXBTC15M', side: 'yes', count: 4, fillCount: '4', maxCost: 3.72, price: 0.93, status: 'filled', ts: TS, settled: false }, over || {});
const sell = (over) => Object.assign({ ticker: 'KXBTC15M-T1', side: 'yes', action: 'sell', count_fp: '4.00', order_id: 'hand-1', created_time: iso(TS + 120000) }, over || {});

const gates = {};

// A fully hand-closed position is settled as "hand": no profit figure, so nothing can count it as a win or a loss.
gates.H1 = async () => {
  const w = world({ result: 'no', fills: [sell()], orders: { a: order() } });
  await w.settle();
  const d = w.docs.get('a');
  assert.deepStrictEqual([d.settled, d.result, d.handSold], [true, 'hand', 4]);
  assert.ok(!('settledPnl' in d), 'no profit figure is invented for it, even though the market result (a loss for a YES) is known');
};

// The bot's own exit sell is not a hand sale; a hand sale that covers only what the bot did not sell is.
gates.H2 = async () => {
  const own = world({ result: 'no', fills: [sell({ order_id: 'exit-1' })], orders: { a: order({ exitOrderId: 'exit-1', exitCount: 4 }) } });
  await own.settle();
  assert.strictEqual(own.docs.get('a').result, 'no', 'the bot\'s own exit sell leaves the old rule in charge');
  const mix = world({ result: 'no', fills: [sell({ order_id: 'exit-1', count_fp: '2.00' }), sell({ count_fp: '2.00' })], orders: { a: order({ exitOrderId: 'exit-1', exitCount: 2 }) } });
  await mix.settle();
  assert.strictEqual(mix.docs.get('a').result, 'hand', 'the bot sold 2 and the owner sold the other 2: nothing was held to the end');
};

// A PARTLY sold position is left to the old rule: the rest was held, and hiding the rest of a loss from the loss stop is the unsafe direction.
gates.H3 = async () => {
  const w = world({ result: 'no', fills: [sell({ count_fp: '1.00' })], orders: { a: order() } });
  await w.settle();
  const d = w.docs.get('a');
  assert.deepStrictEqual([d.result, Number.isFinite(d.settledPnl) && d.settledPnl < 0], ['no', true], 'counted as held, so the loss is still seen');
};

// Fills that cannot be read: the order stays open (counted as lost by the loss stop) and is tried again, never settled on a guess.
gates.H4 = async () => {
  const w = world({ result: 'yes', fillsStatus: 500, orders: { a: order() } });
  const n = await w.settle();
  assert.strictEqual(w.docs.get('a').settled, false, 'left open');
  const risk = await w.risk();
  assert.ok(risk.openCost > 3.7 && risk.net < -3.7 + 1e-9 || risk.worst < -3.7, 'and counted against the loss stop meanwhile: ' + JSON.stringify(risk));
};

// The exit watch's "skipped" (it found nothing held when the price touched its line) is NOT proof of a hand sale: the market may simply have settled before it looked. Oct 21, 2026: it used to say hand, which hid
// that loss from the loss stop. Now it is no evidence at all: with no sale in the account's fills the order settles as the loss it was.
gates.H5 = async () => {
  const w = world({ result: 'no', orders: { a: order({ exitStatus: 'skipped' }) } });
  await w.settle();
  assert.strictEqual(w.docs.get('a').result, 'no', 'settled by the market result, not called hand');
  assert.ok(w.docs.get('a').settledPnl < 0, 'and the loss is on the record');
};

// Oct 21, 2026, the owner: "why are so many of these selling by hand? im not doing anything". Every NO order the bot bought was marked hand: Kalshi books a NO buy on the YES side (the order is sent as "ask"), so its own entry
// fill can read as action "sell", side "no", and looked like a sale of the whole position. The consequence was a NO loss that the stats, the loss stop and the pool never saw. The entry order's own fill is never a sale.
gates.H11 = async () => {
  const entry = sell({ side: 'no', order_id: 'entry-1', created_time: iso(TS + 1000) });      // the buy, as Kalshi reports it
  const w = world({ result: 'yes', fills: [entry], orders: { a: order({ side: 'no' }) } });         // the market went against a NO: a real loss
  await w.settle();
  const d = w.docs.get('a');
  assert.deepStrictEqual([d.result, d.settled], ['yes', true], 'settled by the market, not called hand');
  assert.ok(d.settledPnl < -3, 'and the whole loss is on the record: ' + d.settledPnl);
  const r = await world({ result: 'yes', fills: [entry], orders: { a: order({ side: 'no' }) } }).risk();
  assert.ok(r.net < -3, 'the loss stop sees it: ' + JSON.stringify(r));
};

// An order whose entry id was never saved cannot be told from a sale, so it is never called hand (a loss stays counted).
gates.H12 = async () => {
  const w = world({ result: 'no', fills: [sell()], orders: { a: order({ orderId: undefined }) } });
  await w.settle();
  assert.strictEqual(w.docs.get('a').result, 'no');
};

// The repair: orders the old check marked hand are asked again; the ones the owner did not sell are settled as what they were, a real hand sale stays hand and is not asked again.
gates.H13 = async () => {
  const wrong = order({ side: 'no', ticker: 'KXBTC15M-W', settled: true, result: 'hand', handSold: 4, ts: TS });
  const real = order({ ticker: 'KXBTC15M-R', settled: true, result: 'hand', handSold: 4, orderId: 'entry-2' });
  const docs = { w: wrong, r: real };
  const w = world({ result: 'yes', orders: docs, fills: [sell({ side: 'no', order_id: 'entry-1', ticker: 'KXBTC15M-W' }), sell({ ticker: 'KXBTC15M-R', order_id: 'hand-9' })] });
  w.store.handOrders = async () => [...w.docs.entries()].filter(([, d]) => d.result === 'hand').map(([id, d]) => ({ id, ...d }));
  const out = await w.settle();
  assert.strictEqual(out.repaired, 1);
  assert.deepStrictEqual([w.docs.get('w').result, w.docs.get('w').handRepaired], ['yes', true], 'the wrongly flagged NO is settled by the market');
  assert.ok(w.docs.get('w').settledPnl < -3, 'as the loss it was');
  assert.deepStrictEqual([w.docs.get('r').result, w.docs.get('r').handChecked], ['hand', true], 'a real hand sale stays hand and is marked checked');
  const again = await w.settle();
  assert.strictEqual(again.repaired, 0);
};

// Other sells do not count: another market side, a sell from before the order, a buy.
gates.H6 = async () => {
  const w = world({ result: 'yes', fills: [sell({ side: 'no' }), sell({ created_time: iso(TS - 3600000) }), sell({ action: 'buy' }), sell({ ticker: 'KXBTC15M-OTHER' })], orders: { a: order() } });
  await w.settle();
  assert.strictEqual(w.docs.get('a').result, 'yes', 'none of them is a hand sale of this position');
  assert.ok(Number.isFinite(w.docs.get('a').settledPnl) && w.docs.get('a').settledPnl > 0, 'it settles as the win it was');
};

// The loss stop's figures leave a hand-closed order out entirely (no net, no open cost), and a later look at the same order does the same.
gates.H7 = async () => {
  const w = world({ result: 'no', fills: [sell()], orders: { a: order(), b: order({ ticker: 'KXBTC15M-T2', ts: TS + 1000, settled: true, result: 'no', settledPnl: -3.72 }) } });
  const r = await w.risk();
  assert.ok(Math.abs(r.net - (-3.72)) < 1e-9 && r.openCost === 0, 'only the bot\'s own loss counts: ' + JSON.stringify(r));
  assert.strictEqual(w.docs.get('a').result, 'hand');
  const again = await w.risk();
  assert.ok(Math.abs(again.net - (-3.72)) < 1e-9 && again.openCost === 0, 'the same on the next look');
};

// The pool and savings pass a hand-closed order without a win, a loss or a stall behind it.
gates.H8 = () => {
  const mk = (id, ts, over) => Object.assign({ id, strategy: 'L1', ticker: 'T' + id, ts, fillCount: '4', maxCost: 3.72, settled: true, result: 'yes', settledPnl: 0.2, count: 4 }, over || {});
  const orders = [mk('a', 1000), mk('h', 2000, { result: 'hand', settledPnl: undefined }), mk('b', 3000)];
  const r = live.foldSkim({ pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: 0 }, orders, { everyWin: true });
  assert.strictEqual(r.blocked, null, 'it does not stall the cursor');
  assert.ok(Math.abs(r.cum - 0.4) < 1e-9, 'only the two bot trades counted: ' + r.cum);
  assert.strictEqual(r.appliedTs, 3000, 'and the cursor moved past it');
};

// The detection is the account's own sells only, uses no order endpoint, and is wired into BOTH places an order is settled.
gates.H9 = () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  const body = /async function closedByHand[\s\S]*?\n}\n/.exec(src)[0];
  assert.ok(!/method: "POST"|method: "DELETE"/.test(body), 'it only reads');
  assert.strictEqual((src.match(/await closedByHand\(/g) || []).length, 3, 'settleOpenOrders (twice: the sweep and the repair) and botRisk each ask');
  const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/settleOpenOrders\(\{[^}]*keyId: KALSHI_LIVE_KEY_ID\.value\(\)/.test(idx), 'the scheduled settle sweep passes the key');
  assert.ok(/botRisk\(\{[^}]*keyId, pem \}\)/.test(src), 'the loss stop passes the key');
};

// The page: a hand-closed order is neither a win nor a loss in the pie, has no profit figure in the trade list, and says so.
gates.H10 = () => {
  const counts = new Function(/(function kalshiOutcomeCounts\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html)[1] + '; return kalshiOutcomeCounts;')();
  const c = counts([{ ts: 1, status: 'filled', fillCount: '4', settled: true, result: 'hand', side: 'yes' }, { ts: 2, status: 'filled', fillCount: '4', settled: true, result: 'yes', side: 'yes' }], 0);
  assert.deepStrictEqual([c.won, c.lost, c.other], [1, 0, 1], 'one win, and the hand-closed one is "other", not a loss');
  const pnl = new Function(/(function kalshiTradePnl\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html)[1] + '; return kalshiTradePnl;')();
  assert.strictEqual(pnl({ count: 4, price: '0.93' }, { side: 'yes', settled: true, result: 'hand' }, 'no'), null, 'no held-to-the-end figure for it');
  assert.ok((html.match(/sold by hand/g) || []).length >= 2, 'the orders list and the fills list both say "sold by hand"');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
