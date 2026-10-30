// The nightly order report: read only, behind one secret token, and it never carries an order id or a credential.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const lib = require('../functions/kalshiReportLib');
const gates = {};

const NOW = Date.parse('2026-10-29T00:00:00Z');
const ord = (o) => Object.assign({ ticker: 'KXGOLD15M-26OCT28-T1', side: 'yes', fillCount: 1, avgFill: 0.93, status: 'filled', settled: true, result: 'yes', settledPnl: 0.05, ts: NOW - 3600000, entryLead: '6m', orderId: 'SECRET-ORDER-ID', clientOrderId: 'L1-SECRET' }, o);
const call = async (handler, req) => {
  const out = { code: null, body: null, headers: {} };
  const res = { set: (k, v) => { out.headers[k] = v; }, status: (c) => { out.code = c; return res; }, json: (b) => { out.body = b; } };
  await handler(Object.assign({ method: 'GET', headers: {}, query: {} }, req), res);
  return out;
};
const TOKEN = 'a'.repeat(32);
const handler = (orders, token) => lib.makeReportHandler({ getToken: () => (token === undefined ? TOKEN : token), now: () => NOW, readOrders: async () => orders });

// R1: the report counts wins, losses, net and profit factor the way the page does, and open orders have no result.
gates.R1 = () => {
  const r = lib.buildReport([
    ord({ settledPnl: 0.05 }), ord({ settledPnl: 0.05 }), ord({ settledPnl: -0.9, result: 'no' }),
    ord({ settled: false, settledPnl: null, result: null }), ord({ status: 'no fill', fillCount: 0 }),
    ord({ ts: NOW - 99 * 3600000, settledPnl: -5 }),   // outside the window
  ], NOW, 24, false);
  assert.deepStrictEqual([r.total.filled, r.total.settled, r.total.won, r.total.lost, r.total.open, r.total.noFill], [4, 3, 2, 1, 1, 1]);
  assert.strictEqual(r.total.net, -0.8);
  assert.strictEqual(r.total.profitFactor, 0.11, 'gross win 0.10 over gross loss 0.90');
  assert.strictEqual(lib.buildReport([ord({})], NOW, 24, false).total.profitFactor, null, 'no loss means no profit factor, never infinity');
  assert.deepStrictEqual(Object.keys(r.byMarket), ['KXGOLD15M'], 'split by market');
  assert.ok(r.byEntryLead['6m'], 'and by entry lead');
};

// R2: nothing that identifies an order or the account ever leaves, even in the per-order rows.
gates.R2 = () => {
  const r = lib.buildReport([ord({})], NOW, 24, true);
  const text = JSON.stringify(r);
  assert.ok(!/SECRET-ORDER-ID|L1-SECRET|orderId|clientOrderId/.test(text), 'no order id or client order id');
  assert.strictEqual(r.orders.length, 1);
  assert.deepStrictEqual(Object.keys(r.orders[0]).sort(), ['addon', 'avgFill', 'count', 'depthAtLimit', 'depthLevels', 'entryLead', 'limit', 'orderedCount', 'price', 'result', 'rise3', 'seenAsk', 'seenBid', 'bidSize', 'askSize', 'settledPnl', 'shareOfDepth', 'side', 'smooth', 'status', 'ticker', 'ts'].sort());
  assert.ok(!('orders' in lib.buildReport([ord({})], NOW, 24, false)), 'rows only on request');
};

// R3: closed without the right token, and closed when no token is configured.
gates.R3 = async () => {
  assert.strictEqual((await call(handler([ord({})]), {})).code, 401, 'no header');
  assert.strictEqual((await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + 'b'.repeat(32) } })).code, 401, 'wrong token');
  assert.strictEqual((await call(handler([ord({})], ''), { headers: { authorization: 'Bearer ' } })).code, 401, 'no token configured: closed, never open');
  assert.strictEqual((await call(handler([ord({})], 'short'), { headers: { authorization: 'Bearer short' } })).code, 401, 'a short token is refused');
  const ok = await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + TOKEN } });
  assert.strictEqual(ok.code, 200);
  assert.strictEqual(ok.headers['Cache-Control'], 'no-store');
  const bad = await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + 'b'.repeat(32) } });
  assert.ok(!JSON.stringify(bad.body).includes(TOKEN), 'the secret is never echoed');
};

// R4: GET only; a read failure says nothing about why; the window is bounded.
gates.R4 = async () => {
  assert.strictEqual((await call(handler([]), { method: 'POST', headers: { authorization: 'Bearer ' + TOKEN } })).code, 405);
  const boom = lib.makeReportHandler({ getToken: () => TOKEN, now: () => NOW, readOrders: async () => { throw new Error('Firestore says SECRET internals'); } });
  const r = await call(boom, { headers: { authorization: 'Bearer ' + TOKEN } });
  assert.strictEqual(r.code, 500);
  assert.ok(!/SECRET|Firestore/.test(JSON.stringify(r.body)), 'the error text is not echoed');
  let logged = null;
  const logging = lib.makeReportHandler({ getToken: () => TOKEN, now: () => NOW, readOrders: async () => { throw new Error('boom detail'); }, logError: (e) => { logged = e.message; } });
  await call(logging, { headers: { authorization: 'Bearer ' + TOKEN } });
  assert.strictEqual(logged, 'boom detail', 'the cause reaches the log, not the caller');
  const big = await call(handler([]), { headers: { authorization: 'Bearer ' + TOKEN }, query: { hours: '99999999' } });
  assert.strictEqual(big.body.hours, lib.MAX_HOURS, 'the window is capped');
};

// R5: the function holds no Kalshi key, sends nothing to Kalshi, writes nothing, and the deploy script keeps an existing token.
// R6: the second slot (OICORE) is in the report, apart from L1's figures, which do not change, and added up in allStrategies. Consequence: the research chats can watch OICORE from the nightly report.
gates.R6 = async () => {
  const slot = (o) => Object.assign({ ticker: 'KXBTC15M-26OCT28-T1', side: 'yes', count: 10, fillCount: 10, avgFill: 0.1, status: 'filled', settled: true, result: 'yes', settledPnl: 5, ts: NOW - 3600000, slotId: 'OICORE', strategy: 'SLOT', orderId: 'SECRET-SLOT-ID', clientOrderId: 'SLOT-SECRET' }, o);
  const l1 = [ord({ settledPnl: 0.05 })];
  const r = lib.buildReport(l1, NOW, 24, true, [slot({}), slot({ settledPnl: -1, result: 'no' }), slot({ ts: NOW - 99 * 3600000 })]);
  assert.strictEqual(r.total.net, 0.05, 'L1 figures unchanged by slot orders');
  assert.deepStrictEqual([r.secondSlot.total.settled, r.secondSlot.total.net, Object.keys(r.secondSlot.byStrategy)], [2, 4, ['OICORE']]);
  assert.strictEqual(r.allStrategies.net, 4.05, 'allStrategies adds the two');
  assert.deepStrictEqual(Object.keys(r.byMarket), ['KXGOLD15M'], 'L1 byMarket does not gain slot markets');
  assert.strictEqual(r.slotOrders.length, 2);
  assert.ok(!/SECRET|orderId|clientOrderId/.test(JSON.stringify(r)), 'no ids');
  assert.deepStrictEqual(lib.buildReport(l1, NOW, 24, false).secondSlot.total.filled, 0, 'no slot orders is an empty section, not an error');
  // a failing slot read never blanks the L1 report
  let status = 0, body = null;
  const res = { set() {}, status(c) { status = c; return this; }, json(b) { body = b; } };
  await lib.makeReportHandler({ getToken: () => 'x'.repeat(30), now: () => NOW, readOrders: async () => l1, readSlotOrders: async () => { throw new Error('boom'); } })({ method: 'GET', headers: { authorization: 'Bearer ' + 'x'.repeat(30) }, query: {} }, res);
  assert.ok(status === 200 && body.total.net === 0.05 && body.secondSlot.total.filled === 0, 'L1 report survives a slot read failure');
};
// R7: no-fill rows carry the depth and quote context (the refinement chat's R2), still with no id.
gates.R7 = () => {
  const o = ord({ status: 'no fill', fillCount: 0, count: 9, price: 0.93, limit: 0.94, seen: { bid: 0.92, ask: 0.93, bidSize: 5, askSize: 12, at: 'x' }, depthAtLimit: 12, shareOfDepth: 0.75, depthLevels: 'top', rise3: 0.1, smooth: false, settled: false, settledPnl: null });
  const r = lib.buildReport([o], NOW, 24, true).orders[0];
  assert.deepStrictEqual([r.orderedCount, r.price, r.limit, r.seenBid, r.seenAsk, r.bidSize, r.askSize, r.depthAtLimit, r.shareOfDepth, r.depthLevels, r.rise3, r.smooth], [9, 0.93, 0.94, 0.92, 0.93, 5, 12, 12, 0.75, 'top', 0.1, false]);
  assert.strictEqual(r.count, 0, 'the filled count stays 0 for a no-fill row');
  assert.ok(!/SECRET|orderId|clientOrderId|"at"/.test(JSON.stringify(r)), 'no id and no raw seen object');
  const bare = lib.buildReport([ord({})], NOW, 24, true).orders[0];
  assert.ok(bare.seenBid === null && bare.depthAtLimit === null && bare.smooth === null, 'a field the order lacks is null');
};
gates.R5 = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiReportLib.js'), 'utf8');
  assert.ok(!/KALSHI_LIVE|liveRequest|fetch\(|https?:\/\/|\.set\(\{|\.add\(|\.delete\(|setDoc|runTransaction|firestore|getFirestore/i.test(src.replace(/res\.set\(/g, '').replace(/createHash\("sha256"\)\.update\(/g, '')), 'no key, no network call, no write, and no database access of its own (the order read is passed in)');
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  const fn = idx.slice(idx.indexOf('exports.kalshiNightlyReport'));
  assert.ok(/secrets: \[KALSHI_REPORT_TOKEN\]/.test(fn) && !/KALSHI_LIVE/.test(fn), 'only the report token');
  assert.ok(/ensureDefaultAdminApp\(\); return \(await getFirestore\(\)/.test(fn), 'the default app is ensured before Firestore is read (the first deploy skipped it and every call answered 500)');
  assert.ok(/logError: \(e\) => console\.error/.test(fn) && !/KALSHI_REPORT_TOKEN\.value\(\)[^\n]*console/.test(fn), 'a failure is logged without the token');
  assert.ok(/\.collection\("kalshiLiveOrders"\)\.where\("ts", ">=", sinceMs\)\.get\(\)/.test(fn) && /\.collection\(slotStoreLib\.COLLECTIONS\.SLOT\)\.where\("ts", ">=", sinceMs\)\.get\(\)/.test(fn) && !/\.(set|update|add|delete)\(/.test(fn), 'a read of the bot orders and of the second slot orders, nothing written');
  assert.ok(idx.indexOf('exports.kalshiBookRecorder') < idx.indexOf('exports.kalshiNightlyReport'), 'after the recorder, so the no-order-code slices still cover everything before it');
  const sh = fs.readFileSync(path.join(root, 'functions', 'deploy-report.sh'), 'utf8');
  assert.ok(/functions:secrets:get KALSHI_REPORT_TOKEN/.test(sh) && /keeping it/.test(sh), 'an existing token is kept');
  assert.ok(/ONLY=functions:kalshiNightlyReport\b/.test(sh), 'deploys only this function');
};

(async () => {
  for (const [name, fn] of Object.entries(gates)) { await fn(); console.log('ok   ' + name); }
})().catch((e) => { console.error(e); process.exit(1); });
